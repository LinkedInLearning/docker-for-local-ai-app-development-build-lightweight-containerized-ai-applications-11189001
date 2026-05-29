"""Shared pytest fixtures for the RAG API test suite."""

import os

import pytest
from fastapi.testclient import TestClient


# Set before any module-level import of rag.api.main so _require_auth()
# returns False when the test process loads the app. Tests that exercise
# auth behaviour directly should use the autouse fixture below to restore
# a specific key set and use the `auth_app` / `auth_client` / `auth_unauth_client` fixtures.
os.environ.setdefault("RAG_API_REQUIRE_AUTH", "false")

# Compiled-in rate limits for the test process. Small and known so
# rate-limit tests can count deterministically (5 calls then 429).
# The autouse reset_rate_limiter fixture prevents cross-test leakage.
# These must be set BEFORE rag.api.main is first imported so the
# @limiter.limit(...) decorators compile these strings, not the defaults.
os.environ.setdefault("RAG_API_RATE_LIMIT_INGEST", "5/minute")
os.environ.setdefault("RAG_API_RATE_LIMIT_QUERY", "5/minute")


TEST_API_KEY = "test-key-1"


@pytest.fixture(autouse=True)
def _configure_test_env(monkeypatch):
    """Set RAG_API_KEYS and clear any cached value before each test."""
    monkeypatch.setenv("RAG_API_KEYS", TEST_API_KEY)
    monkeypatch.delenv("RAG_API_REQUIRE_AUTH", raising=False)

    # Bust the lru_cache so the new env value is picked up.
    from rag.api.dependencies import get_api_keys
    get_api_keys.cache_clear()
    yield
    get_api_keys.cache_clear()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear slowapi's in-memory counter before AND after each test so
    the fixed-window state never leaks across tests. The limiter is a
    process-wide singleton (rag/api/rate_limit.py); without this, the
    Nth call in test A counts against test B.

    Also keeps existing tests/test_api.py green: those tests make
    multiple /ingest and /query calls and would trip the 5/minute limit
    without this reset.

    Implementation: slowapi 0.1.9 Limiter does not expose a top-level
    reset(). We fall back to the underlying limits-library storage reset.
    """
    from rag.api.rate_limit import limiter
    _reset_limiter(limiter)
    yield
    _reset_limiter(limiter)


def _reset_limiter(lim):
    """Best-effort reset of the slowapi Limiter's in-memory storage.

    Tries (in order):
      1. lim.reset()                          -- if available
      2. lim.limiter.storage.reset()          -- limits lib internal
      3. lim._storage.reset()                 -- alternative attr name
    """
    reset_fn = getattr(lim, "reset", None)
    if callable(reset_fn):
        try:
            reset_fn()
            return
        except Exception:
            pass

    # Fall back to the underlying limits-library storage object.
    inner = getattr(lim, "limiter", None)
    if inner is not None:
        storage = getattr(inner, "storage", None)
        if storage is not None and hasattr(storage, "reset"):
            try:
                storage.reset()
                return
            except Exception:
                pass

    # Second fallback: _storage attribute on the limiter directly.
    storage2 = getattr(lim, "_storage", None)
    if storage2 is not None and hasattr(storage2, "reset"):
        try:
            storage2.reset()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def fresh_job_registry():
    """Clear the cached JobRegistry singleton so each test starts with an
    empty registry. Autouse so GET /ingest/jobs listings are isolated.

    Note: if a BackgroundTask holds a reference to the old registry
    instance, it will write to the old (now-orphaned) one. The runner_stub
    fixture patches the runner's heavy deps so it completes instantly,
    before any cache-clear confusion can occur.
    """
    from rag.api.dependencies import get_job_registry
    get_job_registry.cache_clear()
    yield
    get_job_registry.cache_clear()


@pytest.fixture
def client():
    """TestClient that auto-injects the test API key on every request."""
    from rag.api.main import app
    return TestClient(app, headers={"X-API-Key": TEST_API_KEY})


@pytest.fixture
def unauth_client():
    """TestClient WITHOUT an auth header -- for negative tests."""
    from rag.api.main import app
    return TestClient(app)


@pytest.fixture
def auth_app(monkeypatch):
    """A FRESH FastAPI app with APIKeyAuthMiddleware ENABLED, independent
    of rag.api.main's import-time _require_auth()==False. Used to test
    auth enforcement, allowlist, and request-id-on-401 behavior without
    mutating the shared app or reloading modules.

    Mirrors main.py's middleware ORDER:
        RequestID (outer) -> APIKeyAuth (inner) -> routes
    plus register_exception_handlers so 401/500 get the sanitized
    envelope + X-Request-ID.

    The /openapi.json, /docs, /redoc paths are served automatically by
    FastAPI and are in AUTH_ALLOWLIST, so the allowlist test is meaningful
    (auth middleware receives the request and lets it through because the
    path is in the allowlist).
    """
    from fastapi import FastAPI, HTTPException
    from rag.api.middleware import (
        APIKeyAuthMiddleware,
        RequestIDMiddleware,
        register_exception_handlers,
    )

    app = FastAPI()

    @app.get("/health")
    def _health():
        return {"status": "ok"}

    @app.get("/config")
    def _config():
        return {"ok": True}

    @app.get("/boom")
    def _boom():
        raise HTTPException(status_code=404, detail="nope")

    @app.get("/explode")
    def _explode():
        raise RuntimeError("internal detail that must not leak")

    app.add_middleware(APIKeyAuthMiddleware, api_keys=(TEST_API_KEY,))
    app.add_middleware(RequestIDMiddleware)  # outermost
    register_exception_handlers(app)
    return app


@pytest.fixture
def auth_client(auth_app):
    """Auth-enabled app, requests carry a valid X-API-Key."""
    return TestClient(auth_app, headers={"X-API-Key": TEST_API_KEY})


@pytest.fixture
def auth_unauth_client(auth_app):
    """Auth-enabled app, NO key -- for 401 negative tests."""
    return TestClient(auth_app)


@pytest.fixture
def runner_stub(monkeypatch):
    """Patch the ingestion runner's heavy dependencies so background
    ingestion completes instantly and deterministically inside the
    synchronous TestClient BackgroundTasks execution.

    Patch targets are the names imported into rag.api.jobs.runner at
    module top (from rag.ingestion... import ... and
    from rag.api.dependencies import ...), so we patch in the runner
    module's namespace, not the source module's namespace.

    Returns a small namespace exposing the fake store so a test can
    assert ingest_chunks was called / check call count.
    """
    from unittest.mock import MagicMock

    fake_store = MagicMock()

    def _fake_ingest_chunks(chunks, embedder, *, source_file, progress_callback=None):
        if progress_callback is not None:
            progress_callback(1, 1)  # drive one progress update
        return len(chunks) or 1

    fake_store.ingest_chunks.side_effect = _fake_ingest_chunks

    monkeypatch.setattr("rag.api.jobs.runner.parse_pdf",
                        lambda path: ["el"])
    monkeypatch.setattr("rag.api.jobs.runner.chunk_elements",
                        lambda *a, **k: ["chunk"])
    monkeypatch.setattr("rag.api.jobs.runner.get_store",
                        lambda: fake_store)
    monkeypatch.setattr("rag.api.jobs.runner.get_embedder_instance",
                        lambda: MagicMock())

    class _Ns:
        store = fake_store

    return _Ns()


@pytest.fixture
def upload_app():
    """Tiny app wrapping ONLY MaxUploadSizeMiddleware (+ RequestID so the
    413 envelope gets a request_id) with a small max_bytes (100 bytes),
    for isolated, deterministic Content-Length tests.

    /query is NOT guarded by the middleware (only /ingest prefix is).
    """
    from fastapi import FastAPI
    from rag.api.middleware import MaxUploadSizeMiddleware, RequestIDMiddleware
    from rag.api.middleware import register_exception_handlers

    app = FastAPI()

    @app.post("/ingest")
    def _ingest():
        return {"ok": True}

    @app.post("/query")
    def _query():
        return {"ok": True}

    app.add_middleware(MaxUploadSizeMiddleware, max_bytes=100)  # 100-byte cap
    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)
    return app


@pytest.fixture
def upload_client(upload_app):
    """TestClient for the upload_app (100-byte cap)."""
    return TestClient(upload_app)
