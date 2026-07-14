"""Ingestion-side routes — the write half of the API.

Served by the heavy ingestion image. Importing this module pulls in the job
runner and, through it, the Docling parsing stack — which is exactly why the
query app must not import it.
"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
    Response,
    status,
)

from rag.api.dependencies import get_job_registry, get_store, get_upload_settings
from rag.api.jobs import IngestJobResponse, JobRecord, run_ingestion_job
from rag.api.models import IngestRequest, SanitizedErrorResponse
from rag.api.rate_limit import get_rate_limit_ingest, limiter
from rag.api.security import PathNotAllowedError, resolve_under

router = APIRouter()


@router.post(
    "/ingest",
    response_model=IngestJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        403: {
            "model": SanitizedErrorResponse,
            "description": "source_dir outside RAG_API_ALLOWED_UPLOAD_DIR",
        },
        404: {
            "model": SanitizedErrorResponse,
            "description": "source_dir not found or contains no PDFs",
        },
        411: {
            "model": SanitizedErrorResponse,
            "description": "Content-Length header required",
        },
        413: {
            "model": SanitizedErrorResponse,
            "description": "Payload exceeds RAG_API_MAX_UPLOAD_MB",
        },
        429: {
            "model": SanitizedErrorResponse,
            "description": "Rate limit exceeded",
        },
    },
)
@limiter.limit(get_rate_limit_ingest())
def ingest_documents(
    request: Request,
    body: IngestRequest,
    background_tasks: BackgroundTasks,
    response: Response,
) -> IngestJobResponse:
    """Submit an ingestion job. Returns 202 immediately; the actual
    parse/chunk/embed work runs in a BackgroundTasks worker. Poll
    GET /ingest/jobs/{job_id} for status."""
    request_id: str = request.state.request_id
    upload = get_upload_settings()

    try:
        source_dir = resolve_under(
            body.source_dir,
            upload.allowed_upload_dir,
            must_exist=True,
        )
    except PathNotAllowedError as exc:
        if exc.reason == "candidate_missing":
            raise HTTPException(
                status_code=404,
                detail=f"Source directory not found: {body.source_dir}",
            )
        raise HTTPException(
            status_code=403,
            detail=(
                f"Source directory not allowed: {body.source_dir} "
                f"(must resolve under {upload.allowed_upload_dir})"
            ),
        )

    pdf_files = list(source_dir.glob("*.pdf"))
    if not pdf_files:
        raise HTTPException(
            status_code=404,
            detail=f"No PDF files found in: {source_dir}",
        )

    registry = get_job_registry()
    record = registry.create(
        request_id=request_id,
        source_dir=body.source_dir,
        chunking_method=body.chunking_method,
        chunk_size=body.chunk_size,
        chunk_overlap=body.chunk_overlap,
        keep_tables_intact=body.keep_tables_intact,
    )

    background_tasks.add_task(
        run_ingestion_job,
        record.job_id,
        body,
        request_id,
    )

    poll_url = f"/ingest/jobs/{record.job_id}"
    response.headers["Location"] = poll_url

    return IngestJobResponse(
        job_id=record.job_id,
        request_id=request_id,
        status=record.status,
        poll_url=poll_url,
    )


@router.get(
    "/ingest/jobs/{job_id}",
    response_model=JobRecord,
    responses={
        404: {
            "model": SanitizedErrorResponse,
            "description": (
                "Unknown job_id (note: jobs are not persisted across "
                "process restarts in v1)"
            ),
        },
    },
)
def get_ingest_job(job_id: str) -> JobRecord:
    """Return the current state of an ingestion job."""
    registry = get_job_registry()
    record = registry.get(job_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Job not found: {job_id}. "
                f"Note: jobs are not persisted across API process "
                f"restarts in v1."
            ),
        )
    return record


@router.get("/ingest/jobs", response_model=list[JobRecord])
def list_ingest_jobs(limit: int = 50) -> list[JobRecord]:
    """List up to `limit` most recent ingestion jobs, newest first.
    Auth-gated (the middleware already enforces this). Intended for
    debugging — not a stable contract."""
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 500",
        )
    registry = get_job_registry()
    return registry.list(limit=limit)


@router.delete("/documents/{source_file}")
def delete_document(source_file: str):
    store = get_store()
    results = store.collection.get(
        where={"source_file": source_file}
    )
    if not results["ids"]:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {source_file}",
        )
    store.delete_by_source(source_file)
    return {"status": "deleted", "file": source_file}
