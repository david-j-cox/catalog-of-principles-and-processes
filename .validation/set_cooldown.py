#!/usr/bin/env python3
"""Record a session-limit cooldown so the heartbeat skips until the reset time.
Usage: python3 .validation/set_cooldown.py "9:20pm"   # ET reset time from the limit error
Writes cooldown_until (epoch) into progress.json and logs the hit.
"""
import json, os, sys, time, datetime, re
try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo('America/New_York')
except Exception:
    NY = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prog = json.load(open(os.path.join(ROOT, '.validation/progress.json')))
arg = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ''

m = re.match(r'(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', arg)
now = datetime.datetime.now(NY) if NY else datetime.datetime.now()
if m:
    hh = int(m.group(1)); mm = int(m.group(2) or 0); ap = m.group(3)
    if ap == 'pm' and hh != 12: hh += 12
    if ap == 'am' and hh == 12: hh = 0
    reset = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    # Session limits reset on a rolling window (a few hours), so the reset clock time is always
    # near-future. If parsing lands in the past, the reset has ALREADY happened (the limit message
    # was generated before it) -> resume shortly. Only treat it as next-day if it is far in the
    # future relative to a plausible window would be wrong; a >12h "future" gap means it's really
    # the same-day time that just passed.
    if reset <= now:
        cooldown_until = now.timestamp() + 60          # reset already passed; resume now
    elif (reset - now).total_seconds() > 12 * 3600:
        cooldown_until = now.timestamp() + 60          # absurdly far -> treat as just-passed
    else:
        cooldown_until = reset.timestamp() + 180       # genuine near-future reset + 3-min grace
else:
    # no parseable time -> default 1h cooldown
    cooldown_until = time.time() + 3600
    reset = now + datetime.timedelta(hours=1)

prog['cooldown_until'] = cooldown_until
prog.setdefault('limit_hits', []).append({'at': now.strftime('%Y-%m-%d %H:%M %Z'),
                                          'resume_after': reset.strftime('%Y-%m-%d %H:%M %Z')})
json.dump(prog, open(os.path.join(ROOT, '.validation/progress.json'), 'w'), indent=2)
print(json.dumps({'cooldown_until_epoch': cooldown_until,
                  'resume_after_et': reset.strftime('%Y-%m-%d %H:%M %Z')}))
