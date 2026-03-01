"""
One-time script to add "journal": "JEAB" to all existing entries in data.json.
Preserves 4-space indent formatting.

Usage:
    python backfill_journal.py
"""

import json
from pathlib import Path

DATA_FILE = Path("data.json")

def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} entries")

    updated = 0
    for entry in data:
        if "journal" not in entry:
            entry["journal"] = "JEAB"
            updated += 1

    DATA_FILE.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {updated} entries with 'journal': 'JEAB'")
    print(f"Skipped {len(data) - updated} entries (already had journal field)")

if __name__ == "__main__":
    main()
