from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from rag.observability.logging import generate_trace_id, request_id_ctx_var


REQUEST_ID_HEADER: str = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inbound: read or generate X-Request-ID, stash on request.state and
    in the ContextVar. Outbound: echo the same value in the response.
    """

    def __init__(self, app: ASGIApp, *, header_name: str = REQUEST_ID_HEADER) -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        raw = request.headers.get(self.header_name, "")
        request_id = raw.strip() if raw.strip() else generate_trace_id()

        request.state.request_id = request_id
        token = request_id_ctx_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx_var.reset(token)

        response.headers[self.header_name] = request_id
        return response
