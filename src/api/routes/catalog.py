from __future__ import annotations

from fastapi import APIRouter

from api.data_service import project_data
from edu_recommender.presentation import display_pathway, display_skill

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/pathways")
def pathways() -> dict[str, object]:
    """Return the public pathways catalogue."""

    _, _, skill_map, _, _, _ = project_data()
    all_skills = sorted(
        {
            skill
            for targets in skill_map.values()
            for skill, level in targets.items()
            if level > 0
        }
    )
    return {
        "pathways": [
            {
                "id": pathway,
                "label": display_pathway(pathway),
                "skills": [
                    {
                        "id": skill,
                        "label": display_skill(skill),
                        "target": level,
                    }
                    for skill, level in targets.items()
                    if level > 0
                ],
            }
            for pathway, targets in skill_map.items()
        ],
        "skills": [
            {"id": skill, "label": display_skill(skill)}
            for skill in all_skills
        ],
    }


@router.get("/profiles")
def profiles() -> dict[str, object]:
    """Return the public profiles catalogue."""

    _, _, _, profile_rows, _, _ = project_data()
    return {
        "profiles": [
            {
                "profile_id": profile.profile_id,
                "name": profile.name,
                "target_pathway": profile.target_pathway,
                "target_pathway_label": display_pathway(
                    profile.target_pathway
                ),
                "current_skills": profile.current_skills,
                "completed_topics": sorted(profile.completed_topics),
                "weak_skills": sorted(profile.weak_skills),
                "preferred_difficulty": profile.preferred_difficulty,
                "preferred_format": profile.preferred_format,
            }
            for profile in profile_rows
        ]
    }
