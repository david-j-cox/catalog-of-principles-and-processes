# Overnight validation runbook

Autonomous, checkpointed validation of the catalog. One "cycle" = one batch of entries
reviewed by the EAB single-reviewer (+escalation) workflow, applied, and committed.

## Config
- Branch: `overnight-validation` (commit each cycle; never push, never PR).
- Window: 20:30-04:30 America/New_York (`.validation/progress.json` -> `window`). Run cycles only inside it.
- Cursor / state: `.validation/progress.json` (done indices, next_cursor, tokens_cumulative, cycles).
- Human queue: `.validation/followup.jsonl` (needs_human verdicts; never auto-applied).
- Taxonomy: `.validation/taxonomy.json` (172 canonical labels + variant->preferred merges).
- Batch size: 40 entries/cycle (~1.2M tokens, ~10 min) so a session-limit hit loses at most one batch.

## One cycle (driven by the heartbeat cron)
0. `python3 .validation/preflight.py` -> JSON decision. If `SKIP`, stop (do nothing this fire).
   If `GO`, continue. (preflight checks: in-window, not in cooldown, no fresh lock, work remains.)
1. `touch .validation/.lock` (claims the cycle; preflight treats a <30 min lock as in-progress).
2. `SEL=$(python3 .validation/gen_batch.py 40)` -> writes `.validation/batch.mjs`, prints selected indices.
3. Run `Workflow({scriptPath: ".validation/batch.mjs"})`; the completion notification re-invokes you.
4. On completion:
   - If the run reports session-limit failures: `python3 .validation/set_cooldown.py "<reset time, e.g. 9:20pm>"`,
     then `rm -f .validation/.lock` and stop. The next heartbeat after the reset resumes automatically.
   - Else: `python3 .validation/apply_batch.py <output_file> <selected_csv> <subagent_tokens>`,
     then `git add -A && git commit -q -m "validation cycle N: <summary>"`, then `rm -f .validation/.lock`.
5. If still inside the window and work remains, you MAY immediately start the next cycle (back to step 1)
   to chain cycles; otherwise the next heartbeat fire will pick up.
6. Done when preflight reports `complete:true` (entry_track done==11920 AND equation_track remaining==[]).

## Tracks remaining
- entry_track: metadata + process tag for all 11,920 (validate existing 785, assign empties, audit metadata).
- equation_track: 205 remaining equation entries (resume run wf_90a9eb5a-350, cached prefix returns instantly).

## Safety invariants
- Only `reviewed==true && !needs_human` verdicts mutate data.json.
- data.json always rewritten with `json.dumps(indent=2, ensure_ascii=True)` (byte-stable diff).
- Every cycle is committed before the next starts; worst-case loss on interruption is one in-flight batch.
