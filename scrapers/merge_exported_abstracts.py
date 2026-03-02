"""
Merge Exported Abstracts into data.json
========================================
Reads CSV/RIS files exported from PsycNET or ScienceDirect and matches
abstracts to data.json entries by DOI.

Usage:
    python scrapers/merge_exported_abstracts.py scrapers/exports/psycnet_export.csv
    python scrapers/merge_exported_abstracts.py scrapers/exports/sciencedirect_export.csv
    python scrapers/merge_exported_abstracts.py scrapers/exports/*.csv
    python scrapers/merge_exported_abstracts.py scrapers/exports/export.ris
    python scrapers/merge_exported_abstracts.py --dry-run scrapers/exports/*.csv

Supports:
  - PsycNET CSV (columns: Abstract, DOI or Digital Object Identifier)
  - ScienceDirect CSV (columns: Abstract, DOI)
  - RIS format (TI, AB, DO tags)
  - Any CSV with 'abstract' and 'doi' columns (case-insensitive)
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data.json"


def clean_abstract(text):
    """Strip HTML tags, normalize whitespace."""
    if not text:
        return ""
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) >= 30 else ""


def normalize_doi(doi):
    """Normalize a DOI to lowercase, stripping URL prefix."""
    if not doi:
        return ""
    doi = doi.strip().lower()
    if "doi.org/" in doi:
        doi = doi.split("doi.org/", 1)[1]
    return doi


def parse_csv(filepath):
    """Parse a CSV file, returning list of (doi, abstract) tuples."""
    results = []
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # Normalize column names to lowercase
        if not reader.fieldnames:
            return results
        col_map = {c.lower().strip(): c for c in reader.fieldnames}

        # Find DOI column
        doi_col = None
        for candidate in ["doi", "digital object identifier", "dc.identifier.doi"]:
            if candidate in col_map:
                doi_col = col_map[candidate]
                break
        if not doi_col:
            print(f"  WARNING: No DOI column found in {filepath}")
            print(f"  Columns: {list(reader.fieldnames)}")
            return results

        # Find Abstract column
        abs_col = None
        for candidate in ["abstract", "ab", "dc.description.abstract", "description"]:
            if candidate in col_map:
                abs_col = col_map[candidate]
                break
        if not abs_col:
            print(f"  WARNING: No Abstract column found in {filepath}")
            print(f"  Columns: {list(reader.fieldnames)}")
            return results

        for row in reader:
            doi = normalize_doi(row.get(doi_col, ""))
            abstract = clean_abstract(row.get(abs_col, ""))
            if doi and abstract:
                results.append((doi, abstract))

    return results


def parse_ris(filepath):
    """Parse an RIS file, returning list of (doi, abstract) tuples."""
    results = []
    current_doi = ""
    current_abstract_lines = []
    in_abstract = False

    with open(filepath, encoding="utf-8-sig") as f:
        for line in f:
            # RIS tags are 2-6 chars followed by "  - "
            tag_match = re.match(r"^([A-Z][A-Z0-9]{0,5})\s{2}-\s?(.*)", line)
            if tag_match:
                tag = tag_match.group(1)
                value = tag_match.group(2).strip()

                # If we were in an abstract, a new tag ends it
                if in_abstract and tag != "AB":
                    in_abstract = False

                if tag == "DO":
                    current_doi = normalize_doi(value)
                elif tag == "AB":
                    if not in_abstract:
                        current_abstract_lines = [value]
                        in_abstract = True
                    else:
                        current_abstract_lines.append(value)
                elif tag == "ER":
                    # End of record
                    abstract = clean_abstract(" ".join(current_abstract_lines))
                    if current_doi and abstract:
                        results.append((current_doi, abstract))
                    current_doi = ""
                    current_abstract_lines = []
                    in_abstract = False
            elif in_abstract:
                # Continuation line for abstract
                current_abstract_lines.append(line.strip())

    # Handle last record if no trailing ER
    abstract = clean_abstract(" ".join(current_abstract_lines))
    if current_doi and abstract:
        results.append((current_doi, abstract))

    return results


def parse_file(filepath):
    """Auto-detect format and parse."""
    path = Path(filepath)
    if path.suffix.lower() == ".ris":
        return parse_ris(filepath)
    else:
        return parse_csv(filepath)


def main():
    parser = argparse.ArgumentParser(
        description="Merge exported abstracts into data.json"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="CSV or RIS files to merge",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report matches without writing",
    )
    args = parser.parse_args()

    # Load data.json and build DOI index
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    doi_to_entries = {}
    for entry in data:
        doi = entry.get("doi", "")
        if doi:
            doi_to_entries.setdefault(doi.strip().lower(), []).append(entry)
        url = entry.get("url", "") or ""
        if "doi.org/" in url:
            url_doi = url.split("doi.org/", 1)[1].strip().lower()
            if url_doi != doi.strip().lower():
                doi_to_entries.setdefault(url_doi, []).append(entry)

    total_parsed = 0
    total_matched = 0
    total_filled = 0
    total_skipped = 0

    for filepath in args.files:
        print(f"\nParsing {filepath}...")
        pairs = parse_file(filepath)
        print(f"  Found {len(pairs)} abstracts with DOIs")
        total_parsed += len(pairs)

        for doi, abstract in pairs:
            entries = doi_to_entries.get(doi, [])
            if not entries:
                continue
            total_matched += 1
            for entry in entries:
                if entry.get("abstract"):
                    total_skipped += 1
                    continue
                if not args.dry_run:
                    entry["abstract"] = abstract
                total_filled += 1

    print(f"\n── Summary ──")
    print(f"  Abstracts parsed: {total_parsed}")
    print(f"  DOIs matched to catalog: {total_matched}")
    print(f"  New abstracts filled: {total_filled}")
    print(f"  Already had abstract (skipped): {total_skipped}")

    if not args.dry_run and total_filled > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.write("\n")
        print(f"  Saved to {DATA_FILE}")
    elif args.dry_run:
        print(f"  (dry-run, nothing written)")


if __name__ == "__main__":
    main()
