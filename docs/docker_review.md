# Docker Setup Review — `docker-local-ai-11189001`

**Reviewed**: 2026-05-27
**Scope**: `docker/`, `docker-compose.yaml`, `.devcontainer/devcontainer.json`, build scripts
**Reference patterns**: see `docs/docker_patterns_for_ai_projects.md` (Part 1)

This is the actionable subset extracted from the broader patterns document. Color codes:
- 🔴 fix soon (functional risk or confusing failure mode)
- 🟡 fix when convenient (clean-up, optimization)
- 🟢 already good — preserve

---

## Architecture overall — ✅ on the right track

Three-tier strategy is already in place:

| Tier | This repo |
|---|---|
| Base | `docker/Dockerfile_Base` → `rkrispin/python-base:0.0.4` |
| Dev | `docker/Dockerfile_Dev` → `rkrispin/python-dev-rag-docker:0.0.3` |
| Runtime | `docker/Dockerfile_API` (exists, not yet wired into compose) |

The pattern is correct. Issues below are details, not architecture.

---

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
- Final image carries pip + build deps. Easy 200 MB savings with a multi-stage build:
  ```dockerfile
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
- It also `COPY config/ /app/config/` — make sure `config/settings.yaml` is tracked in git so CI builds don't fail.

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
