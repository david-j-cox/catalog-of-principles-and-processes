#!/usr/bin/env python3
"""Apply subagent first-pass JSONL coding to the catalog.

This importer is intentionally narrower than apply_batch.py. It accepts the
lightweight JSONL files produced by ad hoc first-pass agents and records their
work as AI review only. It never writes human signoffs.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
PROGRESS_PATH = ROOT / ".validation" / "progress.json"
FOLLOWUP_PATH = ROOT / ".validation" / "followup.jsonl"
KINDS_PATH = ROOT / ".validation" / "label_kinds.json"


def load_rows(patterns: list[str]) -> list[dict]:
    rows: list[dict] = []
    paths: list[str] = []
    for pattern in patterns:
        paths.extend(glob.glob(str(ROOT / pattern)))
    for path in sorted(set(paths)):
        with open(path) as f:
            for line_no, line in enumerate(f, 1):
                if line.strip():
                    row = json.loads(line)
                    row["_source_file"] = os.path.relpath(path, ROOT)
                    row["_source_line"] = line_no
                    rows.append(row)
    return rows


def normalize_non_empirical(value) -> str:
    if value in (False, None, "", "no"):
        return "no"
    if value in (True, "true", "other"):
        return "other"
    if value in ("review", "biographical"):
        return value
    return "other"


def validate(rows: list[dict], kinds: dict[str, str]) -> None:
    if not rows:
        raise SystemExit("No rows found.")
    counts = Counter(row["idx"] for row in rows)
    dupes = sorted(idx for idx, count in counts.items() if count > 1)
    if dupes:
        raise SystemExit(f"Duplicate indices in first-pass rows: {dupes}")

    required = {"idx", "processes", "principles", "other_tags", "reviewed", "signoffs", "needs_human"}
    errors: list[str] = []
    for row in rows:
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"{row.get('idx')}: missing {missing}")
            continue
        for field, expected in (("processes", "process"), ("principles", "principle")):
            for label in row.get(field) or []:
                if kinds.get(label) != expected:
                    errors.append(f"{row['idx']}: {label!r} is not a {expected}")
        for label in row.get("other_tags") or []:
            if kinds.get(label) not in {"phenomenon", "measure", "model"}:
                errors.append(f"{row['idx']}: {label!r} is not an allowed other_tags label")
    if errors:
        raise SystemExit("\n".join(errors[:50]))


def main() -> None:
    patterns = sys.argv[1:] or ["reports/ai_first_pass/batch_*.jsonl"]
    rows = load_rows(patterns)
    kinds_payload = json.load(open(KINDS_PATH))
    kinds = kinds_payload.get("kinds", kinds_payload)
    validate(rows, kinds)

    original = DATA_PATH.read_text()
    data = json.loads(original)
    progress = json.load(open(PROGRESS_PATH))
    followups: list[dict] = []
    applied = excluded = needs_human = confident = 0

    for row in rows:
        idx = row["idx"]
        article = data[idx]
        ne = normalize_non_empirical(row.get("non_empirical"))
        row_needs_human = bool(row.get("needs_human"))
        row_confident = bool(row.get("reviewed")) and int(row.get("signoffs") or 0) > 0 and not row_needs_human

        article["ai-reviewed"] = True
        article["ai-signoffs"] = 1 if row_confident else 0
        article["needs-human"] = row_needs_human
        article.setdefault("signoffs", [])

        if ne != "no" and row_confident:
            article["excluded"] = ne
            for field in ("processes", "principles", "topics", "unmapped", "process"):
                article[field] = []
            excluded += 1
        elif ne == "no":
            article.pop("excluded", None)
            processes = list(row.get("processes") or [])
            principles = list(row.get("principles") or [])
            other = list(row.get("other_tags") or [])
            article["processes"] = processes
            article["principles"] = principles
            article["topics"] = other
            article["unmapped"] = []
            article["process"] = processes + principles + other

        if row_needs_human:
            needs_human += 1
            followups.append({
                "track": "entry",
                "idx": idx,
                "title": article.get("title", ""),
                "source_file": row.get("_source_file"),
                "non_empirical": ne,
                "processes": row.get("processes") or [],
                "principles": row.get("principles") or [],
                "other_tags": row.get("other_tags") or [],
                "needs_human": True,
                "confidence": row.get("confidence"),
                "notes": row.get("notes", ""),
            })
        if row_confident:
            confident += 1
        applied += 1

    done = set(progress["entry_track"].get("done", []))
    done.update(row["idx"] for row in rows)
    progress["entry_track"]["done"] = sorted(done)

    DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=True) + ("\n" if original.endswith("\n") else ""))
    json.dump(progress, open(PROGRESS_PATH, "w"), indent=2)
    if followups:
        with open(FOLLOWUP_PATH, "a") as f:
            for followup in followups:
                f.write(json.dumps(followup, ensure_ascii=True) + "\n")

    print(json.dumps({
        "applied": applied,
        "confident_ai_signoffs": confident,
        "needs_human": needs_human,
        "excluded_non_empirical": excluded,
        "first_idx": min(row["idx"] for row in rows),
        "last_idx": max(row["idx"] for row in rows),
    }, indent=2))


if __name__ == "__main__":
    main()
