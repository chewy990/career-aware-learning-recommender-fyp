"""Own label audit contracts responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

from dataclasses import dataclass

AUTHOR_AUDIT_VERSION = 1

VISIBLE_COLUMNS = (
    "audit_item_id",
    "pathway",
    "profile_name",
    "target_pathway",
    "current_skills",
    "weak_skills",
    "preferred_difficulty",
    "resource_title",
    "provider",
    "topic",
    "skills",
    "resource_difficulty",
    "format",
    "prerequisites",
)

REVIEW_COLUMNS = (
    "reviewer_relevance",
    "reviewer_confidence",
    "reviewer_notes",
)

KEY_COLUMNS = (
    "audit_item_id",
    "profile_id",
    "resource_id",
    "current_label",
    "selection_reason",
)

@dataclass(frozen=True)
class AuthorAuditResult:
    """Record the reconciled decisions and counts from the relevance-label author audit."""

    item_count: int
    definite_count: int
    uncertain_count: int
    agreement_count: int
    disagreement_count: int
    agreement_rate: float
    joined_rows: tuple[dict[str, object], ...]
    disagreement_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    output_files: tuple[str, ...]
