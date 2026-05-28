# RAG Application — Overview & Setup Guide

A containerized Retrieval-Augmented Generation (RAG) system for ingesting financial PDF reports (SEC 10-Q filings) into a vector database and answering natural-language questions about their content.

This document covers **what it is** and **how to run it**. For deeper design rationale see `docs/development_plan.md`; for architectural critique see `docs/system_review.md` and `docs/docker_review.md`.

---

## 1. What this app does

```
┌────────────────────────────────────────────────────────────────┐
│  User                                                          │
│   │                                                            │
│   ▼                                                            │
│  Streamlit UI  ──────────────────► chat with PDFs              │
│   │                                                            │
│   ▼                                                            │
│  rag/ Python package                                           │
│   ├── ingestion/   parse → chunk → embed                       │
│   ├── retrieval/   query → rerank → generate                   │
│   ├── store.py     ChromaDB wrapper                            │
│   └── config.py    YAML + env-var settings                     │
│                                                                │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ python container │ ──────► │ chromadb         │             │
│  │ (dev shell +     │  HTTP   │ container        │             │
│  │  Streamlit)      │ ◄────── │ (vector store)   │             │
│  └──────────────────┘         └──────────────────┘             │
│   network: rag-docker                                          │
└────────────────────────────────────────────────────────────────┘
```

Key capabilities:

- **PDF ingestion** with Docling (text + table extraction, optional OCR).
- **Configurable chunking** (`recursive`, `semantic`, `by_title`) with table-intact mode.
- **Multi-provider embeddings + chat** (OpenAI, Anthropic, Gemini) switchable at runtime.
- **Hybrid retrieval**: ChromaDB similarity search + cross-encoder reranker.
- **Two query modes** in Streamlit:
  - *Upload & query* — ephemeral per-session collection
  - *Connect to existing* — query a persistent ChromaDB collection populated by the notebooks
- **Source citations** with file, page, and section returned alongside every answer.

---

## 2. Folder map

| Folder | Purpose |
|---|---|
| `rag/` | Python engine — `config`, `ingestion/`, `retrieval/`, `api/`, `evaluation/`, `observability/` |
| `clients/` | UI entry points — `streamlit_app.py` + `run_streamlit.sh` |
| `notebooks/` | Walkthrough notebooks: parse → ingest → query (`01_`, `02_`, `03_`) |
| `pdf/` | Sample 10-Q filings (Apple Q1/Q2, Google Q1, generic) |
| `config/` | `settings.yaml` — providers, chunking, retrieval, ChromaDB |
| `docker/` | Dockerfiles (`Base`, `Dev`, `API`), build scripts, model-cache scripts |
| `.devcontainer/` | VS Code Dev Containers entry point (`devcontainer.json`) |
| `tests/` | `pytest` suite for config / ingestion / retrieval / API |
| `docs/` | This doc + development plan + reviews + patterns guide |

---

## 3. Prerequisites

- **Docker Desktop** (macOS / Windows / Linux) running with at least 8 GB RAM allocated.
- **VS Code** with the **Dev Containers** extension (`ms-vscode-remote.remote-containers`).
- API keys for whichever providers you want to use:
  - `OPENAI_API_KEY` — required (default embedding + chat provider)
  - `ANTHROPIC_API_KEY` — optional (chat only)
  - `GEMINI_API_KEY` — optional (embedding + chat)
  - `LANGSMITH_API_KEY` — optional (tracing)

Set them in your host shell (`~/.zshrc` or `~/.bashrc`):

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="AIza..."
```

The devcontainer reads these from host env and injects them into the running container. **Never commit keys to the repo.**

---

## 4. First-time setup

1. **Clone the repo and `cd` into it.**

2. **Pick your HuggingFace cache mode** (see §6 for details). The default in `docker-compose.yaml` is the host bind mount → `~/.cache/huggingface`. Make sure the folder exists:
   ```bash
   mkdir -p ~/.cache/huggingface
   ```

3. **Open in VS Code, choose "Reopen in Container"** (or run `Dev Containers: Rebuild and Reopen in Container` from the command palette). On first run this will:
   - Pull `docker.io/rkrispin/python-dev-rag-docker:0.0.3`
   - Pull `chromadb/chroma:1.3.5`
   - Bring up the `python` + `chromadb` services on the `rag-docker` bridge network

4. **Pre-cache the Docling models** so first ingestion isn't slow. Inside the dev container terminal:
   ```bash
   bash docker/cache_models.sh
   ```
   Downloads ~330 MB of layout + table + cross-encoder models into your HuggingFace cache. One-time.

5. **Launch Streamlit:**
   ```bash
   bash clients/run_streamlit.sh
   ```
   VS Code will surface port 8501 in the **Ports** panel; click *Open in Browser*.

---

## 5. Configuration

### `config/settings.yaml`

The single source of truth for provider/chunking/retrieval defaults. Modify, save, restart Streamlit to apply.

```yaml
providers:
  openai:
    api_key_env: "OPENAI_API_KEY"
    models:
      embedding: { name: "text-embedding-3-small", dimensions: 1536 }
      chat:      { name: "gpt-4o", temperature: 0.0, max_tokens: 2048 }
  anthropic: { ... }
  gemini:    { ... }

active:
  embedding_provider: "openai"
  chat_provider: "openai"

chunking:    { method: "recursive", chunk_size: 1000, chunk_overlap: 200, keep_tables_intact: true }
retrieval:   { top_k: 5, rerank: true, rerank_model: "cross-encoder", score_threshold: 0.3 }
chromadb:    { host: "chromadb", port: 8000, collection_name: "financial_reports" }
observability: { enabled: false, provider: "langsmith", project_name: "rag-docker" }
```

The Streamlit sidebar overrides every one of these values at runtime — config is just the boot-time default.

### `.devcontainer/devcontainer.json`

| Section | What it does |
|---|---|
| `dockerComposeFile` | Points at `docker-compose.yaml` |
| `service`, `runServices` | Which compose services to attach to / start |
| `forwardPorts: [8501, 8080]` | Auto-forwards Streamlit + future FastAPI ports to your browser |
| `remoteEnv` | Pulls API keys from your host env using the `key_is_missing` sentinel fallback |
| `mounts` | Persistent zsh history across container rebuilds |
| `customizations.vscode.extensions` | Pre-installs Python, Jupyter, Ruff, YAML, etc. |

### `docker-compose.yaml`

Two services:
- `python` — dev shell that runs notebooks, tests, Streamlit (image `rkrispin/python-dev-rag-docker:0.0.3`)
- `chromadb` — vector database (image `chromadb/chroma:1.3.5`, port 8000)

They share the `rag-docker` bridge network. Env vars flow from `remoteEnv` → compose's `environment:` block → container processes.

---

## 6. HuggingFace cache — two modes

ML libraries (Docling, sentence-transformers) download models on first use. To avoid re-downloading every container restart, the cache is mounted into the container at `/opt/hf-cache` (= `HF_HOME` env var).

The compose file is set up so you can pick between two storage strategies by uncommenting one line and commenting the other.

### Mode A — host bind mount (current default)

```yaml
volumes:
  - .:/workspace:cached
  # - hf-cache:/opt/hf-cache                            # (b) named volume
  - ${HF_HOME:-~/.cache/huggingface}:/opt/hf-cache     # (c) bind mount   ← active
```

Pros: cache visible at `~/.cache/huggingface/hub` in Finder; shared across all your AI projects.
Cons: starts empty on first ever use; baked-in image content is hidden.

### Mode B — named volume

```yaml
volumes:
  hf-cache:                                            # (b) named volume

services:
  python:
    volumes:
      - .:/workspace:cached
      - hf-cache:/opt/hf-cache                         # (b) named volume   ← active
      # - ${HF_HOME:-~/.cache/huggingface}:/opt/hf-cache   # (c) bind mount
```

Pros: auto-populates from image content on first creation; survives `compose down`; portable.
Cons: not visible in Finder (lives in Docker's Linux VM).

### Switching modes

1. Edit `docker-compose.yaml` per the comments above.
2. VS Code → *Dev Containers: Rebuild Container*.
3. If the cache is empty after switching → `bash docker/cache_models.sh` to populate.

### Verifying the cache is populated

```bash
echo $HF_HOME                 # should print /opt/hf-cache
ls /opt/hf-cache/hub          # should show models--ds4sd--* and models--cross-encoder--*
du -sh /opt/hf-cache/hub      # ~330 MB when fully cached
```

---

## 7. Running the Streamlit app

```bash
bash clients/run_streamlit.sh
```

Open `http://localhost:8501` (or use VS Code's Ports panel).

### Mode selector — top of the sidebar

| Mode | When to use |
|---|---|
| **Upload & query (per-session collection)** | Quick analysis of a one-off PDF. Each Streamlit session gets a fresh `streamlit_<uuid>` collection; "Reset session" drops it. |
| **Connect to existing ChromaDB collection** | Query a persistent collection (e.g. `financial_reports` populated by the notebooks). No upload, just chat. |

### Sidebar sections (both modes)

- **Providers & models** — pick OpenAI/Anthropic/Gemini for chat; OpenAI/Gemini for embedding. Temperature & max tokens.
- **Retrieval** — top-K (1–20), rerank method (cross-encoder / none), score threshold (0.0–1.0).

### Sidebar sections (ad-hoc mode only)

- **PDF parsing** — OCR toggle (default off; enable for scanned PDFs), TableFormer toggle (default on; disable for ~3-5× faster parsing of table-heavy docs).
- **Chunking** — method (recursive/semantic/by_title), size, overlap, keep-tables-intact.
- **PDF library** — one-click ingest of any `*.pdf` in `pdf/`.
- **Session** — current collection name, ingested files list (with Remove buttons), Reset button.

### Sidebar sections (existing-collection mode only)

- **ChromaDB collection** — dropdown of available collections, doc/chunk counts, file list preview.

### Typical first-run flow

1. Switch sidebar **Mode** to *Upload & query*.
2. Upload one of the sample PDFs from `pdf/`, OR click **Ingest** next to one in the PDF library.
3. Wait for the staged progress:
   ```
   ▶ Ingesting `form-10-q.pdf`
     1. Parse — Docling, OCR off, table-structure on
        · ...
        N elements in X.Xs
     2. Chunk — recursive, size=1000, overlap=200, keep_tables_intact=True
        N chunks in X.Xs
     3. Embed + store — openai (text-embedding-3-small) → ChromaDB collection ...
        [████████░░░░] 800 / 1342 chunks embedded
     Done — N chunks ingested
   ```
4. Ask a question in the chat input. Expand **Sources** under each answer to see file/page citations.

---

## 8. Running notebooks (alternative path)

```
notebooks/01_pdf_ingestion.ipynb   - parse + chunk demo (no DB write)
notebooks/02_pdf_ingestion.ipynb   - full ingestion into the persistent `financial_reports` collection
notebooks/03_query_the_pdf.ipynb   - query path demo (retrieve → rerank → generate)
```

Run them inside the dev container via VS Code's Jupyter integration. They write to the same ChromaDB instance Streamlit reads from — so notebook-ingested data is queryable in Streamlit's *Connect to existing* mode.

---

## 9. Common operations

### Pre-cache ML models without rebuilding the image
```bash
bash docker/cache_models.sh
```

### Reset the per-session Streamlit collection
Streamlit sidebar → **Session** → *Reset session* button.

### Drop a specific PDF from the session collection
Streamlit sidebar → **Session** → *Remove* button next to the file.

### Wipe everything (including persistent named volume)
```bash
docker compose down -v
```

### Tail Docling logs during ingestion
The dev terminal that's running Streamlit shows Docling's internal per-page progress (enabled by `logging.basicConfig` in the app's `main()`).

### Switch LLM provider mid-session
Sidebar → *Providers & models*. **Chat provider** can be changed anytime. **Embedding provider** is locked once you've ingested data into a session collection (mismatched embedding spaces break retrieval).

### Run tests
```bash
pytest tests/ -v
```

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Bind for 0.0.0.0:8000 failed: port is already allocated` on container start | A previous chromadb container is still running | `docker compose down` from the project folder before re-opening |
| `Failed to ingest: libxcb.so.1: cannot open shared object file` | Missing system lib in the dev image | Inside the container: `apt-get update && apt-get install -y libxcb1` |
| "No relevant information found in the ingested documents" on every query | Score threshold too high for the distance metric of your collection | Lower **Score threshold** in the sidebar to 0.0 to diagnose; the retriever auto-detects metric (cosine vs L2) so old collections still work |
| Models redownload every container restart | Cache mount not pointed at `HF_HOME` | Verify `echo $HF_HOME` prints `/opt/hf-cache` and `ls /opt/hf-cache/hub` is populated. If empty, run `bash docker/cache_models.sh` |
| `echo $HF_HOME` empty after container rebuild | Image doesn't have `ENV HF_HOME` baked in, and compose env var isn't set | Make sure `docker-compose.yaml` has `HF_HOME=/opt/hf-cache` in the python service's `environment:` block |
| First PDF upload very slow ("stuck" on parse stage) | TableFormer per-table inference on CPU | Sidebar → *PDF parsing* → uncheck *Detect table structure (TableFormer)*. ~3-5× faster, loses table cell structure |
| `streamlit.errors.StreamlitAPIException` after editing the app | Hot-reload picked up partial change | Restart Streamlit (Ctrl-C + `bash clients/run_streamlit.sh`) |
| API keys leaked in dev container logs | `docker compose config` interpolates env vars to plaintext | Use `docker compose config --no-interpolate` for inspection. **Rotate any keys** that appeared in logs/screenshots. |

---

## 11. Cross-references

| Topic | Document |
|---|---|
| Original system design + 8-phase plan | `docs/development_plan.md` |
| Where the implementation diverges from the plan | `docs/system_review.md` |
| Docker setup review (this repo) | `docs/docker_review.md` |
| Generic Docker patterns for any AI project | `docs/docker_patterns_for_ai_projects.md` |
| Architecture diagram (drawio) | `docs/rag_system_architecture.drawio` |
