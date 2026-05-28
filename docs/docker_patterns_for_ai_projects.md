# Docker Patterns for AI Application Projects

A reference for building containerized AI/ML applications with multiple services. Written for projects that look like this one — a Python AI/RAG/LLM app with a vector DB, an API, dev tooling, and the eventual goal of splitting into independently-deployable services.

The document has two halves:
- **Part 1** — generic patterns and templates that apply to any future AI project.
- **Part 2** — review of this specific repository (`docker-local-ai-11189001`) against those patterns.

---

# Part 1 — Patterns

## 1. The three-tier image strategy

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 1 — BASE                                              │
│  • OS, system libs, shell tooling, language-version-agnostic│
│  • Changes monthly at most                                  │
│  • Shared across all your AI projects                       │
│  • Example: rkrispin/python-base:0.0.4                      │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ FROM
┌─────────────────────────────────────────────────────────────┐
│  Tier 2 — DEV                                               │
│  • Python venv + project Python deps + dev extras           │
│  • Pre-cached ML models for fast first-run                  │
│  • Includes Jupyter, pytest, ruff, etc.                     │
│  • Changes weekly when requirements move                    │
│  • Example: rkrispin/python-dev-rag-docker:0.0.3            │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ FROM (production split)
┌─────────────────────────────────────────────────────────────┐
│  Tier 3 — RUNTIME (one image per service)                   │
│  • Service-specific: api, worker, ingestor, scheduler...    │
│  • Smallest possible — no dev tools, no notebooks           │
│  • Built from Tier 2 OR from python:slim with only runtime  │
│    deps                                                     │
│  • Changes on every release                                 │
└─────────────────────────────────────────────────────────────┘
```

**Why three tiers, not one:**

| Concern | Tier handling it |
|---|---|
| Slow-changing system libs (curl, fonts, libxcb, OCR libs) | Base — pull once, reuse forever |
| Python deps that move weekly (langchain, openai SDK) | Dev — rebuild Tier 2 only |
| Per-release service code | Runtime — rebuild Tier 3 only |

When `requirements.txt` changes, you do **not** rebuild the system layer. When you bump an OS package, you do **not** invalidate every Python install. This is the entire point of Docker layer caching, and one-tier Dockerfiles throw it away.

### Tier 1 — Base skeleton

```dockerfile
# docker/Dockerfile_Base
FROM ubuntu:22.04

ARG QUARTO_VER="1.7.32"
ENV DEBIAN_FRONTEND=noninteractive

# System packages — split into "always need" vs "AI/ML specific" so
# new projects can drop sections they don't use.
RUN apt-get update && apt-get install -y --no-install-recommends \
        # core CLI
        curl wget git ca-certificates \
        # build
        build-essential \
        # AI / Docling / OpenCV runtime libs (the libxcb1 incident)
        libxcb1 libxext6 libxrender1 libsm6 libglib2.0-0 libgl1-mesa-glx \
        # shell ergonomics (optional — moves to dev image if you want a
        # leaner base)
        zsh fzf \
    && rm -rf /var/lib/apt/lists/*

# Optional language tooling at the OS level (e.g. Quarto for docs)
COPY install_quarto.sh /tmp/
RUN bash /tmp/install_quarto.sh $QUARTO_VER && rm /tmp/install_quarto.sh

LABEL org.opencontainers.image.title="python-base" \
      org.opencontainers.image.description="Ubuntu + system deps for AI projects" \
      org.opencontainers.image.source="https://github.com/<you>/<repo>"
```

**Build it once, tag it semantically, push it. Don't bump on every change to your app.**

### Tier 2 — Dev skeleton

```dockerfile
# docker/Dockerfile_Dev
FROM your-org/python-base:0.0.4

ARG PYTHON_VER="3.11"
ARG VENV_NAME="app-dev"
ENV VENV_NAME=$VENV_NAME
ENV PYTHON_VER=$PYTHON_VER

# All HF / Torch / sentence-transformers caches live in an image-internal
# path so a host bind mount can't accidentally overlay them.
ENV HF_HOME=/opt/hf-cache

# 1) Install uv + create venv (changes rarely)
COPY install_uv.sh /tmp/
RUN bash /tmp/install_uv.sh $VENV_NAME $PYTHON_VER

# 2) Install Python deps (changes often — keep in its own layer so the
#    uv install layer above stays cached)
COPY requirements.txt /tmp/requirements.txt
RUN /opt/$VENV_NAME/bin/uv pip install --no-cache-dir -r /tmp/requirements.txt

# 3) Pre-cache ML models (changes when model versions change)
COPY cache_models.py /tmp/
RUN mkdir -p $HF_HOME && /opt/$VENV_NAME/bin/python /tmp/cache_models.py

# 4) Dev ergonomics (optional, fast)
RUN echo "source /opt/$VENV_NAME/bin/activate" >> /root/.zshrc
```

Order matters: **least-changing layer first** so cache hits as often as possible.

### Tier 3 — Runtime skeleton

```dockerfile
# docker/Dockerfile_API
FROM python:3.11-slim AS builder
WORKDIR /app
COPY docker/requirements-api.txt .
RUN pip wheel --wheel-dir /wheels -r requirements-api.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY rag/ /app/rag/
COPY config/ /app/config/
EXPOSE 8080
CMD ["uvicorn", "rag.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Multi-stage build keeps build tools out of the runtime image. Final image is 200–400 MB instead of 1+ GB.

---

## 2. Multi-service compose layout

For a typical AI app, you'll grow into something like:

```yaml
# docker-compose.yaml
networks:
  app:
    driver: bridge

# Named volumes — persist across `compose down` but can be wiped with
# `compose down -v`. Prefer over bind mounts for state that doesn't need
# to be visible on the host.
volumes:
  vector-db:
  cache:

services:
  # ── Application layer ───────────────────────────────────────
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile_API
    ports: ["8080:8080"]
    depends_on:
      vector-db:
        condition: service_healthy
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks: [app]

  worker:
    build: { context: ., dockerfile: docker/Dockerfile_Worker }
    depends_on:
      vector-db: { condition: service_healthy }
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks: [app]

  # ── Stateful infra ──────────────────────────────────────────
  vector-db:
    image: chromadb/chroma:1.3.5     # pin exactly — never `latest`
    ports: ["8000:8000"]
    volumes:
      - vector-db:/chroma/chroma
    environment: [ANONYMIZED_TELEMETRY=false]
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/api/v2/heartbeat || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks: [app]

  # ── Dev shell (opt-in via profile) ──────────────────────────
  dev:
    image: your-org/python-dev-app:0.0.3
    profiles: [dev]              # only starts with `--profile dev`
    volumes:
      - .:/workspace:cached
    command: sleep infinity
    depends_on:
      vector-db: { condition: service_healthy }
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks: [app]

  # ── Observability (opt-in) ──────────────────────────────────
  tracer:
    image: arizephoenix/phoenix:<pinned-real-tag>
    profiles: [observability]
    ports: ["6006:6006"]
    networks: [app]
```

**Rules:**

| Rule | Why |
|---|---|
| One responsibility per service | Each can scale, restart, and be replaced independently. |
| Pin every image to an exact tag | `:latest` is reproducibility poison. |
| Always define `healthcheck` on stateful services | `depends_on: condition: service_healthy` only works if the target has one. |
| Use compose `profiles:` for opt-in services | Phoenix, monitoring, GPUs, debug tools — gate them so default `up` is fast. |
| Prefer named volumes for service state | `vector-db:` is portable; `./chroma_data:` ties you to a specific working directory. |
| Use bind mounts for code under dev | `.:/workspace` so edits are live in the dev container. |
| Keep ports `127.0.0.1:8000:8000` for dev | Plain `8000:8000` binds to all interfaces — surprising on shared networks. |

---

## 3. AI-specific gotchas

### Model caching — the trap that bit this repo

ML libraries (HuggingFace transformers, sentence-transformers, Docling, spaCy, …) download model weights to a cache directory on first use. This is fine on a long-running machine and **disastrous in containers** because:

1. Default cache (`~/.cache/huggingface`) lives inside the container → wiped on `docker compose down`.
2. Bind-mounting the host's cache solves persistence — but you have to populate it once, and *every developer machine* downloads independently.
3. Pre-baking models into the image solves "first-run download" — but **the bind mount can overlay and hide them**.

**The decision matrix:**

| Strategy | Survives `down` | Same on all machines | Image size hit | Best for |
|---|---|---|---|---|
| Lazy download to default cache | ❌ | ❌ | None | Throwaway notebooks |
| Lazy download + host bind mount | ✅ | ❌ | None | Solo dev with steady connection |
| Lazy download + named volume | ✅ | ❌ | None | Team dev, no host coupling |
| Pre-bake into image at non-overlaid path | ✅ | ✅ | +200 MB to ~2 GB | Production / CI / reproducibility |

**Pre-bake recipe** (the one that works without bind-mount collisions):

```dockerfile
# Use a path that's *not* the default $HOME/.cache/* — so any
# host bind mount on ~/.cache/huggingface won't overlay it.
ENV HF_HOME=/opt/hf-cache

COPY cache_models.py /tmp/
RUN mkdir -p $HF_HOME && python /tmp/cache_models.py
```

```python
# cache_models.py
from docling.utils.model_downloader import download_models
from sentence_transformers import CrossEncoder

download_models()
CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
```

For lazy → named volume (no rebuild) — see the "Runtime cache warming" pattern below.

### GPU access (if you ever need it)

```yaml
services:
  worker:
    image: ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Plus on the host: install NVIDIA Container Toolkit. CPU-only fallback should always work.

### Image bloat

A dev image that includes Torch + CUDA wheels + Jupyter + Docling models is easily 6–10 GB. For runtime services, **always** make a separate slim image (Tier 3) — don't ship Jupyter to production.

### Pre-installed system libs you'll forget

Docling / OpenCV / Pillow / PaddleOCR commonly fail at runtime with `libXxx.so.N: cannot open shared object file`. Whitelist these in your base image upfront:

```
libxcb1 libxext6 libxrender1 libsm6
libglib2.0-0 libgl1-mesa-glx
libxcb-xinerama0 libxcb-cursor0
```

---

## 4. Secrets and configuration

**Tiered approach, from least to most secret:**

```
config/settings.yaml         ← in repo, no secrets, declares which env
                                vars to read for each provider

.env (gitignored)            ← optional, for local convenience
                                docker compose auto-loads it

host shell rc                ← actual values live here
                                (export OPENAI_API_KEY=sk-...)

devcontainer.json remoteEnv  ← reads from host env, falls back to
                                "key_is_missing" sentinel so missing
                                vars surface as a clean error,
                                not garbled traceback

container environment        ← compose passes through:
                                  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

**Hard rules:**

- Never `COPY .env /app/.env` into an image — secrets get baked into a layer that ships to your registry.
- Never `ARG SECRET=...` for a secret — `ARG` values are stored in image metadata.
- For build-time secrets (rare in AI work), use BuildKit `--mount=type=secret`.
- For pulled images, use the registry's secret store (1Password, AWS Secrets Manager, Doppler).
- Always provide a default sentinel (`key_is_missing`) so that a misconfigured environment fails *loudly and at boot*, not silently at first API call.

The pattern in this repo:

```jsonc
// .devcontainer/devcontainer.json
"remoteEnv": {
  "OPENAI_API_KEY": "${localEnv:OPENAI_API_KEY:key_is_missing}"
}
```

```python
# rag/config.py
def resolve_api_key(self, provider_name: str) -> str:
    value = os.environ.get(env_var, "")
    if not value or value == "key_is_missing":
        raise ValueError(f"Environment variable '{env_var}' is not set ...")
    return value
```

That's the pattern. Reuse it.

---

## 5. Dev container integration (VS Code)

For projects with the dev container extension:

```jsonc
// .devcontainer/devcontainer.json
{
    "name": "<project> Dev",
    "dockerComposeFile": ["../docker-compose.yaml"],
    "service": "dev",
    "runServices": ["dev", "vector-db"],
    "shutdownAction": "none",
    "workspaceFolder": "/workspace/",
    "forwardPorts": [8501, 8080],
    "remoteEnv": {
        "OPENAI_API_KEY": "${localEnv:OPENAI_API_KEY:key_is_missing}"
    },
    "postCreateCommand": "bash docker/post_create.sh",
    "customizations": {
        "vscode": {
            "extensions": [...]
        }
    }
}
```

**Notes:**

- `runServices` lists what auto-starts. Keep it minimal — opt-in services (Phoenix, GPUs, etc.) belong in compose `profiles`, not here.
- `forwardPorts` makes the VS Code Ports panel show host-side access.
- `postCreateCommand` runs once per container creation. Good place for runtime cache warming, schema migrations, or `apt-get install` of libs you forgot.
- `mounts` for shell history persistence is a nice touch:
  ```jsonc
  "mounts": ["source=${localEnv:HOME}/.zsh_history_dev,target=/root/.zsh_history,type=bind"]
  ```

---

## 6. Build optimization checklist

When you start a new AI project, copy and check off:

- [ ] `.dockerignore` excludes `chroma_data/`, `__pycache__/`, `*.pyc`, `notebooks/*/outputs`, large data files, `.git/`, `.venv/`. Without this, every build sends 100s of MB of context.
- [ ] Each `COPY` is as narrow as possible (e.g. `COPY pyproject.toml uv.lock /app/`, not `COPY . /app/`).
- [ ] `RUN apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*` in one layer — saves ~50 MB.
- [ ] Runtime images use multi-stage with `--from=builder` to strip wheels/build deps.
- [ ] Pin every image to an exact tag (including `python:3.11-slim` → `python:3.11.10-slim-bookworm`).
- [ ] `LABEL org.opencontainers.image.{title,description,source,version}` for provenance.
- [ ] Build script does NOT auto-push on success without confirmation. Replace `docker push` with a separate `make push`.
- [ ] CI rebuilds the image on every PR and runs `docker scout cves` or `trivy image` against it.
- [ ] Multi-arch (`linux/amd64,linux/arm64`) only if you have Apple Silicon devs and Linux production. Costs 2x build time.

---

## 7. The runtime cache warming pattern

When you don't want to rebuild the image but want to populate caches inside the container *once*, ship a script alongside it:

```bash
# docker/cache_models.sh — runs INSIDE the dev container
#!/usr/bin/env bash
set -euo pipefail
VENV_BIN=/opt/python-3.11-dev/bin

echo "==> Pre-downloading layout + table models..."
"$VENV_BIN/docling-tools" models download

echo "==> Pre-downloading cross-encoder..."
"$VENV_BIN/python" - <<'PY'
from sentence_transformers import CrossEncoder
CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
PY

du -sh "${HF_HOME:-$HOME/.cache/huggingface}/hub" || true
```

Use cases:
- Image is published by someone else and you can't rebuild
- You want bind-mount-based caching on host
- You want different users on the same image to cache different model sets

Prefer build-time baking for production, runtime warming for dev convenience.

---

# Part 2 — Review of this repository

Scored against the patterns above.

## Architecture overall — ✅ on the right track

Three-tier strategy is already in place:

| Tier | This repo |
|---|---|
| Base | `docker/Dockerfile_Base` → `rkrispin/python-base:0.0.4` |
| Dev | `docker/Dockerfile_Dev` → `rkrispin/python-dev-rag-docker:0.0.3` |
| Runtime | `docker/Dockerfile_API` (exists, not yet wired into compose) |

The pattern is correct. Issues below are details, not architecture.

## Findings

### 🔴 Tag drift between build scripts and Dockerfiles
- `docker/build_base_docker.sh` declares `tag=0.0.1`.
- `docker/Dockerfile_Dev` line 1 references `FROM docker.io/rkrispin/python-base:0.0.4`.
- Versions `0.0.2`, `0.0.3`, `0.0.4` were built by hand without updating the script. If a teammate runs `build_base_docker.sh` they'll produce `0.0.1`, which `Dockerfile_Dev` doesn't reference, and silently use a stale cached image.
- **Fix**: bump `build_base_docker.sh` to `tag=0.0.4` (the actual version Dockerfile_Dev needs). Same review for `build_dev_docker.sh` whenever you bump the dev tag.

### 🔴 No `.dockerignore`
- `build_dev_docker.sh` runs `docker buildx build . -f $dockerfile`, sending the entire repo as build context — including `chroma_data/`, `pdf/` (3 MB of PDFs), `notebooks/02_pdf_ingestion.ipynb` (14 MB), `__pycache__/` everywhere, and your `.git/` directory.
- This slows every build and leaks your data into the build cache.
- **Fix**: add `.dockerignore` at repo root:
  ```
  .git/
  .venv/
  __pycache__/
  *.pyc
  chroma_data/
  pdf/
  notebooks/
  docs/
  .vscode/
  .DS_Store
  ```

### 🟡 Layer caching not optimized
- `Dockerfile_Dev` line: `COPY install_uv.sh requirements.txt cache_docling_models.py settings/`. All three files in one COPY → any change invalidates the layer below (`RUN bash install_uv.sh`) even though `install_uv.sh` didn't change.
- **Fix**: split COPYs in order of change frequency.
  ```dockerfile
  COPY install_uv.sh /tmp/
  RUN bash /tmp/install_uv.sh ...
  COPY requirements.txt /tmp/
  RUN /opt/$VENV_NAME/bin/uv pip install -r /tmp/requirements.txt
  COPY cache_docling_models.py /tmp/
  RUN /opt/$VENV_NAME/bin/python /tmp/cache_docling_models.py
  ```

### 🟡 `Dockerfile_API` is not multi-stage
- Final image carries pip + build deps. Easy 200 MB savings with the multi-stage skeleton from §1.
- It also `COPY config/ /app/config/` — but `config/` was added late in the project and may not exist when CI builds. Make sure it's tracked in git.

### 🟡 `requirements.txt` and `requirements-api.txt` drift
- Two parallel lists. `requirements-api.txt` has `langchain-core>=0.3.0`, `requirements.txt` has the full `langchain==1.2.17`. The API will install a different langchain version than the dev image.
- **Fix**: either (a) use `pip-compile` with `requirements-api.in → requirements-api.txt` derived from a constraint file, or (b) flip to `pyproject.toml` with `[project.optional-dependencies]` and have both Dockerfiles install the right extras.

### 🟡 ChromaDB client version floats while server is pinned
- Server: `chromadb/chroma:1.3.5`.
- Client: `chromadb>=1.3.5` in both requirements files.
- On a rebuild that picks up `chromadb 1.4.0`, you could get a wire-format mismatch.
- **Fix**: pin client to `chromadb==1.3.5`.

### 🟡 `HF_HOME=/opt/hf-cache` (image) vs `~/.cache/huggingface` bind mount (compose) — semantic conflict
- Recently added: `Dockerfile_Dev` sets `ENV HF_HOME=/opt/hf-cache`.
- Compose still bind-mounts `${HF_HOME:-~/.cache/huggingface}:/root/.cache/huggingface`.
- Result: the bind mount now targets a path Docling no longer reads from. It's effectively dead but not obvious.
- **Fix**: pick one:
  - If you want models baked into the image → drop the bind mount.
  - If you want host-side caching → drop `ENV HF_HOME` and let the bind mount + default location work.
  - Hybrid: keep `ENV HF_HOME=/opt/hf-cache` and add `- model-cache:/opt/hf-cache` as a named volume so it survives container removal but doesn't depend on host path.

### 🟢 Good things to preserve

- Three-tier image strategy.
- Multi-arch builds in `build_*_docker.sh` (`linux/amd64,linux/arm64`).
- `uv` for fast Python installs.
- `key_is_missing` sentinel pattern for env vars.
- Pre-cache hook (now correctly downloading models) is the right place for the work.
- Dev container `forwardPorts` + `runServices` keep startup predictable.
- The healthcheck pattern (when restored on chromadb) is correct.
- `Dockerfile_API` exists — half the work of splitting services is already done.

### 🟢 Easy upgrades when you get to it

- Add `LABEL org.opencontainers.image.{title,version,source,licenses}` blocks to all three Dockerfiles. Costs nothing, helps tooling (Docker Hub UI, image scanners, dependency dashboards).
- Add a `Makefile` that wraps `docker buildx`, runs `trivy image` after build, and only pushes on explicit `make push`. Cuts down the "I accidentally pushed broken 0.0.2" risk.
- Move `chromadb/chroma:1.3.5` to a named volume (`vector-db: {}`) instead of `./chroma_data` bind. Cleaner, doesn't pollute repo working dir.
- Add the `api` service to compose so the production split path is exercised in dev too (Roadmap item 1 in `docs/development_plan.md`).

---

## Quick fixes ranked by effort/impact

| # | Fix | Effort | Impact |
|---|---|---|---|
| 1 | Add `.dockerignore` | 2 min | Faster builds, no data leakage |
| 2 | Bump `build_base_docker.sh` tag to `0.0.4` | 30 sec | Removes drift trap |
| 3 | Pin `chromadb==1.3.5` client-side | 30 sec | Prevents wire mismatch |
| 4 | Restore `chromadb` healthcheck + `condition: service_healthy` | 2 min | Removes first-run race |
| 5 | Split COPYs in `Dockerfile_Dev` | 5 min | Better cache hit rate |
| 6 | Decide HF cache strategy and align Dockerfile + compose | 5 min | Removes the bind-mount-overlay confusion |
| 7 | Convert `Dockerfile_API` to multi-stage | 15 min | Smaller production image |
| 8 | Add `api` service to compose | 15 min | Validates production split early |
| 9 | Image labels + Makefile wrapper | 30 min | Provenance + push safety |
