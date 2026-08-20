from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


class GradedResourceSet(set[str]):
    """Carry optional relevance grades while remaining set-compatible."""

    def __init__(
        self,
        resource_ids: set[str],
        grades: dict[str, int] | None = None,
    ) -> None:
        super().__init__(resource_ids)
        self.grades = dict(grades or {})


@dataclass(frozen=True)
class Resource:
    """Describe one learning resource loaded from the project dataset."""

    resource_id: str
    title: str
    provider: str
    topic: str
    skills: set[str]
    difficulty_level: int
    duration_hours: float
    format: str
    prerequisites: set[str]
    cost: str
    popularity_score: float
    quality_score: float
    pathway_relevance: dict[str, int]
    description: str
    source_url: str = ""
    date_checked: str = ""


@dataclass(frozen=True)
class ResourceModule:
    """Describe one independently recommendable module within a resource."""

    module_id: str
    parent_resource_id: str
    module_title: str
    provider: str
    skills: set[str]
    difficulty_level: int
    duration_hours: float
    source_url: str
    date_checked: str


@dataclass(frozen=True)
class LearnerProfile:
    """Describe the learner evidence used to generate and evaluate recommendations."""

    profile_id: str
    name: str
    target_pathway: str
    current_skills: dict[str, int]
    completed_topics: set[str]
    weak_skills: set[str]
    preferred_difficulty: int
    max_duration_hours: float
    preferred_format: str


def read_resources(path: Path) -> list[Resource]:
    """Read resources using the project's CSV parsing conventions."""

    rows = _read_csv(path)
    relevance_fields = [
        field for field in rows[0] if field.endswith("_relevance")
    ] if rows else []
    resources: list[Resource] = []
    for row in rows:
        resources.append(
            Resource(
                resource_id=row["resource_id"],
                title=row["title"],
                provider=row["provider"],
                topic=row["topic"],
                skills=_parse_set(row["skills"]),
                difficulty_level=int(row["difficulty_level"]),
                duration_hours=float(row["duration_hours"]),
                format=row["format"],
                prerequisites=_parse_set(row["prerequisites"]),
                cost=row["cost"],
                popularity_score=float(row["popularity_score"]),
                quality_score=float(row["quality_score"]),
                pathway_relevance={
                    field.removesuffix("_relevance"): int(row.get(field, 0) or 0)
                    for field in relevance_fields
                },
                description=row["description"],
                source_url=row.get("source_url", "").strip(),
                date_checked=row.get("date_checked", "").strip(),
            )
        )
    return resources


def read_resource_modules(path: Path) -> list[ResourceModule]:
    """Read resource modules using the project's CSV parsing conventions."""

    if not path.exists():
        return []
    rows = _read_csv(path)
    return [
        ResourceModule(
            module_id=row["module_id"],
            parent_resource_id=row["parent_resource_id"],
            module_title=row["module_title"],
            provider=row["provider"],
            skills=_parse_set(row["skills"]),
            difficulty_level=int(row["difficulty_level"]),
            duration_hours=float(row["duration_hours"]),
            source_url=row["source_url"],
            date_checked=row["date_checked"],
        )
        for row in rows
    ]


def read_skill_map(path: Path) -> dict[str, dict[str, int]]:
    """Read skill map using the project's CSV parsing conventions."""

    rows = _read_csv(path)
    if not rows:
        return {}
    pathways = [field for field in rows[0] if field != "skill"]
    skill_map: dict[str, dict[str, int]] = {pathway: {} for pathway in pathways}
    for row in rows:
        skill = row["skill"]
        for pathway in pathways:
            skill_map[pathway][skill] = int(row.get(pathway, 0) or 0)
    return skill_map


def read_profiles(path: Path) -> list[LearnerProfile]:
    """Read profiles using the project's CSV parsing conventions."""

    rows = _read_csv(path)
    return [
        LearnerProfile(
            profile_id=row["profile_id"],
            name=row["name"],
            target_pathway=row["target_pathway"],
            current_skills=_parse_skill_levels(row["current_skills"]),
            completed_topics=_parse_set(row["completed_topics"]),
            weak_skills=_parse_set(row["weak_skills"]),
            preferred_difficulty=int(row["preferred_difficulty"]),
            max_duration_hours=float(row["max_duration_hours"]),
            preferred_format=row["preferred_format"],
        )
        for row in rows
    ]


def read_relevance_judgements(
    path: Path,
    graded_path: Path | None = None,
) -> dict[str, set[str]]:
    """Read binary labels and attach optional 1-3 grades to each positive set."""

    rows = _read_csv(path)
    binary = {
        row["profile_id"]: _parse_set(row["relevant_resource_ids"])
        for row in rows
    }
    grades_by_profile: dict[str, dict[str, int]] = {}
    if graded_path is not None and graded_path.is_file():
        for row in _read_csv(graded_path):
            profile_id = row["profile_id"]
            resource_id = row["resource_id"]
            grade = int(row["relevance_grade"])
            if grade not in {1, 2, 3}:
                raise ValueError(
                    f"{graded_path}: relevance grade must be 1, 2, or 3"
                )
            profile_grades = grades_by_profile.setdefault(profile_id, {})
            if resource_id in profile_grades:
                raise ValueError(
                    f"{graded_path}: duplicate grade for {profile_id}/{resource_id}"
                )
            profile_grades[resource_id] = grade
        expected_pairs = {
            (profile_id, resource_id)
            for profile_id, resource_ids in binary.items()
            for resource_id in resource_ids
        }
        actual_pairs = {
            (profile_id, resource_id)
            for profile_id, grades in grades_by_profile.items()
            for resource_id in grades
        }
        if actual_pairs != expected_pairs:
            raise ValueError(
                f"{graded_path}: grades must cover every binary-positive "
                "profile-resource pair exactly once"
            )
    return {
        profile_id: GradedResourceSet(
            resource_ids,
            grades_by_profile.get(profile_id),
        )
        for profile_id, resource_ids in binary.items()
    }


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    """Write rows in stable field and row order."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _parse_set(value: str) -> set[str]:
    if not value.strip():
        return set()
    return {item.strip() for item in value.split(";") if item.strip()}


def _parse_skill_levels(value: str) -> dict[str, int]:
    if not value.strip():
        return {}
    levels: dict[str, int] = {}
    for item in value.split(";"):
        if not item.strip():
            continue
        skill, level = item.split(":", maxsplit=1)
        levels[skill.strip()] = int(level)
    return levels
