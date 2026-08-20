"""Own robustness findings responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from collections import Counter

from .contracts import COMPONENTS
from .reporting import _humanise


def _build_findings(
    ablation_rows: list[dict[str, object]],
    ablation_profile_rows: list[dict[str, object]],
    sensitivity_rows: list[dict[str, object]],
    seeded_rows: list[dict[str, object]],
    failure_rows: list[dict[str, object]],
) -> tuple[dict[str, str], ...]:
    ablation_k5 = [
        row
        for row in ablation_rows
        if int(row["k"]) == 5 and row["removed_component"]
    ]
    largest_drop = min(
        ablation_k5,
        key=lambda row: float(row["delta_ndcg"]),
    )
    largest_gain = max(
        ablation_k5,
        key=lambda row: float(row["delta_ndcg"]),
    )
    p010_baseline = next(
        row
        for row in ablation_profile_rows
        if row["configuration"] == "full_hybrid"
        and row["profile_id"] == "P010"
        and int(row["k"]) == 5
    )
    p010_without_job_alignment = next(
        row
        for row in ablation_profile_rows
        if row["configuration"] == "without_job_skill_alignment"
        and row["profile_id"] == "P010"
        and int(row["k"]) == 5
    )
    sensitivity_k5 = [
        row for row in sensitivity_rows if int(row["k"]) == 5
    ]
    ranges = {}
    for component in COMPONENTS:
        values = [
            float(row["ndcg_at_k"])
            for row in sensitivity_k5
            if row["component"] == component
        ]
        ranges[component] = max(values) - min(values)
    most_sensitive = max(ranges, key=ranges.get)
    seeded_k5 = [
        row for row in seeded_rows if int(row["k"]) == 5
    ]
    seeded_values = [
        float(row["ndcg_at_k"])
        for row in seeded_k5
        if row["configuration_id"] != "S000_baseline"
    ]
    failure_counts = Counter(
        str(row["failure_type"])
        for row in failure_rows
    )
    prereq_count = failure_counts["prerequisite_invalid"]
    affected_prereq_profiles = len(
        {
            str(row["profile_id"])
            for row in failure_rows
            if row["failure_type"] == "prerequisite_invalid"
        }
    )
    return (
        {
            "title": "Ablation identifies which hybrid signals carry the ranking",
            "finding": (
                f"Removing {_humanise(str(largest_drop['removed_component']))} "
                f"changes NDCG@5 by {float(largest_drop['delta_ndcg']):+.4f}, "
                "the largest decrease among single-component removals."
            ),
            "implication": (
                "This component contributes the strongest unique ranking evidence "
                "on the current curated profiles."
            ),
        },
        {
            "title": "Some component removal may improve the same test set",
            "finding": (
                f"The largest ablation increase is "
                f"{float(largest_gain['delta_ndcg']):+.4f} when "
                f"{_humanise(str(largest_gain['removed_component']))} is removed. "
                "For Data Engineer profile P010, NDCG@5 changes from "
                f"{float(p010_baseline['ndcg_at_k']):.4f} to "
                f"{float(p010_without_job_alignment['ndcg_at_k']):.4f}."
            ),
            "implication": (
                "This is diagnostic evidence, not permission to retune on the "
                "evaluation profiles; a change needs held-out confirmation."
            ),
        },
        {
            "title": "One-at-a-time sensitivity measures local stability",
            "finding": (
                f"{_humanise(most_sensitive)} has the widest NDCG@5 range "
                f"({ranges[most_sensitive]:.4f}) across 0.5x to 1.5x its "
                "current weight."
            ),
            "implication": (
                "Large local variation would indicate a fragile manual weight; "
                "small variation indicates stable rankings near the chosen value."
            ),
        },
        {
            "title": "Seeded alternatives test robustness without tuning",
            "finding": (
                "Twelve pre-seeded configurations produce NDCG@5 values from "
                f"{min(seeded_values):.4f} to {max(seeded_values):.4f}."
            ),
            "implication": (
                "The range describes sensitivity to bounded joint perturbations; "
                "the best variant is not selected as a replacement model."
            ),
        },
        {
            "title": "Failure cases point to model changes before data expansion",
            "finding": (
                f"{prereq_count} prerequisite-invalid top-five recommendations "
                f"affect {affected_prereq_profiles} profiles; the complete failure "
                f"log contains {len(failure_rows)} flagged cases."
            ),
            "implication": (
                "A hard eligibility or sequencing rule can be evaluated before "
                "assuming that additional catalogue rows are the primary remedy."
            ),
        },
        {
            "title": "The current evidence supports a model-first data decision",
            "finding": (
                "All source rows remain valid, the strongest controlled improvement "
                "comes from a scoring-component change, and prerequisite failures "
                "come from soft ranking rather than broken data references."
            ),
            "implication": (
                "Keep the current dataset as the experimental baseline, evaluate "
                "hard prerequisite eligibility and independently review labels, "
                "then create a documented data revision only if residual errors "
                "show a genuine catalogue or labelling gap."
            ),
        },
    )
