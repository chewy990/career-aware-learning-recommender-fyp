from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

from edu_recommender.data import (
    read_profiles,
    read_relevance_judgements,
    read_resources,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "graded_relevance_working"
RANDOM_SEED = 20260812

VISIBLE_COLUMNS = (
    "grading_item_id",
    "pathway",
    "profile_name",
    "current_skills",
    "completed_topics",
    "weak_skills",
    "preferred_difficulty",
    "resource_title",
    "provider",
    "topic",
    "skills",
    "resource_difficulty",
    "duration_hours",
    "format",
    "prerequisites",
    "cost",
    "description",
    "relevance_grade",
    "reviewer_confidence",
    "reviewer_notes",
)


def generate_pack(output_dir: Path) -> tuple[Path, Path]:
    """Generate a deterministic positive-only blinded grading sheet and key."""

    data_dir = ROOT / "data"
    profiles = {item.profile_id: item for item in read_profiles(data_dir / "learner_profiles.csv")}
    resources = {item.resource_id: item for item in read_resources(data_dir / "resources.csv")}
    relevance = read_relevance_judgements(data_dir / "relevance_judgements.csv")
    pairs = sorted(
        (profile_id, resource_id)
        for profile_id, resource_ids in relevance.items()
        for resource_id in resource_ids
    )
    random.Random(RANDOM_SEED).shuffle(pairs)

    visible_rows: list[dict[str, object]] = []
    key_rows: list[dict[str, object]] = []
    for index, (profile_id, resource_id) in enumerate(pairs, start=1):
        item_id = f"G{index:03d}"
        profile = profiles[profile_id]
        resource = resources[resource_id]
        visible_rows.append(
            {
                "grading_item_id": item_id,
                "pathway": profile.target_pathway,
                "profile_name": profile.name,
                "current_skills": _skill_levels(profile.current_skills),
                "completed_topics": _tokens(profile.completed_topics),
                "weak_skills": _tokens(profile.weak_skills),
                "preferred_difficulty": profile.preferred_difficulty,
                "resource_title": resource.title,
                "provider": resource.provider,
                "topic": resource.topic,
                "skills": _tokens(resource.skills),
                "resource_difficulty": resource.difficulty_level,
                "duration_hours": resource.duration_hours,
                "format": resource.format,
                "prerequisites": _tokens(resource.prerequisites),
                "cost": resource.cost,
                "description": resource.description,
                "relevance_grade": "",
                "reviewer_confidence": "",
                "reviewer_notes": "",
            }
        )
        key_rows.append(
            {
                "grading_item_id": item_id,
                "profile_id": profile_id,
                "resource_id": resource_id,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    blinded_path = output_dir / "graded_relevance_blinded.csv"
    key_path = output_dir / "graded_relevance_key.csv"
    _write_csv(blinded_path, VISIBLE_COLUMNS, visible_rows)
    _write_csv(key_path, ("grading_item_id", "profile_id", "resource_id"), key_rows)
    _write_browser_reviewer(output_dir, visible_rows, blinded_path)
    return blinded_path, key_path


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_browser_reviewer(
    output_dir: Path,
    rows: list[dict[str, object]],
    blinded_path: Path,
) -> None:
    template = (ROOT / "src" / "graded_relevance_review_template.html").read_text(
        encoding="utf-8"
    )
    pack_id = hashlib.sha256(blinded_path.read_bytes()).hexdigest()[:16]
    items_json = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    fields_json = json.dumps(VISIBLE_COLUMNS, separators=(",", ":"))
    html = (
        template.replace("__ITEMS__", items_json.replace("<", "\\u003c"))
        .replace("__FIELDS__", fields_json)
        .replace("__PACK_ID__", pack_id)
    )
    (output_dir / "graded_relevance_review.html").write_text(
        html,
        encoding="utf-8",
    )


def _tokens(values: set[str]) -> str:
    return ";".join(sorted(values))


def _skill_levels(values: dict[str, int]) -> str:
    return ";".join(f"{skill}:{level}" for skill, level in sorted(values.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the blinded graded-relevance pack.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    blinded_path, key_path = generate_pack(args.output_dir.resolve())
    print(f"Blinded grading sheet: {blinded_path}")
    print(f"Hidden key (do not give to reviewer): {key_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
