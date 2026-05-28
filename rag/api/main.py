import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response, status

from rag.api.dependencies import (
    get_api_keys,
    get_config,
    get_job_registry,
    get_store,
)
from rag.api.jobs import (
    IngestJobResponse,
    JobRecord,
    JobStatus,
    run_ingestion_job,
)
from rag.api.middleware import (
    APIKeyAuthMiddleware,
    RequestIDMiddleware,
    register_exception_handlers,
)
from rag.api.models import (
    ConfigResponse,
    DocumentInfo,
    HealthResponse,
    IngestRequest,
    QueryRequest,
    QueryResponse,
    QueryMetadataResponse,
    SanitizedErrorResponse,
    SourceResponse,
)
from rag.observability.logging import setup_logging
from rag.observability.tracing import configure_tracing
from rag.retrieval.chain import query_rag


def _require_auth() -> bool:
    """`RAG_API_REQUIRE_AUTH=false` (case-insensitive) disables auth.
    Any other value (including unset) leaves auth ENABLED.
    """
    return os.environ.get("RAG_API_REQUIRE_AUTH", "true").lower() != "false"


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

    # Eagerly instantiate the JobRegistry so RAG_API_JOB_REGISTRY_SIZE
    # parse errors fail at startup, not on the first ingest call.
    get_job_registry()

    yield


app = FastAPI(
    title="RAG Docker API",
    description="RAG system for financial PDF reports",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware stack — registration order is INVERSE of runtime.
# Last-added is OUTERMOST. RequestID must be outermost so all
# responses (including 401 from auth) get a request_id header.
if _require_auth():
    app.add_middleware(APIKeyAuthMiddleware, api_keys=get_api_keys())
app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)


@app.get("/health", response_model=HealthResponse)
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


@app.post(
    "/ingest",
    response_model=IngestJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {
            "model": SanitizedErrorResponse,
            "description": "source_dir not found or contains no PDFs",
        },
        403: {
            "model": SanitizedErrorResponse,
            "description": "source_dir outside allowed root",
        },
    },
)
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

    source_dir = Path(body.source_dir).resolve()

    allowed_base = Path.cwd().resolve()
    try:
        source_dir.relative_to(allowed_base)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Source directory must be within the project",
        )

    if not source_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Source directory not found: {source_dir}",
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


@app.get(
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


@app.get("/ingest/jobs", response_model=list[JobRecord])
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


@app.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    config = get_config()

    try:
        response = query_rag(
            question=request.question,
            config=config,
            top_k=request.top_k,
            rerank_method=request.rerank_method,
            chat_provider=request.chat_provider,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}",
        )

    sources = [
        SourceResponse(
            file=s.file,
            page=s.page,
            section=s.section,
            excerpt=s.excerpt,
        )
        for s in response.sources
    ]

    metadata = None
    if response.metadata:
        metadata = QueryMetadataResponse(
            provider=response.metadata.provider,
            model=response.metadata.model,
            retrieval_count=response.metadata.retrieval_count,
            latency_ms=response.metadata.latency_ms,
        )

    return QueryResponse(
        answer=response.answer,
        sources=sources,
        metadata=metadata,
    )


@app.get("/documents", response_model=list[DocumentInfo])
def list_documents():
    store = get_store()
    docs = store.list_documents()
    return [DocumentInfo(**doc) for doc in docs]


@app.delete("/documents/{source_file}")
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


@app.get("/config", response_model=ConfigResponse)
def get_configuration():
    config = get_config()
    return ConfigResponse(
        active_embedding_provider=config.active.embedding_provider,
        active_chat_provider=config.active.chat_provider,
        chunking_method=config.chunking.method,
        chunk_size=config.chunking.chunk_size,
        retrieval_top_k=config.retrieval.top_k,
        rerank_enabled=config.retrieval.rerank,
        rerank_model=config.retrieval.rerank_model,
        chromadb_host=config.chromadb.host,
        chromadb_port=config.chromadb.port,
        collection_name=config.chromadb.collection_name,
        observability_enabled=config.observability.enabled,
    )
