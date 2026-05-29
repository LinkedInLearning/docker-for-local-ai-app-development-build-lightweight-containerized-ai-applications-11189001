# Chapter 5 · Lesson 2 — Multi-Stage Build Demo Runbook

> Recording guide for the multi-stage build demo. The full lesson
> `README.md` / `script_c5_l2.md` / `slides_c5_l2.html` are authored separately;
> this file is the hands-on steps to run on screen.

Demo asset files in this folder:

| File | Role |
| ---- | ---- |
| `Dockerfile_Ingestion.singlestage` | the "before" — toolchain + cache shipped |
| `Dockerfile_Ingestion` | the "after" — multi-stage, slim, non-root |
| `requirements-ingestion.txt` | the heavy ingestion dependency set |
| `.dockerignore` | keeps the build context lean (new to the repo) |
| `ingest_cli.py` | runnable entry point (parse + chunk, offline) |

All commands run from the **repository root** (the build context must contain
`rag/`).

## 1. Build the single-stage image (the "before")

```bash
docker build -f chapter_5/l2/Dockerfile_Ingestion.singlestage \
  -t rag-ingestion:single .
```

## 2. Build the multi-stage image (the "after")

```bash
docker build -f chapter_5/l2/Dockerfile_Ingestion \
  -t rag-ingestion:multi .
```

## 3. Show the payoff — compare sizes

```bash
docker images rag-ingestion
# The :multi tag is smaller: build-essential and the pip cache live only in the
# discarded builder stage. Use `docker history rag-ingestion:single` to point at
# the toolchain layer that :multi never carries.
```

## 4. Prove the slim runtime image actually works

```bash
# Default --check: imports the stack inside the container, prints versions.
docker run --rm rag-ingestion:multi

# Real work, fully offline (no API key, no ChromaDB): parse + chunk a PDF.
docker run --rm -v "$PWD/pdf:/app/pdf" rag-ingestion:multi --pdf pdf/form-10-q.pdf
```

## 5. Show it runs as non-root (least privilege)

```bash
docker run --rm rag-ingestion:multi sh -c 'id'
# uid=10001(appuser) — not root.
```

## Talking points while recording

- The builder stage is **thrown away** — its compiler toolchain and pip cache
  never reach the shipped image.
- The runtime stage copies one thing: the finished `/opt/venv`.
- Same dependencies, smaller + safer image, and it still does real work.
- `.dockerignore`, slim base, non-root user, and "no secrets baked in" are the
  best practices carried in from the rest of the chapter.
