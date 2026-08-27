#!/usr/bin/env python3
"""Generate the taxonomy review page (an Artifact) from the live taxonomy + data."""
import json, os, collections, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tax = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))
kinds = json.load(open(os.path.join(ROOT, '.validation/label_kinds.json')))['kinds']
rows = json.load(open(os.path.join(ROOT, 'data.json')))
canon = tax['canonical']
CI = {c.lower() for c in canon}

use = collections.Counter()
for r in rows:
    for t in (r.get('process') or []):
        use[t] += 1

off = [x for r in rows for x in (r.get('process') or []) if x.lower() not in CI]
cand = sorted({x for x in off if len(x.split()) <= 4})
off_n, cand_n, off_entries = len(off), len(cand), len({id(r) for r in rows if any(
    x.lower() not in CI for x in (r.get('process') or []))})

tagged = [r for r in rows if r.get('process')]
no_prin = sum(1 for r in tagged if not any(kinds.get(t) in ('principle', 'both') for t in r['process']))
no_proc = sum(1 for r in tagged if not any(kinds.get(t) in ('process', 'both') for t in r['process']))

KIND_META = [
 ('principle', 'Principle', 'A fundamental component that interacts within a process to predict its output. Usually inferred from behaviour rather than observed directly.'),
 ('process',   'Process',   'A pattern of behaviour-environment interaction you can arrange, which reliably produces a phenomenon.'),
 ('both',      'Both',      'Reads as a principle and as a procedure you run. These are the calls most worth your eye.'),
 ('phenomenon','Phenomenon','The reliable output a process produces. Distinct from both by your own definition.'),
 ('measure',   'Measure',   'A dependent variable, how the output is observed.'),
 ('model',     'Model',     'A formal quantitative account of principles.'),
 ('context',   'Context',   'The preparation or domain a study sits in, not a behavioural relation.'),
]

kt = collections.Counter(kinds[c] for c in canon)
inst = collections.Counter()
for t, n in use.items():
    inst[kinds.get(t, 'off')] += n
tot_inst = sum(inst.values())

def esc(s): return html.escape(str(s))

groups = ''
for key, name, desc in KIND_META:
    labels = sorted([c for c in canon if kinds[c] == key], key=lambda x: (-use[x], x))
    chips = ''.join(
        f'<li><span class="lb">{esc(l)}</span>'
        f'<span class="ct">{use[l] or ""}</span></li>' for l in labels)
    groups += f'''
    <section class="grp" data-kind="{key}">
      <header class="grp-h">
        <h3>{esc(name)}</h3>
        <span class="grp-n">{len(labels)} labels &middot; {inst[key]} uses</span>
      </header>
      <p class="grp-d">{esc(desc)}</p>
      <ul class="chips">{chips}</ul>
    </section>'''

bars = ''.join(
    f'<div class="bar" style="--w:{100*inst[k]/tot_inst:.2f}%" data-kind="{k}">'
    f'<span class="bar-l">{esc(n)}</span>'
    f'<span class="bar-v">{100*inst[k]/tot_inst:.0f}%</span></div>'
    for k, n, _ in KIND_META if inst[k])
bars += (f'<div class="bar" style="--w:{100*inst["off"]/tot_inst:.2f}%" data-kind="off">'
         f'<span class="bar-l">Not in the vocabulary</span>'
         f'<span class="bar-v">{100*inst["off"]/tot_inst:.0f}%</span></div>')

cand_html = ''.join(f'<li>{esc(c)}</li>' for c in cand)

doc = f'''<title>Processes and Principles</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;1,400&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --ink:#15201d; --ink-2:#41544e; --ink-3:#71857e;
  --paper:#f4f6f4; --card:#fbfcfb; --line:#d9e0dc;
  --accent:#0f6b60; --accent-soft:#e2efeb;
  --k-principle:#0f6b60; --k-process:#2f5d9e; --k-both:#8a5a1f;
  --k-phenomenon:#7a4a86; --k-measure:#4a6572; --k-model:#9c4646; --k-context:#5c6b3f;
  --k-off:#a2aeaa;
  --shadow:0 1px 2px rgba(21,32,29,.05),0 8px 24px -16px rgba(21,32,29,.28);
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ink:#e6ece9; --ink-2:#a7b6b1; --ink-3:#7c8c87;
    --paper:#101614; --card:#182220; --line:#2a3733;
    --accent:#5fbfae; --accent-soft:#1b302c;
    --k-principle:#5fbfae; --k-process:#7aa5e6; --k-both:#d0a05c;
    --k-phenomenon:#bd93c9; --k-measure:#94aab6; --k-model:#e08b8b; --k-context:#a3b878;
    --k-off:#5a6a66;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px -16px rgba(0,0,0,.7);
  }}
}}
:root[data-theme="dark"] {{
  --ink:#e6ece9; --ink-2:#a7b6b1; --ink-3:#7c8c87;
  --paper:#101614; --card:#182220; --line:#2a3733;
  --accent:#5fbfae; --accent-soft:#1b302c;
  --k-principle:#5fbfae; --k-process:#7aa5e6; --k-both:#d0a05c;
  --k-phenomenon:#bd93c9; --k-measure:#94aab6; --k-model:#e08b8b; --k-context:#a3b878;
  --k-off:#5a6a66;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px -16px rgba(0,0,0,.7);
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--paper); color:var(--ink);
  font:400 17px/1.65 "Source Sans 3", ui-sans-serif, system-ui, sans-serif;
  -webkit-font-smoothing:antialiased;
}}
.wrap {{ max-width:76rem; margin:0 auto; padding:clamp(2rem,5vw,4.5rem) clamp(1.1rem,4vw,3rem) 5rem; }}
h1,h2,h3 {{ font-family:Spectral, Georgia, serif; text-wrap:balance; margin:0; }}
h1 {{ font-size:clamp(2.1rem,5vw,3.2rem); font-weight:600; line-height:1.1; letter-spacing:-.015em; }}
h2 {{ font-size:clamp(1.35rem,2.6vw,1.8rem); font-weight:600; }}
h3 {{ font-size:1.12rem; font-weight:600; }}
.eyebrow {{
  font:500 .72rem/1 "IBM Plex Mono", ui-monospace, monospace;
  letter-spacing:.16em; text-transform:uppercase; color:var(--accent); margin:0 0 1rem;
}}
.lede {{ font-size:1.14rem; color:var(--ink-2); max-width:63ch; margin:1.1rem 0 0; }}
header.top {{ border-bottom:1px solid var(--line); padding-bottom:2.4rem; margin-bottom:2.8rem; }}
section.blk {{ margin-top:3.4rem; }}
section.blk > h2 {{ margin-bottom:.5rem; }}
section.blk > .sub {{ color:var(--ink-2); max-width:63ch; margin:0 0 1.6rem; }}

.defs {{ display:grid; gap:1rem; grid-template-columns:repeat(auto-fit,minmax(19rem,1fr)); margin-top:2rem; }}
.def {{
  background:var(--card); border:1px solid var(--line); border-radius:3px;
  padding:1.3rem 1.4rem; box-shadow:var(--shadow); border-top:2px solid var(--accent);
}}
.def h3 {{ font-family:"Source Sans 3",sans-serif; font-size:.74rem; font-weight:600;
  letter-spacing:.14em; text-transform:uppercase; color:var(--accent); margin-bottom:.5rem; }}
.def p {{ margin:0; color:var(--ink-2); font-size:.97rem; }}
.def q {{ display:block; margin-top:.7rem; font-family:Spectral,Georgia,serif;
  font-style:italic; color:var(--ink); font-size:1.02rem; }}

.stats {{ display:grid; gap:.9rem; grid-template-columns:repeat(auto-fit,minmax(11rem,1fr)); margin:1.6rem 0 0; }}
.stat {{ background:var(--card); border:1px solid var(--line); border-radius:3px; padding:1rem 1.1rem; }}
.stat b {{ display:block; font:500 1.85rem/1 "IBM Plex Mono",monospace;
  font-variant-numeric:tabular-nums; letter-spacing:-.02em; }}
.stat span {{ display:block; margin-top:.4rem; font-size:.85rem; color:var(--ink-3); }}

.bars {{ display:flex; flex-direction:column; gap:.45rem; margin-top:1.4rem; }}
.bar {{ display:grid; grid-template-columns:1fr auto; align-items:center; gap:1rem;
  padding:.5rem .8rem; border-radius:2px; position:relative; isolation:isolate; overflow:hidden; }}
.bar::before {{ content:""; position:absolute; inset:0 auto 0 0; width:var(--w);
  background:var(--c); opacity:.17; z-index:-1; }}
.bar-l {{ font-size:.93rem; font-weight:600; color:var(--c); }}
.bar-v {{ font:500 .88rem "IBM Plex Mono",monospace; font-variant-numeric:tabular-nums; color:var(--ink-3); }}

[data-kind="principle"] {{ --c:var(--k-principle); }}
[data-kind="process"] {{ --c:var(--k-process); }}
[data-kind="both"] {{ --c:var(--k-both); }}
[data-kind="phenomenon"] {{ --c:var(--k-phenomenon); }}
[data-kind="measure"] {{ --c:var(--k-measure); }}
[data-kind="model"] {{ --c:var(--k-model); }}
[data-kind="context"] {{ --c:var(--k-context); }}
[data-kind="off"] {{ --c:var(--k-off); }}

.grps {{ display:grid; gap:1.1rem; }}
.grp {{ background:var(--card); border:1px solid var(--line); border-left:3px solid var(--c);
  border-radius:3px; padding:1.2rem 1.3rem 1.35rem; box-shadow:var(--shadow); }}
.grp-h {{ display:flex; align-items:baseline; justify-content:space-between; gap:1rem; flex-wrap:wrap; }}
.grp-h h3 {{ color:var(--c); }}
.grp-n {{ font:500 .8rem "IBM Plex Mono",monospace; color:var(--ink-3); font-variant-numeric:tabular-nums; }}
.grp-d {{ margin:.35rem 0 .95rem; color:var(--ink-2); font-size:.94rem; max-width:70ch; }}
.chips {{ list-style:none; margin:0; padding:0; display:flex; flex-wrap:wrap; gap:.4rem; }}
.chips li {{ display:inline-flex; align-items:baseline; gap:.45rem; padding:.28rem .6rem;
  border:1px solid var(--line); border-radius:2px; background:var(--paper); font-size:.9rem; }}
.chips .ct {{ font:500 .76rem "IBM Plex Mono",monospace; color:var(--ink-3); font-variant-numeric:tabular-nums; }}

details.cands {{ margin-top:1.3rem; border:1px solid var(--line); border-radius:3px;
  background:var(--card); padding:0; }}
details.cands summary {{ cursor:pointer; padding:.95rem 1.2rem; font-weight:600; font-size:.96rem; }}
details.cands summary:focus-visible {{ outline:2px solid var(--accent); outline-offset:-2px; }}
details.cands ul {{ list-style:none; margin:0; padding:0 1.2rem 1.2rem; columns:3; column-gap:1.6rem;
  font-size:.88rem; color:var(--ink-2); }}
details.cands li {{ break-inside:avoid; padding:.12rem 0; }}
@media (max-width:56rem) {{ details.cands ul {{ columns:2; }} }}
@media (max-width:36rem) {{ details.cands ul {{ columns:1; }} }}

.note {{ border-left:2px solid var(--accent); padding:.15rem 0 .15rem 1rem;
  color:var(--ink-2); margin-top:1.5rem; max-width:66ch; font-size:.97rem; }}
footer {{ margin-top:4rem; padding-top:1.4rem; border-top:1px solid var(--line);
  color:var(--ink-3); font-size:.85rem; }}
</style>

<div class="wrap">
<header class="top">
  <p class="eyebrow">Catalog vocabulary &middot; proposal for review</p>
  <h1>Processes and Principles</h1>
  <p class="lede">The catalog stores one flat list of tags. Your distinction says it holds at least
  two different kinds of thing, and the tagged data already behaves that way &mdash; the split is
  latent, just unmarked. This is a proposed kind for all {len(canon)} labels, for you to correct.</p>
  <div class="defs">
    <div class="def">
      <h3>Process</h3>
      <p>The pattern of behaviour-environment interactions that consistently leads to a particular
      phenomenon. Something you arrange and run.</p>
      <span class="q">&ldquo;What happens reliably when I run this?&rdquo;</span>
    </div>
    <div class="def">
      <h3>Principle</h3>
      <p>The fundamental components that interact within any given process to predict precisely the
      output you will see. Like gravity or an electromagnetic field, usually known through its
      output rather than directly.</p>
    </div>
  </div>
</header>

<section class="blk">
  <h2>Where the tags fall today</h2>
  <p class="sub">Every tag instance across the {len(tagged)} tagged entries, sorted into the proposed kinds.
  Process and principle are already the two largest groups by a wide margin.</p>
  <div class="bars">{bars}</div>
  <div class="stats">
    <div class="stat"><b>{no_prin}</b><span>tagged entries with no principle ({100*no_prin//len(tagged)}%)</span></div>
    <div class="stat"><b>{no_proc}</b><span>tagged entries with no process ({100*no_proc//len(tagged)}%)</span></div>
    <div class="stat"><b>{off_n}</b><span>tag uses outside the vocabulary</span></div>
    <div class="stat"><b>{cand_n}</b><span>distinct expansion candidates</span></div>
  </div>
  <p class="note">If the goal is a process <em>and</em> a principle for every article, most tagged
  entries are incomplete rather than wrong &mdash; they name one side of the pair. That is a gap to
  fill on re-review, not a correction to make.</p>
</section>

<section class="blk">
  <h2>The proposed kinds</h2>
  <p class="sub">Two kinds could not absorb everything without distorting it, so this proposes seven.
  You said there is no reason to fix the number in advance; this is what the {len(canon)} labels
  actually demanded. Counts after each label are how often it is currently used.</p>
  <div class="grps">{groups}</div>
</section>

<section class="blk">
  <h2>Expanding the vocabulary</h2>
  <p class="sub">{off_n} tag uses sit outside the vocabulary entirely, across {off_entries} entries.
  {cand_n} of them are short concept-like phrases rather than prose &mdash; real behavioural concepts
  the {len(canon)}-label list cannot express. They came from your students and from the validation
  pipeline independently, which is decent evidence they are needed.</p>
  <details class="cands">
    <summary>All {cand_n} candidates</summary>
    <ul>{cand_html}</ul>
  </details>
  <p class="note">These are deliberately still in <code>data.json</code>. Mapping them onto existing
  labels destroys meaning &mdash; <em>Schedules of Reinforcement</em> collapsing to
  <em>Reinforcement</em> loses the schedule entirely &mdash; so nothing was auto-mapped.</p>
</section>

<footer>
  Generated from <code>taxonomy.json</code> ({len(canon)} canonical labels, {len(tax['merges'])} merge rules)
  and <code>data.json</code> on the <code>overnight-validation</code> branch.
  Nothing here has been applied to the catalog.
</footer>
</div>
'''
out = os.path.join(ROOT, '.validation/taxonomy_review.html')
open(out, 'w').write(doc)
print(f'wrote {out} ({len(doc)} bytes); {len(canon)} labels, {cand_n} candidates')
