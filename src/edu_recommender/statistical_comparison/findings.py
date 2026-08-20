"""Own statistical comparison findings responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from .contracts import AUDIT_ITEMS_PER_PATHWAY


def build_statistical_findings(
    comparison_rows: list[dict[str, object]],
    audit_key_rows: list[dict[str, object]],
) -> tuple[dict[str, str], ...]:
    """Build statistical findings deterministically from the supplied evidence."""

    ndcg_k5 = {
        str(row["baseline_model"]): row
        for row in comparison_rows
        if row["metric"] == "ndcg_at_k"
        and int(row["k"]) == 5
    }
    content = ndcg_k5["content_based"]
    popularity = ndcg_k5["popularity"]
    significant_count = sum(
        bool(row["holm_significant_at_0_05"])
        for row in comparison_rows
    )
    total_tests = len(comparison_rows)
    content_significant_count = sum(
        bool(row["holm_significant_at_0_05"])
        and row["baseline_model"] == "content_based"
        for row in comparison_rows
    )
    popularity_significant_count = sum(
        bool(row["holm_significant_at_0_05"])
        and row["baseline_model"] == "popularity"
        for row in comparison_rows
    )
    fallback_count = sum(
        row["selection_reason"] == "balanced_fallback"
        for row in audit_key_rows
    )
    return (
        {
            "title": "Paired differences quantify the hybrid advantage",
            "finding": (
                "At K=5, hybrid minus content-based NDCG averages "
                f"{float(content['mean_difference']):+.4f} with 95% interval "
                f"[{float(content['ci_95_lower']):+.4f}, "
                f"{float(content['ci_95_upper']):+.4f}], while the Holm-adjusted "
                "exact permutation p-value is "
                f"{float(content['exact_permutation_holm_p']):.6f}."
            ),
            "implication": (
                "The positive mean is suggestive on this test set, but it is not "
                "corrected statistical evidence that hybrid outperforms "
                "content-based."
            ),
        },
        {
            "title": "The popularity comparison is practically large",
            "finding": (
                "At K=5, hybrid minus popularity NDCG averages "
                f"{float(popularity['mean_difference']):+.4f} with paired "
                f"standardized effect dz={float(popularity['standardized_effect_dz']):.4f} "
                "and Holm-adjusted exact permutation p="
                f"{float(popularity['exact_permutation_holm_p']):.6f}."
            ),
            "implication": (
                "Practical magnitude is reported alongside p-values rather than "
                "treating statistical significance as the only evidence."
            ),
        },
        {
            "title": "Corrected tests separate the two baseline conclusions",
            "finding": (
                f"{significant_count} of {total_tests} planned hybrid-baseline "
                "comparisons have Holm-adjusted exact permutation p<0.05: "
                f"{popularity_significant_count} of 9 against popularity and "
                f"{content_significant_count} of 9 against content-based."
            ),
            "implication": (
                "Only corrected results can support statistical claims; all "
                "conclusions remain limited to 11 curated profiles."
            ),
        },
        {
            "title": "Win, tie, and loss counts expose consistency",
            "finding": (
                "For NDCG@5, hybrid records "
                f"{int(content['hybrid_wins'])} wins, {int(content['ties'])} "
                f"ties, and {int(content['hybrid_losses'])} losses against "
                "content-based."
            ),
            "implication": (
                "The counts show whether an average difference is widespread or "
                "driven by a small number of profiles."
            ),
        },
        {
            "title": "A blinded label audit is prepared but not fabricated",
            "finding": (
                f"A deterministic {len(audit_key_rows)}-item audit template contains "
                f"{AUDIT_ITEMS_PER_PATHWAY} cases per pathway and spans all four "
                f"planned case types. {fallback_count} balanced fallback cases were "
                "needed because recommended-but-currently-non-relevant cases were "
                "not numerous enough for a perfect two-per-type split in every "
                "pathway. Reviewer fields are blank and the current-label key is "
                "stored separately."
            ),
            "implication": (
                "An independent reviewer can assess label consistency without "
                "seeing model scores or the current labels."
            ),
        },
    )
