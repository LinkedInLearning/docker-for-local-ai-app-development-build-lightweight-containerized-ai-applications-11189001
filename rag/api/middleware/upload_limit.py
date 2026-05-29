from __future__ import annotations

from typing import Awaitable, Callable, Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from rag.api.middleware.errors import build_error_response
from rag.observability.logging import get_current_request_id, get_logger


DEFAULT_MAX_UPLOAD_MB: int = 50
GUARDED_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH"})
DEFAULT_GUARDED_PATH_PREFIXES: tuple[str, ...] = ("/ingest",)
# /query JSON bodies are tiny — explicitly NOT guarded.


class MaxUploadSizeMiddleware(BaseHTTPMiddleware):
    """Reject POST/PUT/PATCH requests to ingestion routes whose
    Content-Length exceeds `max_bytes`. Returns 413 + sanitized
    envelope BEFORE the request body is read.

    Scope
    -----
    Only requests whose URL path begins with one of `path_prefixes`
    are inspected. Other routes (`/query`, `/health`, `/documents`,
    `/config`, `/ingest/jobs/...`) pass through untouched.

    Missing Content-Length
    ----------------------
    For guarded routes, a missing Content-Length on POST/PUT/PATCH is
    rejected with 411 Length Required. See §3 decision matrix for
    rationale; the short version is: ingestion is JSON-bodied (small,
    well-formed clients always send Content-Length), and ASGI
    receive-side counting would add streaming complexity for a use
    case we deliberately don't support yet (Tier 2 streaming uploads).

    GET / HEAD / DELETE / OPTIONS — never inspected.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        max_bytes: int,
        path_prefixes: Iterable[str] = DEFAULT_GUARDED_PATH_PREFIXES,
        guarded_methods: frozenset[str] = GUARDED_METHODS,
    ) -> None:
        super().__init__(app)
        if max_bytes < 1:
            raise ValueError(f"max_bytes must be >= 1, got {max_bytes}")
        self.max_bytes = max_bytes
        # Sort longest-first so a request to /ingest/jobs/X matches /ingest/jobs
        # before /ingest if both were configured (currently only /ingest is).
        self._prefixes: tuple[str, ...] = tuple(
            sorted(set(path_prefixes), key=len, reverse=True)
        )
        self._guarded_methods = guarded_methods

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method not in self._guarded_methods:
            return await call_next(request)

        path = request.url.path
        if not any(path == p or path.startswith(p + "/") for p in self._prefixes):
            return await call_next(request)

        request_id: str = (
            getattr(request.state, "request_id", None)
            or get_current_request_id()
        )

        raw_len = request.headers.get("content-length")
        logger = get_logger()

        if raw_len is None:
            logger.warning(
                "upload_limit.missing_content_length",
                extra={
                    "stage": "upload_limit.missing_content_length",
                    "extra_data": {"path": path, "method": request.method},
                },
            )
            return build_error_response(
                status_code=411,
                error_message=(
                    "Length Required: ingestion requests must include a "
                    "Content-Length header."
                ),
                request_id=request_id,
            )

        try:
            declared = int(raw_len)
        except ValueError:
            logger.warning(
                "upload_limit.invalid_content_length",
                extra={
                    "stage": "upload_limit.invalid_content_length",
                    "extra_data": {"path": path, "raw": raw_len},
                },
            )
            return build_error_response(
                status_code=400,
                error_message="Invalid Content-Length header.",
                request_id=request_id,
            )

        if declared < 0:
            logger.warning(
                "upload_limit.invalid_content_length",
                extra={
                    "stage": "upload_limit.invalid_content_length",
                    "extra_data": {"path": path, "raw": raw_len},
                },
            )
            return build_error_response(
                status_code=400,
                error_message="Invalid Content-Length header.",
                request_id=request_id,
            )

        if declared > self.max_bytes:
            logger.warning(
                "upload_limit.exceeded",
                extra={
                    "stage": "upload_limit.exceeded",
                    "extra_data": {
                        "path": path,
                        "declared_bytes": declared,
                        "max_bytes": self.max_bytes,
                    },
                },
            )
            return build_error_response(
                status_code=413,
                error_message=(
                    f"Payload too large: {declared} bytes exceeds "
                    f"the {self.max_bytes}-byte limit."
                ),
                request_id=request_id,
            )

        return await call_next(request)
