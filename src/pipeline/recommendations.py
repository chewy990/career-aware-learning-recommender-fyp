"""Serialise ranked recommendations without changing their order.

This module owns CSV row shape only. It must not score or rerank resources.
"""

from __future__ import annotations

from edu_recommender.models import Recommendation


def _recommendation_rows(recommendations: list[Recommendation]) -> list[dict[str, object]]:
    return [
        {
            "profile_id": recommendation.profile_id,
            "model": recommendation.model,
            "rank": recommendation.rank,
            "resource_id": recommendation.resource_id,
            "title": recommendation.title,
            "provider": recommendation.provider,
            "score": recommendation.score,
            "explanation": recommendation.explanation,
        }
        for recommendation in recommendations
    ]

