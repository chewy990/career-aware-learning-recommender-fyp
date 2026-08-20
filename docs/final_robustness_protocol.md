# Final Robustness Experiment Protocol

Version: 1  
Frozen: 13 August 2026  
Scope: three final non-tuning experiments

## Shared Rules

The production hybrid and readiness-gated experimental variant are compared
without changing either ranking formula. No model weight, source dataset,
canonical grade, profile, or candidate rule may be edited from the result.

Each experiment writes to a new output directory. Every manifest records input,
code, and output SHA-256 hashes. A second unchanged run must reproduce every
artifact byte for byte.

These experiments test robustness and expected behaviour. They do not provide
independent validation because the relevance grades remain a blinded author
self-review.

## Experiment 1: Label-Uncertainty Sensitivity

The six confidence-1 and 44 confidence-2 judgements are uncertain. The
canonical grade file remains unchanged. Four deterministic in-memory scenarios
are evaluated:

1. Decrease every confidence-1 and confidence-2 grade by one, with grade 1 as
   the lower bound.
2. Increase every confidence-1 and confidence-2 grade by one, with grade 3 as
   the upper bound.
3. Decrease confidence-1 grades by one and leave all others unchanged.
4. Increase confidence-1 grades by one and leave all others unchanged.

The primary result is gated-minus-production macro graded NDCG@5. The direction
is stable if it remains positive in all four scenarios. Pathway differences,
profile wins, ties, and losses are secondary diagnostics. The scenarios are not
alternative labels and must not be written to `data/`.

## Experiment 2: Leave-One-Profile-Out Stability

Start from the 11 paired gated-minus-production graded NDCG@5 differences.
Recalculate their mean eleven times, omitting exactly one profile each time.

The direction is stable if every leave-one-profile-out mean remains positive.
Report the minimum, maximum, and the profile whose omission produces each.
This experiment does not refit or rerank either model.

## Experiment 3: Counterfactual Behaviour

This experiment uses no relevance labels. It evaluates the readiness-gated
variant against five predeclared invariants across every eligible real case.

1. Adding all missing prerequisites to completed topics must set the target
   resource's prerequisite signal to 1 and must not lower its total score.
2. Raising a declared weak skill to its pathway requirement and removing the
   weak flag must not increase the total score of a resource covering only that
   skill.
3. Moving preferred difficulty to a resource's level, when that level is closer
   than the original preference, must increase its difficulty signal and must
   not lower its total score.
4. Removing one declared weakness must not increase the total score of a
   resource whose only declared-weak match was that skill.
5. Adding an unknown completed-topic token must leave the complete top-ten
   ranking, scores, and explanations unchanged.

Broad tracks and supporting-only formats remain excluded, matching the normal
candidate policy. The experiment passes only if every eligible case satisfies
its invariant. Any failure must be retained and explained rather than removed.

## Stop Rule

After these three experiments, model experimentation against the existing
profiles and author-graded labels ends. Findings may change confidence in the
experimental candidate, but cannot trigger another tuning cycle.
