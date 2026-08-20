# Hard-Prerequisite Eligibility Experiment Protocol

## Question

Does removing currently ineligible resources before hybrid ranking eliminate prerequisite failures without materially weakening relevance ranking?

## Frozen Baseline

- Phase 5 run: `59b8164bc31d1c98`
- Dataset: unchanged six validated source CSVs
- Profiles: unchanged 11 curated evaluation profiles
- Labels: unchanged relevance judgements
- Hybrid weights and scores: unchanged
- Candidate exclusions already used by the baseline, such as broad tracks and supporting-only formats: unchanged

## Experimental Change

The experimental hybrid excludes a resource before scoring when any listed prerequisite is neither:

- present in `completed_topics`, nor
- present in `current_skills` at level 1 or above.

Eligible resources retain their original hybrid scores and deterministic ordering. The candidate list is refilled from the next eligible resources so that K remains comparable.

## Predeclared Outcomes

The primary ranking outcome is the within-profile change in NDCG@5.

Precision@5 and Recall@5 are secondary ranking outcomes. The three K=5 ranking comparisons use exact two-sided sign-flip permutation tests, exact Wilcoxon signed-rank sensitivity checks, seeded 10,000-replicate bootstrap intervals, paired standardized effect `dz`, and one Holm correction across the three planned tests.

Metrics at K=3 and K=10 are descriptive robustness checks. Additional diagnostics are:

- prerequisite validity
- number of changed profiles
- removed and replacement resources
- ranking overlap
- profile and pathway concentration of any losses
- catalogue, skill-gap, provider, format, diversity, and difficulty effects

## Interpretation Rule

- The implementation is valid only if every experimental recommendation satisfies the hard rule and each profile retains a full top-10 list.
- A higher prerequisite-validity rate is a suitability improvement, not automatically an overall model improvement.
- A positive mean ranking change does not prove general superiority with only 11 curated profiles.
- A negative or mixed ranking result must be reported; weights, labels, and source data must not be changed to rescue the experiment.
- The experimental rule must not replace the production hybrid merely because it performs well on the same reporting profiles.

The independent relevance-label audit remains a separate human-review gate. This experiment cannot substitute for that audit.
