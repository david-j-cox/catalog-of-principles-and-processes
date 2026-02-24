"""
judge_equations.py
==================
LLM-as-judge pass over equations_staged.json.

For each staged entry with a non-null static_equation, a second GPT-4o-mini
call evaluates whether the equation:
  1. Is actually present in the source text (not hallucinated)
  2. Is the PRIMARY mathematical contribution of the article
  3. Is correctly formatted as LaTeX
  4. Has accurate variable definitions

Outputs:
    equations_judged.json   — staged entries annotated with judgment fields

The merge script (merge_equations.py) can then be told to only merge
entries where approved == true.

Usage:
    python judge_equations.py              # judge all non-null staged entries
    python judge_equations.py --test       # dry-run: print what would be sent
    python judge_equations.py --limit 50   # judge at most 50 entries

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

STAGED_FILE = Path("equations_staged.json")
JUDGED_FILE = Path("equations_judged.json")
CACHE_DIR   = Path("cache/xml")
DATA_FILE   = Path("data.json")

JUDGE_PROMPT = """\
You are a rigorous peer reviewer for behavioral science journals. You are given:
  1. An article title
  2. The source text from the article (body excerpt or abstract)
  3. A candidate equation extracted by an automated system, plus variable definitions

Your job is to judge the quality of this extraction AND, when the extraction is wrong
or incomplete, provide your own corrected version directly from the source text.

Return ONLY valid JSON with these fields:

{
  "approved": true or false,
  "confidence": "high", "medium", or "low",
  "is_primary": true or false,
  "latex_valid": true or false,
  "notes": "one sentence explanation — especially important when approved is false",
  "suggested_equation": null or "<corrected LaTeX equation>",
  "suggested_definitions": null or "<corrected semicolon-separated variable definitions>"
}

Evaluation criteria:
- approved: true ONLY if the equation is (a) literally present in the source text,
  (b) is a genuine mathematical relationship (not just a statistic like R²=.82),
  and (c) represents a key quantitative model in the article.
- is_primary: true if this is the main equation the article tests or proposes
  (vs. a secondary/peripheral equation).
- latex_valid: true if the LaTeX renders correctly (balanced braces, valid commands).
- confidence: your confidence that this is a correct, useful extraction.
- notes: be specific — cite what's wrong if approved is false.
- suggested_equation: if approved is false but there IS a valid equation in the text
  that the extractor missed or got wrong, provide the correct LaTeX here.
  If approved is true but latex_valid is false, provide the corrected LaTeX.
  Set to null if the article genuinely has no extractable equation.
- suggested_definitions: companion definitions for suggested_equation, or null.

Common reasons to reject (approved=false):
- Equation not literally in the provided text (hallucinated)
- Just a fit statistic (R²=.82, slope=1.08) rather than a behavioral model
- Descriptive arithmetic, not a reusable quantitative law
- Only a variable name or constant, not a full equation
- Wrong equation extracted when a better one exists in the text
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _itertext(el) -> str:
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(_itertext(child))
        if child.tail:
            parts.append(child.tail)
    return " ".join(parts)


def get_source_text(pmcid: str, source_hint: str, data_entry: dict | None) -> str:
    """Re-fetch the same text that was used during extraction."""
    xml_path = CACHE_DIR / f"{pmcid}.xml"

    if xml_path.exists():
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            body = root.find(".//body")

            if body is not None and len(list(body.iter())) > 5:
                formula_tags = {"disp-formula", "inline-formula", "tex-math"}
                collected = []
                for para in body.iter("p"):
                    if any(c.tag.split("}")[-1] in formula_tags for c in para.iter()):
                        collected.append(_itertext(para).strip())
                if collected:
                    return "\n\n".join(collected)[:6000]
                full = _itertext(body).strip()
                if full:
                    return full[:4000]

            abstract_el = root.find(".//abstract")
            if abstract_el is not None:
                txt = _itertext(abstract_el).strip()
                if txt:
                    return txt[:3000]
        except ET.ParseError:
            pass

    # Fall back to data.json abstract
    if data_entry:
        abstract = str(data_entry.get("abstract", "")).strip()
        if abstract:
            return abstract[:3000]

    return ""


def call_judge(title: str, source_text: str, equation: str, definitions: str,
               client) -> dict:
    user_msg = (
        f"Article title: {title}\n\n"
        f"Source text:\n{source_text}\n\n"
        f"Extracted equation: {equation}\n"
        f"Definitions: {definitions or '(none provided)'}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0,
        max_tokens=256,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LLM-as-judge for extracted equations")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max number of judge calls (0 = all)")
    parser.add_argument("--test", action="store_true",
                        help="Dry run: print what would be sent, no API calls")
    args = parser.parse_args()

    # ── Load staged extractions ────────────────────────────────────────────────
    if not STAGED_FILE.exists():
        print(f"ERROR: {STAGED_FILE} not found. Run extract_equations.py first.")
        sys.exit(1)

    with open(STAGED_FILE) as f:
        staged: list[dict] = json.load(f)

    # Only judge entries with a non-null equation
    to_judge = [s for s in staged if s.get("static_equation")]
    print(f"Staged entries with equations: {len(to_judge)} / {len(staged)} total")

    # ── Load already-judged results (for resumability) ─────────────────────────
    if JUDGED_FILE.exists():
        with open(JUDGED_FILE) as f:
            judged: list[dict] = json.load(f)
    else:
        judged = []

    already_judged = {j["pmcid"] for j in judged}
    print(f"Already judged: {len(already_judged)}")

    to_judge = [s for s in to_judge if s["pmcid"] not in already_judged]
    if args.limit > 0:
        to_judge = to_judge[:args.limit]

    print(f"Will judge: {len(to_judge)}")

    # ── Load data.json for abstract fallback ──────────────────────────────────
    data_by_pmcid: dict[str, dict] = {}
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            data = json.load(f)
        for entry in data:
            url = entry.get("url", "")
            m = re.search(r'PMC(\d+)', str(url), re.IGNORECASE)
            if m:
                data_by_pmcid[m.group(1)] = entry

    if args.test:
        print("\n--- TEST MODE: first 3 to judge ---")
        for s in to_judge[:3]:
            pmcid = s["pmcid"]
            text = get_source_text(pmcid, s.get("source",""), data_by_pmcid.get(pmcid))
            print(f"\nTitle:    {s.get('title','')[:70]}")
            print(f"Equation: {s.get('static_equation','')}")
            print(f"Defs:     {(s.get('definitions') or '')[:80]}")
            print(f"Text ({len(text)} chars): {text[:200]}...")
            print("---")
        return

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=OPENAI_API_KEY)

    # ── Judge each entry ───────────────────────────────────────────────────────
    processed = 0
    errors = 0

    for i, s in enumerate(to_judge):
        pmcid = s["pmcid"]
        source_text = get_source_text(pmcid, s.get("source", ""), data_by_pmcid.get(pmcid))

        try:
            judgment = call_judge(
                title       = s.get("title", ""),
                source_text = source_text,
                equation    = s.get("static_equation", ""),
                definitions = s.get("definitions", ""),
                client      = client,
            )
        except Exception as e:
            print(f"  ERROR on PMCID {pmcid}: {e}")
            errors += 1
            with open(JUDGED_FILE, "w") as f:
                json.dump(judged, f, indent=2)
            time.sleep(2)
            continue

        judged_entry = {**s, "judgment": judgment}
        judged.append(judged_entry)
        processed += 1

        approved = judgment.get("approved", False)
        confidence = judgment.get("confidence", "?")
        suggestion = judgment.get("suggested_equation")
        if approved:
            status = "✓ APPROVED"
        elif suggestion:
            status = "~ CORRECTED"
        else:
            status = "✗ REJECTED"
        print(f"[{i+1}/{len(to_judge)}] PMCID {pmcid} [{confidence}] {status}: "
              f"{judgment.get('notes','')[:60]}")
        if suggestion and not approved:
            print(f"    → suggestion: {suggestion[:70]}")

        if processed % 10 == 0:
            with open(JUDGED_FILE, "w") as f:
                json.dump(judged, f, indent=2)
            print(f"  → saved {len(judged)} judged entries")

        time.sleep(0.05)

    # Final save
    with open(JUDGED_FILE, "w") as f:
        json.dump(judged, f, indent=2)

    # Summary stats
    approved_count = sum(1 for j in judged if j.get("judgment", {}).get("approved"))
    print(f"\nDone.")
    print(f"  Judged this run:  {processed}")
    print(f"  Errors:           {errors}")
    print(f"  Total judged:     {len(judged)}")
    print(f"  Approved:         {approved_count} / {len(judged)}")
    print(f"  Rejected:         {len(judged) - approved_count} / {len(judged)}")
    print(f"  Output:           {JUDGED_FILE}")


if __name__ == "__main__":
    main()
