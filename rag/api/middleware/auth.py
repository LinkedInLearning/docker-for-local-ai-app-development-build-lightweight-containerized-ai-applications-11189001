import hmac
from typing import Awaitable, Callable, Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from rag.api.middleware.errors import build_error_response
from rag.observability.logging import get_current_request_id, get_logger


API_KEY_HEADER: str = "X-API-Key"

AUTH_ALLOWLIST: frozenset[str] = frozenset({
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
})


def _matches_any(provided: str, keys: tuple[str, ...]) -> bool:
    provided_b = provided.encode("utf-8")
    matched = False
    for k in keys:
        if hmac.compare_digest(k.encode("utf-8"), provided_b):
            matched = True
    return matched


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Reject any non-allowlisted request lacking a valid X-API-Key."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        api_keys: Iterable[str],
        header_name: str = API_KEY_HEADER,
        allowlist: frozenset[str] = AUTH_ALLOWLIST,
    ) -> None:
        super().__init__(app)
        self._keys: tuple[str, ...] = tuple(k for k in api_keys if k)
        self.header_name = header_name
        self.allowlist = allowlist

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in self.allowlist:
            return await call_next(request)

        logger = get_logger()
        provided = request.headers.get(self.header_name, "")

        if not provided:
            logger.warning(
                "auth.missing_header",
                extra={
                    "stage": "auth.missing_header",
                    "extra_data": {"path": request.url.path},
                },
            )
            return build_error_response(
                status_code=401,
                error_message="Invalid or missing API key",
                request_id=get_current_request_id(),
            )

        if not _matches_any(provided, self._keys):
            logger.warning(
                "auth.invalid_key",
                extra={
                    "stage": "auth.invalid_key",
                    "extra_data": {"path": request.url.path},
                },
            )
            return build_error_response(
                status_code=401,
                error_message="Invalid or missing API key",
                request_id=get_current_request_id(),
            )

        return await call_next(request)
