"""
CrossRef Scraper for Behavioral Process Catalog
=================================================
Fetches article metadata from CrossRef API for supported journals.
Free API, no authentication required. Uses polite pool via mailto header.

Usage:
    python scrapers/crossref_scraper.py --journal BP
    python scrapers/crossref_scraper.py --journal JEP:ALC
    python scrapers/crossref_scraper.py --journal JEAB
    python scrapers/crossref_scraper.py --journal all

Output:
    scrapers/output/<journal_key>_crossref.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

# ── Journal Configuration ────────────────────────────────────────────────────
# Maps journal keys to their CrossRef ISSNs and display info.
# CrossRef uses ISSNs to identify journals; some journals have multiple
# (print, electronic, historical name changes).

JOURNALS = {
    "JEAB": {
        "name": "Journal of the Experimental Analysis of Behavior",
        "issns": ["0022-5002", "1938-3711"],
    },
    "BP": {
        "name": "Behavioural Processes",
        "issns": ["0376-6357"],
    },
    "JEP:ALC": {
        "name": "Journal of Experimental Psychology: Animal Learning and Cognition",
        # Covers both current name and former "Animal Behavior Processes" (1975-2014)
        "issns": [
            "2329-8456",  # JEP:ALC electronic (2015-present)
            "2329-8464",  # JEP:ALC print (2015-present)
            "0097-7403",  # JEP:ABP print (1975-2014)
            "1939-2184",  # JEP:ABP electronic (1975-2014)
        ],
    },
}

# ── CrossRef API settings ────────────────────────────────────────────────────
CROSSREF_BASE = "https://api.crossref.org/works"
MAILTO = "david.cox@endicott.edu"  # polite pool for faster rate limits
ROWS_PER_PAGE = 1000
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────────────────

def crossref_headers():
    return {
        "User-Agent": f"BehavioralProcessCatalog/1.0 (mailto:{MAILTO})",
        "Accept": "application/json",
    }


def fetch_page(issn, cursor="*"):
    """Fetch one page of results from CrossRef for a given ISSN."""
    params = {
        "filter": f"issn:{issn}",
        "rows": ROWS_PER_PAGE,
        "cursor": cursor,
    }
    resp = requests.get(
        CROSSREF_BASE,
        params=params,
        headers=crossref_headers(),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["message"]


def extract_year(item):
    """Extract publication year from CrossRef date-parts."""
    for field in ("published-print", "published-online"):
        date_info = item.get(field)
        if date_info and "date-parts" in date_info:
            parts = date_info["date-parts"][0]
            if parts and parts[0]:
                return int(parts[0])
    return None


def extract_authors(item):
    """Convert CrossRef author list to 'Surname, I.' format."""
    authors = []
    for author in item.get("author", []):
        family = author.get("family", "").strip()
        given = author.get("given", "").strip()
        if family:
            if given:
                # Use first initial
                initials = ". ".join(g[0] for g in given.split() if g) + "."
                authors.append(f"{family}, {initials}")
            else:
                authors.append(family)
    return authors


def transform_item(item, journal_key):
    """Transform a CrossRef work item into a data.json entry."""
    title_list = item.get("title", [])
    title = title_list[0] if title_list else ""
    if not title:
        return None

    doi = item.get("DOI", "")
    url = f"https://doi.org/{doi}" if doi else ""

    year = extract_year(item)
    volume = item.get("volume", "")
    issue = item.get("issue", "")
    pages = item.get("page", "")
    authors = extract_authors(item)

    # CrossRef abstracts are in JATS XML; strip tags for plain text
    abstract_raw = item.get("abstract", "")
    if abstract_raw:
        import re
        abstract = re.sub(r"<[^>]+>", "", abstract_raw).strip()
    else:
        abstract = ""

    # Parse volume/issue to int if possible
    try:
        volume = int(volume) if volume else None
    except (ValueError, TypeError):
        volume = volume or None

    try:
        issue = int(issue) if issue else None
    except (ValueError, TypeError):
        issue = issue or None

    return {
        "title": title,
        "journal": journal_key,
        "year": year,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "authors": authors,
        "doi": doi,
        "url": url,
        "process": [],
        "static-equation": "",
        "static-equation-definitions": "",
        "recursive-equation": "",
        "recursive-equation-definitions": "",
        "abstract": abstract,
    }


# ── Main scrape logic ────────────────────────────────────────────────────────

def scrape_journal(journal_key):
    """Scrape all articles for a journal from CrossRef, deduplicating across ISSNs."""
    config = JOURNALS[journal_key]
    print(f"\nScraping {config['name']} ({journal_key})")
    print(f"  ISSNs: {', '.join(config['issns'])}")

    all_entries = {}  # DOI → entry (dedup across ISSNs)

    for issn in config["issns"]:
        print(f"\n  Fetching ISSN {issn}...")
        cursor = "*"
        page_num = 0
        total_items = None

        while True:
            page_num += 1
            try:
                message = fetch_page(issn, cursor)
            except Exception as e:
                print(f"    ERROR on page {page_num}: {type(e).__name__}: {e}")
                # Retry once after a longer pause
                time.sleep(5)
                try:
                    message = fetch_page(issn, cursor)
                except Exception as e2:
                    print(f"    RETRY FAILED on page {page_num}: {e2}")
                    break

            if total_items is None:
                total_items = message.get("total-results", 0)
                print(f"    Total results for this ISSN: {total_items}")

            items = message.get("items", [])
            if not items:
                print(f"    Page {page_num}: empty items list, stopping")
                break

            for item in items:
                try:
                    entry = transform_item(item, journal_key)
                    if entry and entry.get("doi"):
                        all_entries[entry["doi"]] = entry
                except Exception as e:
                    # Skip individual items that fail to parse
                    continue

            fetched_so_far = len(all_entries)
            print(f"    Page {page_num}: got {len(items)} items "
                  f"(total unique so far: {fetched_so_far})")

            # Advance cursor (CrossRef may return the same cursor value
            # while still paginating — stop only on empty items, not cursor equality)
            next_cursor = message.get("next-cursor")
            if next_cursor:
                cursor = next_cursor

            time.sleep(DELAY_BETWEEN_REQUESTS)

    entries = list(all_entries.values())

    # Sort by year, volume, first page number
    def sort_key(e):
        try:
            page = int(str(e.get("pages", "0")).split("-")[0])
        except (ValueError, AttributeError):
            page = 0
        return (e.get("year") or 9999, e.get("volume") or 9999, page)

    entries.sort(key=sort_key)

    # Write output
    output_file = OUTPUT_DIR / f"{journal_key.replace(':', '_')}_crossref.json"
    output_file.write_text(
        json.dumps(entries, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\n  Done: {len(entries)} entries → {output_file}")
    return entries


def main():
    parser = argparse.ArgumentParser(
        description="Scrape journal metadata from CrossRef API"
    )
    parser.add_argument(
        "--journal",
        required=True,
        choices=list(JOURNALS.keys()) + ["all"],
        help="Journal to scrape (or 'all' for all journals)",
    )
    args = parser.parse_args()

    if args.journal == "all":
        for key in JOURNALS:
            scrape_journal(key)
    else:
        scrape_journal(args.journal)


if __name__ == "__main__":
    main()
