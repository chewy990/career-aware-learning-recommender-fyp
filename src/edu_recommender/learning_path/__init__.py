"""Public compatibility API for the learning path phase."""

from .construction import (
    balance_path_stages,
    build_learning_path,
    deepen_recommendations_for_profile,
    is_broad_track,
    is_supporting_resource,
    project_prerequisite_fit,
    project_recommendations_for_profile,
    structured_tracks_for_profile,
)
from .module_selection import (
    learning_item_reason,
    module_style_resource_title,
    modules_by_parent_resource,
    resource_item_source,
    resource_provider_source,
    selected_module_for_resource,
)
from .readiness import (
    can_gain_tracked_skill,
    can_improve_in_stage,
    completion_readiness,
    skill_completion_cap,
    stage_skill_cap,
    unlock_message,
    unlock_skill_text,
)

__all__ = [
    "balance_path_stages",
    "build_learning_path",
    "can_gain_tracked_skill",
    "can_improve_in_stage",
    "completion_readiness",
    "deepen_recommendations_for_profile",
    "is_broad_track",
    "is_supporting_resource",
    "learning_item_reason",
    "module_style_resource_title",
    "modules_by_parent_resource",
    "project_prerequisite_fit",
    "project_recommendations_for_profile",
    "resource_item_source",
    "resource_provider_source",
    "selected_module_for_resource",
    "skill_completion_cap",
    "stage_skill_cap",
    "structured_tracks_for_profile",
    "unlock_message",
    "unlock_skill_text",
]
