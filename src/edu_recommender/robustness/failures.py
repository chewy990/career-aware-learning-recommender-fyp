"""Own robustness failures responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from collections import Counter

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.evaluation import (
    EvaluationResult,
)
from edu_recommender.models import (
    Recommendation,
)

from .contracts import FAILURE_THRESHOLDS


def _build_failure_rows(
    resources: list[Resource],
    profiles: list[LearnerProfile],
    baseline: dict[str, list[Recommendation]],
    evaluation_result: EvaluationResult,
) -> list[dict[str, object]]:
    profile_lookup = {profile.profile_id: profile for profile in profiles}
    resource_lookup = {resource.resource_id: resource for resource in resources}
    metric_rows = [
        row
        for row in evaluation_result.profile_rows
        if row["model"] == "hybrid" and int(row["k"]) == 5
    ]
    diagnostic_rows = [
        row
        for row in evaluation_result.diagnostic_profile_rows
        if row["model"] == "hybrid" and int(row["k"]) == 5
    ]
    rows: list[dict[str, object]] = []
    for metric_row in metric_rows:
        profile_id = str(metric_row["profile_id"])
        pathway = str(metric_row["pathway"])
        ndcg = float(metric_row["ndcg_at_k"])
        recall = float(metric_row["recall_at_k"])
        if ndcg < FAILURE_THRESHOLDS["low_ndcg_at_5"]:
            rows.append(
                _failure_row(
                    "low_ndcg_at_5",
                    profile_id,
                    pathway,
                    observed=ndcg,
                    threshold=FAILURE_THRESHOLDS["low_ndcg_at_5"],
                    details="Relevant resources are not consistently near the top five.",
                    severity="high",
                )
            )
        if recall < FAILURE_THRESHOLDS["low_recall_at_5"]:
            rows.append(
                _failure_row(
                    "low_recall_at_5",
                    profile_id,
                    pathway,
                    observed=recall,
                    threshold=FAILURE_THRESHOLDS["low_recall_at_5"],
                    details="The top five retrieve less than 15% of the curated relevant set.",
                    severity="medium",
                )
            )

    for diagnostic_row in diagnostic_rows:
        profile_id = str(diagnostic_row["profile_id"])
        pathway = str(diagnostic_row["pathway"])
        gap_coverage = float(diagnostic_row["skill_gap_coverage"])
        if gap_coverage < FAILURE_THRESHOLDS["weak_skill_gap_coverage_at_5"]:
            rows.append(
                _failure_row(
                    "weak_skill_gap_coverage_at_5",
                    profile_id,
                    pathway,
                    observed=gap_coverage,
                    threshold=FAILURE_THRESHOLDS[
                        "weak_skill_gap_coverage_at_5"
                    ],
                    details="The top five cover less than half of weighted skill gaps.",
                    severity="medium",
                )
            )

        recommendations = baseline[profile_id][:5]
        provider_counts = Counter(item.provider for item in recommendations)
        top_provider, top_provider_count = provider_counts.most_common(1)[0]
        provider_share = top_provider_count / len(recommendations)
        if provider_share >= FAILURE_THRESHOLDS["provider_concentration_at_5"]:
            rows.append(
                _failure_row(
                    "provider_concentration_at_5",
                    profile_id,
                    pathway,
                    observed=provider_share,
                    threshold=FAILURE_THRESHOLDS[
                        "provider_concentration_at_5"
                    ],
                    details=(
                        f"{top_provider} supplies {top_provider_count} of "
                        "the top five resources."
                    ),
                    severity="low",
                )
            )

        format_counts = Counter(
            resource_lookup[item.resource_id].format
            for item in recommendations
        )
        top_format, top_format_count = format_counts.most_common(1)[0]
        format_share = top_format_count / len(recommendations)
        if format_share >= FAILURE_THRESHOLDS["format_concentration_at_5"]:
            rows.append(
                _failure_row(
                    "format_concentration_at_5",
                    profile_id,
                    pathway,
                    observed=format_share,
                    threshold=FAILURE_THRESHOLDS[
                        "format_concentration_at_5"
                    ],
                    details=(
                        f"{top_format} accounts for {top_format_count} of "
                        "the top five resources."
                    ),
                    severity="low",
                )
            )

        profile = profile_lookup[profile_id]
        for recommendation in recommendations:
            resource = resource_lookup[recommendation.resource_id]
            missing = sorted(
                prerequisite
                for prerequisite in resource.prerequisites
                if prerequisite not in profile.completed_topics
                and profile.current_skills.get(prerequisite, 0) < 1
            )
            if missing:
                rows.append(
                    _failure_row(
                        "prerequisite_invalid",
                        profile_id,
                        pathway,
                        observed=0.0,
                        threshold=1.0,
                        details=(
                            "Missing prerequisite(s): "
                            + ", ".join(missing)
                        ),
                        severity="high",
                        resource_id=resource.resource_id,
                        rank=recommendation.rank,
                    )
                )
    return sorted(
        rows,
        key=lambda row: (
            str(row["failure_type"]),
            str(row["profile_id"]),
            int(row["rank"] or 0),
            str(row["resource_id"]),
        ),
    )

def _failure_row(
    failure_type: str,
    profile_id: str,
    pathway: str,
    observed: float,
    threshold: float,
    details: str,
    severity: str,
    resource_id: str = "",
    rank: int | str = "",
) -> dict[str, object]:
    return {
        "failure_type": failure_type,
        "profile_id": profile_id,
        "pathway": pathway,
        "resource_id": resource_id,
        "rank": rank,
        "severity": severity,
        "observed_value": round(observed, 4),
        "threshold": round(threshold, 4),
        "details": details,
    }
