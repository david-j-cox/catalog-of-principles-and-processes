#!/usr/bin/env python3
"""Propose a kind for every canonical label, per David's process/principle distinction.

  principle  a fundamental component that interacts within a process to predict the
             output. Usually inferred from behaviour rather than observed directly -
             the gravity/electromagnetism analogy. Reinforcement, discrimination.
  process    a pattern of behaviour-environment interaction you can ARRANGE, which
             reliably produces a phenomenon. "What happens when I run this?"
             Schedules, shaping, chaining, matching-to-sample.
  phenomenon the reliable OUTPUT a process produces. Behavioural contrast, peak shift.
             Distinct from both by David's own definition ("...lead to a particular
             phenomena"), so it needs its own kind rather than being forced into one.
  measure    a dependent variable - how the output is observed. Response rate, IRT.
  model      a formal quantitative account OF principles. Matching law, power law.
  context    the preparation or domain a study sits in, not a behavioural relation.
             Behavioural pharmacology, foraging.

Every label takes exactly ONE kind - nothing is both. Two rules from David decide the
hard cases: an absence cannot be a fundamental component (so extinction is a process,
not a principle - applied to one response it is reallocation relative to the other
contingencies in effect); and if many different processes converge on it, it is a
principle (discrimination, generalization, avoidance).

Writes .validation/label_kinds.json. Does not touch data.json.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
canon = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))['canonical']

KINDS = {
 'principle': [
   'Reinforcement', 'Positive Reinforcement', 'Negative Reinforcement', 'Punishment',
   'Positive Punishment', 'Negative Punishment', 'Conditioned Reinforcement',
   'Conditioned Punishment', 'Alternative Reinforcement', 'Noncontingent Reinforcement',
   'Differential Reinforcement', 'Delay of Reinforcement', 'Delay', 'Contingency',
   'Motivating Operations', 'Deprivation', 'Response Effort', 'Stimulus Control',
   'Aversive Control', 'Aversive Stimuli', 'Aversive Stimuli: Electric Shock',
   'Conditioned Excitation', 'Conditioned Inhibition', 'Temporal Control',
   'Temporal Relations', 'Compound Stimuli', 'Stimulus Classes', 'Response Produced Stimuli',
   'Changeover Delay', 'Stimulus Discriminability',
   'Discrimination', 'Generalization', 'Avoidance',   # (D) many processes get you these
   'Stimulus Generalization', 'Temporal Discrimination',  # follow their parents
   'Escape',                          # parallel to Avoidance
   'Stimulus Equivalence', 'Concept Learning',        # emergent, convergent endpoints
   'Habituation',                     # convergent relation, many procedures reach it
 ],
 'process': [
   'Extinction',                      # (D) absence of a thing cannot be a principle
   'Classical Conditioning', 'Operant Conditioning', 'Conditioning',
   'Second-Order Conditioning',       # arrangements you run, not convergent endpoints
   'Shaping', 'Behavioral Chaining', 'Magazine Training', 'Autoshaping', 'Time-Out',
   'Token Economy', 'Error Correction', 'Repeated Acquisition', 'Discrete Trials',
   'Discrete Trial Teaching', 'Matching to Sample', 'Delayed Matching to Sample',
   'Discrimination Learning', 'Conditional Discrimination', 'Successive Discrimination',
   'Discriminated Avoidance', 'Differential Suppression', 'Response Differentiation',
   'Changeover', 'Signal Detection',
   'Schedule: Alternating', 'Schedule: Chain', 'Schedule: Concurrent',
   'Schedule: Concurrent Chains', 'Schedule: Concurrent Variable-Interval',
   'Schedule: Conjunctive', 'Schedule: Continuous',
   'Schedule: Differential Reinforcement of High Rates',
   'Schedule: Differential Reinforcement of Low Rates',
   'Schedule: Differential Reinforcement of Other Behavior',
   'Schedule: Fixed Interval', 'Schedule: Fixed Ratio', 'Schedule: Fixed Time',
   'Schedule: Interdependent', 'Schedule: Mixed', 'Schedule: Multiple',
   'Schedule: Second-Order', 'Schedule: Tandem', 'Schedule: Variable Interval',
   'Schedule: Variable Ratio', 'Schedule: Variable Time',
 ],
 # David's rule (2026-08-27): an absence cannot be a fundamental component, so
 # extinction is a process only - applied to one response it is reallocation relative
 # to the other contingencies in effect. Conversely, if MANY different processes
 # converge on it, it is a principle. That rule dissolves the 'both' kind entirely;
 # every label below now takes one side. Entries marked (D) are David's explicit calls.
 'phenomenon': [
   'Behavioral Contrast', 'Local Contrast', 'Peak Shift', 'Post-Reinforcement Pause',
   'Generalization Gradient', 'Adjunctive Behavior', 'Elicited Responding',
   'Operant Responding', 'Response Allocation', 'Aggression', 'Imprinting',
   'Overmatching', 'Undermatching', 'Response Bias', 'Bias', 'Momentary Maximizing',
   'Conditioned Suppression', 'Imitation',   # measured outcomes, not components
   'Choice', 'Remembering', 'Short-Term Memory', 'Stimulus Substitution',
 ],
 'measure': [
   'Response Rate', 'Interresponse Time', 'Measurement: Duration', 'Response Topography',
 ],
 'model': [
   'Matching Law', 'Power Law', 'Delay-Reduction Hypothesis', 'Additivity Theory',
   'Optimization',
 ],
 'context': [
   'Behavioral Pharmacology', 'Foraging',
 ],
}

kind_of = {}
dupe = []
for k, labels in KINDS.items():
    for l in labels:
        if l in kind_of:
            dupe.append(l)
        kind_of[l] = k

missing = [c for c in canon if c not in kind_of]
extra = [l for l in kind_of if l not in canon]
assert not dupe, f'label assigned twice: {dupe}'
assert not extra, f'classified a label that is not canonical: {extra}'
assert not missing, f'canonical label with no kind: {missing}'

out = {'kinds': {c: kind_of[c] for c in canon},
       'counts': {k: sum(1 for c in canon if kind_of[c] == k) for k in KINDS}}
json.dump(out, open(os.path.join(ROOT, '.validation/label_kinds.json'), 'w'), indent=2)
for k, v in out['counts'].items():
    print(f'  {k:11} {v:3}')
print(f'  {"TOTAL":11} {len(canon):3}')
