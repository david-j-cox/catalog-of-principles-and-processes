"""
Backfill Abstracts for Behavioral Process Catalog
==================================================
Two-pass pipeline to fill missing abstracts using free APIs:
  Pass 1: OpenAlex (batch DOI lookups, inverted-index → plaintext)
  Pass 2: Semantic Scholar (single DOI gap-fill, plaintext abstracts)

Usage:
    python scrapers/backfill_abstracts.py                    # all missing
    python scrapers/backfill_abstracts.py --journal BP       # just BP
    python scrapers/backfill_abstracts.py --source openalex  # OpenAlex only
    python scrapers/backfill_abstracts.py --source s2        # Semantic Scholar only
    python scrapers/backfill_abstracts.py --dry-run          # report counts only
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

DATA_FILE = Path(__file__).resolve().parent.parent / "data.json"
MAILTO = "david.cox@endicott.edu"

# ── Rate limits ──────────────────────────────────────────────────────────────
OPENALEX_DELAY = 0.1       # seconds between OpenAlex requests
S2_DELAY = 1.0             # seconds between Semantic Scholar batch requests
OPENALEX_BATCH_SIZE = 50   # max DOIs per OpenAlex filter query
S2_BATCH_SIZE = 100        # DOIs per Semantic Scholar batch (max 500)
SAVE_EVERY = 500           # intermediate save interval (entries processed)


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_data():
    """Load and return the full data.json list."""
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    """Write data back to data.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")


def get_doi(entry):
    """Extract DOI from entry, preferring the doi field, falling back to url."""
    doi = entry.get("doi", "")
    if doi:
        return doi.strip().lower()
    url = entry.get("url", "") or ""
    if "doi.org/" in url:
        return url.split("doi.org/", 1)[1].strip().lower()
    return ""


def needs_abstract(entry):
    """True if the entry has a DOI but no abstract."""
    return bool(get_doi(entry)) and not entry.get("abstract")


def get_missing_entries(data, journal=None):
    """Return entries that need abstracts, optionally filtered by journal."""
    entries = data
    if journal:
        entries = [e for e in entries if e.get("journal") == journal]
    return [e for e in entries if needs_abstract(e)]


# ── OpenAlex ─────────────────────────────────────────────────────────────────

def inverted_index_to_text(inverted_index):
    """Convert OpenAlex inverted-index abstract to plaintext.

    OpenAlex stores abstracts as {"word": [position0, position1, ...], ...}.
    We reconstruct the text by placing each word at its positions.
    """
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    # Find total length
    max_pos = -1
    for positions in inverted_index.values():
        for p in positions:
            if p > max_pos:
                max_pos = p
    if max_pos < 0:
        return ""
    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for p in positions:
            words[p] = word
    return " ".join(words)


def fetch_openalex_batch(dois):
    """Fetch abstracts for a batch of DOIs from OpenAlex.

    Returns dict of {lowercase_doi: abstract_text}.
    """
    # Build pipe-separated DOI filter
    doi_filter = "|".join(f"https://doi.org/{d}" for d in dois)
    params = {
        "filter": f"doi:{doi_filter}",
        "select": "doi,abstract_inverted_index",
        "per_page": len(dois),
        "mailto": MAILTO,
    }
    try:
        resp = requests.get(
            "https://api.openalex.org/works",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    OpenAlex request error: {e}")
        return {}

    results = {}
    for work in resp.json().get("results", []):
        doi_url = (work.get("doi") or "").lower()
        doi = doi_url.replace("https://doi.org/", "") if doi_url else ""
        inverted = work.get("abstract_inverted_index")
        if doi and inverted:
            text = inverted_index_to_text(inverted)
            if text:
                results[doi] = text
    return results


def backfill_openalex(data, missing_entries):
    """Pass 1: batch-fetch abstracts from OpenAlex."""
    print(f"\n── OpenAlex pass: {len(missing_entries)} entries to check ──")

    # Build DOI → entry index for fast lookup
    doi_to_entries = {}
    for entry in missing_entries:
        doi = get_doi(entry)
        if doi:
            doi_to_entries.setdefault(doi, []).append(entry)

    all_dois = list(doi_to_entries.keys())
    filled = 0
    processed = 0

    for i in range(0, len(all_dois), OPENALEX_BATCH_SIZE):
        batch = all_dois[i : i + OPENALEX_BATCH_SIZE]
        abstracts = fetch_openalex_batch(batch)

        for doi, abstract in abstracts.items():
            for entry in doi_to_entries.get(doi, []):
                if not entry.get("abstract"):
                    entry["abstract"] = abstract
                    filled += 1

        processed += len(batch)
        if processed % 500 < OPENALEX_BATCH_SIZE:
            print(f"    Processed {processed}/{len(all_dois)} DOIs, "
                  f"filled {filled} abstracts")

        # Intermediate save
        if processed % SAVE_EVERY < OPENALEX_BATCH_SIZE:
            save_data(data)

        time.sleep(OPENALEX_DELAY)

    # Final save after OpenAlex pass
    save_data(data)
    print(f"  OpenAlex done: filled {filled}/{len(all_dois)} abstracts")
    return filled


# ── Semantic Scholar ─────────────────────────────────────────────────────────

def fetch_s2_batch(dois):
    """Fetch abstracts for a batch of DOIs from Semantic Scholar.

    Uses POST /graph/v1/paper/batch (up to 500 IDs per request).
    Returns dict of {lowercase_doi: abstract_text}.
    """
    ids = [f"DOI:{d}" for d in dois]
    backoff = S2_DELAY
    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.semanticscholar.org/graph/v1/paper/batch",
                params={"fields": "externalIds,abstract"},
                json={"ids": ids},
                timeout=30,
            )
            if resp.status_code == 429:
                backoff = min(backoff * 2, 60)
                print(f"    S2 rate limited, backing off {backoff:.0f}s...")
                time.sleep(backoff)
                continue
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"    S2 batch error: {e}")
            time.sleep(backoff)
            continue

        results = {}
        for item in resp.json():
            if not item:
                continue
            abstract = item.get("abstract")
            doi = (item.get("externalIds") or {}).get("DOI", "")
            if doi and abstract:
                results[doi.lower()] = abstract
        return results

    return {}


def backfill_semantic_scholar(data, missing_entries):
    """Pass 2: batch DOI lookups for remaining gaps."""
    # Re-filter to only entries still missing abstracts after OpenAlex pass
    still_missing = [e for e in missing_entries if not e.get("abstract")]
    print(f"\n── Semantic Scholar pass: {len(still_missing)} entries to check ──")

    # Build DOI → entry index
    doi_to_entries = {}
    for entry in still_missing:
        doi = get_doi(entry)
        if doi:
            doi_to_entries.setdefault(doi, []).append(entry)

    all_dois = list(doi_to_entries.keys())
    filled = 0
    processed = 0

    for i in range(0, len(all_dois), S2_BATCH_SIZE):
        batch = all_dois[i : i + S2_BATCH_SIZE]
        abstracts = fetch_s2_batch(batch)

        for doi, abstract in abstracts.items():
            for entry in doi_to_entries.get(doi, []):
                if not entry.get("abstract"):
                    entry["abstract"] = abstract
                    filled += 1

        processed += len(batch)
        if processed % 500 < S2_BATCH_SIZE:
            print(f"    Processed {processed}/{len(all_dois)} DOIs, "
                  f"filled {filled} abstracts")

        # Intermediate save
        if processed % SAVE_EVERY < S2_BATCH_SIZE:
            save_data(data)

        time.sleep(S2_DELAY)

    # Final save after S2 pass
    save_data(data)
    print(f"  Semantic Scholar done: filled {filled}/{len(all_dois)} abstracts")
    return filled


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Backfill missing abstracts from OpenAlex and Semantic Scholar"
    )
    parser.add_argument(
        "--journal",
        choices=["JEAB", "BP", "JEP:ALC"],
        default=None,
        help="Only process entries from this journal (default: all)",
    )
    parser.add_argument(
        "--source",
        choices=["openalex", "s2", "both"],
        default="both",
        help="Which API to use (default: both)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without fetching or writing",
    )
    args = parser.parse_args()

    data = load_data()
    missing = get_missing_entries(data, journal=args.journal)

    # Report current state
    label = args.journal or "all journals"
    total = len([e for e in data if e.get("journal") == args.journal]) if args.journal else len(data)
    has_abs = total - len(missing) - len([
        e for e in (data if not args.journal else [e for e in data if e.get("journal") == args.journal])
        if not get_doi(e) and not e.get("abstract")
    ])

    print(f"Target: {label}")
    print(f"  Total entries: {total}")
    print(f"  Missing abstracts (with DOI): {len(missing)}")
    no_doi = len([
        e for e in (data if not args.journal else [e for e in data if e.get("journal") == args.journal])
        if not get_doi(e)
    ])
    print(f"  No DOI (cannot fetch): {no_doi}")

    if args.dry_run:
        # Per-journal breakdown
        by_journal = {}
        for e in missing:
            j = e.get("journal", "unknown")
            by_journal[j] = by_journal.get(j, 0) + 1
        print("\n  Missing by journal:")
        for j, count in sorted(by_journal.items()):
            print(f"    {j}: {count}")
        return

    if not missing:
        print("  Nothing to backfill!")
        return

    total_filled = 0

    if args.source in ("openalex", "both"):
        total_filled += backfill_openalex(data, missing)

    if args.source in ("s2", "both"):
        total_filled += backfill_semantic_scholar(data, missing)

    # Final summary
    still_missing = len([e for e in missing if not e.get("abstract")])
    print(f"\n── Summary ──")
    print(f"  Abstracts filled: {total_filled}")
    print(f"  Still missing: {still_missing}")


if __name__ == "__main__":
    main()
