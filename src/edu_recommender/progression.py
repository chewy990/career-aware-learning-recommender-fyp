"""Pathway progression derived from the skill map.

Records how much of a target pathway's requirement a learner already meets and
which skills remain. This measures shared skill requirements between pathways.
It is not evidence that learners move between these roles, and it must not be
presented as career advice.

"""

from __future__ import annotations


def remaining_skills(
    skill_map: dict[str, dict[str, int]],
    pathway: str,
    current_skills: dict[str, int],
) -> dict[str, int]:
    """Return how many levels each skill is still short of the pathway requirement."""

    required = skill_map.get(pathway, {})
    shortfalls = {
        skill: level - current_skills.get(skill, 0)
        for skill, level in required.items()
        if level - current_skills.get(skill, 0) > 0
    }
    return dict(sorted(shortfalls.items(), key=lambda item: (-item[1], item[0])))


def pathway_coverage(
    skill_map: dict[str, dict[str, int]],
    pathway: str,
    current_skills: dict[str, int],
) -> float:
    """Return the share of a pathway's total requirement the learner already meets."""

    required_total = sum(skill_map.get(pathway, {}).values())
    if required_total == 0:
        return 0.0
    outstanding = sum(remaining_skills(skill_map, pathway, current_skills).values())
    return 1.0 - outstanding / required_total


def next_pathways(
    skill_map: dict[str, dict[str, int]],
    current_skills: dict[str, int],
    exclude: tuple[str, ...] = (),
    limit: int = 2,
) -> list[dict[str, object]]:
    """Rank candidate pathways by how much of each requirement is already met.

    Ties break on pathway name so the ordering is stable across runs.

    """

    candidates = [
        {
            "pathway": pathway,
            "coverage": pathway_coverage(skill_map, pathway, current_skills),
            "remaining": remaining_skills(skill_map, pathway, current_skills),
        }
        for pathway in sorted(skill_map)
        if pathway not in exclude and sum(skill_map[pathway].values()) > 0
    ]
    ranked = sorted(
        candidates,
        key=lambda entry: (-entry["coverage"], entry["pathway"]),
    )
    return ranked[:limit] if limit else ranked


def pathway_overlap(
    skill_map: dict[str, dict[str, int]],
) -> dict[str, dict[str, float]]:
    """Return coverage of every target pathway from every other pathway's requirements.

    A learner who has met one pathway's requirements holds exactly those levels,
    so this describes how far that leaves them from each other pathway. The
    result is directional, because two pathways rarely require the same depth of
    the same skills.

    """

    return {
        source: {
            target: pathway_coverage(skill_map, target, skill_map[source])
            for target in sorted(skill_map)
            if target != source
        }
        for source in sorted(skill_map)
    }
