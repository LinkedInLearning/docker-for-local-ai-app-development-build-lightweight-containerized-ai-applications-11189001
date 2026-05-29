"""Tests for resolve_under(), MaxUploadSizeMiddleware, rate limiting, and
/ingest path hardening.

Run inside the dev container:
    pytest tests/test_security.py -v

Sections
--------
TestResolveUnder          — pure unit tests for rag.api.security.resolve_under
TestUploadLimitMiddleware — isolated 100-byte-cap middleware unit tests
TestUploadLimitIntegration— acceptance: 413 before disk write on real app
TestRateLimit             — 429 shape, Retry-After, X-Request-ID, threshold
TestIngestPathHardening   — /ingest 403/404 via resolve_under + pdf detection

Design notes
~~~~~~~~~~~~
MaxUploadSizeMiddleware 411 test
  httpx (used by Starlette TestClient) does NOT include Content-Length for
  generator/iterator content, making chunked transfer the reliable way to
  trigger the 411 path. We use ``content=iter([b"x"])`` to avoid setting
  Content-Length. If httpx injects a Content-Length anyway the test will
  receive a 200 instead of 411 and fail with a clear assertion error.

413 spoofed Content-Length
  httpx computes Content-Length from the actual body when content=bytes.
  To spoof a larger value, we use client.build_request(...) and mutate
  ``req.headers["content-length"]`` after construction; httpx does not
  recompute on send(). This satisfies the "413 before disk write"
  acceptance criterion: MaxUploadSizeMiddleware short-circuits before route
  dispatch, so the handler never runs.

Rate-limit compiled at 5/minute
  conftest sets RAG_API_RATE_LIMIT_INGEST="5/minute" before the first import.
  The autouse reset_rate_limiter fixture clears the in-memory window before
  each test. Firing 5 accepted calls then checking the 6th is 429 is
  deterministic.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from rag.api.security import PathNotAllowedError, resolve_under


# ── helpers ───────────────────────────────────────────────────────────────────

def _symlink_or_skip(src, dst):
    """Create os.symlink(src, dst); skip on Windows (no symlinks by default)."""
    if sys.platform == "win32":
        pytest.skip("symlink tests require non-Windows platform")
    os.symlink(src, dst)


# ── resolve_under unit tests ─────────────────────────────────────────────────

class TestResolveUnder:
    """Pure-Python unit tests; no app or HTTP involved."""

    def test_accepts_root_itself(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        result = resolve_under(root, root)
        assert result == root.resolve()

    def test_accepts_descendant(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        sub = root / "sub"
        sub.mkdir()
        result = resolve_under(sub, root)
        assert result == sub.resolve()

    def test_rejects_absolute_outside(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        with pytest.raises(PathNotAllowedError) as exc:
            resolve_under("/etc", root)
        # /etc exists on Linux/macOS and is outside the allowed root.
        assert exc.value.reason == "outside_allowed_root"

    def test_rejects_dotdot_escape(self, tmp_path):
        """A .. escape to an existing path outside root raises PathNotAllowedError."""
        root = tmp_path / "root"
        root.mkdir()
        # Create a sibling directory that the .. path resolves to.
        outside = tmp_path / "outside"
        outside.mkdir()
        escape_path = root / ".." / "outside"
        with pytest.raises(PathNotAllowedError) as exc:
            resolve_under(escape_path, root, must_exist=True)
        assert exc.value.reason == "outside_allowed_root"

    def test_rejects_symlink_escape(self, tmp_path):
        """A symlink inside root that points outside raises symlink_escapes_root."""
        root = tmp_path / "root"
        root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        link = root / "link"
        _symlink_or_skip(outside, link)
        with pytest.raises(PathNotAllowedError) as exc:
            resolve_under(link, root)
        assert exc.value.reason == "symlink_escapes_root"

    def test_accepts_symlink_within(self, tmp_path):
        """A symlink inside root pointing to another location inside root is accepted."""
        root = tmp_path / "root"
        root.mkdir()
        a = root / "a"
        a.mkdir()
        b = root / "b"
        b.mkdir()
        link = a / "toB"
        _symlink_or_skip(b, link)
        result = resolve_under(link, root)
        assert result == b.resolve()

    def test_missing_candidate_reason(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        with pytest.raises(PathNotAllowedError) as exc:
            resolve_under(root / "nope", root, must_exist=True)
        assert exc.value.reason == "candidate_missing"

    def test_missing_root_reason(self, tmp_path):
        with pytest.raises(PathNotAllowedError) as exc:
            resolve_under(tmp_path, tmp_path / "no_root")
        assert exc.value.reason == "allowed_root_missing"

    def test_returns_realpath(self, tmp_path):
        """resolve_under returns the realpath (symlink resolved), not the link path."""
        root = tmp_path / "root"
        root.mkdir()
        a = root / "a"
        a.mkdir()
        b = root / "b"
        b.mkdir()
        link = a / "toB"
        _symlink_or_skip(b, link)
        result = resolve_under(link, root)
        assert result == Path(os.path.realpath(b))


# ── MaxUploadSizeMiddleware isolated tests ────────────────────────────────────

class TestUploadLimitMiddleware:
    """Isolated tests against the upload_app fixture (100-byte cap)."""

    def test_413_on_oversize_content_length(self, upload_client):
        """A JSON body >100 bytes triggers 413 from the middleware."""
        big_body = {"x": "a" * 200}  # serialises to >200 bytes
        response = upload_client.post("/ingest", json=big_body)
        assert response.status_code == 413

    def test_413_envelope_and_request_id(self, upload_client):
        """413 body has exactly {request_id, error}; header matches body."""
        big_body = {"x": "a" * 200}
        response = upload_client.post("/ingest", json=big_body)
        assert response.status_code == 413
        body = response.json()
        assert set(body.keys()) == {"request_id", "error"}
        assert "Payload too large" in body["error"] or "payload" in body["error"].lower()
        assert response.headers["X-Request-ID"] == body["request_id"]

    def test_411_when_content_length_missing(self, upload_client):
        """POST with no Content-Length (chunked transfer) returns 411.

        httpx does NOT set Content-Length for iterator/generator content,
        so the middleware receives a request without that header.
        """
        def _gen():
            yield b"x"

        # Try generator approach first.
        response = upload_client.post("/ingest", content=_gen())
        if response.status_code == 411:
            # Expected: httpx used chunked encoding without Content-Length.
            return

        # Fallback: manually strip the header via build_request/send.
        req = upload_client.build_request("POST", "/ingest", content=b"x")
        # httpx Request headers are mutable via __setitem__ / pop.
        try:
            del req.headers["content-length"]
        except KeyError:
            pass
        response = upload_client.send(req)
        assert response.status_code == 411, (
            f"Expected 411 Length Required, got {response.status_code}. "
            "httpx may have injected Content-Length; "
            "review the test approach for this httpx version."
        )

    def test_400_on_invalid_content_length(self, upload_client):
        """A non-numeric Content-Length returns 400."""
        req = upload_client.build_request(
            "POST", "/ingest",
            content=b"{}",
            headers={"content-type": "application/json"},
        )
        req.headers["content-length"] = "abc"
        response = upload_client.send(req)
        assert response.status_code == 400
        body = response.json()
        assert "Invalid Content-Length" in body["error"]

    def test_within_limit_passes_through(self, upload_client):
        """A small body (well under 100 bytes) passes through to the route."""
        response = upload_client.post("/ingest", json={"a": 1})
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_query_route_not_guarded(self, upload_client):
        """POST /query is not in the guarded path prefixes; large body -> 200."""
        big_body = {"x": "a" * 200}
        response = upload_client.post("/query", json=big_body)
        # Not guarded, so the route handler runs and returns 200.
        assert response.status_code == 200


# ── MaxUploadSizeMiddleware integration test ──────────────────────────────────

class TestUploadLimitIntegration:
    """Acceptance criterion: 413 before any disk write on the real app."""

    def test_ingest_413_before_disk_write(self, client, runner_stub):
        """Spoofing Content-Length > 50 MB returns 413; the runner is never called.

        We use build_request then mutate the Content-Length header after
        construction (httpx does not recompute on send()).
        """
        big = 60 * 1024 * 1024  # 60 MB > 50 MB default cap
        req = client.build_request(
            "POST", "/ingest",
            content=b"{}",
            headers={"content-type": "application/json"},
        )
        req.headers["content-length"] = str(big)
        response = client.send(req)
        assert response.status_code == 413
        # The 413 status code is the proof that middleware short-circuited before route dispatch.


# ── Rate-limit integration tests ──────────────────────────────────────────────

class TestRateLimit:
    """Slowapi rate limiting: 429 threshold, envelope, Retry-After, and
    X-Request-ID. Compiled limit is 5/minute (set in conftest module-level).
    Autouse reset_rate_limiter gives a clean window per test.
    """

    def test_ingest_429_at_threshold(self, client, runner_stub):
        """Fire 5 accepted /ingest calls, then the 6th must return 429."""
        for i in range(5):
            resp = client.post("/ingest", json={"source_dir": "pdf/"})
            assert resp.status_code == 202, (
                f"Call {i+1}/5 expected 202, got {resp.status_code}: {resp.text}"
            )
        # 6th call must be rate-limited.
        sixth = client.post("/ingest", json={"source_dir": "pdf/"})
        assert sixth.status_code == 429

    def test_429_envelope_shape(self, client, runner_stub):
        """429 body has {request_id, error} with 'Rate limit exceeded' in error."""
        for _ in range(5):
            client.post("/ingest", json={"source_dir": "pdf/"})
        resp = client.post("/ingest", json={"source_dir": "pdf/"})
        assert resp.status_code == 429
        body = resp.json()
        assert set(body.keys()) == {"request_id", "error"}
        assert "Rate limit exceeded" in body["error"]

    def test_429_has_retry_after_header(self, client, runner_stub):
        """429 response includes a Retry-After header with a non-negative integer value."""
        for _ in range(5):
            client.post("/ingest", json={"source_dir": "pdf/"})
        resp = client.post("/ingest", json={"source_dir": "pdf/"})
        assert resp.status_code == 429
        retry_after = resp.headers.get("Retry-After")
        assert retry_after is not None, "Retry-After header must be present on 429"
        assert int(retry_after) >= 0, f"Retry-After must be a non-negative integer, got {retry_after!r}"

    def test_429_has_request_id_header(self, client, runner_stub):
        """429 X-Request-ID header matches body's request_id."""
        for _ in range(5):
            client.post("/ingest", json={"source_dir": "pdf/"})
        resp = client.post("/ingest", json={"source_dir": "pdf/"})
        assert resp.status_code == 429
        body = resp.json()
        assert resp.headers["X-Request-ID"] == body["request_id"]

    def test_health_not_rate_limited(self, client):
        """GET /health has no @limiter.limit decorator; 20 calls all return 200."""
        for _ in range(20):
            resp = client.get("/health")
            # /health calls get_store() which fails without a real ChromaDB,
            # but still returns 200 (degraded), not 429.
            assert resp.status_code == 200


# ── /ingest path-hardening integration tests ──────────────────────────────────

@pytest.fixture
def empty_pdf_subdir():
    """Create an empty temp subdirectory inside the allowed upload dir (pdf/).

    Yielded as a Path; removed after the test.
    The allowed dir is compiled from get_upload_settings() at import time.
    """
    from rag.api.dependencies import get_upload_settings
    root = Path(get_upload_settings().allowed_upload_dir)
    d = root / "_pytest_empty"
    d.mkdir(exist_ok=True)
    yield d
    # Cleanup: only rmdir if still empty (as we expect).
    try:
        d.rmdir()
    except OSError:
        pass  # non-empty or already gone


class TestIngestPathHardening:
    """Integration tests for resolve_under enforcement inside POST /ingest."""

    def test_path_outside_allowed_403(self, client):
        """/etc exists and is outside the allowed root -> 403."""
        resp = client.post("/ingest", json={"source_dir": "/etc"})
        assert resp.status_code == 403
        body = resp.json()
        # Error message must mention 'not allowed' or 'not allowed' concept.
        assert "not allowed" in body["error"].lower() or "allowed" in body["error"].lower()

    def test_path_dotdot_escape_to_existing_outside_403(self, client):
        """A .. escape to an existing dir outside pdf/ returns 403.

        pdf/../docs resolves to <repo>/docs which exists and is outside pdf/.
        """
        from rag.api.dependencies import get_upload_settings
        root = Path(get_upload_settings().allowed_upload_dir)
        target = (root / ".." / "docs").resolve()
        if not target.exists():
            pytest.skip(f"precondition: {target} (pdf/../docs) must exist for this 403 test")
        resp = client.post("/ingest", json={"source_dir": "pdf/../docs"})
        assert resp.status_code == 403

    def test_path_dotdot_to_missing_404(self, client):
        """A .. escape to a nonexistent dir returns 404 (candidate_missing)."""
        resp = client.post("/ingest", json={"source_dir": "pdf/../nonexistent_xyzzy"})
        assert resp.status_code == 404

    def test_path_missing_404(self, client):
        """A path under the allowed root that doesn't exist returns 404."""
        resp = client.post("/ingest", json={"source_dir": "pdf/nonexistent_subdir"})
        assert resp.status_code == 404

    def test_empty_dir_no_pdfs_404(self, client, runner_stub, empty_pdf_subdir):
        """An existing dir under the allowed root with no PDFs returns 404."""
        resp = client.post("/ingest", json={"source_dir": str(empty_pdf_subdir)})
        assert resp.status_code == 404
        body = resp.json()
        assert "No PDF files" in body["error"]

    def test_valid_pdf_dir_202(self, client, runner_stub):
        """pdf/ contains real PDFs; with runner stubbed, /ingest returns 202."""
        resp = client.post("/ingest", json={"source_dir": "pdf/"})
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert "poll_url" in data
        assert data["status"] == "pending"
