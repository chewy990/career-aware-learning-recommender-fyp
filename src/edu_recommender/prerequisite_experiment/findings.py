"""Own prerequisite experiment findings responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from .contracts import BASELINE_MODEL, PRIMARY_K, VARIANT_MODEL


def build_findings(
    summary_rows: list[dict[str, object]],
    paired_rows: list[dict[str, object]],
    diagnostic_rows: list[dict[str, object]],
    profile_change_rows: list[dict[str, object]],
    pathway_rows: list[dict[str, object]],
) -> tuple[dict[str, str], ...]:
    """Build findings deterministically from the supplied evidence."""

    paired = {str(row["metric"]): row for row in paired_rows}
    diagnostics = {str(row["model"]): row for row in diagnostic_rows}
    baseline_diagnostic = diagnostics[BASELINE_MODEL]
    variant_diagnostic = diagnostics[VARIANT_MODEL]
    ndcg = paired["ndcg_at_k"]
    changed_count = sum(
        bool(row["ranking_changed"])
        for row in profile_change_rows
    )
    top_5_changed_profiles = [
        str(row["profile_id"])
        for row in profile_change_rows
        if bool(row["top_5_changed"])
    ]
    harmed_profiles = [
        str(row["profile_id"])
        for row in profile_change_rows
        if float(row["ndcg_at_5_difference"]) < 0
    ]
    pathway_lookup = {
        (
            str(row["model"]),
            str(row["pathway"]),
        ): float(row["ndcg_at_k"])
        for row in pathway_rows
        if int(row["k"]) == PRIMARY_K
    }
    pathway_changes = {
        pathway: (
            pathway_lookup[(VARIANT_MODEL, pathway)]
            - pathway_lookup[(BASELINE_MODEL, pathway)]
        )
        for pathway in sorted(
            {
                str(row["pathway"])
                for row in pathway_rows
                if int(row["k"]) == PRIMARY_K
            }
        )
    }
    weakest_pathway = min(
        pathway_changes,
        key=pathway_changes.get,
    )
    summary_lookup = {
        (
            str(row["model"]),
            int(row["k"]),
        ): row
        for row in summary_rows
    }
    baseline_k10 = summary_lookup[(BASELINE_MODEL, 10)]
    variant_k10 = summary_lookup[(VARIANT_MODEL, 10)]
    return (
        {
            "title": "Hard eligibility removes prerequisite-invalid recommendations",
            "finding": (
                "Mean prerequisite validity at K=5 changes from "
                f"{float(baseline_diagnostic['prerequisite_validity_rate']):.1%} "
                "to "
                f"{float(variant_diagnostic['prerequisite_validity_rate']):.1%}."
            ),
            "implication": (
                "The candidate-level rule directly addresses the diagnosed "
                "suitability failure while preserving a full top-10 list."
            ),
        },
        {
            "title": "The primary ranking effect is measured rather than assumed",
            "finding": (
                "Hard eligibility minus baseline NDCG@5 averages "
                f"{float(ndcg['mean_difference']):+.4f} with 95% interval "
                f"[{float(ndcg['ci_95_lower']):+.4f}, "
                f"{float(ndcg['ci_95_upper']):+.4f}], "
                f"{int(ndcg['variant_wins'])} wins, {int(ndcg['ties'])} ties, "
                f"{int(ndcg['variant_losses'])} losses, and Holm-adjusted exact "
                f"p={float(ndcg['exact_permutation_holm_p']):.6f}."
            ),
            "implication": (
                "Suitability and relevance are reported together; neither one "
                "is treated as sufficient by itself."
            ),
        },
        {
            "title": "Profile changes expose who is affected",
            "finding": (
                f"{changed_count} of {len(profile_change_rows)} profile top-10 "
                "rankings change. Top-five resource identities change for "
                f"{len(top_5_changed_profiles)} profiles "
                f"({', '.join(top_5_changed_profiles) if top_5_changed_profiles else 'none'}). "
                "Profiles with lower NDCG@5 are "
                f"{', '.join(harmed_profiles) if harmed_profiles else 'none'}."
            ),
            "implication": (
                "The aggregate result is traceable to explicit removed and "
                "replacement resources for every profile."
            ),
        },
        {
            "title": "Pathway effects remain descriptive",
            "finding": (
                f"The lowest pathway NDCG@5 change is {weakest_pathway} at "
                f"{pathway_changes[weakest_pathway]:+.4f}."
            ),
            "implication": (
                "Only two or three profiles represent each pathway, so this "
                "diagnostic cannot support pathway-wide generalisation."
            ),
        },
        {
            "title": "Longer lists and quality diagnostics show small trade-offs",
            "finding": (
                "At K=10, NDCG changes from "
                f"{float(baseline_k10['ndcg_at_k']):.4f} to "
                f"{float(variant_k10['ndcg_at_k']):.4f}. At K=5, skill-gap "
                "coverage changes from "
                f"{float(baseline_diagnostic['skill_gap_coverage']):.4f} to "
                f"{float(variant_diagnostic['skill_gap_coverage']):.4f}, while "
                "catalogue coverage changes from "
                f"{float(baseline_diagnostic['catalogue_coverage']):.4f} to "
                f"{float(variant_diagnostic['catalogue_coverage']):.4f}."
            ),
            "implication": (
                "The hard rule improves eligibility and broader exposure, but "
                "slightly reduces measured skill-gap coverage at K=5; this "
                "trade-off should be reviewed rather than hidden."
            ),
        },
        {
            "title": "The baseline remains frozen",
            "finding": (
                "The experiment changes only candidate eligibility. Source "
                "data, relevance labels, hybrid weights, and baseline outputs "
                "remain unchanged."
            ),
            "implication": (
                "The result can inform a later implementation decision, but "
                "does not automatically replace the production hybrid."
            ),
        },
    )
