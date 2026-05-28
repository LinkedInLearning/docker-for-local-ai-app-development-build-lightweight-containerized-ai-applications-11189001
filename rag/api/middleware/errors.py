from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from rag.api.middleware.request_id import REQUEST_ID_HEADER
from rag.observability.logging import get_current_request_id, get_logger


GENERIC_500_MESSAGE: str = "Internal server error"


def register_exception_handlers(app: FastAPI) -> None:
    """Install three handlers on `app`:
      1. HTTPException     -> preserve status code, sanitize body
      2. RequestValidationError -> 422 with sanitized body
      3. Exception (catch-all)  -> 500, log traceback, sanitized body

    All responses include `X-Request-ID` header and
    `{"request_id": ..., "error": ...}` body.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None) or get_current_request_id()
        logger = get_logger()
        if exc.status_code >= 500:
            logger.error(
                "http_exception",
                exc_info=exc,
                extra={"stage": "http_exception", "extra_data": {"status_code": exc.status_code}},
            )
            error_message = GENERIC_500_MESSAGE
        else:
            logger.warning(
                "http_exception",
                extra={
                    "stage": "http_exception",
                    "extra_data": {"status_code": exc.status_code, "detail": str(exc.detail)},
                },
            )
            error_message = str(exc.detail)
        return build_error_response(
            status_code=exc.status_code,
            error_message=error_message,
            request_id=request_id,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None) or get_current_request_id()
        logger = get_logger()
        logger.warning(
            "request_validation_error",
            extra={
                "stage": "request_validation_error",
                "extra_data": {"errors": exc.errors()},
            },
        )
        return build_error_response(
            status_code=422,
            error_message="Request validation failed",
            request_id=request_id,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None) or get_current_request_id()
        logger = get_logger()
        logger.error(
            "unhandled_exception",
            exc_info=exc,
            extra={"stage": "unhandled_exception", "extra_data": {"type": type(exc).__name__}},
        )
        return build_error_response(
            status_code=500,
            error_message=GENERIC_500_MESSAGE,
            request_id=request_id,
        )


def build_error_response(
    *,
    status_code: int,
    error_message: str,
    request_id: str,
) -> JSONResponse:
    """Construct the canonical sanitized error envelope. PUBLIC so Phase 3
    middleware (rate limit 429, upload size 413) can reuse the same shape.
    """
    return JSONResponse(
        status_code=status_code,
        content={"request_id": request_id, "error": error_message},
        headers={REQUEST_ID_HEADER: request_id},
    )
