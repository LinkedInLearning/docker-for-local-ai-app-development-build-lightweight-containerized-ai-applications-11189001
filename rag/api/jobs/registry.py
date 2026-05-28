from __future__ import annotations

import os
import threading
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

from rag.api.jobs.models import JobProgress, JobRecord, JobResult, JobStatus


DEFAULT_REGISTRY_SIZE: int = 500
ENV_REGISTRY_SIZE: str = "RAG_API_JOB_REGISTRY_SIZE"


class JobNotFoundError(KeyError):
    """Raised by JobRegistry.update_status() when the job_id is unknown.
    NOT raised by .get() — callers must check None and decide whether
    to 404 themselves (the registry doesn't know HTTP semantics)."""


class JobRegistry:
    """Bounded thread-safe in-memory registry of ingestion jobs.

    Concurrency model
    -----------------
    All access to the underlying OrderedDict goes through `self._lock`
    (a threading.RLock). The lock is held for the DURATION of each
    public method — there is no lock-free fast path. JobRecord
    instances returned by .get() are the LIVE objects, not copies; the
    registry trusts callers to treat them read-only. Mutations must
    go through .update_status().

    Eviction
    --------
    Insertion-ordered OrderedDict + popitem(last=False) gives FIFO
    eviction. When the registry hits `max_size`, the OLDEST job
    (by insertion order) is evicted regardless of status. Bounded
    growth is the whole point — there is no separate TTL/GC pass in
    v1.

    Process-lifetime caveat
    -----------------------
    All state is lost on uvicorn restart. Multi-worker deployments
    each have their own registry. Documented at the API surface
    (404 hint) and in README. See Phase 2 spec §11.
    """

    def __init__(self, *, max_size: int = DEFAULT_REGISTRY_SIZE) -> None:
        if max_size < 1:
            raise ValueError(f"max_size must be >= 1, got {max_size}")
        self._max_size: int = max_size
        self._jobs: OrderedDict[str, JobRecord] = OrderedDict()
        self._lock: threading.RLock = threading.RLock()

    @staticmethod
    def _new_job_id() -> str:
        """Stable opaque ID. 'j_' prefix + 12-char hex matches the
        request_id format from Phase 1."""
        return f"j_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def create(
        self,
        *,
        request_id: str,
        source_dir: str,
        chunking_method: str,
        chunk_size: int,
        chunk_overlap: int,
        keep_tables_intact: bool,
    ) -> JobRecord:
        """Create a new PENDING JobRecord, insert it, evict oldest if
        we're over capacity, and return the (live) record.

        Thread-safety: full method runs under RLock.
        """
        record = JobRecord(
            job_id=self._new_job_id(),
            status=JobStatus.PENDING,
            request_id=request_id,
            source_dir=source_dir,
            chunking_method=chunking_method,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            keep_tables_intact=keep_tables_intact,
            created_at=self._now(),
        )
        with self._lock:
            self._jobs[record.job_id] = record
            while len(self._jobs) > self._max_size:
                self._jobs.popitem(last=False)
        return record

    def get(self, job_id: str) -> JobRecord | None:
        """Return the (live) JobRecord or None if unknown.
        Treat the returned object as read-only."""
        with self._lock:
            return self._jobs.get(job_id)

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        **fields: Any,
    ) -> JobRecord:
        """Mutate the named job: set `status` and assign any extra
        fields by name. Returns the updated (live) record.

        Raises JobNotFoundError if job_id is unknown.

        Auto-stamps started_at when transitioning to RUNNING and
        finished_at when transitioning to COMPLETED or FAILED, unless
        the caller supplied those values explicitly.

        Thread-safety: full method runs under RLock. The model_copy
        + update pattern is intentional — we replace the record in
        the OrderedDict so any caller holding a prior reference sees
        the OLD snapshot (immutable from their view) rather than a
        torn write.
        """
        with self._lock:
            current = self._jobs.get(job_id)
            if current is None:
                raise JobNotFoundError(job_id)

            updates: dict[str, Any] = {"status": status, **fields}
            if (
                status == JobStatus.RUNNING
                and "started_at" not in updates
                and current.started_at is None
            ):
                updates["started_at"] = self._now()
            if (
                status in (JobStatus.COMPLETED, JobStatus.FAILED)
                and "finished_at" not in updates
            ):
                updates["finished_at"] = self._now()

            new_record = current.model_copy(update=updates)
            self._jobs[job_id] = new_record
            return new_record

    def list(self, *, limit: int = 50) -> list[JobRecord]:
        """Return up to `limit` most recent jobs, newest-first.
        Returns a shallow list of the live records (snapshot of the
        list order, not deep copy of each record). Auth-gated by the
        endpoint, intended for debugging."""
        if limit < 1:
            return []
        with self._lock:
            return list(reversed(list(self._jobs.values())))[:limit]

    def __len__(self) -> int:
        with self._lock:
            return len(self._jobs)

    @classmethod
    def from_env(cls) -> "JobRegistry":
        raw = os.environ.get(ENV_REGISTRY_SIZE, "").strip()
        if not raw:
            return cls(max_size=DEFAULT_REGISTRY_SIZE)
        try:
            size = int(raw)
        except ValueError:
            raise RuntimeError(
                f"{ENV_REGISTRY_SIZE} must be an integer >= 1, got {raw!r}"
            )
        return cls(max_size=size)
