# Overnight validation runbook

Autonomous, checkpointed validation of the catalog. One "cycle" = one batch of entries
reviewed by the EAB single-reviewer (+escalation) workflow, applied, and committed.

## Config
- Branch: `overnight-validation` (commit each cycle; never push, never PR).
- Window: 20:30-04:30 America/New_York (`.validation/progress.json` -> `window`). Run cycles only inside it.
- Cursor / state: `.validation/progress.json` (done indices, next_cursor, tokens_cumulative, cycles).
- Human queue: `.validation/followup.jsonl` (needs_human verdicts; never auto-applied).
- Taxonomy: `.validation/taxonomy.json` (172 canonical labels + variant->preferred merges).
- Batch size: 300 entries/cycle (single reviewer + escalations ~= 300-700 agents, under the 1000 cap).

## One cycle
1. `SEL=$(python3 .validation/gen_batch.py 300)` -> writes `.validation/batch.mjs`, prints selected indices.
2. Run `Workflow({scriptPath: ".validation/batch.mjs"})`; await the completion notification.
3. `python3 .validation/apply_batch.py <output_file> <selected_csv> <subagent_tokens>`
   - applies signed-off changes to data.json, queues needs_human, normalizes tags, advances cursor.
4. `git add -A && git commit` with a one-line cycle summary.
5. Decide next:
   - Workflow returned session-limit failures -> parse reset time, ScheduleWakeup ~5 min after reset.
   - Still inside window + work remains -> ScheduleWakeup ~60s (next cycle).
   - Outside window -> ScheduleWakeup for next 20:30 ET.
   - No entries remain (entry_track done == 11920) AND equation_track remaining == [] -> stop; report.

## Tracks remaining
- entry_track: metadata + process tag for all 11,920 (validate existing 785, assign empties, audit metadata).
- equation_track: 205 remaining equation entries (resume run wf_90a9eb5a-350, cached prefix returns instantly).

## Safety invariants
- Only `reviewed==true && !needs_human` verdicts mutate data.json.
- data.json always rewritten with `json.dumps(indent=2, ensure_ascii=True)` (byte-stable diff).
- Every cycle is committed before the next starts; worst-case loss on interruption is one in-flight batch.
