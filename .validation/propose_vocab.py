#!/usr/bin/env python3
"""Propose a covering vocabulary derived from the whole corpus.

Instead of 459 accept/reject calls on one-off strings, this proposes a small set of
labels chosen so that each one covers many articles. Every proposal carries its own
evidence: how many of the 11,554 real articles use the term, and how many put it in the
TITLE - a title term is what the paper is ABOUT, which is the strongest available signal
that the field treats it as a concept rather than a passing word.

Selection follows David's breadth rule at both ends. Nothing paradigm-level (Classical
Conditioning), nothing single-use (Automatic Stimuimus Attenuator). Sources: corpus
n-gram mining (mine_terms.py) plus a targeted probe for named EAB concepts, since a
concept can be central to the field yet lexically diffuse.

Writes .validation/proposed_vocab.json. Applies nothing.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(ROOT, 'data.json')))
tax = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))

FRONT = re.compile(r'^(author index|subject index|editorial board|contents of volume|'
                   r'index (of|to) volume|acknowledg|erratum|corrigendum|supplemental|'
                   r'list of|volume \d|title page|masthead|announcement|in memoriam|'
                   r'obituary|reviewers)', re.I)
arts = [r for r in rows if not FRONT.search((r.get('title') or '').strip())]

# label -> (kind, match terms, why)
PROPOSED = [
 # --- relapse: the vocabulary has none of it, and it is a whole modern literature ---
 ('Resurgence',              'phenomenon', ['resurgence'],
  'return of a previously reinforced response when a newer one is extinguished'),
 ('Renewal',                 'phenomenon', ['renewal'],
  'return of responding on a context change after extinction'),
 ('Reinstatement',           'phenomenon', ['reinstatement'],
  'return of responding after unsignalled reinforcer presentation'),
 ('Behavioral Momentum',     'principle',  ['behavioral momentum', 'behavioural momentum'],
  'resistance to change as a property of a reinforced response'),

 # --- associative interference: also entirely absent ---
 ('Blocking',                'phenomenon', ['blocking'],
  'prior conditioning to one cue prevents learning about a redundant one'),
 ('Overshadowing',           'phenomenon', ['overshadowing'],
  'the more salient element of a compound acquires control at the expense of the other'),
 ('Latent Inhibition',       'phenomenon', ['latent inhibition'],
  'pre-exposure retards later conditioning'),

 # --- behavioural economics / intertemporal choice: absent ---
 ('Delay Discounting',       'principle',  ['delay discounting', 'temporal discounting'],
  'value declines as a function of delay'),
 ('Probability Discounting', 'principle',  ['probability discounting'],
  'value declines as a function of odds against'),
 ('Self-Control',            'phenomenon', ['self-control', 'self control'],
  'choice of a larger later over a smaller sooner reinforcer'),
 ('Impulsivity',             'phenomenon', ['impulsivity', 'impulsive choice'],
  'the converse choice pattern'),
 ('Risky Choice',            'phenomenon', ['risky choice', 'risk sensitivity', 'risk-sensitive'],
  'choice under variable reinforcement outcomes'),
 ('Behavioral Economics',    'context',    ['behavioral economics', 'behavioural economics',
                                            'demand curve', 'unit price'],
  'the demand/elasticity framing of reinforcer value'),
 ('Melioration',             'principle',  ['melioration'],
  'allocation toward the locally higher return rate'),

 # --- reinforcer parameters: the catalog has delay, but not the others ---
 ('Reinforcer Magnitude',    'principle',  ['reinforcer magnitude', 'reinforcement magnitude',
                                            'reinforcer amount', 'magnitude of reinforcement'],
  'amount as a determinant, distinct from rate and delay'),
 ('Reinforcer Rate',         'principle',  ['reinforcement frequency', 'reinforcer rate',
                                            'rate of reinforcement'],
  'the other arm of the matching relation'),
 ('Reinforcer Quality',      'principle',  ['reinforcer quality', 'reinforcer type',
                                            'qualitatively different reinforcers'],
  'type as a determinant'),
 ('Reinforcer Devaluation',  'process',    ['reinforcer devaluation', 'devaluation'],
  'post-training reduction of reinforcer value, the goal-directed test'),
 ('Satiation',               'principle',  ['satiation', 'satiety'],
  'the counterpart to Deprivation, which the vocabulary already has'),

 # --- procedures the corpus runs constantly and cannot name ---
 ('Schedule: Progressive Ratio', 'process', ['progressive ratio', 'progressive-ratio'],
  'breakpoint procedure; a schedule family the list omits'),
 ('Schedule: Interlocking',  'process',    ['interlocking schedule'],
  'named by taggers, absent from the list'),
 ('Schedule: Limited Hold',  'process',    ['limited hold'],
  'named by taggers, absent from the list'),
 ('Peak Procedure',          'process',    ['peak procedure', 'peak interval'],
  'the standard timing preparation'),
 ('Conditioned Taste Aversion', 'process', ['taste aversion'],
  'a distinct preparation, not general classical conditioning'),
 ('Errorless Learning',      'process',    ['errorless'],
  'fading-based discrimination training'),
 ('Stimulus Fading',         'process',    ['stimulus fading', 'fading procedure'],
  'the mechanism errorless training uses'),
 ('Differential Outcomes',   'process',    ['differential outcomes'],
  'outcome-specific expectancies in conditional discrimination'),
 ('Observing Response',      'process',    ['observing response', 'observing behavior'],
  'responses that produce discriminative stimuli'),
 ('Response Cost',           'process',    ['response cost'],
  'a punishment procedure the list cannot express'),
 ('Omission Training',       'process',    ['omission'],
  'reinforcement contingent on not responding'),
 ('Token Economy: Token Reinforcement', 'process', ['token reinforcement', 'token economy'],
  'refines the existing Token Economy toward the reinforcer'),
 ('Reversal Learning',       'process',    ['reversal learning', 'serial reversal'],
  'repeated contingency reversal'),
 ('Time-Place Learning',     'process',    ['time-place learning', 'time place learning'],
  'temporal-spatial discrimination'),

 # --- stimulus-side concepts ---
 ('Discriminative Stimulus', 'principle',  ['discriminative stimulus', 'discriminative stimuli'],
  'the S-delta/S-D relation itself, distinct from Stimulus Control'),
 ('Unconditioned Stimulus',  'principle',  ['unconditioned stimulus', 'unconditioned stimuli'],
  'the respondent counterpart'),
 ('Functional Equivalence',  'principle',  ['functional equivalence'],
  'distinct from Stimulus Equivalence'),
 ('Interstimulus Interval',  'process',    ['interstimulus interval'],
  'a procedural parameter that determines the outcome'),
 ('Intertrial Interval',     'process',    ['intertrial interval'],
  'ditto'),

 # --- response-side and outcomes ---
 ('Behavioral Variability',  'phenomenon', ['behavioral variability', 'behavioural variability',
                                            'response variability'],
  'variability as an operant dimension'),
 ('Response Strength',       'principle',  ['response strength'],
  'the construct behind rate, resistance and persistence'),
 ('Resistance to Extinction','measure',    ['resistance to extinction'],
  'the standard persistence measure'),
 ('Response Bout',           'phenomenon', ['response bout', 'bout length', 'bout-and-pause'],
  'the microstructure of responding'),
 ('Anticipatory Contrast',   'phenomenon', ['anticipatory contrast'],
  'distinct from the Behavioral Contrast already listed'),
 ('Rule-Governed Behavior',  'phenomenon', ['rule-governed', 'rule governed', 'instructional control'],
  'verbally-mediated control'),
 ('Verbal Behavior',         'context',    ['verbal behavior', 'verbal behaviour'],
  'a domain, flagged since it may fail the breadth test'),
 ('Working Memory',          'phenomenon', ['working memory'],
  'sits beside the existing Short-Term Memory'),
 ('Reaction Time',           'measure',    ['reaction time', 'response latency'],
  'a dependent variable the list omits'),
]

txt = [((r.get('title') or '') + ' . ' + (r.get('abstract') or '')).lower() for r in arts]
tit = [(r.get('title') or '').lower() for r in arts]

out = []
for label, kind, terms, why in PROPOSED:
    df = sum(1 for t in txt if any(m in t for m in terms))
    tf = sum(1 for t in tit if any(m in t for m in terms))
    out.append({'label': label, 'kind': kind, 'df': df, 'title_df': tf,
                'terms': terms, 'why': why})

out.sort(key=lambda x: -x['df'])
json.dump(out, open(os.path.join(ROOT, '.validation/proposed_vocab.json'), 'w'), indent=1)

thin = [o for o in out if o['df'] < 8]
print(f'{len(out)} proposed labels, covering {len(arts)} real articles')
print(f'  median articles per label: {sorted(o["df"] for o in out)[len(out)//2]}')
print(f'  below the df>=8 floor (would fail the specificity end of the rule): {len(thin)}')
for t in thin:
    print(f'     {t["label"]} (df={t["df"]})')
print()
for o in out:
    print(f'  {o["df"]:4} art {o["title_df"]:3} ttl  {o["kind"]:11} {o["label"]}')
