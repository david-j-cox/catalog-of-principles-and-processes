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

# launchd starts processes with a 256 file-descriptor limit where an interactive shell
# gets far more, and claude fails outright below roughly a thousand ("possibly due to low
# max file descriptors"). Raise it toward the hard limit before anything else runs; this
# needs no sudo because it only lifts the soft limit for this process and its children.
# Go straight for the hard ceiling: claude still refused at 8192.
ulimit -n 65536 2>/dev/null || ulimit -n unlimited 2>/dev/null || true

# Claude Code stores its credentials in the login Keychain, which a launchd agent cannot
# read - the probe confirmed it fails with the Keychain present but unreachable. The
# supported path for scheduled runs is a long-lived token. Kept in a 0600 file rather
# than in the plist, since the plist is readable by anything on the machine.
TOKEN_FILE="$HOME/.claude/.scheduler-token"
if [ -r "$TOKEN_FILE" ]; then
  CLAUDE_CODE_OAUTH_TOKEN=$(tr -d '\r\n' < "$TOKEN_FILE")
  export CLAUDE_CODE_OAUTH_TOKEN
fi

# macOS TCC blocks a launchd-spawned process from reading ~/Documents unless THAT binary
# has Full Disk Access - and the grant does not pass from bash to the python it starts.
# Homebrew's `python3` symlink also moves between versions, so a grant made once silently
# lapses on the next upgrade. Rather than depend on which interpreter happens to be
# blessed, probe them and use the first that can actually read the project.
PY_BIN=""
for cand in /opt/homebrew/bin/python3 /opt/homebrew/bin/python3.14             /opt/homebrew/bin/python3.12 /usr/bin/python3; do
  [ -x "$cand" ] || continue
  if "$cand" -c "open('$ROOT/.validation/preflight.py').close()" 2>/dev/null; then
    PY_BIN="$cand"; break
  fi
done
if [ -z "$PY_BIN" ]; then
  echo "$(stamp) ERROR no python can read the project - every candidate is blocked by" >> "$LOG"
  echo "$(stamp) ERROR macOS privacy protection. Grant Full Disk Access to the python at" >> "$LOG"
  echo "$(stamp) ERROR /opt/homebrew/bin/python3 (System Settings > Privacy & Security)." >> "$LOG"
  exit 1
fi

DECISION=$("$PY_BIN" "$ROOT/.validation/preflight.py" 2>&1)
RC=$?

# Distinguish "preflight said no" from "preflight could not run". Treating a crash as a
# SKIP is what let the previous scheduler die unnoticed for 14 days, and launchd hits a
# real failure here: macOS TCC blocks launchd-spawned processes from ~/Documents unless
# the interpreter has Full Disk Access, so preflight cannot even be opened.
if [ $RC -ne 0 ] || ! echo "$DECISION" | grep -q '"decision"'; then
  echo "$(stamp) ERROR preflight did not run (rc=$RC): $DECISION" >> "$LOG"
  echo "$(stamp) ERROR the schedule is NOT running. If this says 'Operation not permitted'," >> "$LOG"
  echo "$(stamp) ERROR grant Full Disk Access to $PY_BIN in System Settings > Privacy." >> "$LOG"
  exit 1
fi

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

# Probe mode: `touch .validation/.probe` and the next fire checks that claude itself can
# run from launchd - a different context to the terminal, with no inherited login shell
# or keychain session - instead of spending a real cycle. Self-clearing.
if [ -f "$ROOT/.validation/.probe" ]; then
  rm -f "$ROOT/.validation/.probe"
  {
    echo "$(stamp) PROBE fd soft=$(ulimit -Sn) hard=$(ulimit -Hn)"
    echo "$(stamp) PROBE HOME=$HOME USER=$(id -un) SHELL=${SHELL:-unset} TERM=${TERM:-unset}"
    echo "$(stamp) PROBE claude=$(command -v claude) node=$(command -v node)"
    echo "$(stamp) PROBE token=$([ -r "$TOKEN_FILE" ] && echo present || echo MISSING)"
  } >> "$LOG"
  OUT=$(claude -p "Reply with exactly: PROBE_OK" --debug 2>&1 | tail -25)
  if [ ! -r "$TOKEN_FILE" ] && ! echo "$OUT" | grep -q "PROBE_OK"; then
    echo "$(stamp) PROBE FAILED - no scheduler token. Run: claude setup-token" >> "$LOG"
    echo "$(stamp) PROBE then save the token to $TOKEN_FILE (chmod 600)." >> "$LOG"
    exit 0
  fi
  if echo "$OUT" | grep -q "PROBE_OK"; then
    echo "$(stamp) PROBE ok - claude runs under launchd, the full chain is live" >> "$LOG"
  else
    echo "$(stamp) PROBE FAILED - claude cannot run under launchd: $OUT" >> "$LOG"
  fi
  exit 0
fi
PYTHON_FOR_CYCLE="$PY_BIN" claude -p "Run one validation cycle exactly as specified in .validation/RUNBOOK.md, \
starting at step 1 (preflight has already returned GO). Commit the cycle and release \
the lock before you finish. Do not push." \
  --permission-mode acceptEdits >> "$LOG" 2>&1
echo "$(stamp) cycle finished rc=$?" >> "$LOG"
