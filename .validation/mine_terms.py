#!/usr/bin/env python3
"""Mine candidate vocabulary terms from the whole corpus, using David's breadth rule.

The rule cuts both ways. "Classical Conditioning" is useless because it covers
everything; "Automatic Stimuimus Attenuator" is useless because it covers one paper.
So a usable label lives in a BAND of document frequency: common enough to be a concept
the literature returns to, rare enough to actually discriminate between articles.

Signals combined per candidate n-gram:
  df        how many of the 11,920 articles use the phrase
  in_title  how often it appears in a TITLE - titles name concepts, abstracts describe
  orphan    whether a human tagger already reached for this phrase and had no label

Prints the ranked candidates that are not already covered by the vocabulary.
"""
import json, os, re, collections, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(ROOT, 'data.json')))
tax = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))
canon = tax['canonical']

# --- the band ---------------------------------------------------------------
N = len(rows)
DF_MIN = 8               # below this a phrase names an experiment, not a concept
DF_MAX = int(N * 0.06)   # above this it is paradigm-level: true of everything

STOP = set('''the a an and or of in to on for with by as at from is are was were be been being
that this these those it its their his her they them we our us you your i he she which who whom
whose what when where why how all any both each few more most other some such no nor not only own
same so than too very can will just should now if then else while during before after above below
between into through over under again further once here there than have has had having do does did
doing would could may might must shall about against among within without upon across behind
beyond during except inside near off out outside past round since toward towards under underneath
until up upon versus via' effect effects study studies experiment experiments result results
data subject subjects present presented paper article report reported found finding findings
show showed shown suggest suggested indicate indicated observe observed obtain obtained
increase increased decrease decreased change changed different differences difference
condition conditions group groups control controls test tested testing measure measured
first second third one two three four five six seven eight nine ten also however thus therefore
used using use new higher lower greater less more high low large small long short'''.split())

WORD = re.compile(r"[a-z][a-z\-']+")

def phrases(text):
    """2-4 word phrases whose first and last token carry meaning."""
    out = set()
    for sent in re.split(r'[.;:!?()\[\]]', text):
        w = WORD.findall(sent)
        for n in (2, 3, 4):
            for i in range(len(w) - n + 1):
                g = w[i:i + n]
                if g[0] in STOP or g[-1] in STOP:
                    continue
                if sum(1 for x in g if x in STOP) > 1:
                    continue
                if any(len(x) < 3 for x in (g[0], g[-1])):
                    continue
                out.add(' '.join(g))
    return out

# --- entries that are not articles ------------------------------------------
# 336 catalog rows are journal front matter (editorial boards, volume indexes,
# errata). They carry no behaviour, so they must not seed the vocabulary - and they
# should never be tagged with a process or principle either.
FRONT = re.compile(r'^(author index|subject index|editorial board|contents of volume|'
                   r'index (of|to) volume|acknowledg|erratum|corrigendum|supplemental|'
                   r'list of|volume \d|title page|masthead|announcement|in memoriam|'
                   r'obituary|reviewers)', re.I)

df = collections.Counter()
tf_title = collections.Counter()
articles = 0
for r in rows:
    if FRONT.search((r.get('title') or '').strip()):
        continue
    articles += 1
    title = (r.get('title') or '').lower()
    body = title + ' . ' + (r.get('abstract') or '').lower()
    for p in phrases(body):
        df[p] += 1
    for p in phrases(title):
        tf_title[p] += 1

# --- what the vocabulary already covers -------------------------------------
def key(s):
    return ' '.join(sorted(w for w in WORD.findall(s.lower()) if w not in STOP))
# Coverage must be conceptual, not literal: "concurrent chains" is already
# `Schedule: Concurrent Chains`, and "interval schedules" is already the FI/VI family.
# So a candidate counts as covered when its content words are a SUBSET of an existing
# label's, or vice versa - not only on an exact key match.
def kset(s):
    return frozenset(w for w in WORD.findall(s.lower())
                     if w not in STOP and w not in ('schedule', 'schedules'))
COVER_SETS = [kset(c) for c in canon] + [kset(k) for k in tax['merges']]
COVER_SETS = [c for c in COVER_SETS if c]

def is_covered(phrase):
    ks = kset(phrase)
    if not ks:
        return True
    return any(ks <= c or c <= ks for c in COVER_SETS)

covered = {key(c) for c in canon}
covered |= {key(k) for k in tax['merges']}
# already-settled decisions must not come back as fresh proposals
covered |= {key(x) for x in (tax.get('rejected_too_broad') or [])}
covered |= {key(x) for x in ('Slide Projector', 'Visual Stimulus',
                             'Experimental Analysis of Behavior', 'Measurement',
                             'Schedules of Reinforcement')}

# --- a candidate must speak the domain's language ---------------------------
# The vocabulary and the phrases taggers reached for define what a behavioural label
# is made of. Requiring a shared content word drops species names (macaca mulatta,
# japanese quail) and journal boilerplate without hand-listing either.
DOMAIN = set()
for src in list(canon) + list(tax['merges']):
    DOMAIN |= {w for w in WORD.findall(src.lower()) if w not in STOP and len(w) > 3}
DOMAIN |= set('''reinforcer reinforcing punisher punishing responding response responses
stimulus stimuli schedule schedules contingency contingencies operant respondent behavior
behaviour discriminative reinforcement punishment extinction avoidance escape choice
preference delay delayed magnitude latency rate rates pause bout bouts allocation
acquisition retention forgetting remembering matching maximizing sensitivity bias
aversion aversive appetitive deprivation satiation motivation conditioned unconditioned
inhibition excitation generalization discrimination equivalence transitivity symmetry
reflexivity autoshaping shaping chaining fading prompting tolerance sensitization
habituation impulsivity self-control discounting momentum persistence variability
resurgence relapse renewal reinstatement induction interresponse postreinforcement'''.split())

# --- phrases a tagger already reached for -----------------------------------
orphans = set()
for r in rows:
    for t in (r.get('unmapped') or []):
        orphans.add(key(t))

cands = []
for p, n in df.items():
    if n < DF_MIN or n > DF_MAX:
        continue
    k = key(p)
    if not k or k in covered:
        continue
    if not any(w in DOMAIN for w in WORD.findall(p)):
        continue
    if is_covered(p):
        continue
    # a phrase that only ever occurs inside a longer phrase is not its own concept;
    # titles weighting handles most of that, and near-duplicates collapse on `key`
    score = math.log(n) * (1 + 2.0 * tf_title[p] / n) * (1.6 if k in orphans else 1.0)
    cands.append({'phrase': p, 'df': n, 'title_df': tf_title[p],
                  'orphan': k in orphans, 'score': round(score, 2), 'key': k})

# collapse phrases that normalise to the same concept, keeping the best-scoring form
best = {}
for c in sorted(cands, key=lambda c: -c['score']):
    if c['key'] not in best:
        best[c['key']] = c
cands = sorted(best.values(), key=lambda c: -c['score'])

json.dump(cands, open(os.path.join(ROOT, '.validation/mined_terms.json'), 'w'), indent=1)
print(f'corpus {N} rows, {articles} real articles ({N-articles} front matter excluded)')
print(f'band df {DF_MIN}-{DF_MAX} ({100*DF_MAX/N:.0f}% of corpus)')
print(f'distinct phrases seen: {len(df)}')
print(f'in band, not already covered: {len(cands)}')
print(f'  of which a tagger had reached for: {sum(1 for c in cands if c["orphan"])}')
print('\ntop 40 by score:')
for c in cands[:40]:
    flag = ' *' if c['orphan'] else '  '
    print(f'  {c["score"]:6.2f}{flag} df={c["df"]:4} title={c["title_df"]:3}  {c["phrase"]}')
