"""The `/health` route, shared by every app.

Kept in its own router so both the query and ingestion services expose an
identical readiness probe without pulling in each other's routes.
"""

from fastapi import APIRouter

from rag.api.dependencies import get_store
from rag.api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    try:
        store = get_store()
        doc_count = store.count()
        chromadb_status = "connected"
    except Exception:
        chromadb_status = "disconnected"
        doc_count = 0

    health_status = "healthy" if chromadb_status == "connected" else "degraded"
    return HealthResponse(
        status=health_status,
        chromadb=chromadb_status,
        documents=doc_count,
    )
