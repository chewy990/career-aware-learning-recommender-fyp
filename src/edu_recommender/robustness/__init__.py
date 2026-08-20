"""Public compatibility API for the robustness phase."""

from .contracts import (
    COMPONENTS,
    FAILURE_THRESHOLDS,
    FIGURE_METADATA,
    MODEL_COLOUR,
    NEGATIVE_COLOUR,
    NEUTRAL_COLOUR,
    POSITIVE_COLOUR,
    ROBUSTNESS_VERSION,
    SEEDED_CONFIGURATION_COUNT,
    SEEDED_MULTIPLIER_RANGE,
    SENSITIVITY_MULTIPLIERS,
    RobustnessResult,
)
from .seeded_configurations import build_seeded_weight_configurations
from .service import generate_robustness_analysis

__all__ = [
    "COMPONENTS",
    "FAILURE_THRESHOLDS",
    "FIGURE_METADATA",
    "MODEL_COLOUR",
    "NEGATIVE_COLOUR",
    "NEUTRAL_COLOUR",
    "POSITIVE_COLOUR",
    "ROBUSTNESS_VERSION",
    "SEEDED_CONFIGURATION_COUNT",
    "SEEDED_MULTIPLIER_RANGE",
    "SENSITIVITY_MULTIPLIERS",
    "RobustnessResult",
    "build_seeded_weight_configurations",
    "generate_robustness_analysis",
]
