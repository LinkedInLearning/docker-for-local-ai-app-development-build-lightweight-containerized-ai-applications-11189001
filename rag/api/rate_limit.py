from __future__ import annotations

import os
import time
from functools import lru_cache

from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from rag.api.middleware.errors import build_error_response
from rag.observability.logging import get_current_request_id, get_logger


DEFAULT_RATE_LIMIT_INGEST: str = "5/minute"
DEFAULT_RATE_LIMIT_QUERY: str = "30/minute"
ENV_RATE_LIMIT_INGEST: str = "RAG_API_RATE_LIMIT_INGEST"
ENV_RATE_LIMIT_QUERY: str = "RAG_API_RATE_LIMIT_QUERY"


@lru_cache
def get_rate_limit_ingest() -> str:
    return (
        os.environ.get(ENV_RATE_LIMIT_INGEST, DEFAULT_RATE_LIMIT_INGEST).strip()
        or DEFAULT_RATE_LIMIT_INGEST
    )


@lru_cache
def get_rate_limit_query() -> str:
    return (
        os.environ.get(ENV_RATE_LIMIT_QUERY, DEFAULT_RATE_LIMIT_QUERY).strip()
        or DEFAULT_RATE_LIMIT_QUERY
    )


# Process-wide singleton. Imported directly by main.py for use in the
# @limiter.limit(...) decorators on the route handlers.
limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
    strategy="fixed-window",
    headers_enabled=True,
)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Convert slowapi's RateLimitExceeded into our sanitized envelope.

    Preserves the standard `Retry-After` header that slowapi computes,
    while replacing the default plaintext body with `{request_id, error}`.
    """
    request_id: str = (
        getattr(request.state, "request_id", None)
        or get_current_request_id()
    )
    logger = get_logger()
    logger.warning(
        "rate_limit.exceeded",
        extra={
            "stage": "rate_limit.exceeded",
            "extra_data": {
                "path": request.url.path,
                "client": get_remote_address(request),
                "limit": str(exc.detail) if hasattr(exc, "detail") else None,
            },
        },
    )
    response = build_error_response(
        status_code=429,
        error_message=(
            f"Rate limit exceeded: {exc.detail}"
            if getattr(exc, "detail", None)
            else "Rate limit exceeded."
        ),
        request_id=request_id,
    )
    # slowapi attaches a Retry-After header on its default response; we
    # need to mirror that ourselves since we're replacing the response.
    # slowapi 0.1.9 sets request.state.view_rate_limit before raising;
    # it may be a dict ({"limit": ..., "reset": <epoch>}) or an object.
    view_rate_limit = getattr(request.state, "view_rate_limit", None)
    if view_rate_limit is not None:
        reset = None
        if isinstance(view_rate_limit, dict):
            reset = view_rate_limit.get("reset")
        else:
            reset = getattr(view_rate_limit, "reset", None)
        if reset is not None:
            try:
                seconds_remaining = max(0, int(reset) - int(time.time()))
                response.headers["Retry-After"] = str(seconds_remaining)
            except (TypeError, ValueError):
                pass
        else:
            # Fallback: use a coarse window derived from the limit string (e.g. "5/minute" -> 60)
            response.headers["Retry-After"] = "60"
    return response


def install_rate_limiter(app: FastAPI) -> None:
    """One-call wiring used by main.py. Adds the limiter to app.state,
    installs SlowAPIMiddleware, and registers the 429 exception handler.

    Call BEFORE `app.add_middleware(RequestIDMiddleware)` so RequestID
    remains outermost (Phase 1 §5 contract).
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
