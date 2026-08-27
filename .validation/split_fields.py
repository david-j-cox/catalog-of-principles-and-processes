#!/usr/bin/env python3
"""Split the flat `process` tag list into explicit process / principle fields.

David: "For every article, we should be explicit about process(es) as one field and
principle(s) as a second."

Derives four fields from the legacy `process` list, using label_kinds.json:
    processes   kind == process    - the arrangements the study ran
    principles  kind == principle  - the components those arrangements engage
    topics      phenomenon / measure / model / context - real, but neither of the two
    unmapped    tags not in the vocabulary at all - awaiting the labelling pass

`process` is deliberately KEPT as the immutable source for now, so this stays
re-runnable when the labelling decisions come back and kinds change. Drop it once
the vocabulary settles.

Idempotent: re-running recomputes all four fields from `process` every time.
"""
import json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(ROOT, 'data.json')))
kinds = json.load(open(os.path.join(ROOT, '.validation/label_kinds.json')))['kinds']
TOPIC_KINDS = {'phenomenon', 'measure', 'model', 'context'}

stat = collections.Counter()
for r in rows:
    src = r.get('process') or []
    proc, prin, top, un = [], [], [], []
    for t in src:
        if not isinstance(t, str) or not t.strip():
            continue
        k = kinds.get(t)
        if k == 'process':
            proc.append(t)
        elif k == 'principle':
            prin.append(t)
        elif k in TOPIC_KINDS:
            top.append(t)
        else:
            un.append(t)
    r['processes'], r['principles'], r['topics'], r['unmapped'] = proc, prin, top, un
    if src:
        stat['entries with tags'] += 1
        stat['has process'] += bool(proc)
        stat['has principle'] += bool(prin)
        stat['has both'] += bool(proc and prin)
        stat['has neither'] += not (proc or prin)
    stat['processes'] += len(proc)
    stat['principles'] += len(prin)
    stat['topics'] += len(top)
    stat['unmapped'] += len(un)

json.dump(rows, open(os.path.join(ROOT, 'data.json'), 'w'), indent=2, ensure_ascii=True)

n = stat['entries with tags']
print(f'{len(rows)} entries, {n} carrying tags')
for k in ('has process', 'has principle', 'has both', 'has neither'):
    print(f'  {k:14} {stat[k]:5}  ({100*stat[k]/n:.0f}% of tagged)')
print('tag instances by field:')
for k in ('processes', 'principles', 'topics', 'unmapped'):
    print(f'  {k:12} {stat[k]:5}')
