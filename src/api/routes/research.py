from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth import require_user, validate_request_origin
from api.config import EVALUATION_K, MODELS
from api.data_service import project_data
from api.rate_limit import enforce_compute_rate_limit
from api.schemas import ResearchRequest
from edu_recommender.evaluation import evaluate_recommendations

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/recommendations")
def research_recommendations(
    payload: ResearchRequest,
    request: Request,
    _username: str = Depends(require_user),
) -> dict[str, object]:
    """Return recommendation evidence for the Research View."""

    validate_request_origin(request)
    enforce_compute_rate_limit(request)
    _, _, _, profile_rows, _, suite = project_data()
    profile = next(
        (
            row
            for row in profile_rows
            if row.profile_id == payload.profile_id
        ),
        None,
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Unknown profile")
    recommendations = suite.recommend(
        profile,
        payload.model,
        top_k=payload.top_k,
        include_broad_tracks=True,
    )
    return {
        "recommendations": [
            {
                "rank": item.rank,
                "resource_id": item.resource_id,
                "title": item.title,
                "provider": item.provider,
                "score": item.score,
                "explanation": item.explanation,
            }
            for item in recommendations
        ]
    }


@router.get("/metrics")
def research_metrics(
    _username: str = Depends(require_user),
) -> dict[str, object]:
    """Return the stored evaluation metrics requested by the Research View."""

    return {"metrics": _cached_evaluation_metrics()}


@lru_cache(maxsize=1)
def _cached_evaluation_metrics() -> list[dict[str, object]]:
    """Compute fixed-profile metrics once for the immutable project dataset."""

    _, _, _, profile_rows, relevance, suite = project_data()
    recommendations_by_model = {
        model: {
            profile.profile_id: suite.recommend(
                profile,
                model=model,
                top_k=EVALUATION_K,
            )
            for profile in profile_rows
        }
        for model in MODELS
    }
    return evaluate_recommendations(
        recommendations_by_model,
        relevance,
        k=EVALUATION_K,
    )


@router.get("/dataset-summary")
def research_dataset_summary() -> dict[str, object]:
    """Return validated dataset counts and coverage evidence."""

    resources, modules, skill_map, profile_rows, relevance, _ = project_data()
    skill_count = len(
        {
            skill
            for targets in skill_map.values()
            for skill, level in targets.items()
            if level > 0
        }
    )
    return {
        "learning_resources": len(resources),
        "verified_modules": len(modules),
        "learner_profiles": len(profile_rows),
        "relevance_profiles": len(relevance),
        "pathways": len(skill_map),
        "skills": skill_count,
        "output_folder": "outputs",
    }
