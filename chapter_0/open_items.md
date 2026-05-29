# Open Items & Pending Fixes

> Running log of known gaps, deferred work, and follow-ups across the course.
> Last updated: **2026-05-29**. Newest section first.

---

## Chapter 4 — Testing Multi-Container AI Applications

The lesson content (5 × README + script + slides), the teaching artifacts
(`l2/Dockerfile_*`, `l2/requirements-*.txt`, `l3/docker-compose.test.yaml`,
`l4/test_integration.py`) and the thin HTTP client (`clients/streamlit_services_app.py`)
are written and self-consistent. The items below are what stands between the
chapter's artifacts and a stack that actually boots.

### Blockers (artifacts won't run until these are done)

- [ ] **Route-split refactor not implemented in `rag/`.** The Dockerfiles run
  `uvicorn rag.api.query_app:app` and `rag.api.ingestion_app:app`, but
  `rag/api/` today exposes a **single** app — `rag/api/main.py` (`app` at
  line 100). There is no `query_app.py`, `ingestion_app.py`, or `rag/api/routes/`
  package yet. Per `chapter_4/scope.md` (Decision 1 → Option A) the routes need
  to be extracted into `rag/api/routes/` and wired into two app entrypoints
  before the compose stack can come up.
- [ ] **Live stack never exercised.** Docker daemon was unavailable during the
  build, so `docker compose -f chapter_4/l3/docker-compose.test.yaml config`,
  `... up -d --build`, and `pytest chapter_4/l4/test_integration.py` have **not**
  been run end to end. The decks/READMEs were validated structurally only.

### Verification needed (likely fine, unconfirmed)

- [ ] **Chroma healthcheck probe.** Fixed from `curl` (absent in the
  `chromadb/chroma:1.3.5` image) to a dependency-free Python `urllib.request`
  one-liner. Confirm the `/api/v2/heartbeat` path and that the probe goes
  healthy against the real image once Docker is available.
- [ ] **Requirements splits cover real imports.** `requirements-query.txt` and
  `requirements-ingestion.txt` were authored by service responsibility, not by
  scanning actual imports. Once the two apps exist, confirm each app starts with
  only its own requirements file installed (the whole point of the split is the
  query image carrying no Docling/torch stack).
- [ ] **`config/settings.yaml` works inside the containers.** Both Dockerfiles
  `COPY config/ /app/config/`; confirm the app reads it at the container path
  and that no host-only assumptions leak in.

### Deferred / out of scope (intentional)

- [ ] **Streamlit services client is not containerized.** It runs on the host
  (port 8502) as a thin HTTP client and stays outside the test compose stack.
  Containerizing it is noted as an optional **Chapter 5** extension.

---

## Cross-chapter — chapter-title references (cosmetic)

Tracked in detail in [`naming_convention.md`](naming_convention.md). Older decks
(Ch 1–3) still use informal names — notably **"Docker 101"** for Chapter 2 and
**"Apply to RAG"** for Chapter 3 — instead of the official short forms. The
decks still work; these are polish, fixable when the affected deck is next
touched. Exact files/lines are listed in `naming_convention.md`.

- [ ] `chapter_1/l3/slides_c1_l3.html`, `chapter_1/l4/slides_c1_l4.html` —
  "Docker 101" → "Docker Workflow & Best Practices".
- [ ] `chapter_2/l1/slides_c2_l1.html`, `chapter_2/l6/slides_c2_l6.html` —
  "Docker 101" / "Apply to RAG" → official short forms.
- [ ] `chapter_3/l5/slides_c3_l5.html` — "Testing" → "Testing Multi-Container Apps".
- [ ] Optional prose alignment in `chapter_1/l4/README.md` and
  `chapter_1/l4/script_c1_l4.md`.

---

## How to use this file

When you close an item, check it off (or delete it) and bump the
*Last updated* date. When you discover a new gap, add it under the relevant
chapter with enough context that someone else could action it without you.
