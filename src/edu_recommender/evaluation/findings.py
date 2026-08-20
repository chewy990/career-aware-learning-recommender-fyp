"""Own evaluation findings responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from .contracts import MODEL_LABELS
from .reporting import _humanise


def build_evaluation_findings(
    summary_rows: list[dict[str, object]],
    pathway_rows: list[dict[str, object]],
    uncertainty_rows: list[dict[str, object]],
    diagnostic_rows: list[dict[str, object]],
) -> tuple[dict[str, str], ...]:
    """Build evaluation findings deterministically from the supplied evidence."""

    k5 = [row for row in summary_rows if int(row["k"]) == 5]
    best = max(k5, key=lambda row: float(row["ndcg_at_k"]))
    hybrid_ci = next(
        row
        for row in uncertainty_rows
        if row["model"] == "hybrid"
        and int(row["k"]) == 5
        and row["metric"] == "ndcg_at_k"
    )
    hybrid_pathways = [
        row
        for row in pathway_rows
        if row["model"] == "hybrid" and int(row["k"]) == 5
    ]
    weakest_pathway = min(
        hybrid_pathways,
        key=lambda row: float(row["ndcg_at_k"]),
    )
    strongest_baseline_for_weakest = max(
        (
            row
            for row in pathway_rows
            if row["pathway"] == weakest_pathway["pathway"]
            and int(row["k"]) == 5
            and row["model"] != "hybrid"
        ),
        key=lambda row: float(row["ndcg_at_k"]),
    )
    diagnostic_k5 = {
        str(row["model"]): row
        for row in diagnostic_rows
        if int(row["k"]) == 5
    }
    hybrid_diagnostics = diagnostic_k5["hybrid"]
    return (
        {
            "title": "The hybrid remains the strongest model at K=5",
            "finding": (
                f"{MODEL_LABELS[str(best['model'])]} has the highest macro "
                f"NDCG@5 at {float(best['ndcg_at_k']):.4f}."
            ),
            "implication": (
                "The structured career and skill-gap signals remain useful when "
                "performance is traced to profile-level observations."
            ),
        },
        {
            "title": "The overall estimate still has profile-level uncertainty",
            "finding": (
                "Hybrid NDCG@5 has a seeded profile-bootstrap 95% interval of "
                f"[{float(hybrid_ci['ci_95_lower']):.4f}, "
                f"{float(hybrid_ci['ci_95_upper']):.4f}]."
            ),
            "implication": (
                "The interval describes variation within 11 curated profiles, "
                "not uncertainty for the real learner population."
            ),
        },
        {
            "title": "Pathway performance is not uniform",
            "finding": (
                f"The lowest hybrid pathway NDCG@5 is "
                f"{_humanise(str(weakest_pathway['pathway']))} at "
                f"{float(weakest_pathway['ndcg_at_k']):.4f}; "
                f"{MODEL_LABELS[str(strongest_baseline_for_weakest['model'])]} "
                f"scores {float(strongest_baseline_for_weakest['ndcg_at_k']):.4f} "
                "for the same pathway."
            ),
            "implication": (
                "Pathway-level error analysis is needed before treating the "
                "overall average as equally representative of every pathway."
            ),
        },
        {
            "title": "The hybrid covers only part of the full catalogue",
            "finding": (
                f"Across all profiles at K=5, hybrid recommendations expose "
                f"{int(hybrid_diagnostics['unique_resources_recommended'])} of "
                f"{int(hybrid_diagnostics['catalogue_size'])} resources "
                f"({float(hybrid_diagnostics['catalogue_coverage']):.1%})."
            ),
            "implication": (
                "Coverage should be interpreted alongside the deliberate exclusion "
                "of broad tracks and supporting-only formats from ranked next steps."
            ),
        },
        {
            "title": "Suitability diagnostics provide a second evaluation layer",
            "finding": (
                f"At K=5 the hybrid averages "
                f"{float(hybrid_diagnostics['skill_gap_coverage']):.1%} skill-gap "
                f"coverage, {float(hybrid_diagnostics['difficulty_match_rate']):.1%} "
                "difficulty matching, and "
                f"{float(hybrid_diagnostics['prerequisite_validity_rate']):.1%} "
                "prerequisite validity."
            ),
            "implication": (
                "High relevance metrics should only be accepted when recommendations "
                "also address learner gaps and remain teachable."
            ),
        },
    )
