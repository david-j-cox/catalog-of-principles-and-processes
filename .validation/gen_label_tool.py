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
import json, os, collections, html, re

def slug(x):
    return re.sub(r'[^a-z0-9]+', '-', x.lower()).strip('-')[:60]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tax = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))
kinds = json.load(open(os.path.join(ROOT, '.validation/label_kinds.json')))['kinds']
rows = json.load(open(os.path.join(ROOT, 'data.json')))
canon = tax['canonical']
CI = {c.lower() for c in canon}

# --- queue A ----------------------------------------------------------------
# First: labels David's OWN breadth rule implicates but that he has not ruled on.
# He rejected "Classical Conditioning" as too broad ("like saying Quantum Physics");
# these name a paradigm or a field at the same altitude. Applying his rule to them is
# his call, so they are surfaced rather than assumed - and they lead the queue because
# each one is used on far more entries than a queue-B singleton.
BREADTH = {
 'Operant Conditioning': ('process', 'exactly parallel to Classical Conditioning, which you rejected'),
 'Conditioning': ('process', 'broader still than either paradigm'),
 'Behavioral Pharmacology': ('context', 'names a field, closest thing here to your Quantum Physics example'),
 'Operant Responding': ('phenomenon', 'amounts to "behaviour occurred"'),
 'Elicited Responding': ('phenomenon', 'near-paradigm level'),
 'Foraging': ('context', 'a preparation/domain rather than a relation'),
 'Second-Order Conditioning': ('process', 'more specific - probably survives, but same family'),
}

DERIVED = {
 'Stimulus Generalization': ('principle', 'follows Generalization, which you called a principle'),
 'Temporal Discrimination': ('principle', 'follows Discrimination'),
 'Escape': ('principle', 'parallel to Avoidance'),
 'Stimulus Equivalence': ('principle', 'emergent relations; many processes reach it'),
 'Concept Learning': ('principle', 'convergent endpoint of many procedures'),
 'Habituation': ('principle', 'convergent relation - but arguably a decrement, i.e. an absence'),
 'Operant Conditioning': ('process', 'an arrangement you run'),
 'Conditioning': ('process', 'an arrangement you run'),
 'Second-Order Conditioning': ('process', 'an arrangement you run'),
 'Conditioned Suppression': ('phenomenon', 'a measured outcome (suppression ratio), not a component'),
 'Imitation': ('phenomenon', 'an outcome you observe - could equally be a principle'),
}

# --- queue B: the corpus-derived covering vocabulary ------------------------
# The 459 orphan strings are NOT the source. Measured: they subsume only 6% onto
# corpus-frequent concepts - 455 of 459 appear on exactly one entry, so they are one-off
# coinages, not a taxonomy in waiting. propose_vocab.py derives candidates from all
# 11,554 real articles instead, and each proposal carries its own evidence.
prop = json.load(open(os.path.join(ROOT, '.validation/proposed_vocab.json')))
FRONT = re.compile(r'^(author index|subject index|editorial board|contents of volume|'
                   r'index (of|to) volume|acknowledg|erratum|corrigendum|supplemental|'
                   r'list of|volume \d|title page|masthead|announcement|in memoriam|'
                   r'obituary|reviewers)', re.I)
arts = [r for r in rows if not FRONT.search((r.get('title') or '').strip())]

def example(terms):
    """A title that announces the concept - the clearest evidence it is real."""
    for r in arts:
        t = (r.get('title') or '')
        if any(m in t.lower() for m in terms):
            return t[:112]
    return ''


def mk(l, kind, why, q):
    return {'id': slug(l), 'q': q, 'label': l, 'kind': kind, 'why': why,
            'n': sum(1 for r in rows if l in (r.get('process') or [])), 'ex': ''}

qa = ([mk(l, *BREADTH[l], 'breadth') for l in sorted(BREADTH, key=lambda x: -sum(
          1 for r in rows if x in (r.get('process') or [])))]
      + [mk(l, *DERIVED[l], 'A') for l in sorted(DERIVED)])
qb = [{'id': slug(p['label']), 'q': 'B', 'label': p['label'], 'kind': p['kind'],
       'why': p['why'], 'n': p['df'], 'tn': p['title_df'], 'ex': example(p['terms'])}
      for p in prop]
items = qa + qb

# 'composite' comes from David's Concept Learning note: "not a process as many things
# can produce it. But not an individual principle either, as many principles might be
# used or come together to produce it."
KINDS = [('principle', 'Principle', '1'), ('process', 'Process', '2'),
         ('composite', 'Composite', '3'), ('phenomenon', 'Phenomenon', '4'),
         ('measure', 'Measure', '5'), ('model', 'Model', '6'),
         ('context', 'Context', '7'), ('reject', 'Too broad / not a concept', '0')]

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
  --k-measure:#4a6572; --k-model:#9c4646; --k-context:#5c6b3f; --k-reject:#9aa5a1; --k-composite:#b0682a;
  --shadow:0 1px 2px rgba(21,32,29,.05),0 10px 30px -20px rgba(21,32,29,.4);
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --ink:#e6ece9; --ink-2:#a7b6b1; --ink-3:#7c8c87;
  --paper:#101614; --card:#182220; --line:#2a3733; --accent:#5fbfae; --accent-soft:#1b302c;
  --k-principle:#5fbfae; --k-process:#7aa5e6; --k-phenomenon:#bd93c9;
  --k-measure:#94aab6; --k-model:#e08b8b; --k-context:#a3b878; --k-reject:#5a6a66; --k-composite:#d0a05c;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -20px rgba(0,0,0,.8);
}} }}
:root[data-theme="dark"] {{
  --ink:#e6ece9; --ink-2:#a7b6b1; --ink-3:#7c8c87;
  --paper:#101614; --card:#182220; --line:#2a3733; --accent:#5fbfae; --accent-soft:#1b302c;
  --k-principle:#5fbfae; --k-process:#7aa5e6; --k-phenomenon:#bd93c9;
  --k-measure:#94aab6; --k-model:#e08b8b; --k-context:#a3b878; --k-reject:#5a6a66; --k-composite:#d0a05c;
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
[data-kind="composite"] {{ --c:var(--k-composite); }}
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
  <p class="eyebrow">Catalog vocabulary &middot; {len(items)} calls, down from 477</p>
  <h1>Label the Vocabulary</h1>
  <p class="sub">Queue A is {len(qa)} labels whose kind I inferred rather than you deciding &mdash;
  confirm or flip them. Queue B is {len(qb)} additions derived from all 11,554 articles, each
  carrying its own evidence. Press a kind to accept it as that kind, or 0 to reject; <b>c</b> to
  say why &mdash; the reasons are what a tagging rule gets written from. Progress saves as you go.</p>

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
const STORE = 'catalog-label-v2';   // v1 keyed items by position; v2 keys by label
const SEED = {json.dumps({slug('Concept Learning'): 'principle'})};
const SEED_NOTES = {json.dumps({slug('Concept Learning'):
  'Likely too broad as well. Concept learning involves individual principles '
  '(generalization, discrimination) - maybe a second-order principle. Not a process, '
  'as many things can produce it; not an individual principle either.'})};

let state = {{}}, notes = {{}};
try {{
  const raw = JSON.parse(localStorage.getItem(STORE) || '{{}}');
  state = raw.state || raw || {{}};       // tolerate the pre-notes shape
  notes = raw.notes || {{}};
}} catch (e) {{ state = {{}}; notes = {{}}; }}
for (const k in SEED) if (!(k in state)) state[k] = SEED[k];
for (const k in SEED_NOTES) if (!(k in notes)) notes[k] = SEED_NOTES[k];
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
      '<span class="qtag">' + (it.q === 'breadth' ? 'Your breadth rule may reject this'
          : it.q === 'A' ? 'Confirm my call' : 'Proposed addition') + '</span>' +
      '<p class="term">' + esc(it.label) + '</p>' +
      '<p class="meta">' +
        (it.q === 'B'
          ? '<em>' + it.n + '</em> articles use it, <em>' + (it.tn || 0) + '</em> in the title'
          : 'tagged on <em>' + it.n + '</em> ' + (it.n === 1 ? 'entry' : 'entries')) +
        (it.ex ? ' &middot; &ldquo;' + esc(it.ex) + '&rdquo;' : '') + '</p>' +
      (it.why ? '<p class="why">Proposing <b>' + esc(it.kind) + '</b> &mdash; ' +
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
        '<span class="hint">' + (prev ? 'currently: ' + esc(prev) : 'press 0&ndash;7, or c to explain') + '</span>' +
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
