# Phase 4 — Tests, Docs, Acceptance Verification: Architecture Specification

**Project**: RAG API Tier 1 Hardening (v0.1.0)
**Phase**: 4 of 4
**Source plan**: `pm/v0_1_0/development_plan.md` §9 Phase 4, file lists §7, contract §6, env vars §8, acceptance §10
**Intended save path**: `/Users/ramikrispin/Personal/courses/docker-local-ai-11189001/pm/v0_1_0/phase-4-architecture.md`
**Status**: Ready for Builder
**Scope**: Tests + docs ONLY. No `rag/` source changes.

---

## 1. Phase Overview

### Goal
Cover every Phase 1–3 code path with pytest, write the user-facing "Running the API" docs, add `.env.example`, update `docs/overview.md` §1, and verify the §10 Tier 1 acceptance checklist end-to-end.

### Dependencies on previous phases
Phases 1–3 are committed (`f83c221`, `f1e0090`, `71456fc`, `b4392a3`, `af4554c`). The source files are the source of truth; this spec was written against the **actual implemented code**, not just the prior specs. Several prior-spec details differ from the shipped code — the Builder must follow the implemented behavior documented below (see §9 "Reconciliation with implemented code").

### What this phase delivers (8 deliverables, all under `tests/`, repo root, `docs/`)
1. `tests/test_middleware.py` (new)
2. `tests/test_jobs.py` (new)
3. `tests/test_job_registry.py` (new)
4. `tests/test_security.py` (new)
5. `tests/test_api.py` (edit — only if a gap exists; see §6)
6. `tests/conftest.py` (edit — add fixtures; see §3)
7. `tests/TEST_INDEX.md` (edit — register the new files)
8. `.env.example` (new), `README.md` (edit), `docs/overview.md` (edit)

### What this phase does NOT do
No changes to any `rag/api/` source, `rag/store.py`, `rag/ingestion/`, `rag/retrieval/`, `rag/config.py`, `rag/observability/`, `clients/streamlit_app.py`, `docker-compose.yaml`, `docker/Dockerfile_API`, `docker/requirements*.txt`, `config/settings.yaml`. See §10 for the explicit constraint list.

---

## 2. Critical environment facts the Builder MUST internalize

These are observed from the implemented code and gate every test design choice.

### 2.1 conftest sets `RAG_API_REQUIRE_AUTH=false` at import time
`tests/conftest.py` line 13: `os.environ.setdefault("RAG_API_REQUIRE_AUTH", "false")`. This runs **before** `rag.api.main` is imported by any fixture. In `main.py`, `_require_auth()` is evaluated at **module-import time** (line 116: `if _require_auth(): app.add_middleware(APIKeyAuthMiddleware, ...)`). Therefore, **in the default test process the `APIKeyAuthMiddleware` is NEVER installed.**

Consequence: the existing `client` / `unauth_client` fixtures both reach every route without auth. The existing `tests/test_api.py` redefines its own `client` fixture (no API key header) and passes — because auth is off.

**This means auth tests cannot be exercised against the default `app` instance.** To test auth enforcement, the Builder must build a **fresh app with auth enabled in-process** (see §3 `auth_app` / `auth_client` fixtures). Do NOT attempt to toggle the env var and re-import `rag.api.main` — the `app` object and its middleware stack are frozen at first import, and module reload is fragile under pytest.

### 2.2 BackgroundTasks under Starlette TestClient run SYNCHRONOUSLY
Starlette's `TestClient` (httpx-backed) executes `BackgroundTasks` **after the response is produced but before `client.post(...)` returns** — synchronously, on the same thread, inside the `with TestClient(...)` request context. So for `POST /ingest`:
- The response (202) is returned first.
- Then `run_ingestion_job(...)` runs to completion **before** `client.post("/ingest", ...)` returns control to the test.

This is a gift for testing: by the time the test inspects the result of `client.post("/ingest")`, the job has **already reached a terminal state** (`completed` or `failed`) if the runner's dependencies are mocked to return quickly. There is **no need for a polling loop in tests** — a single `GET /ingest/jobs/{id}` immediately after the POST will show the terminal state.

Caveat: this requires the TestClient to be used as a context manager OR via the fixture-returned instance (Starlette runs background tasks within the ASGI `http` scope completion). The existing fixtures return `TestClient(app, ...)` directly (not via `with`) and the existing `test_ingest_success` only checks the 202 — it does not assert background completion. For the new `test_jobs.py` tests that assert terminal state, the Builder MUST mock the runner's heavy dependencies (`parse_pdf`, `chunk_elements`, `get_store`, `get_embedder_instance`) so the synchronous background execution is fast and deterministic, AND confirm via a quick experiment that the background task has run before the assertion. If any test observes the job still `pending`, wrap the client in `with TestClient(app) as c:` form. **Flag**: document this in the test file header so a future reader understands why no polling loop exists.

### 2.3 slowapi limiter is a single process-wide singleton with persistent in-memory state
`rag/api/rate_limit.py` line 42 constructs `limiter = Limiter(..., storage_uri="memory://", strategy="fixed-window")` at import. Its counter storage (`limiter.limiter` / `limiter._storage`) persists across tests in the same process. The `@limiter.limit(get_rate_limit_ingest())` decorators bake the rate string in at **import time** (e.g. `"5/minute"`), so the limit cannot be changed per-test by env vars after import.

Consequences for rate-limit tests:
- The limit is fixed at whatever `RAG_API_RATE_LIMIT_INGEST` / `_QUERY` were when `rag.api.main` was first imported (default `5/minute` / `30/minute` unless conftest sets them before import).
- The in-memory counter **leaks between tests** — a test that makes 5 `/ingest` calls will affect a later `/ingest` test in the same process.
- **Every rate-limit test MUST reset the limiter storage in setup/teardown.** Add an autouse-or-explicit fixture `reset_rate_limiter` that calls `limiter.reset()` (slowapi `Limiter.reset()` clears the storage) before and after. If `limiter.reset()` is unavailable in 0.1.9, fall back to `limiter.limiter.storage.reset()` or re-instantiate the underlying storage; the Builder verifies which exists. See §3 `reset_rate_limiter` fixture.
- To make rate-limit tests **deterministic without depending on the default 5/30**, drive the limit that is actually compiled in. Two viable strategies, in order of preference:
  - **Strategy A (recommended, robust):** Test against the **known default** limits. For `/ingest` (default `5/minute`): reset the limiter, fire 5 accepted calls, assert the 6th returns 429. For `/query` (default `30/minute`): firing 31 calls is noisy but works; instead test `/ingest` for the 429 path (lower count) and assert `/query`'s 429 envelope shape by exhausting it via a tighter approach — OR set `RAG_API_RATE_LIMIT_*` env in conftest **before import** (see §3 note) so the compiled-in limits are small (e.g. `2/minute`). **Strategy A.2 is the cleanest: set the rate-limit env vars in conftest's module-level block (alongside `RAG_API_REQUIRE_AUTH`) so the decorators compile small limits.** Recommend setting `RAG_API_RATE_LIMIT_INGEST="100/minute"` and `RAG_API_RATE_LIMIT_QUERY="100/minute"` as the **default test env** so existing tests don't trip the limiter, and have rate-limit-specific tests rely on per-test reset + counting against those compiled limits. Pick ONE compiled limit and design counts around it.
  - **Strategy B (heavier):** Build a dedicated app in a subprocess/fresh import with env set first. Avoid — too fragile.

  **Decision for the Builder:** In conftest module-level setup (before importing `app`), set generous rate limits so normal tests never trip:
  ```python
  os.environ.setdefault("RAG_API_RATE_LIMIT_INGEST", "100/minute")
  os.environ.setdefault("RAG_API_RATE_LIMIT_QUERY", "100/minute")
  ```
  Then rate-limit tests reset the limiter and fire 100 + 1 calls? That is too many. **Better:** keep the compiled limits *small and known* for the test process — set them to `"5/minute"` (ingest) and `"5/minute"` (query) in conftest module-level, reset between tests, and have all non-rate-limit tests that hit `/ingest` or `/query` repeatedly also reset the limiter via an autouse fixture. Given non-rate-limit tests rarely fire >5 calls to the same route, an **autouse `reset_rate_limiter` fixture (function-scoped, resets before each test)** is the simplest correct design. **This is the chosen approach — see §3.**

### 2.4 MaxUploadSizeMiddleware runs before auth and only guards `/ingest` POST/PUT/PATCH
- 413/411/400 are returned for guarded routes regardless of auth (auth is off in tests anyway).
- TestClient/httpx **always sets `Content-Length`** for a bytes/JSON body, so a normal `client.post("/ingest", json=...)` never trips 411. To test the **411 missing-Content-Length path**, the Builder must send a request that has no Content-Length. With httpx/TestClient this requires either a streaming/generator body OR explicitly removing the header. See §5.2 for the exact technique.
- The default compiled `max_bytes` for the test process comes from `get_upload_settings().max_upload_bytes` evaluated at `main.py` import (default 50 MB unless `RAG_API_MAX_UPLOAD_MB` set before import). To test 413 deterministically, set `RAG_API_MAX_UPLOAD_MB` low in conftest module-level (e.g. `"1"` → 1 MB) so a ~2 MB declared Content-Length trips it — but a 1 MB cap would break any test sending a >1 MB body (none do). **Decision:** Do NOT lower the global cap (it would couple unrelated tests). Instead, test 413 by sending a request whose `Content-Length` header is **manually set above 50 MB** without an actual large body. With `MaxUploadSizeMiddleware` reading the header before body consumption, you can send a small body but spoof a large `Content-Length`. httpx computes Content-Length from the body and will override a manual header for a known body. Therefore the robust technique is a **custom httpx request with a content generator + explicit `Content-Length` header** (httpx does not override Content-Length when you pass `headers={"content-length": ...}` with a streaming/iterator content). See §5.2 for the precise recipe and a fallback that builds a separate small-cap app.

  **Recommended primary approach for 413/411/400:** build a **dedicated tiny app fixture** (`upload_app` in §3) that wraps `MaxUploadSizeMiddleware` directly around a trivial ASGI route with a small `max_bytes` (e.g. 100 bytes). This isolates the middleware unit from the global app and makes Content-Length manipulation trivial and deterministic. ALSO add one integration test against the real `client` for the 413 path using a spoofed Content-Length to satisfy the acceptance criterion "413 before disk write." See §5.2.

### 2.5 `resolve_under` is a pure function — unit-test it directly with `tmp_path`
No app needed for the `resolve_under` unit tests. For the `/ingest` path-hardening integration tests, the allowed root is `get_upload_settings().allowed_upload_dir`, compiled at import from `RAG_API_ALLOWED_UPLOAD_DIR` (default `pdf/` resolved to abs). Tests that drive `/ingest` with a real `source_dir` must use a directory **under the compiled allowed root**. Since the default allowed root is `<repo>/pdf` and real PDFs live there, `source_dir="pdf/"` resolves under root → passes path check. To test the 403 path, send `source_dir="/etc"` or `"pdf/../etc"`. To control the allowed root precisely for integration tests, set `RAG_API_ALLOWED_UPLOAD_DIR` in conftest module-level to a tmp dir is NOT possible (tmp_path is per-test, env is import-time). **Decision:** Path-hardening integration tests rely on the default `pdf/` allowed root (which exists and has PDFs). Symlink-escape and missing-candidate integration variants are covered at the unit level via `resolve_under` + `tmp_path`; the `/ingest` integration layer asserts the 403/404 status mapping using `/etc` (outside) and a nonexistent path under `pdf/`. See §5.4.

### 2.6 pytest-cov is NOT installed
`docker/requirements.txt` has `pytest==8.3.0` only; **no `pytest-cov`** in either requirements file. Plan §9 step 6 and the §10 checkpoint reference `--cov`. **The Builder must NOT add a hard dependency on `pytest-cov` in the test code** (no `pytestmark` requiring it, no `--cov` in any committed `pytest.ini`/`addopts`). Coverage is an optional manual step. See §7 (Dependencies) and Open Questions §11.

### 2.7 No `[tool.pytest]` config / no `pyproject.toml`
There is no `pyproject.toml`, `setup.cfg`, or `pytest.ini`. Tests are discovered by default rules. Do not introduce a pytest config file in Phase 4 unless the orchestrator approves (it would be a new top-level config artifact). `caplog` and `monkeypatch` are stdlib-pytest builtins — available.

---

## 3. `tests/conftest.py` — additive edits

Keep all existing content. Add the items below. Rationale for each is inline.

### 3.1 Module-level env (before app import) — add rate-limit + upload defaults

```python
# Existing line stays:
os.environ.setdefault("RAG_API_REQUIRE_AUTH", "false")

# NEW — compiled-in limits for the test process. Small + known so
# rate-limit tests can count deterministically; the autouse
# reset_rate_limiter fixture prevents cross-test leakage.
os.environ.setdefault("RAG_API_RATE_LIMIT_INGEST", "5/minute")
os.environ.setdefault("RAG_API_RATE_LIMIT_QUERY", "5/minute")
```

Do NOT set `RAG_API_MAX_UPLOAD_MB` or `RAG_API_ALLOWED_UPLOAD_DIR` here — leave defaults (50 MB, `pdf/`) so the integration path tests use the real `pdf/` dir.

### 3.2 New autouse fixture: `reset_rate_limiter`

**Belongs in conftest** (cross-cutting, every test that touches `/ingest` or `/query` benefits).

```python
@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear slowapi's in-memory counter before AND after each test so
    the fixed-window state never leaks across tests. The limiter is a
    process-wide singleton (rag/api/rate_limit.py); without this, the
    Nth call in test A counts against test B."""
    from rag.api.rate_limit import limiter
    _reset_limiter(limiter)
    yield
    _reset_limiter(limiter)


def _reset_limiter(limiter):
    # slowapi 0.1.9: Limiter.reset() exists; fall back defensively.
    reset = getattr(limiter, "reset", None)
    if callable(reset):
        reset()
        return
    storage = getattr(getattr(limiter, "limiter", None), "storage", None)
    if storage is not None and hasattr(storage, "reset"):
        storage.reset()
```

**Builder note:** verify `limiter.reset()` exists in the installed slowapi 0.1.9 by a quick `python -c "from slowapi import Limiter; print(hasattr(Limiter, 'reset'))"`. If neither path resets state, re-instantiate `limiter.limiter` via `limiter._storage = MemoryStorage()`-equivalent. Document the working mechanism in the fixture docstring.

### 3.3 New fixtures: `auth_app` / `auth_client` / `auth_unauth_client`

**Belong in conftest** (used by `test_middleware.py`; could be in-file, but auth-enabled app construction is reusable and tricky enough to centralize).

These build a **fresh FastAPI app with auth ENABLED**, bypassing the import-time `_require_auth()==False` of the default `app`. Construct it by importing the middleware classes and re-creating an app, OR by adding the auth middleware to a fresh app that mounts the same routes. The cleanest approach that does not touch source: **construct a minimal app and add `APIKeyAuthMiddleware` + `RequestIDMiddleware` + `register_exception_handlers` around a couple of representative routes**, since middleware behavior (allowlist, 401) is independent of which business routes exist.

```python
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

    @app.get("/openapi.json")  # FastAPI provides this automatically; allowlisted
    def _noop():  # pragma: no cover - real openapi used
        return {}

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
    """Auth-enabled app, NO key — for 401 negative tests."""
    return TestClient(auth_app)
```

**Builder note:** FastAPI auto-mounts `/openapi.json`, `/docs`, `/redoc`; the explicit `_noop` `/openapi.json` route above is redundant — drop it and let FastAPI serve the real one so the allowlist test is meaningful. Keep `/health`, `/config`, `/boom`, `/explode`.

### 3.4 New fixture: `runner_stub` (mocking the ingestion runner's heavy deps)

**Belongs in conftest** (shared by `test_jobs.py`; could be in-file). Patches the four heavy callables the runner imports so background ingestion is instant and deterministic. The runner imports `parse_pdf`, `chunk_elements` from `rag.ingestion.*` and calls `get_store()` / `get_embedder_instance()` from `rag.api.dependencies` (imported at runner top as `from rag.api.dependencies import get_embedder_instance, get_store`). Patch targets MUST be where they are looked up: **`rag.api.jobs.runner.parse_pdf`, `rag.api.jobs.runner.chunk_elements`, `rag.api.jobs.runner.get_store`, `rag.api.jobs.runner.get_embedder_instance`** (the runner does `from ... import ...` at module top, so patch the names in `rag.api.jobs.runner`).

```python
@pytest.fixture
def runner_stub(monkeypatch):
    """Patch the ingestion runner's heavy dependencies so background
    ingestion completes instantly and deterministically inside the
    synchronous TestClient BackgroundTasks execution.

    Returns a small namespace exposing the fake store so a test can
    assert ingest_chunks was called / drive progress_callback.
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
```

### 3.5 New fixture: `fresh_job_registry`

**Belongs in conftest.** Busts the `get_job_registry` lru_cache so each job/endpoint test gets a clean registry; also re-instantiates after the test. Important because `POST /ingest` uses the singleton registry and tests must not see jobs from earlier tests in `GET /ingest/jobs`.

```python
@pytest.fixture(autouse=True)
def fresh_job_registry():
    """Clear the cached JobRegistry singleton so each test starts with an
    empty registry. Autouse so GET /ingest/jobs listings are isolated."""
    from rag.api.dependencies import get_job_registry
    get_job_registry.cache_clear()
    yield
    get_job_registry.cache_clear()
```

**Builder note:** `fresh_job_registry` is autouse and harmless for tests that don't touch jobs. Combined with `reset_rate_limiter` (autouse) and the existing `_configure_test_env` (autouse), every test gets a clean limiter + registry + key env.

### 3.6 New fixture: `upload_app` (isolated MaxUploadSizeMiddleware unit harness)

**Belongs in conftest** (used by `test_security.py` 413/411/400 unit tests).

```python
@pytest.fixture
def upload_app():
    """Tiny app wrapping ONLY MaxUploadSizeMiddleware (+ RequestID so the
    413 envelope gets a request_id) with a small max_bytes, for isolated,
    deterministic Content-Length tests."""
    from fastapi import FastAPI
    from rag.api.middleware import MaxUploadSizeMiddleware, RequestIDMiddleware
    from rag.api.middleware import register_exception_handlers

    app = FastAPI()

    @app.post("/ingest")
    def _ingest(body: dict | None = None):
        return {"ok": True}

    @app.post("/query")
    def _query(body: dict | None = None):
        return {"ok": True}

    app.add_middleware(MaxUploadSizeMiddleware, max_bytes=100)  # 100-byte cap
    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)
    return app


@pytest.fixture
def upload_client(upload_app):
    return TestClient(upload_app)
```

---

## 4. Module-by-module: shared conventions

- Use the existing style: class-grouped tests (`class TestX:`) as in `tests/test_api.py`, or flat functions as in `tests/test_ingestion.py`. **Match `test_api.py`'s class grouping** for the endpoint files (`test_jobs.py`, `test_security.py` integration sections) and flat functions for pure-unit files (`test_job_registry.py`, `resolve_under` unit section).
- Import style: `from rag.api.main import app` is acceptable (module-level), but prefer pulling `app` from the `client` fixture to keep auth/registry state controlled.
- All endpoint assertions on error bodies check the **sanitized envelope**: `{"request_id": ..., "error": ...}` (NOT `{"detail": ...}`). Confirmed by `errors.build_error_response`.
- `X-Request-ID` header is present on **every** response (RequestIDMiddleware is installed on the default app and on `auth_app`/`upload_app`).
- No network, no real embeddings, no real ChromaDB: mock at the `rag.api.main.*` or `rag.api.jobs.runner.*` lookup site (follow existing `@patch("rag.api.main.get_store")` pattern).

---

## 5. Test file specifications

### 5.1 `tests/test_middleware.py`

Tests RequestID echo/generation, auth allowlist + 401, error sanitization, and log capture under request_id. Auth tests use `auth_client` / `auth_unauth_client`; RequestID + error tests can use either the default `client` (RequestID is always installed) or `auth_app`. Group into classes.

```python
class TestRequestID:
    def test_request_id_generated_when_absent(self, client): ...
    def test_request_id_echoed_when_present(self, client): ...
    def test_request_id_stripped(self, client): ...
    def test_request_id_differs_across_requests(self, client): ...

class TestAuthAllowlist:
    def test_health_open_without_key(self, auth_unauth_client): ...
    def test_openapi_open_without_key(self, auth_unauth_client): ...
    def test_protected_route_401_without_key(self, auth_unauth_client): ...
    def test_protected_route_200_with_valid_key(self, auth_client): ...
    def test_invalid_key_401(self, auth_app): ...
    def test_401_body_is_sanitized_envelope(self, auth_unauth_client): ...
    def test_401_has_request_id_header(self, auth_unauth_client): ...

class TestErrorSanitization:
    def test_http_4xx_detail_preserved_as_error(self, auth_client): ...
    def test_500_strips_internal_detail(self, auth_client): ...
    def test_500_returns_generic_message(self, auth_client): ...
    def test_error_response_has_request_id_header_and_body_match(self, auth_client): ...

class TestLogCapture:
    def test_auth_failure_logged(self, auth_unauth_client, caplog): ...
    def test_request_id_present_on_log_record(self, client, caplog): ...
```

**Per-test contracts:**

- `test_request_id_generated_when_absent`: GET `/health` (or `/config` via `client`), assert `X-Request-ID` header present, length 12, hex (`int(rid, 16)` parses; `len(rid) == 12`). Matches `generate_trace_id()` (`uuid4().hex[:12]`).
- `test_request_id_echoed_when_present`: send `headers={"X-Request-ID": "trace-abc-123"}`; assert response header equals `"trace-abc-123"`.
- `test_request_id_stripped`: send `"  spaced  "`; assert echoed value is `"spaced"`. (RequestIDMiddleware does `raw.strip()`.)
- `test_request_id_differs_across_requests`: two GETs with no header → two different non-empty IDs.
- `test_health_open_without_key`: `auth_unauth_client.get("/health")` → 200 (allowlisted).
- `test_openapi_open_without_key`: `.get("/openapi.json")` → 200.
- `test_protected_route_401_without_key`: `.get("/config")` → 401.
- `test_protected_route_200_with_valid_key`: `auth_client.get("/config")` → 200.
- `test_invalid_key_401`: build `TestClient(auth_app, headers={"X-API-Key": "wrong"})`; `.get("/config")` → 401.
- `test_401_body_is_sanitized_envelope`: body has keys exactly `{"request_id", "error"}`; `error == "Invalid or missing API key"`; no `detail` key.
- `test_401_has_request_id_header`: 401 response has `X-Request-ID` header, non-empty, equal to body `request_id`. (Auth middleware calls `build_error_response(... request_id=get_current_request_id())`; RequestIDMiddleware outer re-stamps the header. Body and header must match.)
- `test_http_4xx_detail_preserved_as_error`: `auth_client.get("/boom")` (raises `HTTPException(404, "nope")`) → 404, `body["error"] == "nope"`.
- `test_500_strips_internal_detail`: `auth_client.get("/explode")` (raises `RuntimeError("internal detail that must not leak")`) → 500; assert `"internal detail" NOT in response.text`; assert `body["error"] == "Internal server error"`.
  - **Important**: when `TestClient` is constructed without `raise_server_exceptions=False`, an unhandled exception that reaches the catch-all handler is converted to a response by the registered `Exception` handler — so it returns 500, it does not raise. The `register_exception_handlers` installs an `@app.exception_handler(Exception)`. Confirm the handler fires under TestClient; if TestClient re-raises, construct `TestClient(auth_app, raise_server_exceptions=False)`. **Builder: use `raise_server_exceptions=False` for the 500 test client** to guarantee the response is returned, not raised.
- `test_500_returns_generic_message`: same call, assert exactly `GENERIC_500_MESSAGE` ("Internal server error").
- `test_error_response_has_request_id_header_and_body_match`: on the `/boom` 404, `response.headers["X-Request-ID"] == body["request_id"]`.
- `test_auth_failure_logged`: with `caplog.at_level(logging.WARNING, logger="rag")`, do an unauthenticated `/config`; assert a record with `stage == "auth.missing_header"` exists. Access via `record.stage` (the code logs `extra={"stage": ...}`). Note: the `rag` logger has `propagate=False` after `setup_logging()`, which can prevent `caplog` from capturing. **Builder mitigation:** `caplog` attaches a handler to the root logger; with `propagate=False` records won't reach it. Use `caplog.at_level(logging.WARNING, logger="rag")` which sets the level on the `rag` logger and adds caplog's handler **to that logger directly** (pytest's `caplog` adds its handler at the level set; verify capture works — if not, attach `caplog.handler` to `logging.getLogger("rag")` within the test, or assert on the `stage`/message via a temporary handler). Document the chosen mechanism. If capture proves unreliable, downgrade this test to assert the HTTP-level 401 only and move log-capture verification to `test_request_id_present_on_log_record` using an explicit handler.
- `test_request_id_present_on_log_record`: attach a list-capturing `logging.Handler` to `logging.getLogger("rag")` for the duration, fire a request that logs (e.g. unauthenticated `/config` on `auth_app`), assert the captured `LogRecord` has a `request_id` attribute (added by `RequestIDLogFilter` if the filter is attached). **Caveat**: the filter is attached in `setup_logging()`, which only runs via the app's `lifespan`. Under bare `TestClient(app)` (not used as context manager), lifespan may not run, so the filter may be absent and `record.request_id` unset. Use `with TestClient(auth_app) as c:` to trigger lifespan, OR call `setup_logging()` in the test setup. **Builder: call `rag.observability.logging.setup_logging()` at the top of this test** to guarantee the filter is attached, then assert `getattr(record, "request_id", None)` is set. Keep this test resilient: if the explicit-handler approach is flaky, assert only that a record was emitted with the expected `stage`.

**Fixtures used:** `client`, `auth_client`, `auth_unauth_client`, `auth_app`, `caplog`. No mocks needed (these routes don't hit the store).

### 5.2 `tests/test_security.py`

Four sections: `resolve_under` unit tests, `MaxUploadSizeMiddleware` (isolated + one integration), rate-limit integration, `/ingest` path hardening integration.

```python
class TestResolveUnder:
    def test_accepts_root_itself(self, tmp_path): ...
    def test_accepts_descendant(self, tmp_path): ...
    def test_rejects_absolute_outside(self, tmp_path): ...
    def test_rejects_dotdot_escape(self, tmp_path): ...
    def test_rejects_symlink_escape(self, tmp_path): ...
    def test_accepts_symlink_within(self, tmp_path): ...
    def test_missing_candidate_reason(self, tmp_path): ...
    def test_missing_root_reason(self, tmp_path): ...
    def test_returns_realpath(self, tmp_path): ...

class TestUploadLimitMiddleware:
    def test_413_on_oversize_content_length(self, upload_client): ...
    def test_413_envelope_and_request_id(self, upload_client): ...
    def test_411_when_content_length_missing(self, upload_client): ...
    def test_400_on_invalid_content_length(self, upload_client): ...
    def test_within_limit_passes_through(self, upload_client): ...
    def test_query_route_not_guarded(self, upload_client): ...

class TestUploadLimitIntegration:
    def test_ingest_413_before_disk_write(self, client, tmp_path): ...

class TestRateLimit:
    def test_ingest_429_at_threshold(self, client, runner_stub): ...
    def test_429_envelope_shape(self, client, runner_stub): ...
    def test_429_has_retry_after_header(self, client, runner_stub): ...
    def test_429_has_request_id_header(self, client, runner_stub): ...
    def test_health_not_rate_limited(self, client): ...

class TestIngestPathHardening:
    def test_path_outside_allowed_403(self, client): ...
    def test_path_dotdot_403(self, client): ...
    def test_path_missing_404(self, client): ...
    def test_empty_dir_no_pdfs_404(self, client, runner_stub): ...
    def test_valid_pdf_dir_202(self, client, runner_stub): ...
```

**`TestResolveUnder` contracts** (pure, `from rag.api.security import resolve_under, PathNotAllowedError`):
- `test_accepts_root_itself`: `root = tmp_path/"root"; root.mkdir()`; `resolve_under(root, root)` returns `root.resolve()`, no raise.
- `test_accepts_descendant`: make `root/"sub"`; `resolve_under(root/"sub", root)` returns the sub abspath.
- `test_rejects_absolute_outside`: `resolve_under("/etc", root)` raises `PathNotAllowedError`, `exc.value.reason == "outside_allowed_root"`.
- `test_rejects_dotdot_escape`: candidate `root/".."/"etc"`-style path that resolves outside → reason `outside_allowed_root` (the `..` is normalized by `resolve()`; if the candidate doesn't exist, reason is `candidate_missing` first — so make the escape target exist, e.g. create a sibling dir `tmp_path/"etc"` and pass `root/".."/"etc"` with `must_exist=True`; it exists and resolves outside → `outside_allowed_root`). Use `pytest.raises(PathNotAllowedError)` and check reason.
- `test_rejects_symlink_escape`: create `tmp_path/"outside"` dir; create symlink `root/"link" -> tmp_path/"outside"`; `resolve_under(root/"link", root)` → reason `symlink_escapes_root`. (The implementation distinguishes this: unresolved candidate IS under root, resolved is not.)
- `test_accepts_symlink_within`: `root/"a"` and `root/"b"` dirs; symlink `root/"a"/"toB" -> root/"b"`; `resolve_under(root/"a"/"toB", root)` → returns realpath of `root/"b"`, no raise.
- `test_missing_candidate_reason`: `resolve_under(root/"nope", root, must_exist=True)` → reason `candidate_missing`.
- `test_missing_root_reason`: `resolve_under(root, tmp_path/"no_root")` → reason `allowed_root_missing`.
- `test_returns_realpath`: symlink-within case → returned `Path == (root/"b").resolve()`, i.e. realpath, not the symlink path.

**Builder note (symlink tests on the platform):** `os.symlink` requires the dir to exist; skip with `pytest.mark.skipif(not hasattr(os, "symlink"))` is unnecessary on darwin/linux but add `@pytest.mark.skipif(sys.platform == "win32", ...)` defensively for the symlink tests.

**`TestUploadLimitMiddleware` contracts** (`upload_client`, cap=100 bytes):
- `test_413_on_oversize_content_length`: POST `/ingest` with a JSON body >100 bytes (e.g. `json={"x": "a"*200}`) → httpx sets Content-Length ~205 > 100 → **413**. Body is sanitized envelope; `error` contains "Payload too large".
- `test_413_envelope_and_request_id`: same; assert `set(body.keys()) == {"request_id","error"}`, `response.headers["X-Request-ID"] == body["request_id"]`.
- `test_411_when_content_length_missing`: send a POST with **no Content-Length**. Technique: pass a generator/stream content so httpx uses chunked transfer (no Content-Length):
  ```python
  def _gen():
      yield b"x"
  r = upload_client.post("/ingest", content=_gen())
  assert r.status_code == 411
  ```
  httpx sends `Transfer-Encoding: chunked` with no `Content-Length` for an iterator body → middleware returns 411. **Builder: verify** that TestClient/httpx forwards chunked without injecting Content-Length; if it does inject one, fall back to explicitly stripping: `upload_client.post("/ingest", content=b"x", headers={"content-length": ""})` is invalid — instead use the request-builder: `req = upload_client.build_request("POST", "/ingest", content=_gen()); req.headers.pop("content-length", None); r = upload_client.send(req)`. Document the working approach.
- `test_400_on_invalid_content_length`: build a request and set `headers={"content-length": "abc"}` with a small matching body via the `build_request`/`send` escape hatch so httpx doesn't recompute; assert 400, `error == "Invalid Content-Length header."`. If httpx refuses a non-numeric Content-Length at the transport layer, this test instead targets the `upload_app` via a raw ASGI call — **Builder fallback:** call the middleware through Starlette's ASGI test transport with a hand-built scope where `headers` contains `(b"content-length", b"abc")`. Prefer the httpx `build_request` approach first.
- `test_within_limit_passes_through`: `json={"a": 1}` (<100 bytes) → 200 `{"ok": True}`.
- `test_query_route_not_guarded`: POST `/query` with a >100-byte body → 200 (not 413), proving `/query` is outside guarded prefixes.

**`TestUploadLimitIntegration` (acceptance §10 "413 before disk write"):**
- `test_ingest_413_before_disk_write`: against the real `client` (default app, 50 MB cap). Spoof a Content-Length above 50 MB without sending 50 MB:
  ```python
  big = 60 * 1024 * 1024
  req = client.build_request("POST", "/ingest",
                             content=b"{}",
                             headers={"content-length": str(big),
                                      "content-type": "application/json"})
  r = client.send(req)
  assert r.status_code == 413
  ```
  Assert no file was written: point `source_dir` is irrelevant because the middleware rejects before the handler runs — assert the handler never executed by also asserting `runner_stub.store.ingest_chunks` was never called (include `runner_stub` and assert `not runner_stub.store.ingest_chunks.called`). This satisfies "413 before any disk write" at the unit level: the middleware short-circuits before route dispatch.
  **Builder caveat:** httpx may recompute Content-Length from `content=b"{}"` (2 bytes) and override the spoofed header. If it does, use `build_request` then mutate `req.headers["content-length"] = str(big)` after construction and `client.send(req)` — httpx does not recompute on `send`. Verify and document.

**`TestRateLimit` contracts** (compiled limit is `5/minute` for both, per conftest §3.1; autouse `reset_rate_limiter` gives a clean window):
- `test_ingest_429_at_threshold`: with `runner_stub` (so each accepted `/ingest` is cheap), fire 5 POSTs to `/ingest` with a valid `source_dir="pdf/"` → all 202; the 6th → 429.
  - **Note:** `source_dir="pdf/"` resolves under the default allowed root and `pdf/` contains real PDFs, so path + pdf checks pass and each call returns 202. The runner runs synchronously but is stubbed, so it's instant. Confirm 6th call is 429.
- `test_429_envelope_shape`: trip the limit (reset, 5 calls, then 1), assert `set(body.keys()) == {"request_id","error"}`, `"Rate limit exceeded" in body["error"]`, no slowapi plaintext.
- `test_429_has_retry_after_header`: assert `"Retry-After" in response.headers` and it's a non-negative integer string. (Handler sets it from `request.state.view_rate_limit`; fallback is "60".)
- `test_429_has_request_id_header`: `response.headers["X-Request-ID"] == body["request_id"]`.
- `test_health_not_rate_limited`: 20 GETs to `/health` → all 200 (no `@limiter.limit` on it).

**`TestIngestPathHardening` contracts** (default `client`, allowed root = `pdf/`):
- `test_path_outside_allowed_403`: `client.post("/ingest", json={"source_dir": "/etc"})` → 403; `body["error"]` mentions "not allowed".
- `test_path_dotdot_403`: `source_dir="pdf/../etc"` → 403. (Resolves to `<repo>/etc` which is outside `pdf/`; if `<repo>/etc` doesn't exist, `resolve_under` raises `candidate_missing` → 404 instead. **Builder: verify** whether `<repo>/etc` exists — it does not, so this yields 404, not 403.) **Decision:** for the `..` test, target an existing-but-outside dir to force the 403 reason. Use `source_dir="pdf/../docs"` (the repo has a `docs/` dir that exists and is outside `pdf/`) → resolves to `<repo>/docs`, exists, outside root → 403. Rename test `test_path_dotdot_escape_to_existing_outside_403` and use `pdf/../docs`. Add a separate `test_path_dotdot_to_missing_404` using `pdf/../nonexistent` → 404.
- `test_path_missing_404`: `source_dir="pdf/nonexistent_subdir"` (under root, doesn't exist) → 404 (`candidate_missing`).
- `test_empty_dir_no_pdfs_404`: create an empty subdir under the allowed root. Since the allowed root is `<repo>/pdf` and we cannot easily mkdir under it without polluting the repo, **use `tmp_path` won't work** (it's outside `pdf/`). Instead: create `pdf/_empty_test_dir/` in setup and clean up in teardown, OR mock `resolve_under` is not desired. **Decision:** create a temp subdir under `pdf/` via a fixture that mkdir+rmdir around the test:
  ```python
  @pytest.fixture
  def empty_pdf_subdir():
      from rag.api.dependencies import get_upload_settings
      root = Path(get_upload_settings().allowed_upload_dir)
      d = root / "_pytest_empty"
      d.mkdir(exist_ok=True)
      yield d
      d.rmdir()
  ```
  Then `client.post("/ingest", json={"source_dir": str(d)})` → 404, `"No PDF files" in body["error"]`. (This mirrors existing `test_ingest_no_pdfs`.) Put `empty_pdf_subdir` in `test_security.py` (test-specific) or conftest. Recommend in-file.
- `test_valid_pdf_dir_202`: `client.post("/ingest", json={"source_dir": "pdf/"})` with `runner_stub` → 202, body has `job_id`/`poll_url`/`status=="pending"`. (Background runner stubbed.)

**Fixtures used:** `client`, `upload_client`, `runner_stub`, `tmp_path`, `empty_pdf_subdir`, autouse `reset_rate_limiter` + `fresh_job_registry`.

### 5.3 `tests/test_jobs.py`

Endpoint-level tests for the 202 contract, polling/terminal state, failed-job path, unknown-id 404, and listing. Relies on synchronous BackgroundTasks (§2.2) + `runner_stub`.

```python
class TestIngestSubmission:
    def test_post_ingest_returns_202(self, client, runner_stub): ...
    def test_post_ingest_location_header(self, client, runner_stub): ...
    def test_post_ingest_echoes_request_id(self, client, runner_stub): ...
    def test_post_ingest_request_id_honored(self, client, runner_stub): ...

class TestJobPolling:
    def test_job_reaches_completed(self, client, runner_stub): ...
    def test_completed_job_has_result(self, client, runner_stub): ...
    def test_job_failed_path(self, client, monkeypatch): ...
    def test_failed_error_message_sanitized(self, client, monkeypatch): ...
    def test_unknown_job_404(self, client): ...
    def test_unknown_job_404_envelope(self, client): ...

class TestJobListing:
    def test_list_newest_first(self, client, runner_stub): ...
    def test_list_respects_limit(self, client, runner_stub): ...
    def test_list_invalid_limit_400(self, client): ...
```

**Contracts:**
- `test_post_ingest_returns_202`: POST `/ingest` `{"source_dir":"pdf/"}` → 202; body has `job_id`, `request_id`, `poll_url`, `status=="pending"`. (The 202 body is the `IngestJobResponse` snapshot taken at create time, BEFORE the background runner mutates the record — so `status` in the 202 body is always `"pending"` even though by the time the test runs the job is already completed in the registry. Assert `"pending"` here.)
- `test_post_ingest_location_header`: `response.headers["Location"] == data["poll_url"] == f"/ingest/jobs/{data['job_id']}"`.
- `test_post_ingest_echoes_request_id`: `response.headers["X-Request-ID"] == data["request_id"]`.
- `test_post_ingest_request_id_honored`: send `X-Request-ID: my-trace`; assert `data["request_id"] == "my-trace"` and header echoes it.
- `test_job_reaches_completed`: POST `/ingest` (runner_stub), capture `job_id`, then immediately `GET /ingest/jobs/{job_id}` → 200, `status == "completed"` (synchronous background already ran). Assert `result` is populated, `documents_processed >= 1`.
- `test_completed_job_has_result`: same; `body["result"]["documents_ingested"] >= 1`, `body["result"]["status"] == "success"`, `body["result"]["files"]` non-empty.
- `test_job_failed_path`: monkeypatch `rag.api.jobs.runner.parse_pdf` to raise `ValueError("boom")`; POST `/ingest` `{"source_dir":"pdf/"}`; GET the job → `status == "failed"`, `error_message` is non-null.
- `test_failed_error_message_sanitized`: same; assert `"boom" NOT in body["error_message"]` and `body["error_message"]` matches the form `"Failed processing <file>: ValueError"` (runner produces `f"Failed processing {pdf}: {type(exc).__name__}"`). Assert it contains `"ValueError"` and a `.pdf` filename but not the raw message.
- `test_unknown_job_404`: `GET /ingest/jobs/does-not-exist` → 404. (Matches existing `test_get_job_unknown_id_404` in `test_api.py`.)
- `test_unknown_job_404_envelope`: body has `request_id` + `error`; `"not persisted" in body["error"]` (the 404 detail includes the restart hint, passed through `http_exception_handler` as `error`).
- `test_list_newest_first`: with `runner_stub`, submit 3 jobs; `GET /ingest/jobs` → list of 3, newest first (the most recently submitted `job_id` is `result[0]["job_id"]`). Because `fresh_job_registry` is autouse, the registry starts empty.
- `test_list_respects_limit`: submit 3; `GET /ingest/jobs?limit=1` → length 1.
- `test_list_invalid_limit_400`: `?limit=0` and `?limit=501` → 400 (handler raises `HTTPException(400)`; FastAPI also accepts the int so it's not 422). The existing `test_api.py::test_get_jobs_list_invalid_limit_400_or_422` allows `(400, 422)`; here assert specifically 400 since `limit` is a plain `int = 50` query param (valid int parse), and the handler raises 400.

**Fixtures used:** `client`, `runner_stub`, `monkeypatch`, autouse `fresh_job_registry` + `reset_rate_limiter` (5/min limit — submitting 3 jobs is under threshold; the failed-path test submits 1).

**Builder note on rate-limit interaction:** `test_list_*` submits 3 `/ingest` calls; with the 5/minute compiled limit and autouse `reset_rate_limiter`, this is safe. Do not submit ≥6 `/ingest` in a single test or it will 429. If a test needs more submissions, call `registry.create()` directly on the singleton rather than via HTTP — but prefer HTTP for the listing tests (3 is fine).

### 5.4 `tests/test_job_registry.py`

Pure unit + thread-safety smoke tests for `JobRegistry`. No app, no HTTP. `from rag.api.jobs.registry import JobRegistry, JobNotFoundError, DEFAULT_REGISTRY_SIZE, ENV_REGISTRY_SIZE`; `from rag.api.jobs.models import JobStatus`. Flat functions (match `test_ingestion.py` helper-style) or a `TestJobRegistry` class — recommend class grouping.

A helper to build records concisely:
```python
def _create(reg, **over):
    kw = dict(request_id="r1", source_dir="pdf/", chunking_method="recursive",
              chunk_size=1000, chunk_overlap=200, keep_tables_intact=True)
    kw.update(over)
    return reg.create(**kw)
```

```python
class TestJobRegistryUnit:
    def test_create_returns_pending(self): ...
    def test_create_stamps_created_at(self): ...
    def test_get_unknown_returns_none(self): ...
    def test_update_running_stamps_started_at(self): ...
    def test_second_running_does_not_restamp_started_at(self): ...
    def test_completed_stamps_finished_at(self): ...
    def test_failed_stamps_finished_at(self): ...
    def test_update_unknown_raises(self): ...
    def test_explicit_started_at_wins(self): ...
    def test_evicts_oldest_when_full(self): ...
    def test_list_newest_first(self): ...
    def test_list_respects_limit(self): ...
    def test_list_limit_zero_empty(self): ...
    def test_from_env_default(self, monkeypatch): ...
    def test_from_env_parses_int(self, monkeypatch): ...
    def test_from_env_rejects_non_int(self, monkeypatch): ...
    def test_init_rejects_zero_max_size(self): ...

class TestJobRegistryConcurrency:
    def test_concurrent_creates_no_lost_records(self): ...
    def test_concurrent_create_and_evict_consistent_len(self): ...
    def test_concurrent_update_reads_never_torn(self): ...
```

**Unit contracts:**
- `test_create_returns_pending`: `_create(reg).status == JobStatus.PENDING`; `started_at is None`.
- `test_create_stamps_created_at`: `created_at` is a tz-aware datetime.
- `test_get_unknown_returns_none`: `reg.get("nope") is None`.
- `test_update_running_stamps_started_at`: after `update_status(id, RUNNING)`, `started_at is not None`.
- `test_second_running_does_not_restamp_started_at`: capture `started_at` after first RUNNING; call RUNNING again; assert `started_at` unchanged. (Implementation guards with `current.started_at is None`.)
- `test_completed_stamps_finished_at` / `test_failed_stamps_finished_at`: terminal transitions set `finished_at`.
- `test_update_unknown_raises`: `update_status("missing", JobStatus.RUNNING)` raises `JobNotFoundError`.
- `test_explicit_started_at_wins`: pass `started_at=<fixed dt>` to RUNNING update; assert it equals the supplied value.
- `test_evicts_oldest_when_full`: `JobRegistry(max_size=3)`; create 4; `len(reg) == 3`; first job's id is gone (`reg.get(first_id) is None`).
- `test_list_newest_first`: create A, B, C; `reg.list()` → `[C, B, A]` order by job_id.
- `test_list_respects_limit`: create 3; `reg.list(limit=2)` length 2, newest two.
- `test_list_limit_zero_empty`: `reg.list(limit=0) == []`.
- `test_from_env_default`: `monkeypatch.delenv(ENV_REGISTRY_SIZE, raising=False)`; `JobRegistry.from_env()._max_size == DEFAULT_REGISTRY_SIZE`. (Access private `_max_size` — acceptable in a unit test; or assert behavior via eviction.)
- `test_from_env_parses_int`: `monkeypatch.setenv(ENV_REGISTRY_SIZE, "42")`; `_max_size == 42`.
- `test_from_env_rejects_non_int`: `setenv(..., "abc")`; `pytest.raises(RuntimeError)`.
- `test_init_rejects_zero_max_size`: `pytest.raises(ValueError): JobRegistry(max_size=0)`.

**Concurrency contracts** (`from concurrent.futures import ThreadPoolExecutor`):
- `test_concurrent_creates_no_lost_records`: `reg = JobRegistry(max_size=10_000)`; 50 threads × 20 creates = 1000; assert `len(reg) == 1000` and all returned `job_id`s are unique (collect into a set under a local lock or just collect futures' results). Validates no lost inserts under the RLock.
- `test_concurrent_create_and_evict_consistent_len`: `reg = JobRegistry(max_size=50)`; 500 concurrent creates; assert `len(reg) == 50` (eviction keeps it bounded, no overflow/underflow).
- `test_concurrent_update_reads_never_torn`: create one job; spawn 1 writer thread doing 2000 `update_status(id, RUNNING, total_chunks=i, progress=JobProgress(chunks_done=i, chunks_total=2000))` and 1 reader thread doing 2000 `get(id)`; for each read, assert the record validates as a `JobRecord` (it always is, since `get` returns a live `JobRecord`) and `record.total_chunks >= 0` and `record.progress is None or record.progress.chunks_done >= 0` — i.e. never an inconsistent partially-applied state. The model_copy+slot-replace under the lock guarantees readers see a fully-formed prior or new snapshot. Collect any exception from threads and `pytest.fail` if any.

**Builder note:** Concurrency tests must surface thread exceptions: gather futures and call `.result()` on each so exceptions propagate to the test (a thread that raised `JobNotFoundError` or `ValidationError` will fail the test). Keep iteration counts modest (≤2000) to stay fast (<1s).

**Fixtures used:** `monkeypatch` (for env tests). The autouse conftest fixtures (`_configure_test_env`, `reset_rate_limiter`, `fresh_job_registry`) are harmless here (they touch the app singletons, not the local `JobRegistry()` instances these tests construct). `reset_rate_limiter` imports `rag.api.rate_limit.limiter` which is fine. No app import needed.

---

## 6. `tests/test_api.py` — edits (only if needed)

Audit result against the implemented code:

- `test_api.py` defines its **own** `client` fixture (`TestClient(app)` with no key) and does **not** rely on conftest's `client`. Because auth is OFF in the test process (§2.1), no `X-API-Key` header is required and all existing tests pass as-is.
- Existing tests already assert the 202 contract (`test_ingest_success`), the sanitized envelope (`test_query_value_error` checks `response.json()["error"]`), and unknown-job 404. These match the implemented behavior.
- **Gap 1 — rate-limit leakage:** `test_api.py` makes multiple `/ingest` and `/query` calls across its tests. With the conftest compiled limit now `5/minute` (per §3.1) and the autouse `reset_rate_limiter` resetting before each test, no single `test_api.py` test fires ≥6 calls to one route, so they stay green. **No edit required**, provided the autouse `reset_rate_limiter` fixture (conftest) is added. **This is the one cross-file dependency: `test_api.py` correctness now depends on the new autouse `reset_rate_limiter`.** Call this out in the conftest fixture docstring.
- **Gap 2 — `test_ingest_success` patches `rag.api.main.Path.cwd`:** the implemented `/ingest` no longer uses `Path.cwd()` (Phase 3 replaced it with `resolve_under(... allowed_upload_dir)`). The `patch("rag.api.main.Path.cwd", ...)` is now a **no-op** but harmless (the patch target still exists; it just isn't called). The test still passes because `source_dir=str(tmp_path)` — wait: `tmp_path` is OUTSIDE the allowed root `pdf/`, so `resolve_under` would 403, not 202. **This is a latent conflict.** Let me flag precisely:

  `test_ingest_success` sends `source_dir=str(tmp_path)` (an absolute path outside `<repo>/pdf`). Under the Phase 3 `/ingest`, `resolve_under(tmp_path, "<repo>/pdf")` raises `outside_allowed_root` → **403**, but the test asserts **202**. **If this test currently passes, it is because something else is in play** — verify by running it. The most likely reason it passes today: the commits `b4392a3`/`af4554c` may have updated `test_api.py` already (the git log shows phase-3 fixes), OR the test is currently failing/being skipped. **Builder action:** run `pytest tests/test_api.py::TestIngestEndpoint -v` first. If `test_ingest_success` / `test_ingest_missing_directory` / `test_ingest_no_pdfs` fail under the Phase 3 path logic, **fix them** as the §9 step 1 "ensure existing tests pass" deliverable:
    - `test_ingest_success`: change to use `source_dir="pdf/"` (real PDFs exist there, passes path + pdf-count, returns 202) with `runner_stub` so the background task is cheap. Remove the obsolete `patch("rag.api.main.Path.cwd", ...)`.
    - `test_ingest_missing_directory`: send `source_dir="pdf/does_not_exist"` (under allowed root, missing) → 404. Remove the `Path.cwd` patch.
    - `test_ingest_no_pdfs`: use an empty subdir under `pdf/` (the `empty_pdf_subdir` fixture) → 404. Remove the `Path.cwd` patch.
    - `test_ingest_path_traversal_rejected`: `source_dir="../../etc"` — resolves outside `pdf/`; if `/etc` exists it's `outside_allowed_root` → 403 (test asserts 403). But `../../etc` from cwd may resolve to a nonexistent path → `candidate_missing` → 404. **Change to `source_dir="/etc"`** (exists, outside) → reliable 403.
  - These edits ARE within Phase 4 scope (editing `tests/test_api.py` to close gaps is deliverable §5/step 1). **Document exactly which tests changed and why** in the return summary and TEST_INDEX.

  **Builder must run the suite first and only edit the tests that actually fail.** Do not pre-emptively rewrite passing tests.

- **Gap 3 — `X-Request-ID` assertion coverage:** `test_ingest_success` already asserts `response.headers["X-Request-ID"] == data["request_id"]`. Other endpoints (`/query`, `/config`, `/documents`) do not assert the header. This is adequately covered by `test_middleware.py::TestRequestID`. **No edit required.**

**Net:** `test_api.py` edits are conditional on the run. Expected edits: the three `TestIngestEndpoint` tests' `source_dir` + drop of the dead `Path.cwd` patch, plus possibly `test_ingest_path_traversal_rejected`. All are gap-closures permitted by Phase 4 scope. If the run shows them green, make NO edits.

---

## 7. Dependencies (pytest plugins)

- **pytest**: `8.3.0` (in `docker/requirements.txt`). Available.
- **pytest-cov**: **NOT installed** in either requirements file. Do not write tests that import `pytest_cov` or require `--cov`. The §10 coverage step is **optional/manual**; if the orchestrator wants coverage enforced, that requires adding `pytest-cov` to `docker/requirements.txt` — which is OUT of Phase 4 scope (no requirements edits). Flagged in Open Questions §11.1.
- **caplog, monkeypatch, tmp_path, capsys**: pytest builtins, available.
- **httpx / starlette TestClient**: available (`fastapi==0.115.0`, `httpx>=0.28.0`). `TestClient.build_request` / `.send` exist (httpx API) — used for the 411/413 Content-Length manipulation.
- **stdlib**: `concurrent.futures`, `threading`, `os`, `sys`, `logging`, `pathlib`, `datetime` — all used; no new deps.

No new third-party dependency is introduced by Phase 4. Confirmed.

---

## 8. Documentation deliverables

### 8.1 `.env.example` (new, repo root)

Sample env vars, no real secrets. Names exactly per plan §8 and the implemented code (env names confirmed in `dependencies.py`, `rate_limit.py`, `registry.py`, `auth.py`).

```dotenv
# ── Provider keys (already used by the engine) ──────────────────────
OPENAI_API_KEY=sk-...your-key-here...
# ANTHROPIC_API_KEY=
# GOOGLE_API_KEY=

# ── RAG API (Tier 1 hardening) ──────────────────────────────────────
# Comma-separated API keys. REQUIRED unless RAG_API_REQUIRE_AUTH=false.
# Never commit real keys.
RAG_API_KEYS=change-me-key-1,change-me-key-2

# Local dev only: set to "false" to disable auth entirely. Leave unset
# (or "true") for anything resembling production.
# RAG_API_REQUIRE_AUTH=true

# Max aggregate upload size (MB) before 413. Default 50.
# RAG_API_MAX_UPLOAD_MB=50

# Single directory under which /ingest source_dir must resolve.
# Default "pdf/" (project-relative). In a container: /app/pdf
# RAG_API_ALLOWED_UPLOAD_DIR=pdf/

# Per-IP rate limits (slowapi strings). Defaults shown.
# RAG_API_RATE_LIMIT_INGEST=5/minute
# RAG_API_RATE_LIMIT_QUERY=30/minute

# Bounded in-memory job registry size (FIFO eviction). Default 500.
# RAG_API_JOB_REGISTRY_SIZE=500
```

Notes for the Builder:
- `RAG_API_JOB_TTL_SECONDS` and `RAG_API_LOG_LEVEL` from plan §8 are **NOT implemented** (Phase 2 dropped TTL in favor of FIFO; no `RAG_API_LOG_LEVEL` reader exists in code). Do NOT include them in `.env.example` — `.env.example` must reflect variables the code actually reads. Document this discrepancy in the return summary.
- Include the `OPENAI_API_KEY` line since the engine needs it; mark placeholder clearly.

### 8.2 `README.md` — add "Running the API" section

Append a new top-level section (do NOT rewrite the LinkedIn-Learning boilerplate; add after it). Content:
- **Environment setup**: copy `.env.example` to `.env`, set `RAG_API_KEYS`. Note that the API runs via uvicorn **inside the existing `python` dev container** — there is no separate `api` compose service in v1 (per plan §10 NOT-in-scope and §12). Reference: "the future container lift is documented in `pm/v0_1_0/development_plan.md` §12."
- **Start command**:
  ```bash
  export RAG_API_KEYS=your-key
  uvicorn rag.api.main:app --host 0.0.0.0 --port 8080
  ```
- **curl ingest + poll example** (matches the actual 202/poll contract):
  ```bash
  # Submit (returns 202 + job_id)
  curl -s -X POST http://localhost:8080/ingest \
    -H "X-API-Key: your-key" -H "Content-Type: application/json" \
    -d '{"source_dir": "pdf/"}'
  # → {"job_id":"j_...","request_id":"...","status":"pending","poll_url":"/ingest/jobs/j_..."}

  # Poll
  curl -s -H "X-API-Key: your-key" http://localhost:8080/ingest/jobs/j_...
  ```
- **Query example**:
  ```bash
  curl -s -X POST http://localhost:8080/query \
    -H "X-API-Key: your-key" -H "Content-Type: application/json" \
    -d '{"question": "What was revenue?"}'
  ```
- **Sample `.env`**: point to `.env.example`; reproduce the `RAG_API_*` block.
- **Limitations note (v1)**: jobs are in-memory and lost on restart; rate limit + registry are per-process (run a single uvicorn worker); behind a proxy, set `X-Forwarded-For` (Tier 2). `/health` is unauthenticated.

### 8.3 `docs/overview.md` — §1 diagram/pointer

Edit the §1 ASCII diagram (lines 11–32) to show the **API path alongside Streamlit**. Add an arrow/box for the FastAPI service (uvicorn in the `python` container) that fronts the same `rag/` engine, e.g.:
```
│  Streamlit UI  ──────────────────► chat with PDFs           │
│  HTTP client ──► FastAPI (uvicorn) ──► rag/ engine          │
│   (X-API-Key, /ingest 202 + poll, /query)                   │
```
Add one sentence + link below the diagram: "The HTTP API (Tier 1 hardened: API-key auth, async ingestion, rate limits, upload caps) is described in `pm/v0_1_0/development_plan.md`; see the README 'Running the API' section to start it." Keep the change minimal and additive — do not restructure the doc.

### 8.4 `tests/TEST_INDEX.md` — register new files

Update the summary table and add sections for `test_middleware.py`, `test_jobs.py`, `test_job_registry.py`, `test_security.py` with their test lists (mirror the existing format). Update the "FastAPI Service" placeholder (lines 102–106) to reference the real `test_api.py` + the four new files and mark Phase 4. Note: the existing "Phase" column in TEST_INDEX uses the OLD course phase numbering (config=Phase 2, etc.) — for the new rows use "Phase 4 (API Tier 1)" to disambiguate.

---

## 9. Reconciliation with implemented code (differences from prior specs)

The Builder must follow the **implemented code**, not the prior phase specs, where they differ:

1. **`/query` signature**: implemented as `def query_documents(request: Request, body: QueryRequest, response: Response)` — note the extra `response: Response` param (added in commit `af4554c` for slowapi `headers_enabled`). Phase 3 spec omitted `response`. No test impact (wire contract unchanged).
2. **`/query` 400 message**: implemented returns `"Invalid query parameters."` (sanitized, not `str(e)`). Existing `test_api.py::test_query_value_error` asserts exactly this. Match it.
3. **`update_status` started_at guard**: implemented adds `and current.started_at is None` to the re-stamp guard (stronger than the Phase 2 spec). The `test_second_running_does_not_restamp` test relies on this — correct.
4. **`run_ingestion_job` patch targets**: the runner does `from rag.api.dependencies import get_embedder_instance, get_store` and `from rag.ingestion... import parse_pdf, chunk_elements` at module top → patch in `rag.api.jobs.runner`, not at the source modules.
5. **`IngestResponse` retained**, `SanitizedErrorResponse` present, no `JobResult` in `rag/api/models.py` (it's in `rag/api/jobs/models.py`). Tests import job models from `rag.api.jobs` / `rag.api.jobs.models`.
6. **No `api:` block in `rag/config.py`** — all API config is env-driven. `.env.example` reflects env vars only; no `config/settings.yaml` `api:` section to document.
7. **Dropped env vars**: `RAG_API_JOB_TTL_SECONDS`, `RAG_API_LOG_LEVEL` are not read anywhere. Exclude from `.env.example`/README.
8. **413 "before disk write"** is structurally guaranteed because `MaxUploadSizeMiddleware` short-circuits in `dispatch` before route dispatch — the test asserts the handler/runner never executed rather than literally inspecting disk.

---

## 10. Files NOT to touch (hard constraints)

The Builder MUST NOT create, edit, or delete any of:
- Any file under `rag/api/` (`main.py`, `dependencies.py`, `models.py`, `rate_limit.py`, `middleware/*`, `jobs/*`, `security/*`).
- `rag/store.py`, `rag/ingestion/*`, `rag/retrieval/*`, `rag/config.py`, `rag/observability/*`.
- `clients/streamlit_app.py`, `clients/*`.
- `docker-compose.yaml`, `docker/Dockerfile_API`, `docker/Dockerfile_*`.
- `docker/requirements.txt`, `docker/requirements-api.txt` (slowapi already present; no pytest-cov addition in Phase 4).
- `config/settings.yaml`.
- `notebooks/*`.
- `pm/v0_1_0/development_plan.md` and prior phase specs.

The Builder MAY create/edit ONLY:
- `tests/test_middleware.py`, `tests/test_jobs.py`, `tests/test_job_registry.py`, `tests/test_security.py` (new)
- `tests/conftest.py` (additive edits per §3)
- `tests/test_api.py` (gap-closure edits per §6, only if the run shows failures)
- `tests/TEST_INDEX.md` (registration)
- `.env.example` (new)
- `README.md` (additive section)
- `docs/overview.md` (additive §1 edit)

---

## 11. Open questions / risks for the orchestrator

1. **pytest-cov absent.** Plan §9 step 6 / §10 reference `--cov`. It is not installed and adding it requires editing `docker/requirements.txt` (out of Phase 4 scope per §7.3 of the plan, which lists requirements as Phase 3-owned). **Recommendation:** treat the 80% coverage target as a manual, best-effort step (`pip install pytest-cov && pytest --cov=rag/api` run ad hoc by the engineer); do NOT codify a coverage gate. Confirm, or authorize a one-line `docker/requirements.txt` addition.
2. **`test_api.py` ingest-test conflict (§6 Gap 2).** `test_ingest_success` sends a `source_dir` outside the allowed root and asserts 202, which conflicts with the Phase 3 `resolve_under` 403. The Builder will run the suite first and, if these fail, fix them (switch to `source_dir="pdf/"` + `runner_stub`, drop the dead `Path.cwd` patch). This is in-scope gap closure but materially edits existing tests. **Confirm this is acceptable.**
3. **Rate-limit determinism via compiled limits.** The spec sets `RAG_API_RATE_LIMIT_INGEST/_QUERY="5/minute"` in conftest module-level so the singleton limiter compiles a small, known limit, plus an autouse `reset_rate_limiter`. This couples all `/ingest` `/query` tests to the autouse reset. **Confirm** the approach vs. building a separate fresh-import app per rate-limit test (heavier, rejected here).
4. **Auth tests use a fresh `auth_app`, not `rag.api.main.app`.** Because conftest disables auth at import time and middleware is frozen at import, the real `app` can't exercise auth. The `auth_app` fixture rebuilds the middleware stack around stub routes. This tests the middleware behavior faithfully but NOT the real routes' auth wiring. **Recommendation:** accept — the middleware is route-agnostic; the acceptance §10 item "all endpoints reject without key with 401" is verified manually via the README curl block / plan §9 checkpoint (documented), not via TestClient. Confirm.
5. **`.env.example` omits `RAG_API_JOB_TTL_SECONDS` and `RAG_API_LOG_LEVEL`** (not implemented). The README/`.env.example` will therefore not match plan §8 verbatim. **Recommendation:** document only implemented vars; note the divergence. Confirm.
6. **caplog vs `propagate=False`.** The `rag` logger sets `propagate=False`, which can defeat `caplog`. The two log-capture tests have documented fallbacks (explicit handler attach / `caplog.at_level(logger="rag")`). If still flaky, they degrade to asserting HTTP behavior only. **Confirm** that "best-effort log-capture, guaranteed HTTP-level assertions" is acceptable.

---

## 12. Summary

**Files to create (5):** `tests/test_middleware.py`, `tests/test_jobs.py`, `tests/test_job_registry.py`, `tests/test_security.py`, `.env.example`.
**Files to edit (4):** `tests/conftest.py` (6 fixtures + 2 env defaults), `tests/test_api.py` (conditional gap-closure, run-first), `tests/TEST_INDEX.md`, `README.md`, `docs/overview.md`. (4 source/doc files + conftest = effectively 5 edits.)

**Total test functions specified:** ~16 (middleware) + ~13 (jobs) + ~20 (registry incl. 3 concurrency) + ~26 (security across 4 sections) ≈ 75 new tests.

---

## Return summary

I have NOT written files (my available tools are read-only: Read, Grep, Glob). The full Phase 4 architecture specification is delivered above as text for the orchestrator to persist to `/Users/ramikrispin/Personal/courses/docker-local-ai-11189001/pm/v0_1_0/phase-4-architecture.md`.

What the spec covers, grounded in the actual implemented code (read, not assumed):

- **Test files & exact function signatures** for `tests/test_middleware.py`, `tests/test_jobs.py`, `tests/test_job_registry.py`, `tests/test_security.py` (~75 tests), each with assertions, fixtures, and mock targets.
- **conftest additions**: `reset_rate_limiter` (autouse), `fresh_job_registry` (autouse), `auth_app`/`auth_client`/`auth_unauth_client`, `runner_stub`, `upload_app`/`upload_client`, plus module-level rate-limit env defaults — with clear in-conftest-vs-in-file guidance.
- **Docs**: `.env.example` (only implemented env vars), README "Running the API" section, `docs/overview.md` §1 edit, TEST_INDEX registration.
- **Explicit "files NOT to touch"** section.

Key load-bearing risks I flagged concretely:
1. **TestClient + BackgroundTasks run synchronously** — so job tests need no polling loop, but the runner's heavy deps (`parse_pdf`, `chunk_elements`, `get_store`, `get_embedder_instance`) must be patched in `rag.api.jobs.runner`.
2. **slowapi limiter is a process-wide singleton with leaking state and import-time-compiled limits** — requires an autouse `reset_rate_limiter` and setting the rate-limit env before app import; the existing `test_api.py` now depends on that reset fixture.
3. **conftest disables auth at import time and middleware is frozen at import** — auth enforcement cannot be tested on the real `app`; a fresh `auth_app` fixture is required.
4. **"413 before disk write"** is asserted via middleware short-circuit (handler/runner never called) using an httpx `build_request`/`send` Content-Length spoof; the 411 path needs a chunked/streaming body.
5. **`pytest-cov` is NOT installed** (neither requirements file) — coverage must stay a manual step, not a gate.

Open questions for you (details in §11): (1) coverage gate vs. manual given no `pytest-cov`; (2) authorization to fix the conflicting `test_api.py` ingest tests (`source_dir` outside allowed root asserting 202 vs. Phase 3's 403); (3) the rate-limit compiled-limit + autouse-reset approach; (4) auth tested via `auth_app` rather than the real app; (5) `.env.example` omitting unimplemented `RAG_API_JOB_TTL_SECONDS`/`RAG_API_LOG_LEVEL`; (6) acceptance of best-effort `caplog` due to `propagate=False`.

Relevant absolute paths examined: `/Users/ramikrispin/Personal/courses/docker-local-ai-11189001/rag/api/{main.py,dependencies.py,models.py,rate_limit.py}`, `/rag/api/middleware/{request_id,auth,errors,upload_limit}.py`, `/rag/api/jobs/{registry,models,runner}.py`, `/rag/api/security/paths.py`, `/rag/observability/logging.py`, `/tests/{conftest.py,test_api.py,TEST_INDEX.md}`, `/docker/requirements.txt`, `/docker/requirements-api.txt`, `/README.md`, `/docs/overview.md`.