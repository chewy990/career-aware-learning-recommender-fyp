"""Implement the pre-declared weak-skill-alignment scoring variant."""

from __future__ import annotations

from dataclasses import replace

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.models import Recommendation, RecommenderSuite
from edu_recommender.models.signals import _weighted_overlap

VARIANT_MODEL = "hybrid_weak_skill_alignment"
GATED_VARIANT_MODEL = "hybrid_readiness_gated_weak_skill_alignment"


class WeakSkillAlignmentSuite(RecommenderSuite):
    """Replace broad job-skill alignment with remaining declared-weak coverage."""

    def _hybrid_signals(
        self,
        profile: LearnerProfile,
        resource: Resource,
        content_similarity: float,
        gaps: dict[str, float] | None = None,
    ) -> dict[str, float]:
        signals = super()._hybrid_signals(
            profile,
            resource,
            content_similarity,
            gaps,
        )
        if gaps is None:
            gaps = self.skill_gaps(profile)
        remaining_weak_gaps = {
            skill: gaps[skill]
            for skill in profile.weak_skills
            if skill in gaps and gaps[skill] > 0
        }
        signals["job_skill_alignment"] = _weighted_overlap(
            resource.skills,
            remaining_weak_gaps,
        )
        return signals


class ReadinessGatedWeakSkillAlignmentSuite(WeakSkillAlignmentSuite):
    """Gate declared-weak alignment by existing difficulty and prerequisite fit."""

    def _hybrid_signals(
        self,
        profile: LearnerProfile,
        resource: Resource,
        content_similarity: float,
        gaps: dict[str, float] | None = None,
    ) -> dict[str, float]:
        signals = super()._hybrid_signals(
            profile,
            resource,
            content_similarity,
            gaps,
        )
        signals["job_skill_alignment"] *= (
            signals["difficulty_match"] * signals["prerequisite_match"]
        )
        return signals


def build_variant_recommendations(
    suite: WeakSkillAlignmentSuite,
    profiles: list[LearnerProfile],
    top_k: int,
) -> dict[str, list[Recommendation]]:
    """Build deterministic variant rankings with an explicit model label."""

    return {
        profile.profile_id: [
            replace(recommendation, model=VARIANT_MODEL)
            for recommendation in suite.recommend(
                profile,
                model="hybrid",
                top_k=top_k,
            )
        ]
        for profile in profiles
    }


def build_gated_variant_recommendations(
    suite: ReadinessGatedWeakSkillAlignmentSuite,
    profiles: list[LearnerProfile],
    top_k: int,
) -> dict[str, list[Recommendation]]:
    """Build deterministic readiness-gated rankings with an explicit label."""

    return {
        profile.profile_id: [
            replace(recommendation, model=GATED_VARIANT_MODEL)
            for recommendation in suite.recommend(
                profile,
                model="hybrid",
                top_k=top_k,
            )
        ]
        for profile in profiles
    }
