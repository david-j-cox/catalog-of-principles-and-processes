#!/usr/bin/env python3
"""Generate the fast labelling tool (an Artifact) for the calls David needs to make.

Two queues:
  A  the 12 labels whose kind I derived by rule rather than David deciding - confirm or flip.
  B  the 459 off-vocabulary concepts that are candidates to ADD to the taxonomy.

Progress lives in localStorage; an explicit export panel hands the result back as JSON.
The page deliberately does NOT publish over itself: a self-publishing page has to
regenerate its own source, and losing labelling work to a bad republish is worse than
a copy-paste.
"""
import json, os, collections, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tax = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))
kinds = json.load(open(os.path.join(ROOT, '.validation/label_kinds.json')))['kinds']
rows = json.load(open(os.path.join(ROOT, 'data.json')))
canon = tax['canonical']
CI = {c.lower() for c in canon}

# --- queue A: kinds I derived rather than David deciding ---------------------
DERIVED = {
 'Stimulus Generalization': ('principle', 'follows Generalization, which you called a principle'),
 'Temporal Discrimination': ('principle', 'follows Discrimination'),
 'Escape': ('principle', 'parallel to Avoidance'),
 'Stimulus Equivalence': ('principle', 'emergent relations; many processes reach it'),
 'Concept Learning': ('principle', 'convergent endpoint of many procedures'),
 'Habituation': ('principle', 'convergent relation - but arguably a decrement, i.e. an absence'),
 'Classical Conditioning': ('process', 'an arrangement you run (pair the stimuli)'),
 'Operant Conditioning': ('process', 'an arrangement you run'),
 'Conditioning': ('process', 'an arrangement you run'),
 'Second-Order Conditioning': ('process', 'an arrangement you run'),
 'Conditioned Suppression': ('phenomenon', 'a measured outcome (suppression ratio), not a component'),
 'Imitation': ('phenomenon', 'an outcome you observe - could equally be a principle'),
}

# --- queue B: off-vocabulary concepts, with the article that used them -------
usage = collections.defaultdict(list)
for r in rows:
    for t in (r.get('process') or []):
        if t.lower() not in CI:
            usage[t].append(r.get('title', '') or '')
cands = sorted([t for t in usage if len(t.split()) <= 4],
               key=lambda t: (-len(usage[t]), t.lower()))

qa = [{'id': f'A{i}', 'q': 'A', 'label': l, 'kind': DERIVED[l][0], 'why': DERIVED[l][1],
       'n': sum(1 for r in rows if l in (r.get('process') or [])), 'ex': ''}
      for i, l in enumerate(sorted(DERIVED))]
qb = [{'id': f'B{i}', 'q': 'B', 'label': t, 'kind': '', 'why': '',
       'n': len(usage[t]), 'ex': (usage[t][0] or '')[:110]}
      for i, t in enumerate(cands)]
items = qa + qb

KINDS = [('principle', 'Principle', '1'), ('process', 'Process', '2'),
         ('phenomenon', 'Phenomenon', '3'), ('measure', 'Measure', '4'),
         ('model', 'Model', '5'), ('context', 'Context', '6'),
         ('reject', 'Not a concept', '0')]

keybtns = ''.join(
    f'<button class="kb" data-kind="{k}" data-key="{key}">'
    f'<span class="kb-k">{key}</span><span class="kb-n">{html.escape(n)}</span></button>'
    for k, n, key in KINDS)

legend = ''.join(f'<span class="lg" data-kind="{k}">{html.escape(n)}</span>' for k, n, _ in KINDS)

doc = f'''<title>Label the Vocabulary</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@400;600&family=Source+Sans+3:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --ink:#15201d; --ink-2:#41544e; --ink-3:#71857e;
  --paper:#f4f6f4; --card:#fbfcfb; --line:#d9e0dc; --accent:#0f6b60; --accent-soft:#e2efeb;
  --k-principle:#0f6b60; --k-process:#2f5d9e; --k-phenomenon:#7a4a86;
  --k-measure:#4a6572; --k-model:#9c4646; --k-context:#5c6b3f; --k-reject:#9aa5a1;
  --shadow:0 1px 2px rgba(21,32,29,.05),0 10px 30px -20px rgba(21,32,29,.4);
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --ink:#e6ece9; --ink-2:#a7b6b1; --ink-3:#7c8c87;
  --paper:#101614; --card:#182220; --line:#2a3733; --accent:#5fbfae; --accent-soft:#1b302c;
  --k-principle:#5fbfae; --k-process:#7aa5e6; --k-phenomenon:#bd93c9;
  --k-measure:#94aab6; --k-model:#e08b8b; --k-context:#a3b878; --k-reject:#5a6a66;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -20px rgba(0,0,0,.8);
}} }}
:root[data-theme="dark"] {{
  --ink:#e6ece9; --ink-2:#a7b6b1; --ink-3:#7c8c87;
  --paper:#101614; --card:#182220; --line:#2a3733; --accent:#5fbfae; --accent-soft:#1b302c;
  --k-principle:#5fbfae; --k-process:#7aa5e6; --k-phenomenon:#bd93c9;
  --k-measure:#94aab6; --k-model:#e08b8b; --k-context:#a3b878; --k-reject:#5a6a66;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -20px rgba(0,0,0,.8);
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink);
  font:400 17px/1.6 "Source Sans 3", ui-sans-serif, system-ui, sans-serif; }}
.wrap {{ max-width:60rem; margin:0 auto; padding:2rem clamp(1rem,4vw,2rem) 4rem; }}
h1 {{ font-family:Spectral,Georgia,serif; font-weight:600; font-size:clamp(1.7rem,4vw,2.4rem);
  margin:0; letter-spacing:-.015em; }}
.eyebrow {{ font:500 .7rem/1 "IBM Plex Mono",monospace; letter-spacing:.16em;
  text-transform:uppercase; color:var(--accent); margin:0 0 .8rem; }}
.sub {{ color:var(--ink-2); margin:.6rem 0 0; max-width:62ch; }}

.progress {{ display:flex; align-items:center; gap:1rem; margin:1.6rem 0 0; }}
.track {{ flex:1; height:5px; background:var(--line); border-radius:3px; overflow:hidden; }}
.fill {{ height:100%; background:var(--accent); width:0%; transition:width .18s ease; }}
.pcount {{ font:500 .85rem "IBM Plex Mono",monospace; font-variant-numeric:tabular-nums; color:var(--ink-3); }}

.card {{ background:var(--card); border:1px solid var(--line); border-radius:4px;
  padding:1.8rem 1.8rem 1.5rem; box-shadow:var(--shadow); margin-top:1.6rem; }}
.qtag {{ display:inline-block; font:500 .68rem/1 "IBM Plex Mono",monospace; letter-spacing:.12em;
  text-transform:uppercase; padding:.3rem .5rem; border-radius:2px;
  background:var(--accent-soft); color:var(--accent); }}
.term {{ font-family:Spectral,Georgia,serif; font-size:clamp(1.5rem,3.4vw,2.05rem); font-weight:600;
  margin:.7rem 0 .3rem; line-height:1.2; text-wrap:balance; }}
.meta {{ color:var(--ink-3); font-size:.9rem; margin:0; }}
.meta em {{ color:var(--ink-2); font-style:normal; }}
.why {{ margin:.9rem 0 0; padding:.6rem .85rem; border-left:2px solid var(--c,var(--accent));
  background:var(--paper); border-radius:0 2px 2px 0; font-size:.93rem; color:var(--ink-2); }}
.why b {{ color:var(--c,var(--accent)); }}

.keys {{ display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1.5rem; }}
.kb {{ display:inline-flex; align-items:center; gap:.5rem; padding:.55rem .8rem;
  border:1px solid var(--line); background:var(--paper); color:var(--ink);
  border-radius:3px; cursor:pointer; font:inherit; font-size:.93rem;
  border-bottom:2px solid var(--c); transition:background .12s,transform .08s; }}
.kb:hover {{ background:var(--accent-soft); }}
.kb:active {{ transform:translateY(1px); }}
.kb:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.kb-k {{ font:500 .78rem "IBM Plex Mono",monospace; color:var(--ink-3);
  border:1px solid var(--line); border-radius:2px; padding:.1rem .34rem; }}
.kb-n {{ font-weight:600; color:var(--c); }}
[data-kind="principle"] {{ --c:var(--k-principle); }}
[data-kind="process"] {{ --c:var(--k-process); }}
[data-kind="phenomenon"] {{ --c:var(--k-phenomenon); }}
[data-kind="measure"] {{ --c:var(--k-measure); }}
[data-kind="model"] {{ --c:var(--k-model); }}
[data-kind="context"] {{ --c:var(--k-context); }}
[data-kind="reject"] {{ --c:var(--k-reject); }}

.note-wrap {{ margin-top:1.15rem; }}
.note-lbl {{ display:flex; align-items:baseline; justify-content:space-between; gap:1rem;
  font:500 .7rem/1 "IBM Plex Mono",monospace; letter-spacing:.11em; text-transform:uppercase;
  color:var(--ink-3); margin-bottom:.4rem; }}
.note-lbl b {{ color:var(--accent); font-weight:500; letter-spacing:.11em; }}
textarea.note {{ width:100%; min-height:3.4rem; font:inherit; font-size:.93rem;
  background:var(--paper); color:var(--ink); border:1px solid var(--line);
  border-radius:3px; padding:.55rem .7rem; resize:vertical; }}
textarea.note:focus-visible {{ outline:2px solid var(--accent); outline-offset:1px; }}
.has-note {{ border-color:var(--accent) !important; }}
.nav {{ display:flex; gap:.6rem; align-items:center; margin-top:1.2rem;
  padding-top:1.1rem; border-top:1px solid var(--line); flex-wrap:wrap; }}
.nav button {{ font:inherit; font-size:.88rem; padding:.42rem .8rem; border-radius:3px;
  border:1px solid var(--line); background:transparent; color:var(--ink-2); cursor:pointer; }}
.nav button:hover {{ color:var(--ink); border-color:var(--ink-3); }}
.nav button:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.nav .spacer {{ flex:1; }}
.hint {{ font-size:.84rem; color:var(--ink-3); }}

.legend {{ display:flex; flex-wrap:wrap; gap:.4rem; margin-top:2rem; }}
.lg {{ font-size:.78rem; padding:.2rem .5rem; border-radius:2px; color:var(--c);
  border:1px solid var(--c); opacity:.75; }}

.done {{ text-align:center; padding:2.5rem 1rem; }}
.done h2 {{ font-family:Spectral,Georgia,serif; margin:0 0 .5rem; }}

details.out {{ margin-top:2rem; border:1px solid var(--line); border-radius:4px; background:var(--card); }}
details.out summary {{ cursor:pointer; padding:.9rem 1.2rem; font-weight:600; font-size:.95rem; }}
details.out summary:focus-visible {{ outline:2px solid var(--accent); outline-offset:-2px; }}
details.out .body {{ padding:0 1.2rem 1.2rem; }}
textarea {{ width:100%; min-height:14rem; font:400 .82rem/1.5 "IBM Plex Mono",monospace;
  background:var(--paper); color:var(--ink); border:1px solid var(--line);
  border-radius:3px; padding:.8rem; resize:vertical; }}
.row {{ display:flex; gap:.6rem; align-items:center; margin-top:.7rem; flex-wrap:wrap; }}
.btn {{ font:inherit; font-size:.9rem; font-weight:600; padding:.5rem .95rem; border-radius:3px;
  border:1px solid var(--accent); background:var(--accent); color:var(--paper); cursor:pointer; }}
.btn.ghost {{ background:transparent; color:var(--accent); }}
.btn:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.said {{ font-size:.86rem; color:var(--accent); }}
@media (prefers-reduced-motion:reduce) {{ * {{ transition:none !important; }} }}
</style>

<div class="wrap">
  <p class="eyebrow">Catalog vocabulary &middot; {len(items)} calls</p>
  <h1>Label the Vocabulary</h1>
  <p class="sub">Queue A is {len(qa)} labels whose kind I inferred by rule rather than you deciding &mdash;
  confirm or flip them. Queue B is {len(qb)} concepts your students and the pipeline used that the
  vocabulary cannot express; each needs a kind, or a reject. Press a number key. Progress is
  saved in this browser as you go.</p>

  <div class="progress">
    <div class="track"><div class="fill" id="fill"></div></div>
    <span class="pcount" id="pcount">0 / {len(items)}</span>
  </div>

  <div id="stage"></div>

  <div class="legend">{legend}</div>

  <details class="out" id="out">
    <summary>Export decisions</summary>
    <div class="body">
      <p class="hint">Paste this back into the conversation. It also holds your place, so an
      incomplete pass is still worth exporting.</p>
      <textarea id="json" readonly spellcheck="false"></textarea>
      <div class="row">
        <button class="btn" id="copy">Copy to clipboard</button>
        <button class="btn ghost" id="reset">Clear all decisions</button>
        <span class="said" id="said"></span>
      </div>
    </div>
  </details>
</div>

<script>
const ITEMS = {json.dumps(items)};
const KEYMAP = {json.dumps({k: key for k, _, key in KINDS})};
const BYKEY = Object.fromEntries(Object.entries(KEYMAP).map(([k, v]) => [v, k]));
const STORE = 'catalog-label-v1';

let state = {{}}, notes = {{}};
try {{
  const raw = JSON.parse(localStorage.getItem(STORE) || '{{}}');
  state = raw.state || raw || {{}};       // tolerate the pre-notes shape
  notes = raw.notes || {{}};
}} catch (e) {{ state = {{}}; notes = {{}}; }}
let i = 0;
while (i < ITEMS.length && state[ITEMS[i].id]) i++;

const stage = document.getElementById('stage');
const fill = document.getElementById('fill');
const pcount = document.getElementById('pcount');
const jsonBox = document.getElementById('json');

function save() {{
  try {{ localStorage.setItem(STORE, JSON.stringify({{state, notes}})); }} catch (e) {{}}
}}

function esc(s) {{
  return String(s).replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]);
}}

function render() {{
  const n = Object.keys(state).length;
  fill.style.width = (100 * n / ITEMS.length).toFixed(1) + '%';
  pcount.textContent = n + ' / ' + ITEMS.length;
  jsonBox.value = JSON.stringify(
    {{ decided: n, of: ITEMS.length,
      decisions: ITEMS.filter(it => state[it.id])
        .map(it => ({{ label: it.label, queue: it.q, was: it.kind || null,
                      kind: state[it.id], why: notes[it.id] || undefined }})),
      rules: ITEMS.filter(it => notes[it.id])
        .map(it => ({{ label: it.label, kind: state[it.id] || null, why: notes[it.id] }})) }},
    null, 1);

  if (i >= ITEMS.length) {{
    stage.innerHTML = '<div class="card done"><h2>All ' + ITEMS.length + ' done.</h2>' +
      '<p class="sub" style="margin-inline:auto">Open <b>Export decisions</b> below and paste the ' +
      'result back into the conversation.</p></div>';
    document.getElementById('out').open = true;
    return;
  }}
  const it = ITEMS[i];
  const prev = state[it.id];
  stage.innerHTML =
    '<div class="card"' + (it.kind ? ' data-kind="' + it.kind + '"' : '') + '>' +
      '<span class="qtag">' + (it.q === 'A' ? 'Confirm my call' : 'New concept') + '</span>' +
      '<p class="term">' + esc(it.label) + '</p>' +
      '<p class="meta">used on <em>' + it.n + '</em> ' + (it.n === 1 ? 'entry' : 'entries') +
        (it.ex ? ' &middot; e.g. &ldquo;' + esc(it.ex) + '&rdquo;' : '') + '</p>' +
      (it.why ? '<p class="why">I called this <b>' + esc(it.kind) + '</b> &mdash; ' +
        esc(it.why) + '</p>' : '') +
      '<div class="keys">' + {json.dumps(keybtns)} + '</div>' +
      '<div class="note-wrap">' +
        '<div class="note-lbl"><span>Why &mdash; becomes a tagging rule</span>' +
        '<b>press c</b></div>' +
        '<textarea class="note" id="note" rows="2" spellcheck="false" ' +
          'placeholder="e.g. an absence cannot be a component, so this is a process"></textarea>' +
      '</div>' +
      '<div class="nav">' +
        '<button id="back">&larr; Back</button>' +
        '<button id="skip">Skip &rarr;</button>' +
        '<span class="spacer"></span>' +
        '<span class="hint">' + (prev ? 'currently: ' + esc(prev) : 'press 0&ndash;6, or c to explain') + '</span>' +
      '</div>' +
    '</div>';

  const note = document.getElementById('note');
  note.value = notes[it.id] || '';
  if (note.value) note.classList.add('has-note');
  note.addEventListener('input', () => {{
    notes[it.id] = note.value;
    if (!note.value.trim()) delete notes[it.id];
    note.classList.toggle('has-note', !!note.value.trim());
    save();
  }});

  stage.querySelectorAll('.kb').forEach(b =>
    b.addEventListener('click', () => choose(b.dataset.kind)));
  document.getElementById('back').addEventListener('click', () => {{ i = Math.max(0, i - 1); render(); }});
  document.getElementById('skip').addEventListener('click', () => {{ i++; render(); }});
}}

function choose(kind) {{
  state[ITEMS[i].id] = kind;
  save();
  i++;
  render();
}}

document.addEventListener('keydown', e => {{
  if (e.target.tagName === 'TEXTAREA' || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === 'c') {{
    const n = document.getElementById('note');
    if (n) {{ e.preventDefault(); n.focus(); return; }}
  }}
  if (BYKEY[e.key]) {{ e.preventDefault(); choose(BYKEY[e.key]); }}
  else if (e.key === 'ArrowRight') {{ e.preventDefault(); i++; render(); }}
  else if (e.key === 'ArrowLeft') {{ e.preventDefault(); i = Math.max(0, i - 1); render(); }}
}});

document.getElementById('copy').addEventListener('click', async () => {{
  const said = document.getElementById('said');
  try {{
    await navigator.clipboard.writeText(jsonBox.value);
    said.textContent = 'Copied.';
  }} catch (err) {{
    jsonBox.select();
    said.textContent = 'Select and copy manually.';
  }}
  setTimeout(() => {{ said.textContent = ''; }}, 2500);
}});

document.getElementById('reset').addEventListener('click', () => {{
  state = {{}}; notes = {{}}; i = 0; save(); render();
  const said = document.getElementById('said');
  said.textContent = 'Cleared.';
  setTimeout(() => {{ said.textContent = ''; }}, 2000);
}});

render();
</script>
'''

out = os.path.join(ROOT, '.validation/label_tool.html')
open(out, 'w').write(doc)
print(f'wrote {out} ({len(doc)//1024} KB) - queue A {len(qa)}, queue B {len(qb)}, total {len(items)}')
