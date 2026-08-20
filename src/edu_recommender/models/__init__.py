"""Public compatibility API for the models phase."""

from .contracts import (
    HYBRID_WEIGHTS,
    POPULARITY_WEIGHTS,
    HybridScoreDetails,
    Recommendation,
)
from .signals import prerequisites_satisfied
from .suite import RecommenderSuite

__all__ = [
    "HYBRID_WEIGHTS",
    "POPULARITY_WEIGHTS",
    "HybridScoreDetails",
    "Recommendation",
    "RecommenderSuite",
    "prerequisites_satisfied",
]
