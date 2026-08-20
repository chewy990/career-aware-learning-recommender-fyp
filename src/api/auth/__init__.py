"""Expose authentication routes while keeping security concerns separated."""

from api.auth.dependencies import require_user
from api.auth.routes import router
from api.auth.validation import validate_request_origin

__all__ = ["require_user", "router", "validate_request_origin"]
