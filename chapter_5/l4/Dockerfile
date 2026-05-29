# Chapter 5 · Lessons 4–5 — the demo image for multi-platform builds & publishing.
#
# Deliberately tiny and dependency-free so a multi-architecture build and a
# registry push are fast and reliable to record. The same buildx / push
# commands apply unchanged to the heavier rag-ingestion image from Lesson 2 —
# see DEMO.md for the note (and the torch/arm64 wheel caveat).
#
# Best practices carried in from earlier lessons: slim base, non-root user.
# Pinning the base by digest (Ch5 L3) would look like:
#   FROM python:3.11-slim@sha256:<digest>

FROM python:3.11-slim

WORKDIR /app
COPY app.py .

# Least privilege — run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

CMD ["python", "app.py"]
