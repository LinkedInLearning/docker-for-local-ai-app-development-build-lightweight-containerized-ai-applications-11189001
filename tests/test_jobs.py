"""Tests for POST /ingest (202 contract) and GET /ingest/jobs/* polling endpoints.

Run inside the dev container:
    pytest tests/test_jobs.py -v

Key design notes
----------------
Background tasks under Starlette TestClient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Starlette's TestClient executes BackgroundTasks **synchronously**, after the
response is produced but before ``client.post(...)`` returns. Therefore, by the
time a test calls ``GET /ingest/jobs/{job_id}`` immediately after a
``POST /ingest``, the runner has **already finished** (completed or failed) —
no polling loop is needed.

This relies on the ``runner_stub`` fixture patching the four heavy callables
imported into ``rag.api.jobs.runner`` at module top:
  - ``parse_pdf``, ``chunk_elements``  (from rag.ingestion.*)
  - ``get_store``, ``get_embedder_instance``  (from rag.api.dependencies)

Patch targets are in ``rag.api.jobs.runner`` (the import namespace), not the
source modules.

Rate-limit interaction
~~~~~~~~~~~~~~~~~~~~~~
The compiled limit is ``5/minute`` (set in conftest before the first import).
Each test gets a clean limiter via the autouse ``reset_rate_limiter`` fixture.
Tests that submit jobs use at most 3 ``/ingest`` calls — well under the limit.

Registry isolation
~~~~~~~~~~~~~~~~~~
The autouse ``fresh_job_registry`` fixture clears the lru_cache before and
after each test, so GET /ingest/jobs listings never see jobs from other tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


class TestIngestSubmission:
    """202 response contract for POST /ingest."""

    def test_post_ingest_returns_202(self, client, runner_stub):
        """POST /ingest with a valid pdf/ source returns 202 with the job envelope."""
        response = client.post("/ingest", json={"source_dir": "pdf/"})
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert "request_id" in data and data["request_id"]
        assert "poll_url" in data
        # The 202 body is snapshotted at create time (before background runs).
        assert data["status"] == "pending"

    def test_post_ingest_location_header(self, client, runner_stub):
        """Location header on 202 matches poll_url in body."""
        response = client.post("/ingest", json={"source_dir": "pdf/"})
        assert response.status_code == 202
        data = response.json()
        assert response.headers["Location"] == data["poll_url"]
        assert data["poll_url"] == f"/ingest/jobs/{data['job_id']}"

    def test_post_ingest_echoes_request_id(self, client, runner_stub):
        """X-Request-ID response header matches body's request_id."""
        response = client.post("/ingest", json={"source_dir": "pdf/"})
        assert response.status_code == 202
        data = response.json()
        assert response.headers["X-Request-ID"] == data["request_id"]

    def test_post_ingest_request_id_honored(self, client, runner_stub):
        """A client-supplied X-Request-ID is reflected in body and header."""
        response = client.post(
            "/ingest",
            json={"source_dir": "pdf/"},
            headers={"X-Request-ID": "my-trace"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["request_id"] == "my-trace"
        assert response.headers["X-Request-ID"] == "my-trace"


class TestJobPolling:
    """GET /ingest/jobs/{job_id}: terminal state, failed path, unknown-id."""

    def test_job_reaches_completed(self, client, runner_stub):
        """After POST /ingest (runner stubbed), immediately GET the job -> completed."""
        post_resp = client.post("/ingest", json={"source_dir": "pdf/"})
        assert post_resp.status_code == 202
        job_id = post_resp.json()["job_id"]

        get_resp = client.get(f"/ingest/jobs/{job_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["status"] == "completed"
        assert data["documents_processed"] >= 1

    def test_completed_job_has_result(self, client, runner_stub):
        """Completed job has a result block with documents_ingested >= 1."""
        post_resp = client.post("/ingest", json={"source_dir": "pdf/"})
        job_id = post_resp.json()["job_id"]

        get_resp = client.get(f"/ingest/jobs/{job_id}")
        data = get_resp.json()
        assert data["status"] == "completed"
        result = data.get("result")
        assert result is not None, "Completed job must have a 'result' field"
        assert result["documents_ingested"] >= 1
        assert result["status"] == "success"
        assert len(result["files"]) >= 1

    def test_job_failed_path(self, client, monkeypatch):
        """When parse_pdf raises, the job reaches 'failed' status."""
        monkeypatch.setattr(
            "rag.api.jobs.runner.parse_pdf",
            MagicMock(side_effect=ValueError("boom")),
        )
        # Stub the other heavy deps so the runner can at least start.
        monkeypatch.setattr("rag.api.jobs.runner.chunk_elements",
                            lambda *a, **k: ["chunk"])
        monkeypatch.setattr("rag.api.jobs.runner.get_store",
                            lambda: MagicMock())
        monkeypatch.setattr("rag.api.jobs.runner.get_embedder_instance",
                            lambda: MagicMock())

        post_resp = client.post("/ingest", json={"source_dir": "pdf/"})
        assert post_resp.status_code == 202
        job_id = post_resp.json()["job_id"]

        get_resp = client.get(f"/ingest/jobs/{job_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["status"] == "failed"
        assert data["error_message"] is not None

    def test_failed_error_message_sanitized(self, client, monkeypatch):
        """Failed job error_message omits the raw exception message but includes
        the exception class name and the PDF filename."""
        monkeypatch.setattr(
            "rag.api.jobs.runner.parse_pdf",
            MagicMock(side_effect=ValueError("boom")),
        )
        monkeypatch.setattr("rag.api.jobs.runner.chunk_elements",
                            lambda *a, **k: ["chunk"])
        monkeypatch.setattr("rag.api.jobs.runner.get_store",
                            lambda: MagicMock())
        monkeypatch.setattr("rag.api.jobs.runner.get_embedder_instance",
                            lambda: MagicMock())

        post_resp = client.post("/ingest", json={"source_dir": "pdf/"})
        job_id = post_resp.json()["job_id"]
        data = client.get(f"/ingest/jobs/{job_id}").json()

        msg = data.get("error_message", "")
        # Raw exception text must NOT appear.
        assert "boom" not in msg
        # Exception class name and a .pdf filename MUST appear.
        assert "ValueError" in msg
        assert ".pdf" in msg

    def test_unknown_job_404(self, client):
        """GET /ingest/jobs/<unknown> returns 404."""
        response = client.get("/ingest/jobs/does-not-exist")
        assert response.status_code == 404

    def test_unknown_job_404_envelope(self, client):
        """404 body for an unknown job has {request_id, error} with the
        restart hint in the error message."""
        response = client.get("/ingest/jobs/does-not-exist")
        assert response.status_code == 404
        data = response.json()
        assert set(data.keys()) == {"request_id", "error"}
        assert "not persisted" in data["error"] or "not found" in data["error"].lower()


class TestJobListing:
    """GET /ingest/jobs: ordering, limit, and invalid-limit handling."""

    def test_list_newest_first(self, client, runner_stub):
        """Submit 3 jobs; list returns newest first (last submitted is result[0])."""
        ids = []
        for _ in range(3):
            resp = client.post("/ingest", json={"source_dir": "pdf/"})
            assert resp.status_code == 202
            ids.append(resp.json()["job_id"])

        list_resp = client.get("/ingest/jobs")
        assert list_resp.status_code == 200
        listed = list_resp.json()
        assert len(listed) == 3
        # Newest-first: the last submitted job_id is first in the list.
        assert listed[0]["job_id"] == ids[-1]

    def test_list_respects_limit(self, client, runner_stub):
        """?limit=1 returns only 1 job even when 3 exist."""
        for _ in range(3):
            client.post("/ingest", json={"source_dir": "pdf/"})

        list_resp = client.get("/ingest/jobs?limit=1")
        assert list_resp.status_code == 200
        listed = list_resp.json()
        assert len(listed) == 1

    def test_list_invalid_limit_400(self, client):
        """?limit=0 and ?limit=501 both return 400."""
        for bad in ("0", "501"):
            resp = client.get(f"/ingest/jobs?limit={bad}")
            assert resp.status_code == 400, (
                f"Expected 400 for limit={bad}, got {resp.status_code}"
            )
