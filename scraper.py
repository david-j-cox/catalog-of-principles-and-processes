"""
JEAB PMC Scraper
================
Fetches all JEAB articles available on PubMed Central (v.1 1958 – v.98 2012)
and outputs them as jeab_scraped.json in the data.json schema.

Usage:
    python scraper.py

Outputs:
    jeab_scraped.json   — scraped entries ready for review/merge
    cache/xml/          — cached raw XML (so re-runs don't re-fetch)

Requires:
    pip install requests python-dotenv lxml
"""

import json
import os
import re
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv()
API_KEY = os.getenv("NCBI_API_KEY", "")

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
JEAB_NLMID = "0203727"           # NLM Unique ID for JEAB
CACHE_DIR = Path("cache/xml")
OUTPUT_FILE = Path("jeab_scraped.json")
BATCH_SIZE = 100                 # IDs per efetch request
DELAY = 0.11 if API_KEY else 0.4 # seconds between requests (10/s with key, 3/s without)

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── NCBI helpers ──────────────────────────────────────────────────────────────

def ncbi_get(endpoint, params):
    """GET from NCBI E-utilities with API key and polite delay."""
    if API_KEY:
        params["api_key"] = API_KEY
    time.sleep(DELAY)
    r = requests.get(f"{EUTILS}/{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r


def fetch_all_pmcids():
    """Return every PMC ID for JEAB articles."""
    print("Fetching JEAB article list from PMC...")

    # First call: get total count
    r = ncbi_get("esearch.fcgi", {
        "db": "pmc",
        "term": f"{JEAB_NLMID}[nlmid]",
        "retmax": 0,
        "retmode": "json",
    })
    total = int(r.json()["esearchresult"]["count"])
    print(f"  Total articles found: {total}")

    pmcids = []
    for start in range(0, total, 500):
        r = ncbi_get("esearch.fcgi", {
            "db": "pmc",
            "term": f"{JEAB_NLMID}[nlmid]",
            "retstart": start,
            "retmax": 500,
            "retmode": "json",
        })
        batch = r.json()["esearchresult"]["idlist"]
        pmcids.extend(batch)
        print(f"  Retrieved IDs {start + 1}–{start + len(batch)}")

    return pmcids


def fetch_xml_batch(pmcids):
    """Fetch full-text JATS XML for a batch of PMCIDs. Returns raw XML string."""
    r = ncbi_get("efetch.fcgi", {
        "db": "pmc",
        "id": ",".join(pmcids),
        "rettype": "xml",
        "retmode": "xml",
    })
    return r.text


# ── JATS XML parsing ──────────────────────────────────────────────────────────

# JATS namespace map
NS = {
    "mml": "http://www.w3.org/1998/Math/MathML",
    "xlink": "http://www.w3.org/1999/xlink",
}

def _text(el):
    """Recursively collect all text inside an element."""
    return "".join(el.itertext()).strip()


def _find(el, *tags):
    """Try multiple tag names, return first match or None."""
    for tag in tags:
        found = el.find(tag)
        if found is not None:
            return found
    return None


def parse_authors(article_meta):
    authors = []
    for contrib in article_meta.findall(".//contrib[@contrib-type='author']"):
        surname = contrib.findtext("name/surname", "").strip()
        given = contrib.findtext("name/given-names", "").strip()
        if surname:
            name = f"{surname}, {given[0]}." if given else surname
            authors.append(name)
    return authors


def parse_equations(article):
    """
    Extract display (block) equations from <disp-formula> elements.
    Preference order:
      1. <tex-math> LaTeX string (best for rendering)
      2. Text content of <mml:math> (human-readable, Claude-refinable later)
      3. Plain text of the whole formula element
    Returns a list of strings.
    """
    equations = []
    for formula in article.findall(".//disp-formula"):
        # 1. Try TeX
        tex = formula.findtext("tex-math")
        if tex:
            tex = re.sub(r"\\begin\{document\}|\\end\{document\}", "", tex).strip()
            if tex:
                equations.append(tex)
            continue

        # 2. Try MathML text content (readable form, e.g. "B = R / (R + Re)")
        mml = formula.find("mml:math", NS)
        if mml is None:
            # Namespace may be serialized differently after caching
            mml = formula.find("{http://www.w3.org/1998/Math/MathML}math")
        if mml is not None:
            txt = _text(mml).strip()
            # Strip equation labels like "(1)" at the start
            txt = re.sub(r"^\(\d+\)\s*", "", txt).strip()
            if txt:
                equations.append(txt)
            continue

        # 3. Plain text fallback
        txt = _text(formula).strip()
        txt = re.sub(r"^\(\d+\)\s*", "", txt).strip()
        if txt:
            equations.append(txt)

    return equations


def parse_article(article_el):
    """Parse a single <article> JATS element into a data.json entry dict."""
    meta = article_el.find("front/article-meta")
    if meta is None:
        return None

    # ── Identifiers ───────────────────────────────────────────────────────────
    doi = meta.findtext("article-id[@pub-id-type='doi']", "").strip()
    # 'pmcaid' holds the bare numeric ID; fallback: strip 'PMC' from 'pmcid'
    pmcid = meta.findtext("article-id[@pub-id-type='pmcaid']", "").strip()
    if not pmcid:
        pmcid = meta.findtext("article-id[@pub-id-type='pmcid']", "").strip().replace("PMC", "")
    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/" if pmcid else (
          f"https://doi.org/{doi}" if doi else "")

    # ── Bibliographic ─────────────────────────────────────────────────────────
    title_el = meta.find(".//article-title")
    title = _text(title_el) if title_el is not None else ""

    authors = parse_authors(meta)

    year_str = (meta.findtext("pub-date[@pub-type='ppub']/year")
                or meta.findtext("pub-date[@pub-type='epub']/year")
                or meta.findtext("pub-date/year")
                or "")
    year = int(year_str) if year_str.isdigit() else None

    volume_str = meta.findtext("volume", "").strip()
    volume = int(volume_str) if volume_str.isdigit() else volume_str or None

    issue_str = meta.findtext("issue", "").strip()
    issue = int(issue_str) if issue_str.isdigit() else issue_str or None

    fpage = meta.findtext("fpage", "").strip()
    lpage = meta.findtext("lpage", "").strip()
    pages = f"{fpage}-{lpage}" if fpage and lpage else fpage or ""

    # ── Abstract ──────────────────────────────────────────────────────────────
    abstract_el = meta.find("abstract")
    abstract = _text(abstract_el).strip() if abstract_el is not None else ""
    # Discard OCR artifacts from scanned articles (too short or just image refs)
    if len(abstract) < 80 or re.match(r"^(Images?|Fig\.|Figure)", abstract):
        abstract = ""

    # ── Equations ─────────────────────────────────────────────────────────────
    equations = parse_equations(article_el)

    return {
        "title": title,
        "journal": "JEAB",
        "year": year,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "authors": authors,
        "doi": doi,
        "url": url,
        "process": [],                        # filled in later
        "static-equation": equations,
        "static-equation-definitions": "",    # filled in later
        "recursive-equation": "",
        "recursive-equation-definitions": "",
        "abstract": abstract,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not API_KEY:
        print("WARNING: No NCBI_API_KEY found in .env — rate limited to 3 req/s")

    # 1. Get all PMCIDs
    pmcids = fetch_all_pmcids()
    print(f"\nTotal PMCIDs to fetch: {len(pmcids)}")

    # 2. Fetch XML in batches, using cache where available
    entries = []
    uncached = [p for p in pmcids if not (CACHE_DIR / f"{p}.xml").exists()]
    cached   = [p for p in pmcids if     (CACHE_DIR / f"{p}.xml").exists()]

    print(f"  Cached: {len(cached)}  |  To fetch: {len(uncached)}")

    # Fetch uncached in batches
    for i in range(0, len(uncached), BATCH_SIZE):
        batch = uncached[i:i + BATCH_SIZE]
        print(f"  Fetching batch {i // BATCH_SIZE + 1} "
              f"({i + 1}–{min(i + BATCH_SIZE, len(uncached))} of {len(uncached)})...")
        try:
            xml_text = fetch_xml_batch(batch)
            # Cache individual articles from the batch response
            root = ET.fromstring(xml_text.encode("utf-8"))
            for article_el in root.findall(".//article"):
                pmcid = article_el.findtext(".//article-id[@pub-id-type='pmcaid']", "")
                if not pmcid:
                    pmcid = article_el.findtext(".//article-id[@pub-id-type='pmcid']", "").replace("PMC", "")
                if pmcid:
                    cache_path = CACHE_DIR / f"{pmcid}.xml"
                    cache_path.write_text(
                        ET.tostring(article_el, encoding="unicode"), encoding="utf-8"
                    )
        except Exception as e:
            print(f"  ERROR on batch starting {i}: {e}")
            continue

    # 3. Parse all cached XMLs
    print(f"\nParsing {len(pmcids)} articles...")
    skipped = 0
    for pmcid in pmcids:
        cache_path = CACHE_DIR / f"{pmcid}.xml"
        if not cache_path.exists():
            skipped += 1
            continue
        try:
            article_el = ET.fromstring(cache_path.read_bytes())
            entry = parse_article(article_el)
            if entry and entry["title"]:
                entries.append(entry)
        except Exception as e:
            print(f"  Parse error PMC{pmcid}: {e}")
            skipped += 1

    # 4. Sort by year, volume, pages
    def sort_key(e):
        try:
            page = int(str(e.get("pages", "0")).split("-")[0])
        except (ValueError, AttributeError):
            page = 0
        return (e.get("year") or 9999, e.get("volume") or 9999, page)

    entries.sort(key=sort_key)

    # 5. Write output
    OUTPUT_FILE.write_text(json.dumps(entries, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone. {len(entries)} entries written to {OUTPUT_FILE}")
    print(f"Skipped: {skipped}")
    print(f"Articles with equations: {sum(1 for e in entries if e['static-equation'])}")


if __name__ == "__main__":
    main()
