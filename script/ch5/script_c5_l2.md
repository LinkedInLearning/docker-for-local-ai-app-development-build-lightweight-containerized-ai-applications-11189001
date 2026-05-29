# Chapter 5 — Lesson 2: Slimming Images with Multi-Stage Builds

The first column of the checklist is **size**, and the single biggest lever on it is the **multi-stage build**. We saw the baseline last lesson: the ingestion image is heavy. Let's cut it down.

[CLICK]

Here's the problem. A normal, single-stage image keeps everything the build needed — compilers, build tools, package caches, development headers. None of that runs in production. It's dead weight, and every extra package is more attack surface.

[CLICK]

The idea behind a multi-stage build is simple: use one stage to **build**, and a second, clean stage to **run**. The builder stage installs and compiles; the final stage copies only the finished artifacts and ships those.

[CLICK]

In practice, the builder installs dependencies into an isolated virtual environment, and the runtime stage copies just that environment across:

```dockerfile
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements-ingestion.txt .
RUN pip install -r requirements-ingestion.txt

FROM python:3.11-slim          # clean runtime — no compilers
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY rag/ /app/rag/
```

The compiler toolchain and the pip cache live only in the builder, which is thrown away.

[CLICK]

A few supporting levers multiply the win. Start from a **smaller base** — `slim` instead of the full image, or even a `distroless` base that ships no shell or package manager at all.

[CLICK]

Then **order layers** so the things that change least sit lowest — the cache idea from Chapter 3 — and add a **`.dockerignore`** so junk like `.venv`, `chroma_data/`, and tests never enter the build context. Our repo had none until this chapter.

[CLICK]

The demo makes it concrete: we build the ingestion image two ways and compare.

```bash
docker build -f chapter_5/l2/Dockerfile_Ingestion.singlestage -t rag-ingestion:single .
docker build -f chapter_5/l2/Dockerfile_Ingestion            -t rag-ingestion:multi  .
docker images rag-ingestion
```

Same dependencies, smaller image — and it still does real work.

[CLICK]

One AI-specific note. For our images the torch and Docling layers are the dramatic win. But be careful: model **weights** are *data*, not build output. Don't bake gigabytes of weights into a layer blindly — handle them at runtime, which we'll touch on next lesson.

[CLICK]

So: same dependencies, a smaller and safer image, built by throwing the toolchain away.

Next: locking that image down — security.
