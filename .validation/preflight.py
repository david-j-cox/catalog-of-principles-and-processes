#!/usr/bin/env python3
"""Heartbeat preflight: decide whether to run a validation cycle now.
Prints a single JSON line: {"decision":"GO"|"SKIP","reason":...,"batch_size":N,...}
GO  -> the caller should run one cycle (gen_batch -> Workflow -> apply_batch -> commit).
SKIP-> do nothing this fire.
"""
import json, os, time, datetime
try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo('America/New_York')
except Exception:
    NY = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prog = json.load(open(os.path.join(ROOT, '.validation/progress.json')))
now = datetime.datetime.now(NY) if NY else datetime.datetime.now()
now_ts = time.time()

def out(decision, reason, **kw):
    print(json.dumps({'decision': decision, 'reason': reason,
                      'now_et': now.strftime('%Y-%m-%d %H:%M %Z'), **kw}))
    raise SystemExit(0)

# 1) within nightly window?  (handles the cross-midnight 20:30-04:30 range)
w = prog['window']
sh, sm = map(int, w['start'].split(':'))
eh, em = map(int, w['end'].split(':'))
cur = now.hour * 60 + now.minute
start = sh * 60 + sm
end = eh * 60 + em
in_window = (cur >= start or cur < end)  # spans midnight
if not in_window:
    out('SKIP', f"outside window {w['start']}-{w['end']} ET")

# 2) limit cooldown active?
cd = prog.get('cooldown_until', 0)
if cd and now_ts < cd:
    mins = int((cd - now_ts) / 60)
    out('SKIP', f'in limit cooldown ~{mins} min remaining', cooldown_until=cd)

# 3) a cycle already in progress (fresh lock)?
lock = os.path.join(ROOT, '.validation/.lock')
if os.path.exists(lock):
    age = now_ts - os.path.getmtime(lock)
    if age < 30 * 60:   # stale after 30 min
        out('SKIP', f'cycle in progress (lock age {int(age)}s)')

# 4) work remaining?
done = set(prog['entry_track']['done'])
remaining_entries = prog['entry_track']['total'] - len(done)
remaining_eq = len(prog['equation_track']['remaining'])
if remaining_entries <= 0 and remaining_eq <= 0:
    out('SKIP', 'all tracks complete', complete=True)

out('GO', 'within window, free, work remains',
    batch_size=40, remaining_entries=remaining_entries, remaining_eq=remaining_eq,
    cycles_done=prog['cycles_completed'], tokens_cumulative=prog['tokens_cumulative'])
