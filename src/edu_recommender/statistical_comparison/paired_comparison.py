"""Own statistical comparison paired comparison responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from statistics import mean, median, stdev

from edu_recommender.evaluation import (
    bootstrap_mean_confidence_interval,
)

from .contracts import BASELINE_MODELS, METRICS, SIGNIFICANCE_LEVEL
from .reporting import _derived_seed
from .tests import (
    effect_magnitude,
    exact_paired_permutation_test,
    exact_wilcoxon_signed_rank_test,
    holm_adjust,
)


def build_paired_difference_rows(
    profile_metric_rows: tuple[dict[str, object], ...]
    | list[dict[str, object]],
) -> list[dict[str, object]]:
    """Build paired difference rows deterministically from the supplied evidence."""

    lookup = {
        (
            str(row["model"]),
            str(row["profile_id"]),
            int(row["k"]),
        ): row
        for row in profile_metric_rows
    }
    profile_ids = sorted(
        {
            str(row["profile_id"])
            for row in profile_metric_rows
            if row["model"] == "hybrid"
        }
    )
    k_values = sorted(
        {
            int(row["k"])
            for row in profile_metric_rows
        }
    )
    rows: list[dict[str, object]] = []
    for baseline in BASELINE_MODELS:
        comparison = f"hybrid_vs_{baseline}"
        for metric in METRICS:
            for k in k_values:
                for profile_id in profile_ids:
                    hybrid_row = lookup[("hybrid", profile_id, k)]
                    baseline_row = lookup[(baseline, profile_id, k)]
                    hybrid_value = float(hybrid_row[metric])
                    baseline_value = float(baseline_row[metric])
                    rows.append(
                        {
                            "comparison": comparison,
                            "baseline_model": baseline,
                            "metric": metric,
                            "k": k,
                            "profile_id": profile_id,
                            "pathway": hybrid_row["pathway"],
                            "hybrid_value": round(hybrid_value, 6),
                            "baseline_value": round(baseline_value, 6),
                            "paired_difference": round(
                                hybrid_value - baseline_value,
                                6,
                            ),
                        }
                    )
    return rows

def build_paired_comparison_rows(
    difference_rows: list[dict[str, object]],
    random_seed: int,
    bootstrap_replicates: int,
) -> list[dict[str, object]]:
    """Build paired comparison rows deterministically from the supplied evidence."""

    rows: list[dict[str, object]] = []
    raw_permutation_p_values: list[float] = []
    raw_wilcoxon_p_values: list[float] = []
    comparisons = [
        f"hybrid_vs_{baseline}"
        for baseline in BASELINE_MODELS
    ]
    k_values = sorted({int(row["k"]) for row in difference_rows})
    for comparison in comparisons:
        baseline = comparison.removeprefix("hybrid_vs_")
        for metric in METRICS:
            for k in k_values:
                values = [
                    float(row["paired_difference"])
                    for row in difference_rows
                    if row["comparison"] == comparison
                    and row["metric"] == metric
                    and int(row["k"]) == k
                ]
                derived_seed = _derived_seed(
                    random_seed,
                    comparison,
                    metric,
                    k,
                )
                lower, upper = bootstrap_mean_confidence_interval(
                    values,
                    seed=derived_seed,
                    replicates=bootstrap_replicates,
                )
                sample_sd = stdev(values) if len(values) > 1 else 0.0
                effect = mean(values) / sample_sd if sample_sd else 0.0
                permutation_p = exact_paired_permutation_test(values)
                w_plus, wilcoxon_p = exact_wilcoxon_signed_rank_test(values)
                raw_permutation_p_values.append(permutation_p)
                raw_wilcoxon_p_values.append(wilcoxon_p)
                rows.append(
                    {
                        "comparison": comparison,
                        "baseline_model": baseline,
                        "metric": metric,
                        "k": k,
                        "profile_count": len(values),
                        "mean_difference": round(mean(values), 4),
                        "median_difference": round(median(values), 4),
                        "sample_stddev_difference": round(sample_sd, 4),
                        "ci_95_lower": round(lower, 4),
                        "ci_95_upper": round(upper, 4),
                        "standardized_effect_dz": round(effect, 4),
                        "effect_magnitude": effect_magnitude(effect),
                        "hybrid_wins": sum(value > 0 for value in values),
                        "ties": sum(value == 0 for value in values),
                        "hybrid_losses": sum(value < 0 for value in values),
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

    permutation_adjusted = holm_adjust(raw_permutation_p_values)
    wilcoxon_adjusted = holm_adjust(raw_wilcoxon_p_values)
    for (
        row,
        raw_permutation_p,
        permutation_p,
        raw_wilcoxon_p,
        wilcoxon_p,
    ) in zip(
        rows,
        raw_permutation_p_values,
        permutation_adjusted,
        raw_wilcoxon_p_values,
        wilcoxon_adjusted,
    ):
        row["exact_permutation_p"] = round(raw_permutation_p, 6)
        row["exact_permutation_holm_p"] = round(permutation_p, 6)
        row["wilcoxon_p"] = round(raw_wilcoxon_p, 6)
        row["wilcoxon_holm_p"] = round(wilcoxon_p, 6)
        row["holm_significant_at_0_05"] = (
            permutation_p < SIGNIFICANCE_LEVEL
        )
    return rows
