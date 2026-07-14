"""Combined API entry point — all routes in one process.

Kept for local development and the single-container dev image
(`docker/Dockerfile_API`): it mounts every router, so `main:app` behaves like
the pre-split monolith. The production split images use `query_app` and
`ingestion_app` instead. All three assemble from the same routers via
`create_app`, so route behavior stays identical across them.
"""

from rag.api.app_factory import create_app
from rag.api.routes import health, ingestion, query

app = create_app(
    title="RAG Docker API",
    routers=[health.router, ingestion.router, query.router],
    eager_job_registry=True,
)
