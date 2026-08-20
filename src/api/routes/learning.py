from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import require_user, validate_request_origin
from api.config import TOP_K
from api.data_service import project_data
from api.learning_service import (
    course_complete,
    item_payload,
    make_profile,
    next_pathway_options,
    validate_known_skills,
)
from api.rate_limit import enforce_compute_rate_limit
from api.schemas import (
    CompleteItemRequest,
    LearningPathRequest,
    NextPathwaysRequest,
)
from edu_recommender.learning_path import (
    build_learning_path,
    modules_by_parent_resource,
    selected_module_for_resource,
    skill_completion_cap,
)
from edu_recommender.presentation import (
    display_pathway,
    display_skill,
    skill_level_label,
)

router = APIRouter(prefix="/api", tags=["learning"])


@router.post("/learning-path")
def learning_path(
    payload: LearningPathRequest,
    request: Request,
    _username: str = Depends(require_user),
) -> dict[str, object]:
    """Return a stable learning path for the authenticated learner request."""

    validate_request_origin(request)
    enforce_compute_rate_limit(request)
    resources, modules, skill_map, _, _, suite = project_data()
    resources_by_id = {resource.resource_id: resource for resource in resources}
    modules_by_parent = modules_by_parent_resource(modules)
    profile = make_profile(payload, skill_map)
    gaps = suite.skill_gaps(profile)
    path = build_learning_path(
        suite,
        profile,
        resources_by_id,
        total_k=TOP_K,
    )
    completed_item_ids = set(payload.completed_item_ids)
    skill_targets = skill_map[profile.target_pathway]

    stages = []
    for stage, recommendations in path.items():
        stage_items = []
        for recommendation in recommendations:
            resource = resources_by_id[recommendation.resource_id]
            module = selected_module_for_resource(
                profile,
                resource,
                modules_by_parent.get(resource.resource_id, []),
                gaps,
            )
            item = item_payload(
                profile,
                stage,
                resource,
                module,
                gaps,
                completed_item_ids,
                skill_targets,
                score=recommendation.score,
                explanation=recommendation.explanation,
            )
            if item["completed"] or item["can_improve"]:
                stage_items.append(item)
        stages.append({"name": stage, "items": stage_items})

    visible_items = [item for stage in stages for item in stage["items"]]
    return {
        "profile": {
            "profile_id": profile.profile_id,
            "name": profile.name,
            "target_pathway": profile.target_pathway,
            "target_pathway_label": display_pathway(profile.target_pathway),
            "current_skills": profile.current_skills,
            "completed_topics": sorted(profile.completed_topics),
            "preferred_difficulty": profile.preferred_difficulty,
            "preferred_format": profile.preferred_format,
        },
        "skill_gaps": [
            {
                "skill": skill,
                "label": display_skill(skill),
                "current": profile.current_skills.get(skill, 0),
                "target": skill_targets.get(skill, 0),
                "current_label": skill_level_label(
                    profile.current_skills.get(skill, 0)
                ),
                "target_label": skill_level_label(skill_targets.get(skill, 0)),
                "priority": (
                    "High" if score >= 0.75 else "Medium" if score >= 0.4 else "Low"
                ),
            }
            for skill, score in sorted(
                gaps.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "stages": stages,
        "course_complete": course_complete(visible_items),
    }


@router.post("/complete-item")
def complete_item(
    payload: CompleteItemRequest,
    request: Request,
    _username: str = Depends(require_user),
) -> dict[str, object]:
    """Apply one completion event and return the resulting learner state."""

    validate_request_origin(request)
    enforce_compute_rate_limit(request)
    _, _, skill_map, _, _, _ = project_data()
    if payload.target_pathway not in skill_map:
        raise HTTPException(status_code=404, detail="Unknown pathway")
    validate_known_skills(payload.current_skills, skill_map)
    validate_known_skills(payload.skills, skill_map)
    active_skills = dict(payload.current_skills)
    completed_topics = set(payload.completed_topics)
    before = dict(active_skills)

    for skill in payload.skills:
        current = active_skills.get(skill, 0)
        cap = skill_completion_cap(
            payload.stage,
            current,
            skill,
            skill_map[payload.target_pathway],
        )
        if current < cap:
            active_skills[skill] = min(current + 1, cap)
        completed_topics.add(skill)
    if payload.topic:
        completed_topics.add(payload.topic)

    changes = [
        {
            "skill": skill,
            "label": display_skill(skill),
            "before": before.get(skill, 0),
            "after": active_skills.get(skill, 0),
            "before_label": skill_level_label(before.get(skill, 0)),
            "after_label": skill_level_label(active_skills.get(skill, 0)),
        }
        for skill in sorted(payload.skills)
        if before.get(skill, 0) != active_skills.get(skill, 0)
    ]
    response: dict[str, object] = {
        "current_skills": active_skills,
        "completed_topics": sorted(completed_topics),
        "skill_changes": changes,
    }
    return response


@router.post("/next-pathways")
def next_pathways_view(
    payload: NextPathwaysRequest,
    request: Request,
    _username: str = Depends(require_user),
) -> dict[str, object]:
    """Return where a learner's current skills could take them next.

    Computed from live learner state on every call rather than stored on the
    path snapshot, because it depends on skills gained across every course and
    on which courses the learner already holds.

    """

    validate_request_origin(request)
    enforce_compute_rate_limit(request)
    _, _, skill_map, _, _, _ = project_data()
    if payload.target_pathway and payload.target_pathway not in skill_map:
        raise HTTPException(status_code=404, detail="Unknown pathway")
    validate_known_skills(payload.current_skills, skill_map)
    return {
        "next_pathways": next_pathway_options(
            skill_map,
            payload.current_skills,
            payload.target_pathway,
            (*payload.selected_pathways, *payload.completed_courses),
        )
    }
