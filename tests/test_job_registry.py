"""Unit and thread-safety tests for JobRegistry.

Run inside the dev container:
    pytest tests/test_job_registry.py -v

No app, no HTTP. Tests construct local JobRegistry instances directly.
The autouse conftest fixtures (reset_rate_limiter, fresh_job_registry) are
harmless here — they touch the singleton objects, not the local registries
these tests create.
"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import pytest

from rag.api.jobs.models import JobProgress, JobRecord, JobStatus
from rag.api.jobs.registry import (
    DEFAULT_REGISTRY_SIZE,
    ENV_REGISTRY_SIZE,
    JobNotFoundError,
    JobRegistry,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _create(reg: JobRegistry, **over) -> JobRecord:
    """Create a record with sensible defaults; override via kwargs."""
    kw = dict(
        request_id="r1",
        source_dir="pdf/",
        chunking_method="recursive",
        chunk_size=1000,
        chunk_overlap=200,
        keep_tables_intact=True,
    )
    kw.update(over)
    return reg.create(**kw)


# ── unit tests ───────────────────────────────────────────────────────────────

class TestJobRegistryUnit:

    def test_create_returns_pending(self):
        reg = JobRegistry(max_size=10)
        record = _create(reg)
        assert record.status == JobStatus.PENDING
        assert record.started_at is None

    def test_create_stamps_created_at(self):
        reg = JobRegistry(max_size=10)
        record = _create(reg)
        assert record.created_at is not None
        assert isinstance(record.created_at, datetime)
        # Must be timezone-aware (UTC).
        assert record.created_at.tzinfo is not None

    def test_get_unknown_returns_none(self):
        reg = JobRegistry(max_size=10)
        assert reg.get("nope") is None

    def test_update_running_stamps_started_at(self):
        reg = JobRegistry(max_size=10)
        record = _create(reg)
        updated = reg.update_status(record.job_id, JobStatus.RUNNING)
        assert updated.status == JobStatus.RUNNING
        assert updated.started_at is not None

    def test_second_running_does_not_restamp_started_at(self):
        """A second RUNNING update must not overwrite the original started_at."""
        reg = JobRegistry(max_size=10)
        record = _create(reg)
        first = reg.update_status(record.job_id, JobStatus.RUNNING)
        original_started = first.started_at
        second = reg.update_status(record.job_id, JobStatus.RUNNING)
        assert second.started_at == original_started

    def test_completed_stamps_finished_at(self):
        reg = JobRegistry(max_size=10)
        record = _create(reg)
        reg.update_status(record.job_id, JobStatus.RUNNING)
        done = reg.update_status(record.job_id, JobStatus.COMPLETED)
        assert done.status == JobStatus.COMPLETED
        assert done.finished_at is not None

    def test_failed_stamps_finished_at(self):
        reg = JobRegistry(max_size=10)
        record = _create(reg)
        reg.update_status(record.job_id, JobStatus.RUNNING)
        failed = reg.update_status(record.job_id, JobStatus.FAILED,
                                   error_message="oops")
        assert failed.status == JobStatus.FAILED
        assert failed.finished_at is not None

    def test_update_unknown_raises(self):
        reg = JobRegistry(max_size=10)
        with pytest.raises(JobNotFoundError):
            reg.update_status("missing-id", JobStatus.RUNNING)

    def test_explicit_started_at_wins(self):
        """Caller-supplied started_at overrides the auto-stamp."""
        reg = JobRegistry(max_size=10)
        record = _create(reg)
        fixed_dt = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        updated = reg.update_status(record.job_id, JobStatus.RUNNING,
                                    started_at=fixed_dt)
        assert updated.started_at == fixed_dt

    def test_evicts_oldest_when_full(self):
        """When capacity is exceeded, the oldest record is evicted (FIFO)."""
        reg = JobRegistry(max_size=3)
        first = _create(reg)
        _create(reg)
        _create(reg)
        # Registry is full (3). Adding a 4th evicts the first.
        _create(reg)
        assert len(reg) == 3
        assert reg.get(first.job_id) is None, "Oldest record should have been evicted"

    def test_list_newest_first(self):
        """list() returns jobs in newest-first order."""
        reg = JobRegistry(max_size=10)
        a = _create(reg)
        b = _create(reg)
        c = _create(reg)
        listed = reg.list()
        assert len(listed) == 3
        assert listed[0].job_id == c.job_id
        assert listed[1].job_id == b.job_id
        assert listed[2].job_id == a.job_id

    def test_list_respects_limit(self):
        """list(limit=2) returns only the 2 most recent."""
        reg = JobRegistry(max_size=10)
        _create(reg)
        b = _create(reg)
        c = _create(reg)
        listed = reg.list(limit=2)
        assert len(listed) == 2
        assert listed[0].job_id == c.job_id
        assert listed[1].job_id == b.job_id

    def test_list_limit_zero_empty(self):
        """list(limit=0) returns an empty list."""
        reg = JobRegistry(max_size=10)
        _create(reg)
        assert reg.list(limit=0) == []

    def test_from_env_default(self, monkeypatch):
        """from_env() with no env var uses DEFAULT_REGISTRY_SIZE."""
        monkeypatch.delenv(ENV_REGISTRY_SIZE, raising=False)
        reg = JobRegistry.from_env()
        assert reg._max_size == DEFAULT_REGISTRY_SIZE

    def test_from_env_parses_int(self, monkeypatch):
        """from_env() with RAG_API_JOB_REGISTRY_SIZE=42 uses 42."""
        monkeypatch.setenv(ENV_REGISTRY_SIZE, "42")
        reg = JobRegistry.from_env()
        assert reg._max_size == 42

    def test_from_env_rejects_non_int(self, monkeypatch):
        """from_env() with a non-integer env var raises RuntimeError."""
        monkeypatch.setenv(ENV_REGISTRY_SIZE, "abc")
        with pytest.raises(RuntimeError):
            JobRegistry.from_env()

    def test_init_rejects_zero_max_size(self):
        """JobRegistry(max_size=0) raises ValueError."""
        with pytest.raises(ValueError):
            JobRegistry(max_size=0)


# ── concurrency tests ─────────────────────────────────────────────────────────

class TestJobRegistryConcurrency:
    """Thread-safety smoke tests for the RLock-based JobRegistry."""

    def test_concurrent_creates_no_lost_records(self):
        """50 threads × 20 creates = 1000 total; all must be present
        (registry is large enough to avoid eviction)."""
        reg = JobRegistry(max_size=10_000)
        results: list[str] = []

        def _worker():
            ids = []
            for _ in range(20):
                r = _create(reg)
                ids.append(r.job_id)
            return ids

        with ThreadPoolExecutor(max_workers=50) as ex:
            futures = [ex.submit(_worker) for _ in range(50)]
            for fut in as_completed(futures):
                ids = fut.result()  # propagates any thread exception
                results.extend(ids)

        assert len(results) == 1000, f"Expected 1000 job_ids, got {len(results)}"
        assert len(set(results)) == 1000, "All job_ids must be unique"
        assert len(reg) == 1000

    def test_concurrent_create_and_evict_consistent_len(self):
        """500 concurrent creates against a registry capped at 50;
        final length must be exactly 50 (no overflow or underflow)."""
        reg = JobRegistry(max_size=50)

        def _worker():
            for _ in range(10):
                _create(reg)

        with ThreadPoolExecutor(max_workers=50) as ex:
            futures = [ex.submit(_worker) for _ in range(50)]
            for fut in as_completed(futures):
                fut.result()

        assert len(reg) == 50

    def test_concurrent_update_reads_never_torn(self):
        """One writer doing 500 RUNNING updates, one reader doing 500 gets;
        every read must return a valid JobRecord with non-negative numeric
        fields (no torn write)."""
        reg = JobRegistry(max_size=100)
        record = _create(reg)
        job_id = record.job_id
        errors: list[str] = []

        def _writer():
            for i in range(500):
                try:
                    reg.update_status(
                        job_id,
                        JobStatus.RUNNING,
                        total_chunks=i,
                        progress=JobProgress(
                            chunks_done=i,
                            chunks_total=500,
                            current_file="test.pdf",
                        ),
                    )
                except JobNotFoundError:
                    errors.append(f"writer: JobNotFoundError at i={i}")
                except Exception as exc:
                    errors.append(f"writer: {type(exc).__name__}: {exc}")

        def _reader():
            for _ in range(500):
                try:
                    r = reg.get(job_id)
                    if r is None:
                        errors.append("reader: got None for known job")
                        continue
                    # Check no torn fields.
                    assert isinstance(r, JobRecord)
                    assert r.total_chunks >= 0
                    if r.progress is not None:
                        assert r.progress.chunks_done >= 0
                        assert r.progress.chunks_total >= 0
                except AssertionError as exc:
                    errors.append(f"reader assertion: {exc}")
                except Exception as exc:
                    errors.append(f"reader: {type(exc).__name__}: {exc}")

        with ThreadPoolExecutor(max_workers=2) as ex:
            fw = ex.submit(_writer)
            fr = ex.submit(_reader)
            fw.result()
            fr.result()

        assert not errors, f"Thread errors detected:\n" + "\n".join(errors)
