"""
extract_equations.py
====================
Uses GPT-4o-mini to extract LaTeX equations from cached JEAB article XMLs
for entries in data.json that are missing a static-equation.

Usage:
    python extract_equations.py               # process all eligible entries
    python extract_equations.py --limit 50    # process at most 50 entries
    python extract_equations.py --test        # dry-run: print what would be sent, no API calls

Outputs:
    equations_staged.json   — staged results for human review before merging

After reviewing, run merge_equations.py to apply results to data.json.

Requires:
    pip install openai python-dotenv
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from xml.etree import ElementTree as ET

from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DATA_FILE   = Path("data.json")
CACHE_DIR   = Path("cache/xml")
STAGED_FILE = Path("equations_staged.json")

# Keywords that suggest an article contains quantitative equations worth extracting
EQUATION_KEYWORDS = [
    "equation", "formula", "model", "function", "law", "hyperbolic", "exponential",
    "matching law", "ratio", "rate", "parameter", "exponent", "logarithm",
    "linear", "nonlinear", "regression", "fit", "curve", "slope", "intercept",
    "vi schedule", "vr schedule", "concurrent", "reinforcement rate", "response rate",
    "delay discount", "probability discount", "subjective value", "utility",
    "generalization gradient", "power function", "sigmoid", "logistic",
]

SYSTEM_PROMPT = """\
You are an expert in behavioral science and mathematical modeling. \
Your task is to extract mathematical equations that are EXPLICITLY WRITTEN OUT in the text \
of a Journal of the Experimental Analysis of Behavior (JEAB) article.

CRITICAL RULES:
1. Return ONLY valid JSON — no markdown, no code fences, no explanation outside JSON.
2. Only extract equations that are LITERALLY PRESENT in the text (e.g., "V = A/(1+kD)" or
   "the equation B = aR^b / (aR^b + bR^a)"). Do NOT invent, infer, or guess equations.
3. If you find a clearly written quantitative equation, return:
   {
     "static_equation": "<LaTeX string of the main equation>",
     "definitions": "<semicolon-separated definitions of each variable, e.g. V = subjective value; A = amount>"
   }
4. If there are multiple distinct equations central to the article, join them with "; ".
5. If the text does NOT explicitly write out a mathematical equation — even if it describes
   quantitative relationships in words — return:
   {
     "static_equation": null,
     "definitions": null
   }
6. Use standard LaTeX notation (e.g. \\frac{a}{b}, x^{n}, \\cdot). Keep equations concise.
7. Do NOT include equation numbering labels like "(1)" in the output.
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_pmcid(url: str) -> str | None:
    """Return numeric PMCID from a PMC URL, e.g. '.../PMC1234567/' → '1234567'."""
    m = re.search(r'PMC(\d+)', str(url), re.IGNORECASE)
    return m.group(1) if m else None


def keyword_screen(entry: dict) -> bool:
    """Return True if title/abstract suggest the article likely contains equations."""
    text = " ".join([
        str(entry.get("title", "")),
        str(entry.get("abstract", "")),
    ]).lower()
    return any(kw in text for kw in EQUATION_KEYWORDS)


def _itertext(el) -> str:
    """Recursively collect text content of an XML element."""
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(_itertext(child))
        if child.tail:
            parts.append(child.tail)
    return " ".join(parts)


def extract_body_text(pmcid: str) -> tuple[str | None, str]:
    """
    Parse cached XML and return (text_excerpt, source) where source is
    'body', 'abstract', or 'none'.

    Priority:
    1. Body paragraphs containing formula elements (best)
    2. Full body text (first 4000 chars, if no formula paragraphs)
    3. Abstract only (fallback when no body is available)
    """
    xml_path = CACHE_DIR / f"{pmcid}.xml"
    if not xml_path.exists():
        return None, "none"

    try:
        tree = ET.parse(xml_path)
    except ET.ParseError:
        return None, "none"

    root = tree.getroot()
    body = root.find(".//body")

    if body is not None and len(list(body.iter())) > 5:
        # Collect paragraphs that contain formula/math elements
        formula_tags = {"disp-formula", "inline-formula", "tex-math"}
        collected = []

        for para in body.iter("p"):
            has_formula = any(
                child.tag.split("}")[-1] in formula_tags
                for child in para.iter()
            )
            if has_formula:
                collected.append(_itertext(para).strip())

        # Also grab standalone disp-formula elements
        for formula in body.findall(".//disp-formula"):
            txt = _itertext(formula).strip()
            txt = re.sub(r"^\(\d+\)\s*", "", txt).strip()
            if txt and txt not in " ".join(collected):
                collected.append(f"[FORMULA: {txt}]")

        if collected:
            return "\n\n".join(collected)[:6000], "body"

        # No formula paragraphs — fall back to first 4000 chars of body
        full = _itertext(body).strip()
        if full:
            return full[:4000], "body"

    # No body — try abstract from XML or from data.json entry (caller passes it)
    abstract_el = root.find(".//abstract")
    if abstract_el is not None:
        txt = _itertext(abstract_el).strip()
        if txt:
            return txt[:3000], "abstract"

    return None, "none"


def call_gpt(body_text: str, title: str, client) -> dict:
    """Call GPT-4o-mini and return parsed JSON result."""
    user_msg = f"Article title: {title}\n\nBody text excerpt:\n{body_text}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0,
        max_tokens=512,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract equations from JEAB articles via GPT-4o-mini")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max number of API calls to make (0 = no limit)")
    parser.add_argument("--test", action="store_true",
                        help="Dry run: print candidates and body text, no API calls")
    args = parser.parse_args()

    # ── Load data ──────────────────────────────────────────────────────────────
    with open(DATA_FILE) as f:
        data = json.load(f)

    # ── Load already-staged results (for resumability) ─────────────────────────
    if STAGED_FILE.exists():
        with open(STAGED_FILE) as f:
            staged: list[dict] = json.load(f)
    else:
        staged = []

    already_done = {s["pmcid"] for s in staged}
    print(f"Already staged: {len(already_done)} entries")

    # ── Build candidate list ───────────────────────────────────────────────────
    candidates = []
    for entry in data:
        pmcid = extract_pmcid(entry.get("url", ""))
        if not pmcid:
            continue

        eq = entry.get("static-equation")
        has_eq = bool(eq) and eq != [] and eq != ""
        if has_eq:
            continue  # already has an equation

        if pmcid in already_done:
            continue  # already processed in a previous run

        if not (CACHE_DIR / f"{pmcid}.xml").exists():
            continue  # no cached XML

        candidates.append((entry, pmcid))

    # Pre-filter: only keep entries that have some text to send to GPT
    def has_text(entry_pmcid):
        entry, pmcid = entry_pmcid
        _, source = extract_body_text(pmcid)
        if source in ("body", "abstract"):
            return True
        # Check data.json abstract as fallback
        abstract = str(entry.get("abstract", "")).strip()
        return len(abstract) > 50

    print("Pre-filtering candidates for text availability...")
    candidates = [c for c in candidates if has_text(c)]
    print(f"Candidates with extractable text: {len(candidates)}")

    # Order candidates: body-text first, then keyword-matched abstract-only, then rest
    def has_body(entry_pmcid):
        _, pmcid = entry_pmcid
        xml_path = CACHE_DIR / f"{pmcid}.xml"
        if not xml_path.exists():
            return False
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            body = root.find(".//body")
            return body is not None and len(list(body.iter())) > 5
        except Exception:
            return False

    body_text_candidates   = [c for c in candidates if has_body(c)]
    abstract_only_keyword  = [c for c in candidates if not has_body(c) and keyword_screen(c[0])]
    abstract_only_other    = [c for c in candidates if not has_body(c) and not keyword_screen(c[0])]
    ordered = body_text_candidates + abstract_only_keyword + abstract_only_other

    total_eligible = len(ordered)
    limit = args.limit if args.limit > 0 else total_eligible
    to_process = ordered[:limit]

    print(f"Eligible candidates: {total_eligible} "
          f"({len(body_text_candidates)} body-text, "
          f"{len(abstract_only_keyword)} abstract+keyword, "
          f"{len(abstract_only_other)} abstract-only)")
    print(f"Will process: {len(to_process)}")

    if args.test:
        print("\n--- TEST MODE: showing first 3 candidates ---")
        for entry, pmcid in to_process[:3]:
            print(f"\nTitle: {entry.get('title')}")
            print(f"PMCID: {pmcid}")
            text, source = extract_body_text(pmcid)
            print(f"Source: {source} | Length: {len(text) if text else 0} chars")
            print((text or "")[:500])
            print("---")
        return

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    # ── Set up OpenAI client ───────────────────────────────────────────────────
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=OPENAI_API_KEY)

    # ── Process entries ────────────────────────────────────────────────────────
    processed = 0
    skipped_no_body = 0
    errors = 0

    for i, (entry, pmcid) in enumerate(to_process):
        text, source = extract_body_text(pmcid)

        # Fall back to data.json abstract if XML had none
        if not text or source == "none":
            data_abstract = str(entry.get("abstract", "")).strip()
            if data_abstract and len(data_abstract) > 50:
                text = data_abstract[:3000]
                source = "abstract"

        # For abstract source, prefer the richer of XML abstract vs data.json abstract
        if source == "abstract":
            data_abstract = str(entry.get("abstract", "")).strip()
            if data_abstract and len(data_abstract) > len(text or ""):
                text = data_abstract[:3000]

        if not text:
            skipped_no_body += 1
            continue

        try:
            result = call_gpt(text, entry.get("title", ""), client)
        except Exception as e:
            print(f"  ERROR on PMCID {pmcid}: {e}")
            errors += 1
            # Save progress so far before continuing
            with open(STAGED_FILE, "w") as f:
                json.dump(staged, f, indent=2)
            time.sleep(2)
            continue

        staged_entry = {
            "pmcid": pmcid,
            "title": entry.get("title"),
            "year": entry.get("year"),
            "source": source,
            "static_equation": result.get("static_equation"),
            "definitions": result.get("definitions"),
        }
        staged.append(staged_entry)
        processed += 1

        eq_preview = (result.get("static_equation") or "null")[:60]
        print(f"[{i+1}/{len(to_process)}] PMCID {pmcid} ({source}): {eq_preview}")
        time.sleep(0.05)  # polite rate limit (~20 req/s max)

        # Save every 10 entries
        if processed % 10 == 0:
            with open(STAGED_FILE, "w") as f:
                json.dump(staged, f, indent=2)
            print(f"  → saved {len(staged)} staged entries")

    # Final save
    with open(STAGED_FILE, "w") as f:
        json.dump(staged, f, indent=2)

    print(f"\nDone.")
    print(f"  Processed:         {processed}")
    print(f"  Skipped (no body): {skipped_no_body}")
    print(f"  Errors:            {errors}")
    print(f"  Total staged:      {len(staged)}")
    print(f"  Staged file:       {STAGED_FILE}")


if __name__ == "__main__":
    main()
