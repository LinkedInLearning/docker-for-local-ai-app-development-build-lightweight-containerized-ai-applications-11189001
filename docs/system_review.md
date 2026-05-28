# Folder Structure & RAG Implementation Review

**Reviewed**: 2026-05-27
**Source of truth**: `docs/development_plan.md` (8-phase RAG system spec)
**Repo state**: branch `dev` (commits `7ab68a6`, `dfc92e5`)

This document covers three things:

1. **Folder-by-folder functionality reference** — what each top-level directory does
2. **Structural correctness assessment** — where the layout matches the plan and where it diverges
3. **Containerized RAG implementation review** — how the Docker pieces fit together and what is missing

---

## 1. Folder Functionality Reference

### `rag/` — RAG engine source code

The Python package implementing the full RAG pipeline. Importable as `from rag import …`.

| Subfolder | Role |
|---|---|
| `rag/config.py` | Pydantic-based settings loader. Reads YAML, validates providers/active selections, resolves API keys from environment variables. Single source of typed configuration for every other module. |
| `rag/store.py` | `ChromaStore` — thin wrapper over the ChromaDB HTTP client. Owns collection creation, upsert/query/delete, source-grouped document listing, and end-to-end chunk ingestion (`ingest_chunks` embeds and writes in one call). |
| `rag/ingestion/` | **Document ingestion pipeline.** `pdf_parser.py` runs Docling and yields typed `ParsedElement`s (text/heading/table) with page + section metadata. `chunker.py` provides `recursive`, `semantic`, and `by_title` strategies that respect `keep_tables_intact`. `embedder.py` returns a LangChain `Embeddings` instance for the active provider (OpenAI or Gemini) plus a batched helper. `store.py` re-exports `ChromaStore` from the top-level `rag/store.py`. |
| `rag/retrieval/` | **Query pipeline.** `retriever.py` embeds the question, queries ChromaDB for `top_k * 2` candidates, score-thresholds, and trims to `top_k`. `reranker.py` re-scores with a cross-encoder (`ms-marco-MiniLM-L-6-v2`, lazily cached) — `llm` mode is a stub raising `NotImplementedError`. `chain.py` builds the prompt, dispatches to the configured chat model (OpenAI / Anthropic / Gemini), and returns a `QueryResponse(answer, sources, metadata)`. |
| `rag/api/` | **FastAPI service** wrapping the engine. `main.py` exposes `GET /health`, `POST /ingest`, `POST /query`, `GET /documents`, `DELETE /documents/{id}`, `GET /config`. `models.py` holds Pydantic request/response schemas. `dependencies.py` provides `lru_cache`-backed singletons for `Settings`, `ChromaStore`, and the embedder. |
| `rag/evaluation/` | **Quality benchmarking.** `metrics.py` implements keyword-based precision/recall/relevancy/faithfulness scoring (custom, *not* RAGAS) and a `run_evaluation`/`format_report` pair. `test_set.yaml` holds 10 financial-report questions tagged with categories and `expected_keywords`. |
| `rag/observability/` | **Tracing & logging.** `logging.py` provides a JSON formatter, a `TraceContext` for stage timing, and `setup_logging` (idempotent — checks `logger.handlers`). `tracing.py` toggles LangSmith (env vars) or Phoenix (OTel exporter to `http://phoenix:6006`) based on `observability.provider`. |

### `docker/` — Image build assets

| File | Role |
|---|---|
| `Dockerfile_Base` | Ubuntu 22.04 base layer with shell tooling (`zsh`, `oh-my-zsh`, `fzf`, `btop`, …) and Quarto. Built and pushed as `rkrispin/python-base:0.0.1`. |
| `Dockerfile_Dev` | Inherits the base, installs `uv` + Python 3.11 venv `python-3.11-dev`, then installs `requirements.txt`. Pre-downloads Docling models so first ingestion is fast. Built as `rkrispin/python-dev-rag-docker:0.0.2`. |
| `Dockerfile_API` | **Standalone runtime image** (Roadmap item 1). `python:3.11-slim` + `requirements-api.txt` only; copies `rag/` and `config/`; runs `uvicorn rag.api.main:app` on port 8080. |
| `requirements.txt` | Full dev stack — Jupyter, plotly, ragas, streamlit, langchain, docling, etc. Used by `Dockerfile_Dev`. |
| `requirements-api.txt` | Minimal runtime deps — langchain providers, chromadb, fastapi, uvicorn, sentence-transformers. Used by `Dockerfile_API`. |
| `install_uv.sh` / `install_dependencies.sh` / `install_quarto.sh` | Helpers invoked from the Dockerfiles. |
| `build_base_docker.sh` / `build_dev_docker.sh` | `docker buildx` multi-arch (amd64+arm64) build & push scripts. |
| `setting_git.sh`, `.p10k.zsh` | Shell ergonomics for the dev container. |

### `pdf/` — Sample financial reports

Four 10-Q filings (Apple Q1 & Q2 2026, Google Q1 2026, generic SEC `form-10-q.pdf`) used as ingestion fixtures.

> ⚠️ Plan spec calls this folder `docs/`. See §2 for the implications.

### `notebooks/` — Interactive examples

Walkthrough notebooks meant to be run inside the dev container.

| Notebook | Purpose |
|---|---|
| `01_pdf_ingestion.ipynb` | Parse + chunk demo for the four sample PDFs; lightweight (~40 KB). |
| `02_pdf_ingestion.ipynb` | End-to-end ingestion (parse → chunk → embed → store). 14 MB — outputs are committed and inflate the file. |
| `03_query_the_pdf.ipynb` | Query path demo: `retrieve` + `rerank` + `query_rag` against the populated collection. |

### `.devcontainer/` — VS Code Dev Containers entry point

| File | Role |
|---|---|
| `devcontainer.json` | Points at `../docker-compose.yaml`, attaches to the `python` service, also auto-starts `phoenix`. Mounts `~/.zsh_history_dev` for persistent shell history. Injects `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `LANGSMITH_API_KEY`, `CHROMA_DATA_PATH` from the host via `remoteEnv` with the documented `key_is_missing` sentinel. |
| `devcontainer.env` | Two placeholder vars (`VAR1`, `VAR2`). **Not referenced anywhere — appears stale.** |

### `.vscode/` — Editor settings

`extensions.json` and `settings.json`. Repo-local VS Code preferences; orthogonal to the RAG runtime.

### `docs/` — Project documentation

Currently holds `development_plan.md` (the spec) and `rag_system_architecture.drawio` (the architecture diagram). This file is a sibling.

### Other top-level files

| File | Role |
|---|---|
| `docker-compose.yaml` | Three-service stack: `python` (dev), `chromadb` (vector store), `phoenix` (optional, profile `observability`). Bridge network `rag-docker`, volume mount for ChromaDB persistence. |
| `chroma_data/` | Bind-mount target for ChromaDB persistence. Empty in the working copy. |
| `README.md` | LinkedIn course boilerplate — **does not document this project**. |
| `CONTRIBUTING.md`, `LICENSE`, `NOTICE` | Standard course-repo metadata. |
| `.gitignore` | Minimal: `.DS_Store`, `node_modules`, `.tmp`, `npm-debug.log`. |

---

## 2. Folder-Structure Correctness

### Plan vs. reality (top-level)

| Plan path | Actual path | Status |
|---|---|---|
| `config/settings.yaml` | — | ❌ **Missing** |
| `rag/` (package) | `rag/` | ✅ Matches structure |
| `clients/cli.py`, `clients/streamlit_app.py`, `clients/notebook_client.py` | — | ❌ **Folder missing** (Phase 6 not landed) |
| `docs/` (PDFs) | `pdf/` | ⚠️ **Renamed** — see callers below |
| `dev/` (e.g. `02_evaluation.py`) | — | ❌ Not created |
| `docker/` | `docker/` | ✅ |
| `.devcontainer/` | `.devcontainer/` | ✅ |
| `docker-compose.yaml`, `ruff.toml`, `README.md` | `docker-compose.yaml`, no `ruff.toml`, README is course boilerplate | ⚠️ Partial |
| `tests/` (test_config / test_ingestion / test_retrieval / test_api) | — | ❌ **No tests anywhere in the repo** |

### Detailed issues

**🔴 Blocker — `config/settings.yaml` is missing.** `rag/config.py:9` defaults to `<repo>/config/settings.yaml`. With no `RAG_CONFIG_PATH` override and no file at that path, every entry point (`load_config()` in `dependencies.py`, every notebook, every test) raises `FileNotFoundError`. The plan §5.1 specifies the full YAML — that file needs to be created (or `RAG_CONFIG_PATH` must be set everywhere) before the system can run end-to-end.

**🔴 PDF folder name is inconsistent.** Three places assume `docs/`:
- `notebooks/01_pdf_ingestion.ipynb` (`DOCS_DIR = project_root / "docs"`) — was clearly run earlier when `docs/` held the PDFs (notebook output shows `/workspace/docs/...`).
- `rag/api/models.py:6` — `IngestRequest.source_dir: str = "docs/"`.
- `docs/development_plan.md` throughout.

But the PDFs now live at `pdf/`, and `docs/` has been repurposed for documentation (`development_plan.md` and now this file). Result: hitting `POST /ingest` with default args returns 404. **Pick one and align.** Recommendation: keep `docs/` for documentation (its conventional meaning) and rename the API default + notebook constants to `pdf/` — it is the smaller blast radius.

**🟡 No `clients/` folder.** ~~Phase 6 (CLI, Streamlit, Jupyter helper) is checked off in the plan but the deliverables are absent.~~ ✅ Streamlit app added 2026-05-27 (`clients/streamlit_app.py`) with sidebar controls for providers/models/chunking/retrieval, a PDF library view, and per-session ephemeral collections. CLI and notebook helper still TBD.

**🟡 No `tests/` folder.** Every phase has a "Test checkpoint" with shell snippets, plus `tests/test_*.py` deliverables. No automated tests exist. For a course repo this is acceptable; for a system advertised as "Phase 7: Evaluation completed" it is misleading.

**🟡 `chroma_data/` is not in `.gitignore`.** Plan step 1.5 explicitly required it. Currently the directory is empty and untracked, but the moment ChromaDB writes anything binary it will start showing up in `git status`.

**🟡 `rag/ingestion/store.py` is a one-line re-export of `rag/store.py`.** Two `ChromaStore` import paths exist:
- `from rag.store import ChromaStore` (used by `rag/api/dependencies.py`, `rag/__init__.py`)
- `from rag.ingestion.store import ChromaStore` (used by `rag/retrieval/retriever.py`)

Both resolve to the same class, but the plan §5.2 lists `ingestion/store.py` as the canonical owner and the top-level location is undocumented. Pick one home; the other should be deleted.

**🟢 What is right.**
- Package layout under `rag/` (`ingestion`, `retrieval`, `api`, `evaluation`, `observability`) matches the plan exactly.
- The Pydantic config schema, FastAPI route surface, ingestion data model (`ParsedElement` → `Chunk` with metadata), and retrieval flow (`retrieve` → `rerank` → `query_rag`) are all faithful to the spec.
- Multi-provider routing (OpenAI / Anthropic / Gemini) works through the `active.{embedding,chat}_provider` selectors with deferred imports so missing optional packages don't break unrelated providers.

---

## 3. Containerized RAG Implementation Review

### Architecture as built

```
┌────────────────────────────────────────────────────────────┐
│  Docker network: rag-docker (bridge)                       │
│                                                            │
│   python (dev)              chromadb               phoenix │
│   ┌──────────────────┐      ┌─────────────┐    ┌─────────┐ │
│   │ /workspace bind  │      │ chromadb    │    │ :6006   │ │
│   │ runs uvicorn     │ ───► │ /chroma/    │    │ OTel    │ │
│   │ (in-container)   │      │ chroma vol  │    │ tracer  │ │
│   └──────────────────┘      └─────────────┘    └─────────┘ │
│         ▲                          ▲                       │
│         │ remoteEnv keys           │ ${CHROMA_DATA_PATH}   │
└─────────┼──────────────────────────┼───────────────────────┘
          │                          │
   devcontainer.json           bind mount on host
```

### What works well

- **Service topology matches the plan.** Bridge network, `python` ↔ `chromadb` connectivity by hostname (`chromadb:8000`), persistent bind mount via `${CHROMA_DATA_PATH:-./chroma_data}`, optional Phoenix gated behind a Compose profile.
- **Secret hygiene is clean.** API keys are pulled from the host through `remoteEnv` with the `key_is_missing` sentinel, then passed into the `python` service's `environment` block — no secrets in any committed file. `rag/config.py:resolve_api_key` rejects the sentinel value with a clear error.
- **Image strategy is sensible.** Two-stage build (`base` → `dev`) keeps shell tooling out of the runtime image, and `Dockerfile_API` exists separately for the eventual standalone API container (Roadmap item 1).
- **HuggingFace cache is mounted** (`${HF_HOME:-~/.cache/huggingface}:/root/.cache/huggingface`) so Docling/cross-encoder models aren't re-downloaded on every container rebuild — matches the plan.
- **Phoenix is wired correctly.** ~~`rag/observability/tracing.py:_configure_phoenix` posts to `http://phoenix:6006/v1/traces` which is reachable inside the bridge network.~~ Note: the phoenix service was removed from `docker-compose.yaml` on 2026-05-27 because tag `arizephoenix/phoenix:4.6.0` is not published. The tracing code path in `rag/observability/tracing.py` still exists and remains a no-op while `observability.enabled: false` — re-add the service with a valid tag (and rerun `runServices`) to bring tracing back.

### Issues to fix

**🔴 `docker-compose.yaml` lost two safeguards from the plan:**
1. The plan's `chromadb` service has a `healthcheck` block; the actual file does not. Without it, the next item is also broken.
2. The plan's `python` service has `depends_on: chromadb: { condition: service_healthy }`; the actual file degrades to plain `depends_on: - chromadb`. That waits for the *container* to start, not for ChromaDB to accept connections — first-run race conditions are likely (the dev container can attach before the API on port 8000 is ready). Restore both blocks.

**🟡 ChromaDB version drift.** Plan uses `chromadb/chroma:latest`; compose pins `chromadb/chroma:1.3.5`. Pinning is the right call (`latest` is a footgun for persistent stores), but the client side in `requirements.txt` is `chromadb>=1.3.5` and `requirements-api.txt` is `chromadb>=1.3.5`. Floating client versions can drift past server compatibility — pin the client too, e.g. `chromadb==1.3.5`.

**🟡 No `api` service in `docker-compose.yaml`.** `Dockerfile_API` exists, but nothing in compose builds or runs it. Currently `uvicorn` is run *inside* the dev container, which is fine for development but means there is no production-shaped path. To realize Roadmap item 1, add:

```yaml
api:
  build:
    context: .
    dockerfile: docker/Dockerfile_API
  ports: ["8080:8080"]
  depends_on:
    chromadb: { condition: service_healthy }
  environment: [OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, LANGSMITH_API_KEY]
  networks: [rag-docker]
```

**🟡 `Dockerfile_API` does not copy `config/`.** Line 9 says `COPY config/ /app/config/`, but `config/` doesn't exist in the repo. This image will fail to build until `config/settings.yaml` is added (which is the §2 blocker again).

**🟡 `chromadb/chroma:1.3.5` healthcheck endpoint.** When you re-add the healthcheck, note that Chroma 1.x uses `/api/v2/heartbeat`, not the `/api/v1/heartbeat` from the plan (which was written against an older release). Use:

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -fsS http://localhost:8000/api/v2/heartbeat || exit 1"]
  interval: 5s
  timeout: 5s
  retries: 5
  start_period: 10s
```

**🟡 `.devcontainer/devcontainer.env` is unused.** No service in compose references it, no `--env-file` flag points at it, and its contents are placeholder. Either delete it or document it.

**🟡 `notebooks/02_pdf_ingestion.ipynb` is 14 MB.** The committed cell outputs (likely embedded images / very long text) bloat the repo. Strip outputs (`jupyter nbconvert --clear-output --inplace`) before committing — or add an nbstripout pre-commit hook.

**🟢 What is good in the implementation.**
- `rag/store.py:ingest_chunks` — embeds, hashes a deterministic `chunk_id`, stamps `ingestion_timestamp`, and upserts in one call. Idempotent on re-ingest.
- `rag/retrieval/reranker.py:_get_cross_encoder` is `lru_cache(1)` so the cross-encoder model loads once per process — important since `rerank()` is called on every query.
- `rag/api/main.py:ingest_documents` validates that `source_dir` stays inside the project (`relative_to(allowed_base)`), preventing path traversal via the API.
- `rag/observability/logging.py:setup_logging` is idempotent (checks `logger.handlers`), so reload-time double-handler bugs are avoided.
- `rag/observability/tracing.py` falls back gracefully when LangSmith / Phoenix are unavailable rather than failing the API boot.

### Code-level observations (smaller items)

| Where | Note |
|---|---|
| `rag/api/main.py:65` | `config = get_config()` is fetched but never used in `ingest_documents`. Dead variable — fine to delete. |
| `rag/retrieval/chain.py:74` | `if config.retrieval.rerank and rerank_method != "none":` — the per-call `rerank_method` arg is honored only if global `rerank` is true. If a caller passes `rerank_method="cross-encoder"` while config has `rerank: false`, reranking is silently skipped. Either drop the global gate or document the precedence. |
| `rag/ingestion/chunker.py:_split_text` | The "find a separator" loop returns at the *first* separator that produces an `idx > start`, regardless of how close to `end`. With long single-paragraph blocks this can produce very small chunks. Acceptable for a course example; flag for production. |
| `rag/evaluation/metrics.py` | Plan says "use RAGAS framework or custom evaluation". Current implementation is keyword-overlap heuristics — workable as a smoke signal but not what `ragas==0.2.0` (already in `requirements.txt`) would give. If RAGAS is intended, this needs a rewrite; if not, drop the dep. |
| `rag/api/dependencies.py` | `lru_cache` singletons mean the API process holds one ChromaDB HTTP client and one embedder for its lifetime. Restart the API after editing `config/settings.yaml`. |

---

## 4. Recommended Cleanup Punch List (in order)

1. ~~**Create `config/settings.yaml`**~~ ✅ Added 2026-05-27.
2. ~~**Pick one PDF folder name.**~~ ✅ Resolved 2026-05-27 — kept PDFs in `pdf/`; updated `rag/api/models.py` (`source_dir` default), `tests/test_ingestion.py` (`DOCS_DIR`), and both notebooks (`notebooks/01_pdf_ingestion.ipynb`, `notebooks/02_pdf_ingestion.ipynb`). Stale printed *output* in notebook 01 still mentions `/workspace/docs/...`; will refresh on next rerun.
3. **Restore `chromadb` healthcheck and `python` `depends_on: condition: service_healthy`** in `docker-compose.yaml`.
4. ~~**Add `chroma_data/` to `.gitignore`.**~~ ✅ Added 2026-05-27.
5. **Decide on `rag/ingestion/store.py`** — keep it as the canonical location and remove `rag/store.py`, or vice versa.
6. **Rewrite `README.md`** with project-specific instructions (LinkedIn course boilerplate is leftover).
7. **Strip outputs from `notebooks/02_pdf_ingestion.ipynb`.**
8. **Delete `.devcontainer/devcontainer.env`** (or wire it up).
9. **(Optional) Add the `api` service to compose** to realize Roadmap item 1 — this also exercises `Dockerfile_API`.
10. ~~**(Optional) Add a minimal `tests/` directory**~~ ✅ Added 2026-05-27 (`tests/test_config.py`, `tests/test_ingestion.py`, `tests/test_retrieval.py`, `tests/test_api.py`, `tests/TEST_INDEX.md`). Test contents not yet audited in this review.

---

## 5. Bottom Line

The Python package is well-organized and faithfully implements the engine described in the development plan. The container topology is sound and the dev-container experience is thoughtfully wired up. The repo is **one missing file (`config/settings.yaml`) away from being runnable**, and a handful of small alignments — folder name, healthcheck, .gitignore, README — away from being a clean reference implementation of the spec.
