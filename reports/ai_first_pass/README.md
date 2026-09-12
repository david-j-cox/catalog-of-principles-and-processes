# AI first-pass coding and adversarial audit

This release adds 480 first-pass article reviews across 12 JSONL batches, with a
second AI audit of every record in `../ai_first_pass_audit/`.

## Audit results

| Verdict | Records |
| --- | ---: |
| Accept first pass | 392 |
| Revise first pass | 42 |
| Needs human review | 46 |
| Total audited | 480 |

The first-pass and audit reports preserve the proposed labels, confidence, and
reasoning. The importers in `.validation/` apply these as AI review only. Human
`signoffs` and `reviewed` values were unchanged by these batches. A needs-human
audit clears AI signoff and records a follow-up; suggested tags may remain in the
article and must not be treated as human-validated classifications.

## Coverage at this release

- 11,920 total records; 11,360 visible and 560 excluded as non-empirical.
- 817 records have an AI review attempt, including earlier validation work.
- 698 records have an AI signoff, including excluded records.
- 119 records require human follow-up across the full catalog.

These counts describe different dimensions and are not additive categories.
The catalog has not completed first-pass coding or human validation.

## Evidence limits

These are provisional AI classifications, not verified scientific ground truth.
Evidence varies by record. Some judgments, including some exclusions, were made
from a title or stored abstract without full-text verification. The reports state
that limitation where known. A second AI accepting a judgment does not establish
its correctness or substitute for an independent human examination of the paper.

Both passes use the existing controlled vocabulary, distinguishing processes,
principles, and other tags. Structural checks verify unique record indices,
matching first-pass article titles, complete audit coverage, allowed label kinds,
preserved human signoffs, and the needs-human signoff rule. These checks establish
data integrity, not the scientific accuracy of each tag.

The JSONL index refers to the ordered `data.json` in this release. Preserve that
version when reproducing the import. The import scripts append follow-up records;
repeated application to the same files can duplicate follow-up events.
