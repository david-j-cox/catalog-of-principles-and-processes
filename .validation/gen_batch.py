#!/usr/bin/env python3
"""Generate the next batch workflow script. Equation track drains first, then the entry track.
Usage: python3 .validation/gen_batch.py <entry_count> [indices_csv]
Writes .validation/batch.mjs and prints JSON: {track, selected, count}.
"""
import json, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prog = json.load(open(os.path.join(ROOT, '.validation/progress.json')))
tax = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))
data = json.load(open(os.path.join(ROOT, 'data.json')))
canon = tax['canonical']

entry_count = int(sys.argv[1]) if len(sys.argv) > 1 else 40
override = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 and sys.argv[2] else None

EQ_BATCH = 8  # equation panel is 4 agents/entry; keep small to stay under the session limit
SWEEP_YEAR = 1997  # below this, sources are scans/paywalls: the equation sweep cannot resolve them

eq_remaining = list(prog['equation_track']['remaining'])
if override is not None:
    # explicit indices: treat as entry track unless they're all equation-remaining
    track = 'equation' if set(override) <= set(eq_remaining) else 'entry'
    sel = override
elif len(eq_remaining) >= EQ_BATCH or (eq_remaining and len(prog['entry_track']['done']) >= prog['entry_track']['total']):
    # Equations discovered by the entry sweep accumulate until they fill a panel batch,
    # so a single find does not trigger a one-entry equation cycle.
    track = 'equation'
    sel = eq_remaining[:EQ_BATCH]
else:
    track = 'entry'
    done = set(prog['entry_track']['done'])
    # Machine-readable era first: 1997+ sources can actually be fetched, so the equation
    # sweep works and escalation should be lower. Pre-1997 (scans/paywalls) comes after.
    cand = [i for i in range(len(data)) if i not in done]
    # Source reachability decides order (see .validation/fulltext_probe.py):
    #   0 fulltext - PMC serves machine-readable HTML body
    #   1 scan     - PMC has abstract only; Europe PMC render PDF yields OCR text
    #   2 nopmc    - Elsevier / APA / no DOI; needs publisher access
    try:
        FT = json.load(open(os.path.join(ROOT, '.validation/fulltext_map.json')))
    except Exception:
        FT = {}
    RANK = {'fulltext': 0, 'scan': 1}
    def rank(i):
        return RANK.get((FT.get(str(i)) or {}).get('status'), 2)
    cand.sort(key=lambda i: (rank(i), i))
    sel = cand[:entry_count]

if track == 'equation':
    batch = []
    for i in sel:
        d = data[i]
        batch.append({
            'idx': i, 'title': d.get('title', ''), 'authors': d.get('authors', []),
            'year': d.get('year'), 'journal': d.get('journal', ''), 'volume': d.get('volume'),
            'issue': d.get('issue'), 'pages': d.get('pages', ''), 'url': d.get('url', ''),
            'static_equation': d.get('static-equation', '') or '',
            'static_definitions': d.get('static-equation-definitions', '') or '',
            'recursive_equation': d.get('recursive-equation', '') or '',
            'recursive_definitions': d.get('recursive-equation-definitions', '') or '',
        })
    tpl = open(os.path.join(ROOT, '.validation/tpl_equation.mjs')).read()
    js = tpl.replace('__BATCH__', json.dumps(batch))
else:
    batch = []
    for i in sel:
        d = data[i]
        batch.append({
            'idx': i, 'title': d.get('title', ''), 'authors': d.get('authors', []),
            'year': d.get('year'), 'journal': d.get('journal', ''), 'url': d.get('url', ''),
            'abstract': (d.get('abstract', '') or '')[:2500],
            'process': d.get('process', []) or [], 'reviewed': bool(d.get('reviewed')),
            'sweep_equations': str(d.get('year')).isdigit() and int(d['year']) >= SWEEP_YEAR,
            'source_status': (FT.get(str(i)) or {}).get('status', 'unknown'),
            'pmcid': (FT.get(str(i)) or {}).get('pmcid'),
        })
    tpl = open(os.path.join(ROOT, '.validation/tpl_entry.mjs')).read()
    js = tpl.replace('__CANON__', json.dumps(canon)).replace('__BATCH__', json.dumps(batch))

open(os.path.join(ROOT, '.validation/batch.mjs'), 'w').write(js)
print(json.dumps({'track': track, 'selected': sel, 'count': len(sel), 'script_bytes': len(js)}))
