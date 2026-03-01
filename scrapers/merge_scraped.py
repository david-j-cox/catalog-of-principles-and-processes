"""
Merge Scraped Data into data.json
==================================
Merges new scraped entries into the main data.json file, deduplicating by
DOI (primary) and title+year (fallback). Preserves manually enriched entries
(process, equations, contributor data, signoffs, etc.).

Usage:
    python scrapers/merge_scraped.py scrapers/output/BP_crossref.json
    python scrapers/merge_scraped.py scrapers/output/JEP_ALC_crossref.json
    python scrapers/merge_scraped.py scrapers/output/*.json

Output:
    Updates data.json in place (with 4-space indent).
"""

import json
import re
import sys
from pathlib import Path

DATA_FILE = Path("data.json")

# Fields that represent manual enrichment — never overwrite these from scraped data
PROTECTED_FIELDS = {
    "process", "static-equation", "static-equation-definitions",
    "recursive-equation", "recursive-equation-definitions",
    "reviewed", "contributor", "signoffs", "correctors",
}


def normalize_title(title):
    """Lowercase, strip punctuation/whitespace for fuzzy matching."""
    if not title:
        return ""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def build_index(data):
    """Build lookup indexes for deduplication."""
    doi_index = {}   # doi → index
    title_year_index = {}  # (normalized_title, year) → index

    for i, entry in enumerate(data):
        doi = (entry.get("doi") or "").strip().lower()
        if doi:
            doi_index[doi] = i

        norm_title = normalize_title(entry.get("title", ""))
        year = entry.get("year")
        if norm_title and year:
            title_year_index[(norm_title, year)] = i

    return doi_index, title_year_index


def is_enriched(entry):
    """Check if an entry has any manually enriched fields."""
    for field in PROTECTED_FIELDS:
        val = entry.get(field)
        if val and val != [] and val != "" and val is not False:
            return True
    return False


def merge_entry(existing, new_entry):
    """
    Merge a new scraped entry into an existing one.
    Only updates empty/missing fields; never overwrites protected fields.
    """
    for key, value in new_entry.items():
        if key in PROTECTED_FIELDS:
            continue
        existing_val = existing.get(key)
        # Only fill in if existing value is empty/missing
        if not existing_val and value:
            existing[key] = value
    return existing


def main():
    if len(sys.argv) < 2:
        print("Usage: python scrapers/merge_scraped.py <scraped_file.json> [...]")
        sys.exit(1)

    # Load existing data
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found. Run from project root.")
        sys.exit(1)

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    original_count = len(data)
    print(f"Loaded {original_count} existing entries from {DATA_FILE}")

    doi_index, title_year_index = build_index(data)

    total_new = 0
    total_updated = 0
    total_skipped = 0

    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            continue

        scraped = json.loads(path.read_text(encoding="utf-8"))
        print(f"\nProcessing {path.name}: {len(scraped)} entries")

        file_new = 0
        file_updated = 0
        file_skipped = 0

        for entry in scraped:
            doi = (entry.get("doi") or "").strip().lower()
            norm_title = normalize_title(entry.get("title", ""))
            year = entry.get("year")

            # Check DOI match first
            existing_idx = None
            if doi and doi in doi_index:
                existing_idx = doi_index[doi]
            elif norm_title and year and (norm_title, year) in title_year_index:
                existing_idx = title_year_index[(norm_title, year)]

            if existing_idx is not None:
                # Entry already exists — merge non-protected fields
                existing = data[existing_idx]
                if not is_enriched(existing):
                    data[existing_idx] = merge_entry(existing, entry)
                    file_updated += 1
                else:
                    file_skipped += 1
            else:
                # New entry — add it
                data.append(entry)
                new_idx = len(data) - 1
                if doi:
                    doi_index[doi] = new_idx
                if norm_title and year:
                    title_year_index[(norm_title, year)] = new_idx
                file_new += 1

        print(f"  New: {file_new}  Updated: {file_updated}  Skipped (enriched): {file_skipped}")
        total_new += file_new
        total_updated += file_updated
        total_skipped += file_skipped

    # Sort: journal → year → volume → first page
    def sort_key(e):
        journal = e.get("journal", "JEAB")
        journal_order = {"JEAB": 0, "BP": 1, "JEP:ALC": 2}.get(journal, 9)
        try:
            page = int(str(e.get("pages", "0")).split("-")[0])
        except (ValueError, AttributeError):
            page = 0
        return (journal_order, e.get("year") or 9999, e.get("volume") or 9999, page)

    data.sort(key=sort_key)

    # Write updated data
    DATA_FILE.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"\nSummary:")
    print(f"  Original entries: {original_count}")
    print(f"  New entries added: {total_new}")
    print(f"  Existing updated: {total_updated}")
    print(f"  Skipped (enriched): {total_skipped}")
    print(f"  Total entries now: {len(data)}")
    print(f"  Written to {DATA_FILE}")


if __name__ == "__main__":
    main()
