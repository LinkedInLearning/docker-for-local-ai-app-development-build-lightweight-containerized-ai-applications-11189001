# RAG API — Production Roadmap

Assessment of the current ingestion pipeline + a phased plan for taking the FastAPI service from "course demo" to "real users."

**Audience**: future-you planning the next sprint.
**Scope**: the `rag/` engine + `rag/api/` FastAPI service + `docker-compose.yaml` topology.
**Companion docs**: see `docs/overview.md` (current behavior), `docs/system_review.md` (architecture audit), `docs/docker_review.md` (container critique).

---

## 1. Where the ingestion pipeline stands today

### Works well for a single-user demo / course

- **Stage separation is clean**: `parse → chunk → embed → store`. Each stage has its own module, typed data classes (`ParsedElement`, `Chunk`, `RetrievedChunk`), and is independently testable.
- **Configurable at every step** — chunking method/size, OCR on/off, table-structure on/off, batch size, score threshold, rerank method, top-K.
- **Progress observability** — `parse_pdf` and `ChromaStore.ingest_chunks` both accept callbacks; Streamlit uses them for the staged status box.
- **Idempotent** — deterministic SHA-256 chunk IDs from `(source_file, index, content_prefix)`. Re-ingesting the same PDF upserts the same rows.
- **Multi-provider embedding** (OpenAI / Gemini) via `get_embedder(config)`; chat across OpenAI / Anthropic / Gemini via `_get_chat_llm(config, provider)`.

### Fixes that landed recently in this codebase

- Score formula auto-adapts to ChromaDB's distance metric (cosine vs. squared L2) — fixed the "no relevant info found" bug.
- New collections default to `hnsw:space=cosine`.
- HF model cache wired correctly (`HF_HOME=/opt/hf-cache` in compose + bind/named-volume options).
- OCR off by default — digital PDFs don't need it.
- Per-stage Streamlit status with elapsed-time output.

### Functional gaps that hurt even today

- `retrieve()` instantiates a fresh `ChromaStore` and `Embedder` on every query — wasteful (~50–200 ms per call). `rag/api/dependencies.py` has `@lru_cache` singletons, but `rag/retrieval/retriever.py` ignores them.
- `query_rag()` has a confusing precedence — per-call `rerank_method` only applies if `config.retrieval.rerank` is true globally.
- No content-based change detection: if a PDF gets updated, old chunks aren't auto-removed.
- `ChromaStore.ingest_chunks` only batches embeddings when a callback is passed; without it, the whole batch goes in one call (rate-limit risk on big PDFs).
- No streaming PDF parse — Docling loads the entire document into memory. A 500-page PDF can OOM the container.

---

## 2. What "production-ready" requires

Grouped by what needs to be true *before users hit it*, vs. things you can defer.

### 🔴 Tier 1 — must fix before any external user

| # | Gap | Why critical |
|---|---|---|
| 1 | `/ingest` is **synchronous** — blocks the request thread for 1–5 min per 10-Q | HTTP clients time out; load balancer kills the request. Block one user → block all of them with the same uvicorn worker. |
| 2 | **No authentication** on any endpoint | Anyone with network access can ingest, query, delete documents, and inspect config. |
| 3 | **No file size / rate limits** on `/ingest` | Single 500 MB PDF upload can OOM your container; a script can spend your OpenAI budget in minutes. |
| 4 | **Path-traversal check is narrow** — `/ingest` only blocks outside the project root, but inside the project root anything goes | Trivially leak `config/settings.yaml` via a malicious `source_dir`. |
| 5 | **Errors leak internals** — `raise HTTPException(detail=f"Query failed: {str(e)}")` returns full exception chains to clients | Information disclosure (stack frames, file paths, library versions). |
| 6 | **API runs inside the dev container** (not its own image) | Shipping Jupyter + pytest + ruff + 6 GB of dev tools to production. Slow cold starts, larger attack surface. |

### 🟡 Tier 2 — fix before you cross ~10 concurrent users

| # | Gap | Why important |
|---|---|---|
| 7 | **Single shared collection** (`financial_reports`) — no per-tenant isolation | Customer A's docs are visible to customer B's queries. |
| 8 | **No retry on transient failures** — OpenAI 429? Whole ingestion fails | One flaky network blip wastes 5 min of compute. |
| 9 | **No streaming chat responses** — `query_rag` blocks until full LLM response | 5-second perceived latency vs. 200ms first-token with SSE streaming. |
| 10 | **`get_config()` is `lru_cache`d** — changing `settings.yaml` requires restart | Can't rotate API keys, toggle rerank, or swap providers without downtime. |
| 11 | **No observability beyond logs** — no Prometheus metrics, no distributed tracing, no error tracking | When latency spikes at 3 AM you have nothing to look at. |
| 12 | **Cross-encoder loaded per-worker** | With 4 uvicorn workers, you've got 4 × 80 MB of model in RAM and 4× the cold-start cost. Move to a shared model server or a sidecar. |

### 🟢 Tier 3 — for scale / polish

- **Idempotency keys on `/ingest`** so clients can safely retry without double-processing.
- **Webhook callbacks** on ingestion completion (since the operation is async).
- **Multi-document comparison endpoint** — currently you can only query the union; users want "compare these two specific filings".
- **Cost tracking** — token-in/token-out per request, surfaced in response metadata.
- **Connection pooling** for ChromaDB client.
- **Backup strategy** for ChromaDB.
- **Multi-arch image scanning** in CI (`trivy`).

---

## 3. Recommended order of work — 4-week sequence

Assuming one engineer.

### Week 1 — split the API out + add the basics

1. Wire `Dockerfile_API` into `docker-compose.yaml` as its own `api` service (already half-done in `docs/development_plan.md` Roadmap item 1).
2. Move `/ingest` to a **background task** (FastAPI `BackgroundTasks` for v1, swap to Celery / RQ if you need real durability later). Return `202 Accepted` with a job ID; add `GET /ingest/{job_id}` to poll status.
3. Add **API key auth** middleware. Simplest viable: `X-API-Key` header → check against a `.env`-loaded set. Upgrade to JWTs / OAuth later.
4. Add `slowapi` for per-IP rate limiting on `/ingest` and `/query`.
5. Enforce a `MAX_UPLOAD_SIZE_MB` config bound.
6. Stop returning raw exception strings — log them server-side, return a request ID to the client.

### Week 2 — multi-tenancy + observability

7. Add a `tenant_id` concept (header, JWT claim, whatever fits your auth model). Use it as the collection name: `f"{tenant_id}__financial_reports"`. Existing single-tenant code becomes a special case (`tenant_id="default"`).
8. Add **Prometheus middleware** (`prometheus-fastapi-instrumentator`) for latency / error rate per endpoint.
9. Add **OpenTelemetry tracing** — span per pipeline stage. Phoenix is already half-wired; pick a real published tag and turn it back on, OR send to a managed backend (Datadog, Honeycomb, etc.).
10. Add structured request IDs (`X-Request-ID`) that propagate through logs and traces.
11. Add a `GET /metrics` endpoint behind auth.

### Week 3 — query path productionization

12. **Cache the `ChromaStore` and `Embedder`** in `retrieve()` — they're currently re-created every call. Use the same `@lru_cache` singleton pattern as `rag/api/dependencies.py`, or take them as constructor args.
13. **Stream LLM responses** via Server-Sent Events. Add a `/query/stream` endpoint that yields chunks as the LLM generates.
14. Add **retry-with-backoff** around embedding and chat calls (`tenacity` library, exponential jitter).
15. Validate that the cross-encoder isn't a per-worker bottleneck — either pin to one worker per machine, or extract reranking to its own service.

### Week 4 — deployment + reliability

16. Decide deployment target (Cloud Run / GKE / ECS / Fly) and write the manifests.
17. **CI pipeline**: build → scan (`trivy`) → push → deploy to staging on `main`.
18. **ChromaDB backups** — periodic snapshot of the persistent volume to S3/GCS. Without this, a disk failure loses every ingested document.
19. **Health probes**: `/health/live` (basic) + `/health/ready` (depends on ChromaDB heartbeat). Cloud Run / Kubernetes use these to control traffic.
20. **Load test** (`locust` or `k6`) — establish baseline RPS and identify the bottleneck before users do.

---

## 4. What I'd skip (or defer hard)

- **Migrating off ChromaDB** to Pinecone / Weaviate / Qdrant — only if you actually hit ChromaDB limits. Single-machine performance ceiling is real, but ~10k–100k documents is fine for it.
- **Custom reranker** — cross-encoder is the right baseline. Only invest in fine-tuning if your eval metrics demand it.
- **GPU inference** — for embedding and reranking with current model sizes, CPU is fine until you're north of ~50 RPS sustained. The cross-encoder is the bottleneck, not embedding.
- **Vector DB sharding** — until you have evidence it's needed. Premature complexity.

---

## 5. Per-tier acceptance criteria

A way to know you're "done" with each tier.

### Tier 1 (done means: you'd let a friend use this)

- [ ] Ingestion endpoint returns `202` with a job ID in < 200 ms regardless of PDF size.
- [ ] All endpoints reject requests without a valid API key with `401`.
- [ ] Upload of a 1 GB file is rejected with `413` before any disk write.
- [ ] Rate limiting trips at the documented threshold under load.
- [ ] Path-traversal probe against `/ingest` is rejected.
- [ ] An induced exception returns a generic error to the client; the stack trace is in server logs with a matching request ID.
- [ ] The API process is a separate container — `docker compose ps` shows `api`, not `python` running uvicorn.

### Tier 2 (done means: you could onboard a paying customer)

- [ ] Two tenants ingest the same filename — queries from each only see their own data.
- [ ] An OpenAI 429 during ingestion retries up to N times and succeeds; the user sees no error.
- [ ] First token of an LLM response arrives at the client in < 1 s for a well-cached question.
- [ ] Updating `settings.yaml` (e.g. swapping chat model) takes effect on next request.
- [ ] `GET /metrics` exposes p50/p95/p99 latency for `/query` and `/ingest`.
- [ ] A distributed trace shows: receive → auth → retrieve → rerank → generate → respond, with timing per span.

### Tier 3 (done means: comfortable on the front page of HN)

- [ ] Idempotency key on `/ingest` — replay the same request → exactly one ingestion job runs.
- [ ] Ingestion-complete webhook fires reliably (with retry).
- [ ] Cost per query is in the response: tokens in/out, $ estimate.
- [ ] ChromaDB volume is backed up nightly to S3; documented restore procedure works.

---

## 6. Things to fix opportunistically along the way

Small bites that don't fit cleanly in a phase but pay back quickly:

- `query_rag()` rerank-method precedence is confusing — either remove the global gate or document it (`rag/retrieval/chain.py:74`).
- `ChromaStore.ingest_chunks` should always batch when `len(texts) > batch_size`, not just when a callback is provided (`rag/store.py:53`).
- Drop the dead `config = get_config()` in `ingest_documents` (`rag/api/main.py:65`).
- Pick one canonical home for `ChromaStore` — `rag/store.py` or `rag/ingestion/store.py`, not both.
- Pin `chromadb==1.3.5` client-side to match the server (`docker/requirements.txt`, `docker/requirements-api.txt`).
- `Dockerfile_API` should be multi-stage (covered in `docs/docker_review.md` punch list).
