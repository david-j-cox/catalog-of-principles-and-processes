#!/usr/bin/env python3
"""Apply adversarial audit results for first-pass AI coding.

Accept verdicts leave the first pass as-is. Revise verdicts update the AI-coded
tags. Needs-human verdicts clear the AI signoff and append an audit follow-up.
Human signoffs are never written by this script.
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
        raise SystemExit("No audit rows found.")
    counts = Counter(row["idx"] for row in rows)
    dupes = sorted(idx for idx, count in counts.items() if count > 1)
    if dupes:
        raise SystemExit(f"Duplicate audited indices: {dupes}")

    allowed = {"accept", "revise", "needs_human"}
    errors: list[str] = []
    for row in rows:
        verdict = row.get("audit_verdict")
        if verdict not in allowed:
            errors.append(f"{row.get('idx')}: invalid verdict {verdict!r}")
        for field, expected in (("revised_processes", "process"), ("revised_principles", "principle")):
            for label in row.get(field) or []:
                if kinds.get(label) != expected:
                    errors.append(f"{row['idx']}: {label!r} is not a {expected}")
        for label in row.get("revised_other_tags") or []:
            if kinds.get(label) not in {"phenomenon", "measure", "model"}:
                errors.append(f"{row['idx']}: {label!r} is not an allowed other_tags label")
    if errors:
        raise SystemExit("\n".join(errors[:50]))


def set_tags(article: dict, row: dict) -> None:
    processes = list(row.get("revised_processes") or [])
    principles = list(row.get("revised_principles") or [])
    other = list(row.get("revised_other_tags") or [])
    article["processes"] = processes
    article["principles"] = principles
    article["topics"] = other
    article["unmapped"] = []
    article["process"] = processes + principles + other


def main() -> None:
    patterns = sys.argv[1:] or ["reports/ai_first_pass_audit/audit_*.jsonl"]
    rows = load_rows(patterns)
    kinds_payload = json.load(open(KINDS_PATH))
    kinds = kinds_payload.get("kinds", kinds_payload)
    validate(rows, kinds)

    original = DATA_PATH.read_text()
    data = json.loads(original)
    verdicts = Counter()
    followups: list[dict] = []

    for row in rows:
        idx = row["idx"]
        article = data[idx]
        verdict = row["audit_verdict"]
        verdicts[verdict] += 1

        if verdict == "accept":
            continue

        ne = normalize_non_empirical(row.get("revised_non_empirical"))
        article["ai-reviewed"] = True
        article.setdefault("signoffs", [])

        if verdict == "revise":
            article["ai-signoffs"] = 1
            article["needs-human"] = False
            if ne != "no":
                article["excluded"] = ne
                for field in ("processes", "principles", "topics", "unmapped", "process"):
                    article[field] = []
            else:
                article.pop("excluded", None)
                set_tags(article, row)
            continue

        article["ai-signoffs"] = 0
        article["needs-human"] = True
        followups.append({
            "track": "entry-audit",
            "idx": idx,
            "title": article.get("title", ""),
            "source_file": row.get("_source_file"),
            "audit_verdict": verdict,
            "suggested_processes": row.get("revised_processes") or [],
            "suggested_principles": row.get("revised_principles") or [],
            "suggested_other_tags": row.get("revised_other_tags") or [],
            "suggested_non_empirical": ne,
            "needs_human": True,
            "audit_confidence": row.get("audit_confidence"),
            "reason": row.get("reason", ""),
        })

    DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=True) + ("\n" if original.endswith("\n") else ""))
    if followups:
        with open(FOLLOWUP_PATH, "a") as f:
            for followup in followups:
                f.write(json.dumps(followup, ensure_ascii=True) + "\n")

    print(json.dumps({
        "audit_rows": len(rows),
        "accepted": verdicts["accept"],
        "revised": verdicts["revise"],
        "needs_human": verdicts["needs_human"],
    }, indent=2))


if __name__ == "__main__":
    main()
