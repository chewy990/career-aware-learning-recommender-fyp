from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.auth import router as auth_router
from api.auth.storage import initialize_auth_database
from api.config import ALLOWED_ORIGINS, IS_PRODUCTION, MAX_REQUEST_BODY_BYTES
from api.middleware import RequestBodyLimitMiddleware
from api.routes.catalog import router as catalog_router
from api.routes.learning import router as learning_router
from api.routes.research import router as research_router


@asynccontextmanager
async def lifespan(_application: FastAPI):
    """Initialize local persistence before accepting requests."""
    initialize_auth_database()
    yield


def create_app() -> FastAPI:
    """Create the FastAPI application with its existing middleware and route contracts."""

    application = FastAPI(
        title="Career-Aware Learning Recommender API",
        lifespan=lifespan,
        docs_url=None if IS_PRODUCTION else "/docs",
        redoc_url=None if IS_PRODUCTION else "/redoc",
        openapi_url=None if IS_PRODUCTION else "/openapi.json",
    )
    application.add_middleware(
        RequestBodyLimitMiddleware,
        max_bytes=MAX_REQUEST_BODY_BYTES,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(ALLOWED_ORIGINS),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.include_router(auth_router)
    application.include_router(catalog_router)
    application.include_router(learning_router)
    application.include_router(research_router)

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        if request.url.path.startswith("/api/auth/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
