# Command-Line Usage — Ingest & Query

This guide runs the RAG pipeline from the command line **inside the project's
development container**, so you inherit its Python environment, the running
ChromaDB service, and the provider API keys — no local setup or key-passing per
command.

> **Prerequisites**
> - The Dev Container / dev stack is up, and `OPENAI_API_KEY` is set — see
>   [`01_settings.md`](01_settings.md).
> - Run the commands below from the **repo root** on your host.

---

## 1. Get a shell inside the container

The dev service is named `python` in `docker-compose.yaml`. Either use the
**VS Code Dev Container terminal** (already inside the container), or open one
from your host:

```bash
docker compose exec python bash
```

Everything below runs from that shell. It already has:

- the full Python stack (Docling, ChromaDB client, LangChain, …),
- `OPENAI_API_KEY` (and any other keys you exported) in its environment,
- network access to ChromaDB at `chromadb:8000` (from `config/settings.yaml`).

> If `python` isn't on `PATH` in your shell, use the Dev Container interpreter
> explicitly: `/opt/python-3.11-dev/bin/python`.

Quick check that the environment is wired up:

```bash
python -c "import os; print('key set:', os.environ.get('OPENAI_API_KEY','') not in ('','key_is_missing'))"
python -c "import urllib.request; print('chromadb:', urllib.request.urlopen('http://chromadb:8000/api/v2/heartbeat').status)"
```

---

## 2. Check what's already in the database (before)

```bash
python - <<'PY'
from rag.config import load_config
from rag.store import ChromaStore

store = ChromaStore(load_config())
print("total chunks:", store.count())
for d in store.list_documents():
    print(f"  {d['file']}: {d['chunks']} chunks")
PY
```

On a fresh database this prints `total chunks: 0`.

---

## 3. Ingest a PDF

Parse → chunk → embed → store, using the settings from `config/settings.yaml`.
Point `pdf` at any file under the mounted workspace (e.g. `pdf/form-10-q.pdf`):

```bash
python - <<'PY'
from rag.config import load_config
from rag.ingestion import parse_pdf, chunk_elements
from rag.ingestion.embedder import get_embedder
from rag.store import ChromaStore

cfg = load_config()
store = ChromaStore(cfg)
embedder = get_embedder(cfg)

pdf = "pdf/form-10-q.pdf"
elements = parse_pdf(pdf)                       # Docling parse (CPU; can take a bit)
chunks = chunk_elements(
    elements,
    method=cfg.chunking.method,                 # recursive (default)
    chunk_size=cfg.chunking.chunk_size,         # 1000
    chunk_overlap=cfg.chunking.chunk_overlap,   # 200
    keep_tables_intact=cfg.chunking.keep_tables_intact,
)
stored = store.ingest_chunks(chunks, embedder, source_file="form-10-q.pdf")
print(f"parsed {len(elements)} elements -> {len(chunks)} chunks -> stored {stored}")
PY
```

Notes:
- `ingest_chunks` **skips a document that's already stored** (matched by
  `source_file`) and returns `0`. Pass `overwrite=True` to re-embed it.
- `OPENAI_API_KEY` must be set — embedding calls the provider.

**Offline smoke test (no key, no DB).** To just prove parsing/chunking works,
the Chapter 5 demo CLI parses and chunks without embedding or storing:

```bash
python chapter_5/l2/ingest_cli.py --pdf pdf/form-10-q.pdf
```

---

## 4. Confirm it landed (after)

Re-run the check from step 2 — the counts should now be non-zero:

```bash
python - <<'PY'
from rag.config import load_config
from rag.store import ChromaStore

store = ChromaStore(load_config())
print("total chunks:", store.count())
for d in store.list_documents():
    print(f"  {d['file']}: {d['chunks']} chunks")
PY
```

---

## 5. Query the database

`query_rag` embeds the question, retrieves the most similar chunks, reranks
them, and generates a grounded answer with the LLM:

```bash
python - <<'PY'
from rag.config import load_config
from rag.retrieval.chain import query_rag

cfg = load_config()
resp = query_rag("What was the total revenue?", cfg)

print("ANSWER:\n", resp.answer, "\n")
print("SOURCES:")
for s in resp.sources:
    print(f"  - {s.file} p.{s.page} · {s.section}")
print("META:", resp.metadata)
PY
```

### Controlling `top_k`

Retrieval returns the **`top_k`** most similar chunks (default `5`, from
`config/settings.yaml`); those are what the LLM sees and what come back in
`sources`. Raise it per call for more context (more tokens / latency):

```bash
python - <<'PY'
from rag.config import load_config
from rag.retrieval.chain import query_rag

cfg = load_config()
resp = query_rag("What were total revenues for the quarter?", cfg, top_k=15)
print(resp.answer)
print("retrieved:", resp.metadata.retrieval_count if resp.metadata else "n/a")
PY
```

You can also switch the chat model per call with `chat_provider=` (e.g.
`"anthropic"`, `"gemini"`) — provided that provider's key is set. The
**embedding** provider is fixed once data is ingested; changing it requires
re-ingesting.

---

## 6. Where the data lives

Chunks are stored in the ChromaDB collection `financial_reports`, persisted to
the host path in `CHROMA_DATA_PATH` (default `./chroma_data`, mounted into the
`chromadb` container). It survives `docker compose down`/`up`. To list
collections directly, see [`02_rag.md`](02_rag.md) §5 (`ChromaStore`) — or, if you
prefer the HTTP API instead of the library, the curl walkthrough in
`chapter_4/l3/README.md`.
