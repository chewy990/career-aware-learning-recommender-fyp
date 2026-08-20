"""Build deterministic reporting rows for the weak-skill experiment."""

from __future__ import annotations

import hashlib
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from edu_recommender.evaluation import bootstrap_mean_confidence_interval
from edu_recommender.models import Recommendation
from edu_recommender.statistical_comparison import (
    exact_paired_permutation_test,
    exact_wilcoxon_signed_rank_test,
)


def recommendation_rows(
    recommendations: dict[str, list[Recommendation]],
) -> list[dict[str, object]]:
    """Flatten variant recommendations in stable profile and rank order."""

    return [
        {
            "profile_id": item.profile_id,
            "model": item.model,
            "rank": item.rank,
            "resource_id": item.resource_id,
            "title": item.title,
            "provider": item.provider,
            "score": item.score,
            "explanation": item.explanation,
        }
        for profile_id in sorted(recommendations)
        for item in recommendations[profile_id]
    ]


def paired_ndcg_row(
    profile_rows: list[dict[str, object]],
    baseline_model: str,
    variant_model: str,
    primary_k: int,
    random_seed: int,
    bootstrap_replicates: int,
) -> dict[str, object]:
    """Build the single pre-declared paired graded-NDCG comparison."""

    lookup = {
        (str(row["model"]), str(row["profile_id"]), int(row["k"])): row
        for row in profile_rows
    }
    profile_ids = sorted(
        str(row["profile_id"])
        for row in profile_rows
        if row["model"] == baseline_model and int(row["k"]) == primary_k
    )
    differences = [
        float(lookup[(variant_model, profile_id, primary_k)]["ndcg_at_k"])
        - float(lookup[(baseline_model, profile_id, primary_k)]["ndcg_at_k"])
        for profile_id in profile_ids
    ]
    lower, upper = bootstrap_mean_confidence_interval(
        differences,
        seed=random_seed,
        replicates=bootstrap_replicates,
    )
    sample_sd = stdev(differences) if len(differences) > 1 else 0.0
    w_plus, wilcoxon_p = exact_wilcoxon_signed_rank_test(differences)
    return {
        "metric": "graded_ndcg_at_k",
        "k": primary_k,
        "profile_count": len(differences),
        "mean_difference": round(mean(differences), 6),
        "ci_95_lower": round(lower, 6),
        "ci_95_upper": round(upper, 6),
        "standardized_effect_dz": round(
            mean(differences) / sample_sd if sample_sd else 0.0,
            6,
        ),
        "variant_wins": sum(value > 0 for value in differences),
        "ties": sum(value == 0 for value in differences),
        "variant_losses": sum(value < 0 for value in differences),
        "exact_permutation_p": round(
            exact_paired_permutation_test(differences),
            6,
        ),
        "wilcoxon_w_plus": round(w_plus, 6),
        "wilcoxon_p": round(wilcoxon_p, 6),
        "bootstrap_replicates": bootstrap_replicates,
        "random_seed": random_seed,
    }


def profile_difference_rows(
    profile_rows: list[dict[str, object]],
    baseline_model: str,
    variant_model: str,
    primary_k: int,
) -> list[dict[str, object]]:
    """Return paired profile-level NDCG differences at the primary cutoff."""

    primary = [row for row in profile_rows if int(row["k"]) == primary_k]
    lookup = {
        (str(row["model"]), str(row["profile_id"])): row
        for row in primary
    }
    profile_ids = sorted(
        profile_id
        for model, profile_id in lookup
        if model == baseline_model
    )
    return [
        {
            "profile_id": profile_id,
            "pathway": lookup[(baseline_model, profile_id)]["pathway"],
            "baseline_ndcg_at_5": lookup[(baseline_model, profile_id)]["ndcg_at_k"],
            "variant_ndcg_at_5": lookup[(variant_model, profile_id)]["ndcg_at_k"],
            "difference": round(
                float(lookup[(variant_model, profile_id)]["ndcg_at_k"])
                - float(lookup[(baseline_model, profile_id)]["ndcg_at_k"]),
                6,
            ),
        }
        for profile_id in profile_ids
    ]


def experiment_decision(
    summary_rows: list[dict[str, object]],
    pathway_rows: list[dict[str, object]],
    profile_differences: list[dict[str, object]],
    diagnostic_rows: list[dict[str, object]],
    baseline_model: str,
    variant_model: str,
    primary_k: int,
) -> dict[str, Any]:
    """Apply the frozen exploratory decision thresholds exactly once."""

    summary = {
        str(row["model"]): row
        for row in summary_rows
        if int(row["k"]) == primary_k
    }
    macro_delta = round(
        float(summary[variant_model]["ndcg_at_k"])
        - float(summary[baseline_model]["ndcg_at_k"]),
        6,
    )
    pathway_lookup = {
        (str(row["model"]), str(row["pathway"])): float(row["ndcg_at_k"])
        for row in pathway_rows
        if int(row["k"]) == primary_k
    }
    pathway_deltas = {
        pathway: round(
            pathway_lookup[(variant_model, pathway)]
            - pathway_lookup[(baseline_model, pathway)],
            6,
        )
        for model, pathway in pathway_lookup
        if model == baseline_model
    }
    weak_case_mean = mean(
        float(row["difference"])
        for row in profile_differences
        if row["profile_id"] in {"P003", "P004", "P010", "P011"}
    )
    diagnostics = {
        str(row["model"]): row
        for row in diagnostic_rows
        if int(row["k"]) == primary_k
    }
    readiness_deltas = {
        field: round(
            float(diagnostics[variant_model][field])
            - float(diagnostics[baseline_model][field]),
            6,
        )
        for field in ("difficulty_match_rate", "prerequisite_validity_rate")
    }
    criteria = {
        "macro_ndcg_delta_at_least_0_01": macro_delta >= 0.01,
        "weak_case_mean_delta_positive": weak_case_mean > 0,
        "no_pathway_ndcg_drop_below_minus_0_03": min(pathway_deltas.values()) >= -0.03,
        "no_readiness_drop_below_minus_0_05": min(readiness_deltas.values()) >= -0.05,
    }
    return {
        "status": (
            "candidate_for_independent_validation"
            if all(criteria.values())
            else "reject_or_revise_before_independent_validation"
        ),
        "criteria": criteria,
        "macro_ndcg_at_5_delta": macro_delta,
        "weak_case_mean_ndcg_at_5_delta": round(weak_case_mean, 6),
        "pathway_ndcg_at_5_deltas": pathway_deltas,
        "readiness_deltas_at_5": readiness_deltas,
        "interpretation_limit": (
            "Exploratory reuse of the author-graded answer key. The result cannot "
            "establish independent generalisation."
        ),
    }


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of one experiment input or output."""

    return hashlib.sha256(path.read_bytes()).hexdigest()
