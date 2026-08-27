#!/usr/bin/env python3
"""Apply David's 62 vocabulary decisions, and the rules they imply.

Three rules came out of the pass, in increasing order of reach:

RULE 1 - BREADTH. A label naming a paradigm rather than a specific relation is useless
even when true. He rejected every breadth candidate offered, including ones I expected
to survive (Second-Order Conditioning), plus Behavioral Economics, Verbal Behavior,
Rule-Governed Behavior, Concept Learning, Self-Control, Impulsivity and Risky Choice.
The bar is higher than I had been applying it.

RULE 2 - FOLD, DON'T DUPLICATE. "Stimulus equivalence is about the functional
equivalence of those stimuli. These are not separate concepts." -> merge.

RULE 3 - PARAMETERS ARE MEASURES, NOT PRINCIPLES. Stated eight times:
"more like a measure of a known input that would then drive the influence of a
principle within a process." A principle is the invisible thing doing the work; an
input you can point at, set, or read off the apparatus is a measure. He applied this to
Reinforcer Rate/Magnitude/Quality, Discriminative Stimulus, Unconditioned Stimulus,
Intertrial Interval, Interstimulus Interval and Observing Response.

Rule 3 has consequences he was never shown, because those labels were already in the
vocabulary classified as principles. They are applied here and listed as RULE-DERIVED so
they can be vetoed - they are inferences from his rule, not decisions he made.
"""
import json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAX = os.path.join(ROOT, '.validation/taxonomy.json')
KINDS_F = os.path.join(ROOT, '.validation/label_kinds.json')
tax = json.load(open(TAX))
kinds = json.load(open(KINDS_F))['kinds']

REJECT = ['Operant Conditioning', 'Conditioning', 'Behavioral Pharmacology', 'Foraging',
          'Operant Responding', 'Elicited Responding', 'Second-Order Conditioning',
          'Concept Learning']

FOLD = {'Functional Equivalence': 'Stimulus Equivalence'}

ADD = {
 'principle':  ['Satiation', 'Behavioral Momentum', 'Response Strength', 'Melioration'],
 'process':    ['Omission Training', 'Reinforcer Devaluation', 'Peak Procedure',
                'Schedule: Progressive Ratio', 'Conditioned Taste Aversion',
                'Reversal Learning', 'Response Cost', 'Time-Place Learning',
                'Errorless Learning', 'Differential Outcomes', 'Stimulus Fading',
                'Token Economy: Token Reinforcement', 'Schedule: Limited Hold',
                'Schedule: Interlocking'],
 'phenomenon': ['Delay Discounting', 'Probability Discounting', 'Blocking', 'Resurgence',
                'Overshadowing', 'Renewal', 'Latent Inhibition', 'Reinstatement',
                'Working Memory', 'Behavioral Variability', 'Anticipatory Contrast',
                'Response Bout'],
 'measure':    ['Reinforcer Rate', 'Reinforcer Magnitude', 'Reinforcer Quality',
                'Discriminative Stimulus', 'Unconditioned Stimulus', 'Intertrial Interval',
                'Interstimulus Interval', 'Reaction Time', 'Observing Response',
                'Resistance to Extinction'],
}

# RULE 3 carried into labels already in the vocabulary. Each is a direct parallel to one
# he decided: a stimulus you present, or a temporal/effort parameter you set.
RULE3 = {
 'Delay of Reinforcement':        'parallel to Intertrial Interval - a temporal parameter you set',
 'Delay':                         'same',
 'Changeover Delay':              'same',
 'Response Effort':               'a parameter you set, read off the apparatus',
 'Aversive Stimuli':              'parallel to Unconditioned Stimulus - an input you present',
 'Aversive Stimuli: Electric Shock': 'same, more specific',
 'Compound Stimuli':              'parallel to Discriminative Stimulus',
 'Response Produced Stimuli':     'parallel to Discriminative Stimulus',
 'Stimulus Discriminability':     'a property of the input you arrange',
}

canon = set(tax['canonical'])
merges = {k: (v if isinstance(v, list) else [v]) for k, v in tax['merges'].items()}

canon -= set(REJECT)
tax['rejected_too_broad'] = sorted(set(tax.get('rejected_too_broad') or []) | set(REJECT))
for src, dst in FOLD.items():
    canon.discard(src)
    merges[src] = [dst]
for k, labels in ADD.items():
    canon |= set(labels)

new_kinds = {}
for c in canon:
    if c in RULE3:
        new_kinds[c] = 'measure'
    elif c in kinds:
        new_kinds[c] = kinds[c]
    else:
        new_kinds[c] = next(k for k, v in ADD.items() if c in v)

# a merge whose TARGET was just rejected has nowhere to point: drop the rule, so the
# source label lands in `unmapped` and the entry surfaces as needing a specific tag
dead = {k: v for k, v in merges.items() if any(t not in canon for t in v)}
for k in dead:
    del merges[k]

canon = sorted(canon)
assert not [c for c in canon if c in merges], 'merge key survived into canonical'
assert all(t in canon for v in merges.values() for t in v), 'merge target not canonical'
assert set(new_kinds) == set(canon)

tax['canonical'] = canon
tax['merges'] = merges
json.dump(tax, open(TAX, 'w'), indent=2, ensure_ascii=True)
json.dump({'kinds': {c: new_kinds[c] for c in canon},
           'counts': dict(collections.Counter(new_kinds.values()))},
          open(KINDS_F, 'w'), indent=2)

print(f'canonical -> {len(canon)} labels')
for k, v in sorted(collections.Counter(new_kinds.values()).items(), key=lambda x: -x[1]):
    print(f'   {k:11} {v:3}')
print(f'\nrejected as too broad this pass: {len(REJECT)}')
print(f'merge rules dropped (target was rejected): {len(dead)} -> {sorted(dead)}')
print(f'folded: {FOLD}')
print(f'\nRULE-DERIVED, not decided by David - {len(RULE3)} existing labels moved principle -> measure:')
for l, why in RULE3.items():
    print(f'   {l:34} {why}')
