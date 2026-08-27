#!/bin/bash
# launchd heartbeat: run one validation cycle if preflight says GO.
# Design-agnostic: launchd only wakes us up; the cycle body lives in RUNBOOK.md,
# so re-architecting the cycle (sharding, local pre-pass) does not touch this file.
set -uo pipefail
ROOT="/Users/davidjcox/Documents/SideProjects/catalog-of-principles-and-processes"
cd "$ROOT" || exit 1
LOG="$ROOT/.validation/heartbeat.log"
export PATH="/Users/davidjcox/.local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

stamp() { date "+%Y-%m-%d %H:%M:%S"; }

DECISION=$(python3 .validation/preflight.py 2>&1)
if ! echo "$DECISION" | grep -q '"decision": "GO"'; then
  echo "$(stamp) SKIP $DECISION" >> "$LOG"
  exit 0
fi

# On battery, skip: a cycle is a long burst of network and model work.
if pmset -g batt 2>/dev/null | grep -q "Battery Power"; then
  echo "$(stamp) SKIP on battery power" >> "$LOG"
  exit 0
fi

echo "$(stamp) GO $DECISION" >> "$LOG"
claude -p "Run one validation cycle exactly as specified in .validation/RUNBOOK.md, \
starting at step 1 (preflight has already returned GO). Commit the cycle and release \
the lock before you finish. Do not push." \
  --permission-mode acceptEdits >> "$LOG" 2>&1
echo "$(stamp) cycle finished rc=$?" >> "$LOG"
