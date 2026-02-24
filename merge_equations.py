"""
merge_equations.py
==================
Merges equation extraction results into data.json.

Prefers equations_judged.json (LLM-reviewed) over equations_staged.json (raw).
When using the judged file, only entries where judgment.approved == true are merged.

Usage:
    python merge_equations.py              # auto-detect best source, apply
    python merge_equations.py --staged     # force use of equations_staged.json
    python merge_equations.py --dry-run    # show what would change without writing

Entries already having a static-equation in data.json are NOT overwritten.
Creates data.json.bak before writing.
"""

import argparse
import json
import re
import shutil
from pathlib import Path

DATA_FILE   = Path("data.json")
STAGED_FILE = Path("equations_staged.json")
JUDGED_FILE = Path("equations_judged.json")
BACKUP_FILE = Path("data.json.bak")


def extract_pmcid(url: str) -> str | None:
    m = re.search(r'PMC(\d+)', str(url), re.IGNORECASE)
    return m.group(1) if m else None


def load_source(use_staged: bool) -> tuple[list[dict], str, int]:
    """
    Returns (entries_list, source_label, approved_count).
    Entries have 'pmcid', 'static_equation', 'definitions'.
    """
    if not use_staged and JUDGED_FILE.exists():
        with open(JUDGED_FILE) as f:
            judged = json.load(f)

        usable = []
        for j in judged:
            judgment = j.get("judgment", {})
            approved = judgment.get("approved") is True
            suggestion = judgment.get("suggested_equation")

            if approved:
                # Use original extraction as-is (possibly with latex fix from judge)
                corrected = dict(j)
                if not judgment.get("latex_valid") and suggestion:
                    corrected["static_equation"] = suggestion
                    corrected["definitions"] = judgment.get("suggested_definitions") or j.get("definitions", "")
                    corrected["_merge_source"] = "judge_corrected_latex"
                else:
                    corrected["_merge_source"] = "extractor_approved"
                usable.append(corrected)
            elif suggestion:
                # Rejected original but judge has a better equation
                corrected = dict(j)
                corrected["static_equation"] = suggestion
                corrected["definitions"] = judgment.get("suggested_definitions") or ""
                corrected["_merge_source"] = "judge_suggested"
                usable.append(corrected)
            # else: rejected with no suggestion → skip

        total_with_eq = sum(1 for j in judged if j.get("static_equation"))
        n_approved    = sum(1 for j in judged if j.get("judgment", {}).get("approved"))
        n_corrected   = sum(1 for u in usable if u.get("_merge_source") == "judge_suggested")
        print(f"Judged file: {len(judged)} total, {total_with_eq} extracted, "
              f"{n_approved} approved, {n_corrected} judge-corrected")
        return usable, "equations_judged.json (approved + judge corrections)", len(usable)

    if STAGED_FILE.exists():
        with open(STAGED_FILE) as f:
            staged = json.load(f)
        entries = [s for s in staged if s.get("static_equation")]
        print(f"Staged file: {len(staged)} total, {len(entries)} with equations")
        return entries, "equations_staged.json (all non-null)", len(entries)

    return [], "none", 0


def main():
    parser = argparse.ArgumentParser(description="Merge equations into data.json")
    parser.add_argument("--staged", action="store_true",
                        help="Force use of equations_staged.json even if judged file exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change without writing files")
    args = parser.parse_args()

    entries, source_label, n_approved = load_source(use_staged=args.staged)

    if not entries:
        print("No approved equations to merge.")
        return

    print(f"Source: {source_label}")
    print(f"Equations to merge: {n_approved}")

    with open(DATA_FILE) as f:
        data = json.load(f)

    # Build PMCID → entry index
    merge_index = {e["pmcid"]: e for e in entries}

    updated = 0
    skipped_has_eq = 0
    skipped_no_match = 0

    for entry in data:
        pmcid = extract_pmcid(entry.get("url", ""))
        if not pmcid or pmcid not in merge_index:
            skipped_no_match += 1
            continue

        # Don't overwrite manually curated equations
        existing_eq = entry.get("static-equation")
        if existing_eq and existing_eq != [] and existing_eq != "":
            skipped_has_eq += 1
            continue

        source_entry = merge_index[pmcid]
        eq   = source_entry["static_equation"]
        defs = source_entry.get("definitions") or ""

        if args.dry_run:
            merge_src = source_entry.get("_merge_source", "staged")
            print(f"\n[DRY RUN] Would update PMCID {pmcid} [{merge_src}]:")
            print(f"  Title:    {entry.get('title', '')[:70]}")
            print(f"  Equation: {eq}")
            if defs:
                print(f"  Defs:     {defs[:80]}")
        else:
            entry["static-equation"] = eq
            if defs:
                entry["static-equation-definitions"] = defs
        updated += 1

    print(f"\nSummary:")
    print(f"  {'Would update' if args.dry_run else 'Updated'}:     {updated}")
    print(f"  Skipped (already has eq):  {skipped_has_eq}")
    print(f"  Skipped (not in source):   {skipped_no_match}")

    if args.dry_run:
        print("\n(Dry run — no files written)")
        return

    shutil.copy(DATA_FILE, BACKUP_FILE)
    print(f"\nBacked up data.json → {BACKUP_FILE}")

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Updated data.json with {updated} new equations.")


if __name__ == "__main__":
    main()
