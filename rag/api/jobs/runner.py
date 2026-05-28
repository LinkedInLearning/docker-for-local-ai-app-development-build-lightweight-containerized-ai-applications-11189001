from __future__ import annotations

from pathlib import Path

from rag.api.dependencies import get_embedder_instance, get_store
from rag.api.jobs.models import JobProgress, JobRecord, JobResult, JobStatus
from rag.api.jobs.registry import JobNotFoundError, JobRegistry
from rag.api.models import IngestRequest
from rag.ingestion.chunker import chunk_elements
from rag.ingestion.pdf_parser import parse_pdf
from rag.observability.logging import get_logger

logger = get_logger()


def run_ingestion_job(
    job_id: str,
    request_body: IngestRequest,
    request_id: str,
    *,
    registry: JobRegistry | None = None,
) -> None:
    """Execute the full ingestion pipeline for `job_id` in the
    BackgroundTasks worker thread. NEVER raises — every exception is
    caught, logged with the supplied request_id for log correlation,
    and the JobRecord is marked FAILED.

    Args:
        job_id: ID of an already-created PENDING JobRecord in the
            registry.
        request_body: The original POST /ingest body, echoed for
            chunking parameters.
        request_id: The inbound HTTP request's correlation ID
            (request.state.request_id). Phase 1 contract §8.1: the
            ContextVar may NOT propagate into BackgroundTasks, so
            this is passed EXPLICITLY and threaded into every log
            call as extra={"trace_id": request_id, ...}.
        registry: Optional registry override for tests. Defaults
            to the lru_cache singleton from get_job_registry().

    Side effects:
        - Mutates the JobRecord via registry.update_status() at four
          checkpoints: RUNNING (start), per-file progress updates,
          COMPLETED, FAILED.
        - Calls ChromaStore.ingest_chunks() which upserts to the
          live ChromaDB collection.
        - Emits structured log lines under `request_id` at INFO and
          ERROR levels.
    """
    if registry is None:
        from rag.api.dependencies import get_job_registry
        registry = get_job_registry()

    try:
        try:
            registry.update_status(job_id, JobStatus.RUNNING)
        except JobNotFoundError:
            logger.warning(
                "ingest.job.evicted_before_start",
                extra={
                    "trace_id": request_id,
                    "stage": "ingest.job.evicted_before_start",
                    "extra_data": {"job_id": job_id},
                },
            )
            return

        logger.info(
            "ingest.job.started",
            extra={
                "trace_id": request_id,
                "stage": "ingest.job.started",
                "extra_data": {
                    "job_id": job_id,
                    "source_dir": request_body.source_dir,
                },
            },
        )

        source_dir = Path(request_body.source_dir).resolve()

        pdf_files = sorted(source_dir.glob("*.pdf"))
        if not pdf_files:
            registry.update_status(
                job_id,
                JobStatus.FAILED,
                error_message="No PDF files found in source_dir",
                error_request_id=request_id,
            )
            return

        store = get_store()
        embedder = get_embedder_instance()
        total_chunks = 0
        ingested_files: list[str] = []

        for pdf_path in pdf_files:
            try:
                elements = parse_pdf(pdf_path)
                chunks = chunk_elements(
                    elements,
                    method=request_body.chunking_method,
                    chunk_size=request_body.chunk_size,
                    chunk_overlap=request_body.chunk_overlap,
                    keep_tables_intact=request_body.keep_tables_intact,
                )

                def _on_progress(
                    done: int, total: int, _pdf: str = pdf_path.name
                ) -> None:
                    try:
                        registry.update_status(
                            job_id,
                            JobStatus.RUNNING,
                            progress=JobProgress(
                                chunks_done=done,
                                chunks_total=total,
                                current_file=_pdf,
                            ),
                        )
                    except JobNotFoundError:
                        return  # job was evicted mid-run; nothing to update

                count = store.ingest_chunks(
                    chunks,
                    embedder,
                    source_file=pdf_path.name,
                    progress_callback=_on_progress,
                )
                total_chunks += count
                ingested_files.append(pdf_path.name)

                registry.update_status(
                    job_id,
                    JobStatus.RUNNING,
                    documents_processed=len(ingested_files),
                    total_chunks=total_chunks,
                    files_ingested=list(ingested_files),
                )

            except Exception as exc:
                logger.error(
                    "ingest.job.file_failed",
                    exc_info=exc,
                    extra={
                        "trace_id": request_id,
                        "stage": "ingest.job.file_failed",
                        "extra_data": {
                            "job_id": job_id,
                            "pdf": pdf_path.name,
                        },
                    },
                )
                registry.update_status(
                    job_id,
                    JobStatus.FAILED,
                    error_message=(
                        f"Failed processing {pdf_path.name}: "
                        f"{type(exc).__name__}"
                    ),
                    error_request_id=request_id,
                )
                return

        result = JobResult(
            status="success",
            documents_ingested=len(ingested_files),
            total_chunks=total_chunks,
            files=ingested_files,
        )
        registry.update_status(
            job_id,
            JobStatus.COMPLETED,
            result=result,
            documents_processed=len(ingested_files),
            total_chunks=total_chunks,
            files_ingested=ingested_files,
            progress=None,
        )
        logger.info(
            "ingest.job.completed",
            extra={
                "trace_id": request_id,
                "stage": "ingest.job.completed",
                "extra_data": {
                    "job_id": job_id,
                    "documents_ingested": len(ingested_files),
                    "total_chunks": total_chunks,
                },
            },
        )

    except Exception as exc:
        logger.error(
            "ingest.job.failed",
            exc_info=exc,
            extra={
                "trace_id": request_id,
                "stage": "ingest.job.failed",
                "extra_data": {"job_id": job_id},
            },
        )
        try:
            registry.update_status(
                job_id,
                JobStatus.FAILED,
                error_message=f"Ingestion failed: {type(exc).__name__}",
                error_request_id=request_id,
            )
        except JobNotFoundError:
            pass
