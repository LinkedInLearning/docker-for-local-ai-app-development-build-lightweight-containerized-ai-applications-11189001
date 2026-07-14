"""App assembly shared by all three entry points.

`create_app` wires the identical middleware stack, lifespan, and exception
handlers that the monolith used, then mounts whichever routers a service
needs. This keeps the query, ingestion, and combined apps byte-for-byte
consistent in their cross-cutting behavior while differing only in the routes
they expose.

Import-safety: this module and everything it imports at module scope is free
of the Docling parsing stack. The only ingestion-specific hook — eagerly
instantiating the job registry — is gated behind `eager_job_registry` and only
*called* (never imported) so the query app never touches the job runner.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI

from rag.api.dependencies import (
    get_api_keys,
    get_config,
    get_job_registry,
    get_upload_settings,
)
from rag.api.middleware import (
    APIKeyAuthMiddleware,
    MaxUploadSizeMiddleware,
    RequestIDMiddleware,
    register_exception_handlers,
)
from rag.api.rate_limit import (
    get_rate_limit_ingest,
    get_rate_limit_query,
    install_rate_limiter,
)
from rag.observability.logging import get_logger, setup_logging
from rag.observability.tracing import configure_tracing


def _require_auth() -> bool:
    """`RAG_API_REQUIRE_AUTH=false` (case-insensitive) disables auth.
    Any other value (including unset) leaves auth ENABLED.
    """
    return os.environ.get("RAG_API_REQUIRE_AUTH", "true").lower() != "false"


def create_app(
    *,
    title: str,
    routers: list[APIRouter],
    eager_job_registry: bool = False,
) -> FastAPI:
    """Build a FastAPI app with the shared middleware/lifespan and the given
    routers mounted.

    Args:
        title: OpenAPI title for the service.
        routers: Routers to mount, in order.
        eager_job_registry: When True, the lifespan instantiates the job
            registry at startup so a bad ``RAG_API_JOB_REGISTRY_SIZE`` fails
            loud on boot rather than on first ingest. Left False for the query
            service, which has no job routes — and, importantly, this keeps the
            query process from importing the Docling-backed job runner.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        setup_logging()
        config = get_config()
        configure_tracing(config)

        if _require_auth() and not get_api_keys():
            raise RuntimeError(
                "RAG_API_KEYS env var is empty. Set a comma-separated list "
                "of API keys or export RAG_API_REQUIRE_AUTH=false for local dev."
            )

        if eager_job_registry:
            # Eagerly instantiate the JobRegistry so RAG_API_JOB_REGISTRY_SIZE
            # parse errors fail at startup, not on the first ingest call.
            get_job_registry()

        # Eagerly resolve upload settings so a bad env var fails at startup.
        upload = get_upload_settings()
        logger = get_logger()
        if not Path(upload.allowed_upload_dir).exists():
            logger.warning(
                "startup.allowed_upload_dir_missing",
                extra={
                    "stage": "startup.allowed_upload_dir_missing",
                    "extra_data": {"path": upload.allowed_upload_dir},
                },
            )
        logger.info(
            "startup.api_limits",
            extra={
                "stage": "startup.api_limits",
                "extra_data": {
                    "max_upload_mb": upload.max_upload_mb,
                    "allowed_upload_dir": upload.allowed_upload_dir,
                    "rate_limit_ingest": get_rate_limit_ingest(),
                    "rate_limit_query": get_rate_limit_query(),
                },
            },
        )
        yield

    app = FastAPI(
        title=title,
        description="RAG system for financial PDF reports",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ─── Middleware stack ──────────────────────────────────────────────────
    # Registration order is INVERSE of runtime. LAST-added = OUTERMOST.
    # Required runtime order (outer → inner):
    #   RequestID  → SlowAPI  → MaxUploadSize  → APIKeyAuth → router
    #
    # So we register in REVERSE of that. RequestID must always be last so its
    # request_id is on request.state by the time any inner middleware (or the
    # rate-limit / 413 handlers) tries to read it.
    if _require_auth():
        app.add_middleware(APIKeyAuthMiddleware, api_keys=get_api_keys())
    app.add_middleware(
        MaxUploadSizeMiddleware,
        max_bytes=get_upload_settings().max_upload_bytes,
    )
    install_rate_limiter(app)
    app.add_middleware(RequestIDMiddleware)

    register_exception_handlers(app)

    for router in routers:
        app.include_router(router)

    return app
