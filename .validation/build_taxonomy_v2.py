#!/usr/bin/env python3
"""Rebuild the taxonomy: fold duplicates, split compound schedule labels.

Decision (David, 2026-08-27): the bare "Schedule: X" spelling wins over
"Schedules of Reinforcement: X". But that spelling carried a distinction worth
keeping, so the compound splits into TWO tags rather than collapsing:

    Schedules of Reinforcement: Fixed Interval
        -> Schedule: Fixed Interval   (the arrangement you run)
        +  Reinforcement              (the consequence type)

which requires merges to be one-to-many. A punishment schedule maps the same way
to Schedule: X + Punishment.

Writes .validation/taxonomy.json in place (canonical + merges), and prints a diff.
"""
import json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAX = os.path.join(ROOT, '.validation/taxonomy.json')
tax = json.load(open(TAX))
old_canon = list(tax['canonical'])

# --- schedule compounds: split into arrangement + consequence type -----------
SCHEDULE_SPLIT = {
    'Schedules of Reinforcement: Concurrent': ['Schedule: Concurrent', 'Reinforcement'],
    'Schedules of Reinforcement: Continuous Reinforcement': ['Schedule: Continuous', 'Reinforcement'],
    'Schedules of Reinforcement: DRL': ['Schedule: Differential Reinforcement of Low Rates', 'Reinforcement'],
    'Schedules of Reinforcement: Differential Reinforcement of Other Behavior':
        ['Schedule: Differential Reinforcement of Other Behavior', 'Reinforcement'],
    'Schedules of Reinforcement: Fixed Interval': ['Schedule: Fixed Interval', 'Reinforcement'],
    'Schedules of Reinforcement: Fixed Rate': ['Schedule: Fixed Ratio', 'Reinforcement'],
    'Schedules of Reinforcement: Fixed Ratio': ['Schedule: Fixed Ratio', 'Reinforcement'],
    'Schedules of Reinforcement: Mixed': ['Schedule: Mixed', 'Reinforcement'],
    'Schedules of Reinforcement: Multiple': ['Schedule: Multiple', 'Reinforcement'],
    'Schedules of Reinforcement: Multiple Schedules': ['Schedule: Multiple', 'Reinforcement'],
    'Schedules of Reinforcement: Variable Interval': ['Schedule: Variable Interval', 'Reinforcement'],
    'Schedules of Reinforcement: Variable Ratio': ['Schedule: Variable Ratio', 'Reinforcement'],
    'Alternating Schedules of Reinforcement': ['Schedule: Alternating', 'Reinforcement'],
    'Multiple Schedules of Reinforcement': ['Schedule: Multiple', 'Reinforcement'],
    'Conjunctive Schedules': ['Schedule: Conjunctive'],
    'Second-Order Schedules': ['Schedule: Second-Order'],
    'DRL': ['Schedule: Differential Reinforcement of Low Rates'],
    'DRH': ['Schedule: Differential Reinforcement of High Rates'],
    'DRO': ['Schedule: Differential Reinforcement of Other Behavior'],
    'Differential Reinforcement: Low Rates': ['Schedule: Differential Reinforcement of Low Rates'],
    'Differential reinforcement of low rates': ['Schedule: Differential Reinforcement of Low Rates'],
    'Schedule: Chained': ['Schedule: Chain'],
    'Schedule: Concurrent-Chain': ['Schedule: Concurrent Chains'],
    'Schedule: Random Interval': ['Schedule: Variable Interval'],
}

# --- plain duplicates: spelling, number, typo, and near-synonym collapses -----
DUPES = {
    'Avoidance Behavior': 'Avoidance',
    'Avoidance Learning': 'Avoidance',
    'Behavior Contrast': 'Behavioral Contrast',
    'Behavioral contrast under multiple schedules': 'Behavioral Contrast',
    'Conditioned Supression': 'Conditioned Suppression',
    'Conditioned Reinforcer': 'Conditioned Reinforcement',
    'Aversive Stimulation': 'Aversive Stimuli',
    'Aversive Stimulus: Electric Shock': 'Aversive Stimuli: Electric Shock',
    'Electric Shock': 'Aversive Stimuli: Electric Shock',
    'Shock': 'Aversive Stimuli: Electric Shock',
    'Delayed Reinforcement': 'Delay of Reinforcement',
    'Reinforcement Delay': 'Delay of Reinforcement',
    'Reinforcement: Delayed': 'Delay of Reinforcement',
    'Generalization Gradients': 'Generalization Gradient',
    'Interresponse Times': 'Interresponse Time',
    'Match to Sample': 'Matching to Sample',
    'Delayed Match to Sample': 'Delayed Matching to Sample',
    'Reinforcement: Postive': 'Positive Reinforcement',
    'Reinforcement: Positive': 'Positive Reinforcement',
    'Reinforcer: Positive': 'Positive Reinforcement',
    'Reinforcement: Negative': 'Negative Reinforcement',
    'Punishment: Positive': 'Positive Punishment',
    'Punishment: Negative': 'Negative Punishment',
    'Postreinforcement Pause': 'Post-Reinforcement Pause',
    'Response Chains': 'Behavioral Chaining',
    'Signal-Detection Theory': 'Signal Detection',
    'Timeout': 'Time-Out',
    'Discriminability': 'Stimulus Discriminability',
    'Respondent Conditioning': 'Classical Conditioning',
    'Generalized Matching Law': 'Matching Law',
    'Herrnsteins Equation': 'Matching Law',
    'Matching': 'Matching Law',
    'Discrimination Training': 'Discrimination Learning',
}

# labels that name apparatus or a field, not a behavioural process or principle
DROP = ['Slide Projector', 'Visual Stimulus', 'Experimental Analysis of Behavior', 'Measurement']

new_labels = ['Schedule: Alternating', 'Schedule: Differential Reinforcement of Low Rates',
              'Schedule: Differential Reinforcement of High Rates',
              'Schedule: Differential Reinforcement of Other Behavior',
              'Delayed Matching to Sample', 'Positive Punishment', 'Negative Punishment']

merges = {}
for k, v in (tax.get('merges') or {}).items():
    merges[k] = [v] if isinstance(v, str) else list(v)
for k, v in SCHEDULE_SPLIT.items():
    merges[k] = v
for k, v in DUPES.items():
    merges[k] = [v]

canon = set(old_canon) | set(new_labels)
canon -= set(merges)          # anything now merged is no longer canonical
canon -= set(DROP)
for targets in merges.values():
    canon |= set(targets)     # every merge target must itself be canonical
canon = sorted(canon)

# resolve chains so no merge target is itself a merge key
for _ in range(5):
    changed = False
    for k, tgts in merges.items():
        flat = []
        for t in tgts:
            flat.extend(merges.get(t, [t]))
        if flat != tgts:
            merges[k] = list(dict.fromkeys(flat)); changed = True
    if not changed:
        break
bad = [k for k, v in merges.items() for t in v if t not in canon]
assert not bad, f'merge targets missing from canonical: {bad[:5]}'

tax['canonical'] = canon
tax['merges'] = merges
tax['merge_note'] = ('merges values are LISTS: a compound label may split into several tags '
                     '(Schedules of Reinforcement: X -> Schedule: X + Reinforcement).')
json.dump(tax, open(TAX, 'w'), indent=2, ensure_ascii=True)

print(f'canonical  {len(old_canon)} -> {len(canon)}')
print(f'merges     {len(tax.get("merges") or {})} rules ({sum(1 for v in merges.values() if len(v) > 1)} one-to-many)')
print(f'dropped    {DROP}')
print(f'added      {new_labels}')
