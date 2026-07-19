# Course Settings — Running with Dev Containers

Throughout this course, you will use tools such as Docker, VS Code, and the
terminal to learn how Docker works and explore the development workflow for
containerized AI applications. A retrieval-augmented generation (RAG)
application serves as the running example for demonstrating these concepts.

This document provides detailed information about the course requirements and
settings, including the local Docker environment, VS Code Dev Container,
environment variables, application configuration, and persistent storage.

---

## 1. Course repository structure

A high-level map of the repository so you know where things live:

```
.
├── rag/              # The RAG library — the heart of the course application
├── clients/          # Streamlit web UIs on top of the rag/ library
├── config/           # settings.yaml — app behavior (models, chunking, retrieval)
├── docker/           # Dockerfiles, build scripts, and pinned requirements
├── notebooks/        # Jupyter notebooks: ingest, query, inspect ChromaDB
├── docs/             # Course documentation
├── pdf/              # Sample financial PDFs (10-Q filings) to ingest
├── chroma_data/      # Local ChromaDB vector store (gitignored, auto-created)
├── chapter_1/ … chapter_5/   # Course lesson materials
├── docker-compose.yaml       # Dev stack: python + chromadb services
└── README.md         # Course overview
```

| Folder / file | What it covers |
| ------------- | -------------- |
| **`rag/`** | The Retrieval-Augmented Generation library — config loading, PDF ingestion, retrieval/reranking, the query chain, the ChromaDB store, the FastAPI service, evaluation, and observability. Organized into `api/`, `ingestion/`, `retrieval/`, `evaluation/`, and `observability/` subpackages. See [`02_rag.md`](02_rag.md). |
| **`clients/`** | Streamlit apps that provide a web UI over the `rag/` library, plus their launch scripts. |
| **`config/`** | Application configuration. Holds `settings.yaml` — the single source of truth for app behavior (see [§5](#5-application-configuration-configsettingsyaml)). |
| **`docker/`** | Everything for building the images: `Dockerfile_Base` / `Dockerfile_Dev` / `Dockerfile_API`, build & install scripts, and the pinned `requirements*.txt`. |
| **`notebooks/`** | Jupyter notebooks that walk through PDF ingestion, querying, and inspecting the ChromaDB collection. |
| **`docs/`** | Course documentation (this folder). |
| **`pdf/`** | Sample financial PDFs (10-Q filings) used as ingestion input. |
| **`chroma_data/`** | The local ChromaDB vector store (bind-mount target). Gitignored and auto-created on first run — see [§6](#6-chromadb-storage--persistence). |
| **`chapter_1/` … `chapter_5/`** | Self-contained course lesson materials (each with per-lesson `l1`, `l2`, … subfolders). They teach the Docker + local-AI concepts used by the application; not needed to run the app. |
| **`docker-compose.yaml`** | Defines the dev stack — the `python` development container and the `chromadb` service (see [§3](#3-launching-the-course-environment)). |
| **`README.md` / `CONTRIBUTING.md` / `LICENSE` / `NOTICE`** | Top-level course overview, contribution guide, and licensing. |

---

## 2. Requirements

| Tool | Purpose | Notes |
| ---- | ------- | ----- |
| **Docker** | Runs the containers | [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS/Windows) or Docker Engine (Linux). Must be running before you open the course repository. |
| **Visual Studio Code** | Editor / host for the dev container | <https://code.visualstudio.com> |
| **Dev Containers extension** | Builds and attaches to the container | `ms-vscode-remote.remote-containers` |

The other VS Code extensions the environment expects (Python, Pylance, Ruff,
Jupyter, YAML, Quarto, Mermaid, …) are installed **automatically inside the
container** — they're listed under `customizations.vscode.extensions` in
`devcontainer.json`, so you don't install them by hand.

> **Internet access on first launch.** The dev image
> (`rkrispin/python-dev-rag-docker`) and the ChromaDB image
> (`chromadb/chroma:1.3.5`) are pulled from registries the first time, and the
> Docling / cross-encoder models are cached into the image. Allow a few minutes
> for the initial build.

---

## 3. Launching the course environment

1. Start Docker (Docker Desktop, or `dockerd` on Linux).
2. Set the required environment variables on your host — see [§4](#4-environment-variables).
3. Open the course repository folder in VS Code.
4. Run **“Dev Containers: Reopen in Container”** (Command Palette, `⌘⇧P` / `Ctrl⇧P`),
   or click **Reopen in Container** when VS Code prompts.

VS Code then uses `docker-compose.yaml` to start two services on the
`rag-docker` bridge network:

- **`python`** — the development container (your workspace is mounted at
  `/workspace`; the container idles on `sleep infinity`).
- **`chromadb`** — the vector database (`chromadb/chroma:1.3.5`), reachable from
  the `python` container by the hostname **`chromadb:8000`** and published to the
  host on `localhost:8000`.

Ports **8501** (Streamlit) and **8080** (query API) are forwarded to your host
(`forwardPorts` in `devcontainer.json`); ChromaDB's **8000** is published by the
compose file.

---

## 4. Environment variables

The app reads provider keys and a few settings from the environment. The
`python` service declares them in `docker-compose.yaml`, and
`devcontainer.json` re-exports them into the container via `remoteEnv`.

### Required

| Variable | Used for |
| -------- | -------- |
| `OPENAI_API_KEY` | Default embedding (`text-embedding-3-small`) **and** chat (`gpt-4o`) provider. Needed for ingestion (embedding) and querying. |

### Optional

| Variable | Used for | Default |
| -------- | -------- | ------- |
| `ANTHROPIC_API_KEY` | Alternate chat provider (`claude-sonnet-4`) | — |
| `GEMINI_API_KEY` | Alternate embedding/chat provider (`gemini-2.5-flash`) | — |
| `LANGSMITH_API_KEY` | LangSmith tracing (only if observability is enabled) | — |
| `CHROMA_DATA_PATH` | Host path persisted as the ChromaDB volume | `./chroma_data` |
| `HF_HOME` | Host directory bind-mounted as the Docling / Hugging Face model cache (see [§7](#7-hugging-face--docling-model-cache)) | `~/.cache/huggingface` |
| `RAG_API_KEYS` | Comma-separated API keys the FastAPI services require | — |

> The config loader treats the literal value `key_is_missing` as “unset” — that
> is the placeholder `devcontainer.json` injects when a key isn't found on the
> host, so a missing key fails with a clear error rather than a confusing one.

### How to provide them

**For the VS Code Dev Container (recommended):** export the keys in your
**host** shell before launching VS Code — `devcontainer.json` reads them from
the local environment (`${localEnv:...}`) and passes them into the container:

```bash
# e.g. in ~/.zshrc or ~/.bashrc, then restart VS Code
export OPENAI_API_KEY="sk-...your-key..."
# optional:
export ANTHROPIC_API_KEY="..."
export GEMINI_API_KEY="..."
export CHROMA_DATA_PATH="./chroma_data"
```

**For running `docker compose` directly** (outside VS Code), Docker Compose also
reads a **`.env` file at the repo root** for `${VAR}` substitution. Copy the
template and fill it in:

```bash
cp .env.example .env      # then edit .env (it is gitignored)
```

`.env.example` also documents the FastAPI hardening knobs used by the service
images — `RAG_API_REQUIRE_AUTH`, `RAG_API_MAX_UPLOAD_MB`,
`RAG_API_ALLOWED_UPLOAD_DIR`, `RAG_API_RATE_LIMIT_INGEST` / `_QUERY`, and
`RAG_API_JOB_REGISTRY_SIZE` — all optional, with sane defaults.

---

## 5. Application configuration (`config/settings.yaml`)

Section [§4](#4-environment-variables) covers **secrets and infrastructure**
(provider API keys, where ChromaDB lives). The application's **behavior** — which
models it calls, how it chunks documents, and how it retrieves and reranks — is
driven separately by a single YAML file:
[`config/settings.yaml`](../config/settings.yaml). At startup,
[`rag/config.py`](../rag/config.py) loads and validates it into a typed
`Settings` object, so an invalid or inconsistent file fails fast with a clear
error rather than misbehaving at runtime.

### The `config/` folder

The folder holds exactly one file:

```
config/
└── settings.yaml     # single source of truth for the app's behavior
```

- **One file for every run.** There is no per-environment split
  (`settings.dev.yaml` / `settings.prod.yaml`); the few values that legitimately
  differ between machines are read from the environment instead (see
  [environment overrides](#environment-overrides) below).
- **No secrets live here.** The file only names the *environment variable* that
  holds each provider key (`api_key_env`), never the key itself — so it is safe
  to commit.
- **Relocatable.** Set `RAG_CONFIG_PATH` to point the loader at a different file;
  it defaults to `config/settings.yaml` at the repo root.

### Structure of `settings.yaml`

The file has six top-level sections:

| Section | Purpose |
| ------- | ------- |
| `providers` | Per-provider model catalog and the env var holding its API key. |
| `active` | Which provider is currently used for embedding and for chat. |
| `chunking` | How parsed documents are split before embedding. |
| `retrieval` | How many chunks to retrieve and whether/how to rerank them. |
| `chromadb` | How to reach the vector store and which collection to use. |
| `observability` | Optional tracing (LangSmith). |

#### `providers`

A map of provider name → configuration. Each entry names the env var that
supplies its key (`api_key_env`) and lists the models it offers under
`models.embedding` and/or `models.chat`:

```yaml
providers:
  openai:
    api_key_env: "OPENAI_API_KEY"
    models:
      embedding:
        name: "text-embedding-3-small"
        dimensions: 1536
      chat:
        name: "gpt-4o"
        temperature: 0.0
        max_tokens: 2048
```

Per-model fields: `name` (required), plus optional `dimensions` (embedding
models), `temperature`, and `max_tokens` (chat models). The shipped file defines
`openai` (embedding + chat), `anthropic` (chat only), and `gemini`
(embedding + chat).

#### `active`

Selects which configured provider is live for each role:

```yaml
active:
  embedding_provider: "openai"
  chat_provider: "openai"
```

These are validated on load: the named provider must exist under `providers`
**and** define the required model (an `active.embedding_provider` must have an
`embedding` model; an `active.chat_provider` must have a `chat` model), otherwise
loading raises an error. This is how you switch providers — e.g. set
`chat_provider: "anthropic"` to answer with Claude while still embedding with
OpenAI.

#### `chunking`

| Field | Default | Notes |
| ----- | ------- | ----- |
| `method` | `recursive` | One of `recursive`, `semantic`, `by_title` (validated). |
| `chunk_size` | `1000` | Target chunk size. |
| `chunk_overlap` | `200` | Overlap between adjacent chunks. |
| `keep_tables_intact` | `true` | Avoid splitting tables across chunks. |

#### `retrieval`

| Field | Default | Notes |
| ----- | ------- | ----- |
| `top_k` | `5` | Number of chunks retrieved per query. |
| `rerank` | `true` | Whether to rerank retrieved chunks. |
| `rerank_model` | `cross-encoder` | Reranker to use. |
| `score_threshold` | `0.3` | Minimum similarity score to keep a chunk. |

#### `chromadb`

| Field | Default | Notes |
| ----- | ------- | ----- |
| `host` | `chromadb` | Service name on the compose network. |
| `port` | `8000` | ChromaDB port. |
| `collection_name` | `financial_reports` | Collection the app reads/writes. |

#### `observability`

| Field | Default | Notes |
| ----- | ------- | ----- |
| `enabled` | `false` | Turn tracing on/off. |
| `provider` | `langsmith` | Tracing backend. |
| `project_name` | `rag-docker` | Tracing name reported to the backend. |

When `enabled: true`, tracing also needs `LANGSMITH_API_KEY` in the environment
(see [§4](#4-environment-variables)).

### Environment overrides

Every section other than the two below is taken verbatim from the YAML. The
ChromaDB **location** is the exception: so the container / Compose can be the
source of truth for where the database lives (12-factor), `rag/config.py`
applies these overrides *after* loading, falling back to the YAML when unset:

| Variable | Overrides | Notes |
| -------- | --------- | ----- |
| `CHROMA_HOST` | `chromadb.host` | Used as-is when set. |
| `CHROMA_PORT` | `chromadb.port` | Must be an integer, or loading fails. |

Note these differ from `CHROMA_DATA_PATH` in [§6](#6-chromadb-storage--persistence),
which sets the *host storage folder* rather than the connection target.

---

## 6. ChromaDB storage & persistence

The `chromadb` service persists the vector database to a folder on your host
via a **bind mount**, so ingested data survives container restarts and
`docker compose down` (in `docker-compose.yaml`):

```yaml
  chromadb:
    image: chromadb/chroma:1.3.5
    ports:
      - 8000:8000
    volumes:
      - ${CHROMA_DATA_PATH:-./chroma_data}:/chroma/chroma   # host : container
    environment:
      - ANONYMIZED_TELEMETRY=false
```

- **Container side (`/chroma/chroma`)** — ChromaDB's own persistence directory;
  leave it as-is.
- **Host side (`${CHROMA_DATA_PATH:-./chroma_data}`)** — the folder on your
  machine that holds the data files. It defaults to **`./chroma_data`** (relative
  to the repo root, where you run `docker compose`) and can point anywhere by
  setting `CHROMA_DATA_PATH`.

**Setting the path** — the same two mechanisms as the other variables (§4):

```bash
# Option A — export on the host (used by compose and the Dev Container)
export CHROMA_DATA_PATH="./chroma_data"        # or absolute, e.g. /data/rag-chroma

# Option B — set it in the repo-root .env (for direct `docker compose`)
echo 'CHROMA_DATA_PATH=./chroma_data' >> .env
```

Notes:

- The folder is created automatically on first run; `chroma_data/` is gitignored,
  so your local vectors are never committed.
- A **relative** path resolves against the directory containing the Compose
  file (the repo root for the dev `docker-compose.yaml`). Use an **absolute**
  path to keep the store outside the repo, share it across repositories, or put
  it on a larger disk.
- Inside the app, services reach the database by service name **`chromadb:8000`**
  (see `config/settings.yaml`); from your host it's on `localhost:8000`.
- **Resetting the database:** because this is a *bind mount* (not a named
  volume), `docker compose down -v` does **not** erase it — delete the host
  folder instead (`rm -rf ./chroma_data`, or your `CHROMA_DATA_PATH`), then bring
  the stack back up.

> The Chapter 4 test stack (`chapter_4/l3/docker-compose.test.yaml`) uses the
> same pattern with its own `chapter_4/l3/chroma_data` folder, so its data is
> independent of the dev database here.

---

## 7. Hugging Face / Docling model cache

Ingestion uses **Docling** (layout + TableFormer models) to parse PDFs, and
retrieval uses a **cross-encoder reranker** — both downloaded from Hugging Face
(~330 MB total). To avoid re-downloading them on every container rebuild, the
cache lives on your **host** and is bind-mounted into the container.

Two settings work together (both in `docker-compose.yaml`, `python` service):

```yaml
    volumes:
      - ${HF_HOME:-~/.cache/huggingface}:/opt/hf-cache   # host : container
    environment:
      - HF_HOME=/opt/hf-cache
```

- **`HF_HOME` on the host** (the bind-mount source) — the folder on *your machine*
  that stores the models. Defaults to `~/.cache/huggingface`; override it (e.g.
  to relocate the cache to a larger disk) by exporting `HF_HOME` on the host or
  setting it in `.env` **before** launching:

  ```bash
  # Option A — export on the host (used by compose and the Dev Container)
  export HF_HOME="~/.cache/huggingface"      # or absolute, e.g. /data/hf-cache

  # Option B — set it in the repo-root .env (for direct `docker compose`)
  echo 'HF_HOME=~/.cache/huggingface' >> .env
  ```

- **`HF_HOME=/opt/hf-cache` in the container** (the `environment:` entry) — tells
  Docling / Hugging Face where the cache lives *inside* the container, and must
  match the mount target. Setting it here makes the layout work even if the image
  wasn't built with `ENV HF_HOME=/opt/hf-cache` (e.g. a pre-built `0.0.3` image
  pulled from Docker Hub). **Leave this as-is** — only the host side is meant to
  be customized.

Because the cache is a bind mount, the models **persist across
`docker compose down` / `up`** and are shared with any other environment using
the same host folder.

### Pre-warming the cache

The dev image caches the models at build time. If you're on a pre-built image (or
want to fetch them explicitly), run this **inside the container** once — it
downloads the Docling and cross-encoder models into `$HF_HOME` so the first
ingestion and first query don't stall:

```bash
bash docker/cache_models.sh
```

---

## 8. Verifying the environment

Once the container is up, from a terminal **inside** it:

```bash
# ChromaDB is reachable by service name
python -c "import urllib.request; print(urllib.request.urlopen('http://chromadb:8000/api/v2/heartbeat').status)"   # -> 200

# the provider key made it in (prints nothing sensitive)
python -c "import os; print('OPENAI_API_KEY set:', bool(os.environ.get('OPENAI_API_KEY')) and os.environ['OPENAI_API_KEY'] != 'key_is_missing')"
```

From here you can use the library directly — see [`02_rag.md`](02_rag.md) for the
system overview and [`03_rag_cli.md`](03_rag_cli.md) for command-line ingest/query examples.
