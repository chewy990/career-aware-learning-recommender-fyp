"""ASGI middleware used by the maintained FastAPI application."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from starlette.responses import JSONResponse

AsgiCallable = Callable[
    [dict[str, Any], Callable[[], Awaitable[dict[str, Any]]], Callable[..., Awaitable[None]]],
    Awaitable[None],
]


class RequestBodyLimitMiddleware:
    """Reject oversized request bodies before FastAPI parses their content."""

    def __init__(self, app: AsgiCallable, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[..., Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = self._content_length(scope)
        if content_length is not None and content_length > self.max_bytes:
            await self._reject(scope, receive, send)
            return

        messages: list[dict[str, Any]] = []
        total = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.disconnect":
                break
            total += len(message.get("body", b""))
            if total > self.max_bytes:
                await self._reject(scope, receive, send)
                return
            if not message.get("more_body", False):
                break

        index = 0

        async def replay_receive() -> dict[str, Any]:
            nonlocal index
            if index < len(messages):
                message = messages[index]
                index += 1
                return message
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, replay_receive, send)

    @staticmethod
    def _content_length(scope: dict[str, Any]) -> int | None:
        headers = dict(scope.get("headers", []))
        value = headers.get(b"content-length")
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    async def _reject(
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[..., Awaitable[None]],
    ) -> None:
        response = JSONResponse(
            {"detail": "Request body is too large"},
            status_code=413,
        )
        await response(scope, receive, send)
