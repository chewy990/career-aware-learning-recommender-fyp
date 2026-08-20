# Graded Weak-Case Refinement Experiments

## Purpose And Status

The completed graded relevance review exposed ranking weaknesses that binary
labels had hidden. This record documents two bounded experiments conducted on
13 August 2026 after the weak-case diagnosis.

Both experiments are adaptive exploratory analyses. Their hypotheses were
declared before each run, but they reuse the same 258 author-graded judgements
that revealed the weaknesses. They are not held-out validation, independent
validation, or evidence of generalisation.

The production hybrid remains unchanged. The second variant is a candidate for
future independent validation rather than a production replacement.

## Baseline Diagnosis

The production hybrid recorded graded NDCG@5 of `0.8078`. It lost to the
content-based model for P003, P004, and P010. Data Engineer was the weakest
pathway at `0.4485`, with P010 at `0.349237` and P011 at `0.547664`.

Score tracing found two recurring causes:

- broad job-skill alignment rewarded resources for covering pathway skills even
  when those skills were not the learner's declared immediate weaknesses
- exact difficulty and prerequisite rewards could outweigh stronger evidence
  of immediate need, while an ungated focus on weak skills could recommend
  resources before the learner was ready

## Experiment 1: Ungated Weak-Skill Alignment

The first experiment replaced the `job_skill_alignment` signal with weighted
coverage of declared weak skills that retained a positive gap. Its weight stayed
at `0.15`. All other weights, signals, data, labels, and candidate rules stayed
fixed.

The variant raised macro graded NDCG@5 from `0.8078` to `0.8779` and raised Data
Engineer from `0.4485` to `0.7175`. However, P002 and P008 each fell by
`0.125201`. Machine Learning Engineer and Data Scientist each fell by `0.0626`
at pathway level. The variant also reduced prerequisite validity from `0.9091`
to `0.8727`.

The failure showed that weak-skill membership alone was too aggressive.
Resources covering several declared weaknesses could receive a large reward
despite unsuitable sequence, difficulty, or prerequisites. The variant failed
the declared pathway-safety criterion and was rejected.

## Experiment 2: Readiness-Gated Weak-Skill Alignment

The second experiment followed directly from the first failure. It used the
fixed signal:

`weak-skill alignment * difficulty match * prerequisite match`

The signal retained the existing `0.15` weight. No weight search was conducted.
The other signals, source data, graded labels, and candidate rules remained
unchanged.

Before execution, the variant was required to meet all four conditions:

1. Increase macro graded NDCG@5 by at least `0.01`.
2. Produce a positive mean change across P003, P004, P010, and P011.
3. Avoid a pathway graded NDCG@5 decrease below `-0.03`.
4. Avoid a difficulty or prerequisite validity decrease below `-0.05`.

The variant passed all four conditions.

| Measure | Production hybrid | Gated variant | Difference |
|---|---:|---:|---:|
| Precision@5 | 0.9455 | 0.9818 | +0.0363 |
| Recall@5 | 0.2077 | 0.2143 | +0.0066 |
| Graded NDCG@3 | 0.8143 | 0.9205 | +0.1062 |
| Graded NDCG@5 | 0.8078 | 0.8864 | +0.0786 |
| Graded NDCG@10 | 0.8181 | 0.8659 | +0.0478 |
| Prerequisite validity@5 | 0.9091 | 0.9636 | +0.0545 |
| Skill-gap coverage@5 | 0.6126 | 0.6051 | -0.0075 |

Five profiles improved, six tied, and none declined. Data Engineer rose from
`0.4485` to `0.6879`. P010 rose from `0.349237` to `0.596116`, and P011 rose
from `0.547664` to `0.779671`. No pathway declined.

The mean paired graded NDCG@5 difference was `+0.078611`, with a bootstrap
interval of `[+0.021862, +0.135846]` and `dz=0.782436`. The exact two-sided
permutation result was `p=0.0625`. Only five profiles had non-zero differences,
so `0.0625` is the smallest attainable two-sided sign-flip p-value. This is not
a statistically significant result at `0.05`.

## Interpretation

The experiments support one bounded conclusion. Immediate weak-skill evidence
is more useful when it is conditioned on whether the resource is currently
learnable. Ungated weak-skill alignment over-prioritised resources that mentioned
several weaknesses. Difficulty and prerequisite gating removed the observed
regressions while preserving most weak-case gains.

The result does not justify production promotion because the same author-graded
answer key informed both diagnosis and evaluation. The absence of a second
reviewer prevents independent label validation. The current hybrid therefore
remains the maintained model, and the gated variant remains experimental.

## Evidence And Reproduction

- Frozen graded baseline: `outputs/graded_relevance_run/`
- Rejected ungated experiment: `outputs/weak_skill_alignment_experiment_run/`
- Gated candidate: `outputs/readiness_gated_alignment_experiment_run/`
- Ungated runner: `src/run_weak_skill_alignment_experiment.py`
- Gated runner: `src/run_readiness_gated_alignment_experiment.py`
- Variant implementation: `src/edu_recommender/weak_skill_alignment_experiment/`

Both experiment directories reproduce byte for byte from their runners. The
available scientific suite completed with 76 passing tests. The authentication
test was excluded because the local environment lacks its required `httpx2`
package. This environment limitation is unrelated to the ranking experiments.

## Final Robustness Experiments

Three non-tuning experiments followed under the frozen protocol in
`docs/final_robustness_protocol.md`.

Label-uncertainty sensitivity shifted every confidence-1 and confidence-2 grade
down or up by one, subject to the 1 to 3 bounds. Two further scenarios shifted
confidence-1 grades alone. The canonical grade file was never edited. The gated
minus production NDCG@5 difference stayed positive in every scenario, ranging
from `+0.0786` to `+0.0889`. No scenario produced a gated profile loss or a
negative pathway difference.

Leave-one-profile-out analysis omitted each of the 11 paired differences in
turn. Every retained ten-profile mean stayed positive. The range was `+0.061784`
when P010 was omitted to `+0.086472` when a tied profile was omitted. The
direction therefore does not depend on any single profile, although P010 and
P011 contribute the largest gains.

The counterfactual experiment used no relevance labels. It evaluated five
behavioural invariants across 1,126 eligible real cases. A total of 1,125 passed.
All 396 prerequisite-completion cases, 496 preferred-difficulty cases, 207
weakness-removal cases, and 11 irrelevant-topic cases passed. Fifteen of 16
skill-improvement cases passed.

The single failure was P001 with R061, `DataCamp Module SQL Filtering and
Sorting`. Raising SQL from 0 to the pathway requirement removed its skill-gap
signal, but also changed its prerequisite signal from 0 to 1. The prerequisite
contribution rose by `0.10`, outweighing the lost gap and content contributions.
Its total score rose from `0.480635` to `0.534407` even though the learner no
longer needed SQL development.

This failure exposes a boundary between readiness and need. The model correctly
recognises that R061 becomes learnable, but the additive prerequisite reward can
make a mastered-skill resource more prominent. The result is retained as a
limitation. It does not trigger another tuning cycle under the protocol stop
rule.

The three evidence directories are:

- `outputs/label_uncertainty_sensitivity_run/`
- `outputs/leave_one_profile_out_run/`
- `outputs/counterfactual_behavior_run/`

All manifests verify, and a second unchanged run reproduced every artifact byte
for byte. The available scientific suite now completes with 79 passing tests.
