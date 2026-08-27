#!/usr/bin/env python3
"""Apply a completed batch workflow output to data.json and advance the cursor.
Auto-detects track (equation vs entry) from the result payload.
Usage: python3 .validation/apply_batch.py <output_file> <selected_csv> <tokens_spent>
"""
import json, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_file, selected_csv, tokens = sys.argv[1], sys.argv[2], int(sys.argv[3])
selected = [int(x) for x in selected_csv.split(',') if x != '']

raw = json.load(open(out_file))
res = raw.get('result', raw)
if isinstance(res, str):
    res = json.loads(res)
results = res.get('results', [])
track = res.get('track')
if not track and results:
    track = 'equation' if 'final_static_equation' in results[0] else 'entry'

orig = open(os.path.join(ROOT, 'data.json')).read()
data = json.loads(orig)
prog = json.load(open(os.path.join(ROOT, '.validation/progress.json')))
_TAX = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))
MERGES = _TAX.get('merges', {})
CANON = _TAX['canonical']
_CANON_CI = {c.lower(): c for c in CANON}
_MERGE_CI = {k.lower(): v for k, v in MERGES.items()}
followup_fh = open(os.path.join(ROOT, '.validation/followup.jsonl'), 'a')
rejected_tags = []

def normtags(tags, idx=None):
    """Snap to the controlled vocabulary; never let free text into `process`.

    The reviewer prompt asks for canonical labels but nothing enforced it, so 33% of
    processed entries acquired free-text descriptions ("Temporal patterning of operant
    responses") that the site cannot filter or group on. Off-vocabulary tags are now
    dropped from the entry and recorded for human vocabulary review instead.
    """
    out = []
    for t in tags:
        if not isinstance(t, str) or not t.strip():
            continue
        k = t.strip().lower()
        if k in _MERGE_CI:
            k = _MERGE_CI[k].lower()
        if k in _CANON_CI:
            c = _CANON_CI[k]
            if c not in out:
                out.append(c)
        else:
            rejected_tags.append({'idx': idx, 'tag': t})
    return out

applied = queued = 0
returned = {r['idx'] for r in results}

if track == 'equation':
    for r in results:
        d = data[r['idx']]
        d['static-equation'] = r['final_static_equation']
        d['static-equation-definitions'] = r['final_static_definitions']
        d['recursive-equation'] = r['final_recursive_equation']
        d['recursive-equation-definitions'] = r['final_recursive_definitions']
        # `reviewed`/`signoffs` are reserved for human verification via the site.
        # The automated pass records its own status separately.
        d['ai-reviewed'] = True
        d['ai-signoffs'] = int(r.get('signoffs') or 0)
        d['needs-human'] = bool(r.get('human_followup_required'))
        d.setdefault('signoffs', [])
        if r.get('equation_provenance'):
            d['equation-provenance'] = r['equation_provenance']
        if r.get('diverges_from_printed'):
            d['equation-diverges-from-printed'] = True
        applied += 1
        if r.get('human_followup_required'):
            followup_fh.write(json.dumps({'track': 'equation', **r}) + '\n')
            queued += 1
    rem = [i for i in prog['equation_track']['remaining'] if i not in returned]
    prog['equation_track']['remaining'] = rem
    prog['equation_track']['done'] = sorted(set(prog['equation_track']['done']) | returned)
    remaining_after = len(rem)
else:
    META_KEYS = {'authors', 'abstract', 'url', 'year', 'journal', 'title'}
    for r in results:
        d = data[r['idx']]
        if r.get('reviewed') and not r.get('needs_human'):
            if r.get('metadata_changed') and isinstance(r.get('metadata_fixes'), dict):
                for k, v in r['metadata_fixes'].items():
                    if k in META_KEYS and v not in (None, '', []):
                        d[k] = v
            if r.get('process_action') != 'left_empty' and isinstance(r.get('process_final'), list):
                d['process'] = normtags(r['process_final'], r['idx'])
            d['ai-reviewed'] = True
            d['ai-signoffs'] = max(int(d.get('ai-signoffs') or 0), int(r.get('signoffs') or 0))
            d['needs-human'] = False
            d.setdefault('signoffs', [])
            applied += 1
        else:
            followup_fh.write(json.dumps({'track': 'entry', 'idx': r['idx'], 'title': data[r['idx']].get('title', ''), **r}) + '\n')
            queued += 1
    # Entries whose source displays an equation the catalog never captured go back
    # into the equation-track queue for the three-editor panel.
    eq_done = set(prog['equation_track']['done'])
    eq_queue = set(prog['equation_track']['remaining'])
    found = 0
    for r in results:
        if r.get('equation_in_text') == 'present' and r['idx'] not in eq_done and r['idx'] not in eq_queue:
            eq_queue.add(r['idx'])
            found += 1
    if found:
        prog['equation_track']['remaining'] = sorted(eq_queue)

    for rj in rejected_tags:
        followup_fh.write(json.dumps({'track': 'vocabulary', 'idx': rj['idx'],
                                      'title': data[rj['idx']].get('title', '') if rj['idx'] is not None else '',
                                      'rejected_tag': rj['tag'], 'needs_human': True,
                                      'notes': 'off-vocabulary tag proposed by the reviewer; '
                                               'not written to process. Add to taxonomy or discard.'}) + '\n')

    done = set(prog['entry_track']['done']) | returned
    prog['entry_track']['done'] = sorted(done)
    if selected:
        prog['entry_track']['next_cursor'] = max(prog['entry_track']['next_cursor'], max(selected) + 1)
    remaining_after = prog['entry_track']['total'] - len(done)

followup_fh.close()
prog['tokens_cumulative'] += tokens
prog['cycles_completed'] += 1
unreturned = sorted(set(selected) - returned)

out = json.dumps(data, indent=2, ensure_ascii=True) + ('\n' if orig.endswith('\n') else '')
open(os.path.join(ROOT, 'data.json'), 'w').write(out)
json.dump(prog, open(os.path.join(ROOT, '.validation/progress.json'), 'w'), indent=2)

print(json.dumps({
    'track': track, 'applied': applied, 'queued_for_human': queued,
    **({'equations_discovered': found} if track != 'equation' else {}),
    'returned': len(returned), 'unreturned_retry': unreturned, f'{track}_remaining': remaining_after,
    'tokens_cumulative': prog['tokens_cumulative'], 'cycles': prog['cycles_completed'],
    'off_vocabulary_tags_rejected': len(rejected_tags),
}))
