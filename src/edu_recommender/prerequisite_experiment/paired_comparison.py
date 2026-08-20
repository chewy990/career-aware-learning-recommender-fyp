"""Own prerequisite experiment paired comparison responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from statistics import mean, median, stdev

from edu_recommender.evaluation import (
    bootstrap_mean_confidence_interval,
)
from edu_recommender.statistical_comparison import (
    effect_magnitude,
    exact_paired_permutation_test,
    exact_wilcoxon_signed_rank_test,
    holm_adjust,
)

from .contracts import (
    BASELINE_MODEL,
    PLANNED_METRICS,
    PRIMARY_K,
    SIGNIFICANCE_LEVEL,
    VARIANT_MODEL,
)
from .reporting import _derived_seed


def build_paired_rows(
    profile_rows: list[dict[str, object]],
    random_seed: int,
    bootstrap_replicates: int,
) -> list[dict[str, object]]:
    """Build paired rows deterministically from the supplied evidence."""

    lookup = {
        (
            str(row["model"]),
            str(row["profile_id"]),
            int(row["k"]),
        ): row
        for row in profile_rows
    }
    profile_ids = sorted(
        {
            str(row["profile_id"])
            for row in profile_rows
            if row["model"] == BASELINE_MODEL
        }
    )
    rows: list[dict[str, object]] = []
    raw_permutation: list[float] = []
    raw_wilcoxon: list[float] = []
    for metric in PLANNED_METRICS:
        values = [
            float(lookup[(VARIANT_MODEL, profile_id, PRIMARY_K)][metric])
            - float(lookup[(BASELINE_MODEL, profile_id, PRIMARY_K)][metric])
            for profile_id in profile_ids
        ]
        lower, upper = bootstrap_mean_confidence_interval(
            values,
            seed=_derived_seed(random_seed, metric),
            replicates=bootstrap_replicates,
        )
        sample_sd = stdev(values) if len(values) > 1 else 0.0
        effect = mean(values) / sample_sd if sample_sd else 0.0
        permutation_p = exact_paired_permutation_test(values)
        w_plus, wilcoxon_p = exact_wilcoxon_signed_rank_test(values)
        raw_permutation.append(permutation_p)
        raw_wilcoxon.append(wilcoxon_p)
        rows.append(
            {
                "metric": metric,
                "k": PRIMARY_K,
                "profile_count": len(values),
                "mean_difference": round(mean(values), 4),
                "median_difference": round(median(values), 4),
                "sample_stddev_difference": round(sample_sd, 4),
                "ci_95_lower": round(lower, 4),
                "ci_95_upper": round(upper, 4),
                "standardized_effect_dz": round(effect, 4),
                "effect_magnitude": effect_magnitude(effect),
                "variant_wins": sum(value > 0 for value in values),
                "ties": sum(value == 0 for value in values),
                "variant_losses": sum(value < 0 for value in values),
                "exact_permutation_p": permutation_p,
                "exact_permutation_holm_p": 0.0,
                "wilcoxon_w_plus": round(w_plus, 4),
                "wilcoxon_p": wilcoxon_p,
                "wilcoxon_holm_p": 0.0,
                "holm_significant_at_0_05": False,
                "bootstrap_replicates": bootstrap_replicates,
                "random_seed": random_seed,
            }
        )
    permutation_adjusted = holm_adjust(raw_permutation)
    wilcoxon_adjusted = holm_adjust(raw_wilcoxon)
    for (
        row,
        raw_permutation_p,
        adjusted_permutation_p,
        raw_wilcoxon_p,
        adjusted_wilcoxon_p,
    ) in zip(
        rows,
        raw_permutation,
        permutation_adjusted,
        raw_wilcoxon,
        wilcoxon_adjusted,
    ):
        row["exact_permutation_p"] = round(raw_permutation_p, 6)
        row["exact_permutation_holm_p"] = round(
            adjusted_permutation_p,
            6,
        )
        row["wilcoxon_p"] = round(raw_wilcoxon_p, 6)
        row["wilcoxon_holm_p"] = round(adjusted_wilcoxon_p, 6)
        row["holm_significant_at_0_05"] = (
            adjusted_permutation_p < SIGNIFICANCE_LEVEL
        )
    return rows
