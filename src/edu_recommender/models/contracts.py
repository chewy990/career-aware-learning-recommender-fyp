"""Own models contracts responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from dataclasses import dataclass

HYBRID_WEIGHTS = {
    "career_relevance": 0.25,
    "skill_gap_match": 0.25,
    "job_skill_alignment": 0.15,
    "difficulty_match": 0.10,
    "prerequisite_match": 0.10,
    "resource_quality": 0.10,
    "content_similarity": 0.05,
    "scope_penalty": -0.12,
}

POPULARITY_WEIGHTS = {"quality_score": 0.65, "popularity_score": 0.35}

@dataclass(frozen=True)
class Recommendation:
    """Represent a ranked resource and its deterministic explanation."""

    profile_id: str
    model: str
    rank: int
    resource_id: str
    title: str
    provider: str
    score: float
    explanation: str

@dataclass(frozen=True)
class HybridScoreDetails:
    """Expose the component signals that form one hybrid recommendation score."""

    raw_signals: dict[str, float]
    weighted_contributions: dict[str, float]
    total_score: float
