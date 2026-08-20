"""Counterfactual behavior tests for the readiness-gated scoring variant."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from edu_recommender.data import (
    read_profiles,
    read_resources,
    read_skill_map,
    write_rows,
)
from edu_recommender.weak_skill_alignment_experiment import (
    ReadinessGatedWeakSkillAlignmentSuite,
)

from .common import write_json, write_manifest

EPSILON = 1e-12
UNKNOWN_TOPIC = "counterfactual_irrelevant_topic"


def run_counterfactual_experiment(
    data_dir: Path,
    protocol_path: Path,
    output_dir: Path,
    runner_path: Path,
) -> None:
    """Evaluate five frozen invariants across all eligible real cases."""

    resources = read_resources(data_dir / "resources.csv")
    resource_lookup = {resource.resource_id: resource for resource in resources}
    profiles = read_profiles(data_dir / "learner_profiles.csv")
    skill_map = read_skill_map(data_dir / "skill_map.csv")
    suite = ReadinessGatedWeakSkillAlignmentSuite(resources, skill_map)
    rows: list[dict[str, object]] = []

    for profile in profiles:
        eligible_ids = {
            item.resource_id
            for item in suite.recommend(profile, model="hybrid", top_k=len(resources))
        }
        eligible = [resource_lookup[resource_id] for resource_id in sorted(eligible_ids)]
        rows.extend(_prerequisite_cases(suite, profile, eligible))
        rows.extend(_skill_improvement_cases(suite, profile, eligible, skill_map))
        rows.extend(_difficulty_cases(suite, profile, eligible))
        rows.extend(_weakness_removal_cases(suite, profile, eligible))
        rows.append(_irrelevant_topic_case(suite, profile))

    for index, row in enumerate(rows, start=1):
        row["case_id"] = f"C{index:04d}"
    invariants = sorted({str(row["invariant"]) for row in rows})
    summary_rows = []
    for invariant in invariants:
        group = [row for row in rows if row["invariant"] == invariant]
        passed = sum(bool(row["passed"]) for row in group)
        summary_rows.append(
            {
                "invariant": invariant,
                "case_count": len(group),
                "passed_count": passed,
                "failed_count": len(group) - passed,
                "pass_rate": round(passed / len(group), 6) if group else 0.0,
            }
        )
    failures = [row for row in rows if not bool(row["passed"])]
    decision = {
        "criterion": "every eligible case satisfies its predeclared invariant",
        "passed": not failures,
        "case_count": len(rows),
        "passed_count": len(rows) - len(failures),
        "failed_count": len(failures),
        "relevance_labels_used": False,
    }

    output_dir.mkdir(parents=True, exist_ok=False)
    fieldnames = [
        "case_id",
        "invariant",
        "profile_id",
        "resource_id",
        "changed_skill",
        "before_signal",
        "after_signal",
        "before_score",
        "after_score",
        "passed",
        "component_changes",
        "details",
    ]
    write_rows(output_dir / "counterfactual_cases.csv", fieldnames, rows)
    write_rows(
        output_dir / "counterfactual_summary.csv",
        list(summary_rows[0]),
        summary_rows,
    )
    write_json(output_dir / "decision.json", decision)
    write_json(
        output_dir / "protocol.json",
        {
            "version": "1",
            "frozen_protocol": "docs/final_robustness_protocol.md",
            "invariants": invariants,
            "eligibility": "normal ranked candidate policy",
            "pass_rule": "all eligible cases pass",
        },
    )
    project_root = data_dir.parent
    source = project_root / "src"
    write_manifest(
        output_dir,
        "counterfactual_behavior",
        [
            data_dir / "resources.csv",
            data_dir / "skill_map.csv",
            data_dir / "learner_profiles.csv",
            protocol_path,
        ],
        [
            Path(__file__).resolve(),
            Path(__file__).with_name("common.py").resolve(),
            runner_path.resolve(),
            source / "edu_recommender" / "models" / "suite.py",
            source / "edu_recommender" / "models" / "signals.py",
            source / "edu_recommender" / "weak_skill_alignment_experiment" / "service.py",
        ],
    )


def _base_row(invariant: str, profile_id: str, resource_id: str = "") -> dict[str, object]:
    return {
        "invariant": invariant,
        "profile_id": profile_id,
        "resource_id": resource_id,
        "changed_skill": "",
        "before_signal": "",
        "after_signal": "",
        "before_score": "",
        "after_score": "",
        "passed": False,
        "component_changes": "",
        "details": "",
    }


def _prerequisite_cases(suite, profile, resources) -> list[dict[str, object]]:
    rows = []
    for resource in resources:
        missing = resource.prerequisites - profile.completed_topics - {
            skill for skill, level in profile.current_skills.items() if level >= 1
        }
        if not missing:
            continue
        changed = replace(
            profile,
            completed_topics=profile.completed_topics | missing,
        )
        before = suite.hybrid_score_details(profile, resource)
        after = suite.hybrid_score_details(changed, resource)
        passed = (
            after.raw_signals["prerequisite_match"] == 1.0
            and after.total_score + EPSILON >= before.total_score
        )
        row = _base_row("prerequisite_completion", profile.profile_id, resource.resource_id)
        row.update(
            {
                "changed_skill": ";".join(sorted(missing)),
                "before_signal": round(before.raw_signals["prerequisite_match"], 6),
                "after_signal": round(after.raw_signals["prerequisite_match"], 6),
                "before_score": round(before.total_score, 6),
                "after_score": round(after.total_score, 6),
                "passed": passed,
                "component_changes": _component_changes(before, after),
                "details": "Missing prerequisites added to completed topics.",
            }
        )
        rows.append(row)
    return rows


def _skill_improvement_cases(suite, profile, resources, skill_map) -> list[dict[str, object]]:
    rows = []
    requirements = skill_map[profile.target_pathway]
    for skill in sorted(profile.weak_skills):
        if requirements.get(skill, 0) <= profile.current_skills.get(skill, 0):
            continue
        for resource in resources:
            if resource.skills != {skill}:
                continue
            before = suite.hybrid_score_details(profile, resource)
            changed_levels = dict(profile.current_skills)
            changed_levels[skill] = requirements[skill]
            changed = replace(
                profile,
                current_skills=changed_levels,
                weak_skills=profile.weak_skills - {skill},
            )
            after = suite.hybrid_score_details(changed, resource)
            row = _base_row("skill_improvement", profile.profile_id, resource.resource_id)
            row.update(
                {
                    "changed_skill": skill,
                    "before_signal": round(before.raw_signals["skill_gap_match"], 6),
                    "after_signal": round(after.raw_signals["skill_gap_match"], 6),
                    "before_score": round(before.total_score, 6),
                    "after_score": round(after.total_score, 6),
                    "passed": after.total_score <= before.total_score + EPSILON,
                    "component_changes": _component_changes(before, after),
                    "details": "Skill raised to pathway requirement and weak flag removed.",
                }
            )
            rows.append(row)
    return rows


def _difficulty_cases(suite, profile, resources) -> list[dict[str, object]]:
    rows = []
    for resource in resources:
        if resource.difficulty_level == profile.preferred_difficulty:
            continue
        before = suite.hybrid_score_details(profile, resource)
        changed = replace(profile, preferred_difficulty=resource.difficulty_level)
        after = suite.hybrid_score_details(changed, resource)
        passed = (
            after.raw_signals["difficulty_match"] > before.raw_signals["difficulty_match"]
            and after.total_score + EPSILON >= before.total_score
        )
        row = _base_row("preferred_difficulty", profile.profile_id, resource.resource_id)
        row.update(
            {
                "changed_skill": str(resource.difficulty_level),
                "before_signal": round(before.raw_signals["difficulty_match"], 6),
                "after_signal": round(after.raw_signals["difficulty_match"], 6),
                "before_score": round(before.total_score, 6),
                "after_score": round(after.total_score, 6),
                "passed": passed,
                "component_changes": _component_changes(before, after),
                "details": "Preference moved exactly to the resource difficulty.",
            }
        )
        rows.append(row)
    return rows


def _weakness_removal_cases(suite, profile, resources) -> list[dict[str, object]]:
    rows = []
    for skill in sorted(profile.weak_skills):
        for resource in resources:
            if resource.skills & profile.weak_skills != {skill}:
                continue
            before = suite.hybrid_score_details(profile, resource)
            changed = replace(profile, weak_skills=profile.weak_skills - {skill})
            after = suite.hybrid_score_details(changed, resource)
            row = _base_row("weakness_removal", profile.profile_id, resource.resource_id)
            row.update(
                {
                    "changed_skill": skill,
                    "before_signal": round(before.raw_signals["job_skill_alignment"], 6),
                    "after_signal": round(after.raw_signals["job_skill_alignment"], 6),
                    "before_score": round(before.total_score, 6),
                    "after_score": round(after.total_score, 6),
                    "passed": after.total_score <= before.total_score + EPSILON,
                    "component_changes": _component_changes(before, after),
                    "details": "The resource's only declared-weak overlap was removed.",
                }
            )
            rows.append(row)
    return rows


def _irrelevant_topic_case(suite, profile) -> dict[str, object]:
    before = suite.recommend(profile, model="hybrid", top_k=10)
    changed = replace(
        profile,
        completed_topics=profile.completed_topics | {UNKNOWN_TOPIC},
    )
    after = suite.recommend(changed, model="hybrid", top_k=10)
    row = _base_row("irrelevant_completed_topic", profile.profile_id)
    row.update(
        {
            "changed_skill": UNKNOWN_TOPIC,
            "passed": before == after,
            "details": "Top-ten recommendations, scores, and explanations compared exactly.",
        }
    )
    return row


def _component_changes(before, after) -> str:
    """Describe every raw signal that changed in one counterfactual case."""

    return ";".join(
        f"{component}:{before.raw_signals[component]:.6f}>{after.raw_signals[component]:.6f}"
        for component in before.raw_signals
        if abs(before.raw_signals[component] - after.raw_signals[component]) > EPSILON
    )
