"""Public compatibility API for the eda phase."""

from .contracts import (
    DIFFICULTY_LABELS,
    DURATION_BANDS,
    EDA_VERSION,
    FIGURE_FILES,
    PATHWAY_ORDER,
    TABLE_FIELDS,
    EdaResult,
)
from .service import generate_eda
from .tables import build_eda_tables

__all__ = [
    "DIFFICULTY_LABELS",
    "DURATION_BANDS",
    "EDA_VERSION",
    "FIGURE_FILES",
    "PATHWAY_ORDER",
    "TABLE_FIELDS",
    "EdaResult",
    "build_eda_tables",
    "generate_eda",
]
