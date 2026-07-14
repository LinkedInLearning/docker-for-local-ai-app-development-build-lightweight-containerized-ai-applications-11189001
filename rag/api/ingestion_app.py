"""Ingestion service entry point — the heavy image's app.

Serves only the write-side routes (ingest + jobs, document delete). Importing
the ingestion router pulls in the Docling parsing stack, which is expected
here. Launched by `chapter_4/l2/Dockerfile_Ingestion`.
"""

from rag.api.app_factory import create_app
from rag.api.routes import health, ingestion

app = create_app(
    title="RAG Ingestion Service",
    routers=[health.router, ingestion.router],
    eager_job_registry=True,
)
