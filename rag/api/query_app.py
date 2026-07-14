"""Query service entry point — the lean image's app.

Serves only the read-side routes. It never imports the ingestion router or the
job runner, so the Docling parsing stack stays out of this process (and image).
Launched by `chapter_4/l2/Dockerfile_Query`.
"""

from rag.api.app_factory import create_app
from rag.api.routes import health, query

app = create_app(
    title="RAG Query Service",
    routers=[health.router, query.router],
    eager_job_registry=False,
)
