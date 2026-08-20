from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

SkillLevel = Annotated[int, Field(ge=0, le=3)]
DifficultyLevel = Annotated[int, Field(ge=1, le=3)]
Identifier = Annotated[
    str,
    Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]
StageName = Literal[
    "1. Learn just enough",
    "2. Start a practical project",
    "3. Deepen later",
    "Optional structured tracks",
]
ModelName = Literal["popularity", "content_based", "hybrid"]


class ApiRequest(BaseModel):
    """Reject undeclared fields so removed preferences cannot fail silently."""

    model_config = ConfigDict(extra="forbid")


class LearningPathRequest(ApiRequest):
    """Validate and serialise the learningpathrequest API contract."""

    target_pathway: Identifier
    current_skills: dict[Identifier, SkillLevel] = Field(
        default_factory=dict,
        max_length=64,
    )
    completed_topics: list[Identifier] = Field(default_factory=list, max_length=128)
    completed_item_ids: list[Identifier] = Field(default_factory=list, max_length=128)
    preferred_difficulty: DifficultyLevel = 1
    preferred_format: Literal["course", "project", "article", "video"] = "course"
    profile_id: Identifier = "custom"
    name: str = Field(default="Custom learner", min_length=1, max_length=120)


class CompleteItemRequest(ApiRequest):
    """Validate and serialise the completeitemrequest API contract."""

    target_pathway: Identifier
    stage: StageName
    current_skills: dict[Identifier, SkillLevel] = Field(
        default_factory=dict,
        max_length=64,
    )
    completed_topics: list[Identifier] = Field(default_factory=list, max_length=128)
    topic: Identifier | Literal[""] = ""
    skills: list[Identifier] = Field(default_factory=list, max_length=32)


class NextPathwaysRequest(ApiRequest):
    """Validate and serialise the nextpathwaysrequest API contract."""

    target_pathway: Identifier
    selected_pathways: list[Identifier] = Field(default_factory=list, max_length=20)
    completed_courses: list[Identifier] = Field(default_factory=list, max_length=20)
    current_skills: dict[Identifier, SkillLevel] = Field(
        default_factory=dict,
        max_length=64,
    )


class ResearchRequest(ApiRequest):
    """Validate and serialise the researchrequest API contract."""

    profile_id: Identifier
    model: ModelName = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)


class AuthRequest(ApiRequest):
    """Validate and serialise the authrequest API contract."""

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class ChangePasswordRequest(ApiRequest):
    """Validate and serialise the changepasswordrequest API contract."""

    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=1, max_length=200)
