"""Own models suite responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from edu_recommender.data import LearnerProfile, Resource
from edu_recommender.text import TfidfVectorizer, cosine_similarity

from .contracts import (
    HYBRID_WEIGHTS,
    POPULARITY_WEIGHTS,
    HybridScoreDetails,
    Recommendation,
)
from .signals import (
    _is_broad_track,
    _is_supporting_resource,
    _job_skill_alignment,
    _prerequisite_match,
    _scope_fit,
    _weighted_overlap,
    prerequisites_satisfied,
)
from .text_features import _profile_document, _resource_document


class RecommenderSuite:
    """Provide the popularity, content-based, and hybrid recommenders over shared data."""

    def __init__(
        self,
        resources: list[Resource],
        skill_map: dict[str, dict[str, int]],
        hybrid_weights: dict[str, float] | None = None,
    ) -> None:
        self.resources = resources
        self.skill_map = skill_map
        self.hybrid_weights = dict(HYBRID_WEIGHTS)
        if hybrid_weights is not None:
            unknown_weights = set(hybrid_weights) - set(HYBRID_WEIGHTS)
            if unknown_weights:
                raise ValueError(
                    "Unknown hybrid weight(s): "
                    + ", ".join(sorted(unknown_weights))
                )
            self.hybrid_weights.update(hybrid_weights)
        self.vectorizer = TfidfVectorizer()
        self.resource_documents = {resource.resource_id: _resource_document(resource) for resource in resources}
        self.vectorizer.fit(list(self.resource_documents.values()))
        self.resource_vectors = {
            resource_id: self.vectorizer.transform(document)
            for resource_id, document in self.resource_documents.items()
        }

    def recommend(
        self,
        profile: LearnerProfile,
        model: str,
        top_k: int = 5,
        include_broad_tracks: bool = False,
        enforce_prerequisites: bool = False,
    ) -> list[Recommendation]:
        if model not in {"popularity", "content_based", "hybrid"}:
            raise ValueError(f"Unknown recommender model: {model}")

        scored = []
        gaps = self.skill_gaps(profile) if model != "popularity" else {}
        learner_vector = None
        if model != "popularity":
            learner_document = _profile_document(profile, gaps)
            learner_vector = self.vectorizer.transform(learner_document)

        for resource in self.resources:
            if not include_broad_tracks and _is_broad_track(resource):
                continue
            if _is_supporting_resource(resource):
                continue
            if (
                enforce_prerequisites
                and not prerequisites_satisfied(profile, resource)
            ):
                continue
            if model == "popularity":
                score = self._popularity_score(resource)
                explanation = "Recommended because this resource has strong general quality and popularity signals."
            else:
                content_similarity = cosine_similarity(
                    learner_vector,
                    self.resource_vectors[resource.resource_id],
                )
                if model == "content_based":
                    score = content_similarity
                    explanation = self._content_explanation(profile, resource)
                else:
                    components = self._hybrid_components(
                        profile,
                        resource,
                        content_similarity,
                        gaps,
                    )
                    score = sum(components.values())
                    explanation = self._hybrid_explanation(
                        profile,
                        resource,
                        components,
                        gaps,
                    )
            scored.append((score, resource, explanation))

        scored.sort(key=lambda item: (-item[0], item[1].title, item[1].resource_id))
        return [
            Recommendation(
                profile_id=profile.profile_id,
                model=model,
                rank=index + 1,
                resource_id=resource.resource_id,
                title=resource.title,
                provider=resource.provider,
                score=round(score, 4),
                explanation=explanation,
            )
            for index, (score, resource, explanation) in enumerate(scored[:top_k])
        ]

    def skill_gaps(self, profile: LearnerProfile) -> dict[str, float]:
        pathway_requirements = self.skill_map[profile.target_pathway]
        gaps: dict[str, float] = {}
        for skill, required_level in pathway_requirements.items():
            current_level = profile.current_skills.get(skill, 0)
            gap = max(required_level - current_level, 0)
            if skill in profile.weak_skills:
                gap += 0.5
            if gap > 0:
                gaps[skill] = min(gap / 3.5, 1.0)
        return gaps

    def _popularity_score(self, resource: Resource) -> float:
        return (
            POPULARITY_WEIGHTS["quality_score"] * resource.quality_score
            + POPULARITY_WEIGHTS["popularity_score"] * resource.popularity_score
        )

    def _hybrid_components(
        self,
        profile: LearnerProfile,
        resource: Resource,
        content_similarity: float,
        gaps: dict[str, float] | None = None,
    ) -> dict[str, float]:
        signals = self._hybrid_signals(
            profile,
            resource,
            content_similarity,
            gaps,
        )
        return {
            component: self.hybrid_weights[component] * signal
            for component, signal in signals.items()
        }

    def hybrid_score_details(
        self,
        profile: LearnerProfile,
        resource: Resource,
    ) -> HybridScoreDetails:
        gaps = self.skill_gaps(profile)
        learner_document = _profile_document(profile, gaps)
        learner_vector = self.vectorizer.transform(learner_document)
        content_similarity = cosine_similarity(
            learner_vector,
            self.resource_vectors[resource.resource_id],
        )
        raw_signals = self._hybrid_signals(
            profile,
            resource,
            content_similarity,
            gaps,
        )
        contributions = {
            component: self.hybrid_weights[component] * signal
            for component, signal in raw_signals.items()
        }
        return HybridScoreDetails(
            raw_signals=raw_signals,
            weighted_contributions=contributions,
            total_score=sum(contributions.values()),
        )

    def _hybrid_signals(
        self,
        profile: LearnerProfile,
        resource: Resource,
        content_similarity: float,
        gaps: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if gaps is None:
            gaps = self.skill_gaps(profile)
        career_relevance = resource.pathway_relevance[profile.target_pathway] / 3
        skill_gap_match = _weighted_overlap(resource.skills, gaps)
        job_skill_alignment = _job_skill_alignment(resource.skills, self.skill_map[profile.target_pathway])
        difficulty_match = max(0.0, 1 - abs(resource.difficulty_level - profile.preferred_difficulty) / 2)
        prerequisite_match = _prerequisite_match(profile, resource)
        resource_quality = self._popularity_score(resource)
        scope_fit = _scope_fit(resource)

        return {
            "career_relevance": career_relevance,
            "skill_gap_match": skill_gap_match,
            "job_skill_alignment": job_skill_alignment,
            "difficulty_match": difficulty_match,
            "prerequisite_match": prerequisite_match,
            "resource_quality": resource_quality,
            "content_similarity": content_similarity,
            "scope_penalty": 1 - scope_fit,
        }

    def _content_explanation(self, profile: LearnerProfile, resource: Resource) -> str:
        matching_skills = sorted(resource.skills & (profile.weak_skills | set(profile.current_skills)))
        if matching_skills:
            return f"Recommended because its metadata matches learner needs around {', '.join(matching_skills)}."
        return "Recommended because its title, topic, skills, and description are similar to the learner profile."

    def _hybrid_explanation(
        self,
        profile: LearnerProfile,
        resource: Resource,
        components: dict[str, float],
        gaps: dict[str, float] | None = None,
    ) -> str:
        if gaps is None:
            gaps = self.skill_gaps(profile)
        matched_gaps = sorted(
            resource.skills & set(gaps),
            key=lambda skill: (-gaps[skill], skill),
        )
        reasons: list[str] = []

        if matched_gaps:
            reasons.append(f"it targets skill gaps in {', '.join(matched_gaps[:3])}")
        if resource.format == "career_track" or resource.duration_hours >= 20:
            reasons.append("it is broad and should be treated as an optional structured track rather than a first step")
        if components["difficulty_match"] >= 0.075:
            reasons.append("its difficulty matches the learner's current level")
        if components["prerequisite_match"] >= 0.075:
            reasons.append("the learner appears to meet the prerequisites")

        if not reasons:
            reasons.append("it has useful resource metadata and quality signals")
        return "Recommended because " + "; ".join(reasons) + "."
