from __future__ import annotations

from functools import lru_cache

from api.config import DATA_DIR
from edu_recommender.data import (
    LearnerProfile,
    Resource,
    ResourceModule,
    read_profiles,
    read_relevance_judgements,
    read_resource_modules,
    read_resources,
    read_skill_map,
)
from edu_recommender.models import RecommenderSuite

ProjectData = tuple[
    list[Resource],
    list[ResourceModule],
    dict[str, dict[str, int]],
    list[LearnerProfile],
    dict[str, set[str]],
    RecommenderSuite,
]


@lru_cache(maxsize=1)
def project_data() -> ProjectData:
    """Load immutable project datasets and build the shared recommender once."""
    resources = read_resources(DATA_DIR / "resources.csv")
    modules = read_resource_modules(DATA_DIR / "resource_modules.csv")
    skill_map = read_skill_map(DATA_DIR / "skill_map.csv")
    profiles = read_profiles(DATA_DIR / "learner_profiles.csv")
    relevance = read_relevance_judgements(
        DATA_DIR / "relevance_judgements.csv",
        DATA_DIR / "relevance_judgements_graded.csv",
    )
    suite = RecommenderSuite(resources, skill_map)
    return resources, modules, skill_map, profiles, relevance, suite
