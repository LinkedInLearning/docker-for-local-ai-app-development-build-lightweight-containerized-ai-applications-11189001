from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Lifecycle states for an ingestion job. String enum so it serializes
    to a plain JSON string."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobProgress(BaseModel):
    """Per-file embedding progress. Updated by the progress_callback hook
    inside ChromaStore.ingest_chunks. None until the runner reaches the
    embed/store stage of the first file."""

    chunks_done: int = Field(ge=0)
    chunks_total: int = Field(ge=0)
    current_file: str | None = None


class JobResult(BaseModel):
    """Final aggregate output. Populated only when status == COMPLETED.
    Shape intentionally mirrors the old (Phase 1) IngestResponse so
    clients that already consumed that body need only adapt to the new
    poll-based flow, not to a new field schema."""

    status: str = "success"
    documents_ingested: int = Field(ge=0)
    total_chunks: int = Field(ge=0)
    files: list[str] = Field(default_factory=list)


class JobRecord(BaseModel):
    """The full server-side state for one ingestion job. This IS the
    response model for GET /ingest/jobs/{job_id}.

    Field-level concurrency note: every mutation goes through
    JobRegistry.update_status() under an RLock. Callers MUST NOT mutate
    a JobRecord instance returned by registry.get() — treat as
    read-only; the registry hands out the live object but the caller
    should copy if it needs a stable snapshot.
    """

    # Identity
    job_id: str
    status: JobStatus = JobStatus.PENDING
    request_id: str = Field(
        description=(
            "Correlation ID of the POST /ingest call that created this job. "
            "Matches the X-Request-ID header on the 202 response."
        )
    )

    # Inputs (echoed for diagnostics)
    source_dir: str
    chunking_method: str
    chunk_size: int
    chunk_overlap: int
    keep_tables_intact: bool

    # Lifecycle timestamps (UTC, ISO-8601 via Pydantic default)
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    # Progress (updated as embedding batches complete)
    documents_processed: int = 0
    total_chunks: int = 0
    files_ingested: list[str] = Field(default_factory=list)
    progress: JobProgress | None = None

    # Terminal-state fields
    result: JobResult | None = None
    error_message: str | None = Field(
        default=None,
        description=(
            "Sanitized human-readable failure reason. Full traceback is in "
            "server logs under error_request_id."
        ),
    )
    error_request_id: str | None = Field(
        default=None,
        description=(
            "The request_id used in the structured log entry for the failure. "
            "Equal to `request_id` in nearly all cases; surfaced separately so "
            "future implementations (retries, fan-out) can attach a different "
            "log correlation token."
        ),
    )


class IngestJobResponse(BaseModel):
    """Response body for POST /ingest. Returned with status 202.
    Replaces the prior synchronous IngestResponse on this endpoint.

    IngestResponse is NOT deleted: its shape is now reused INSIDE
    JobResult so polling clients see the same field names they
    previously saw on the synchronous 200 response.
    """

    job_id: str
    request_id: str
    status: JobStatus = JobStatus.PENDING
    poll_url: str = Field(
        description=(
            "Relative URL the client should poll for status. "
            "Always /ingest/jobs/{job_id}. Echoed in the "
            "Location header of the 202 response."
        )
    )
