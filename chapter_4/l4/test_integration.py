"""Chapter 4 · Lesson 4 — end-to-end integration test for the RAG stack.

This is the test a single-container prototype cannot give you: it ingests a
document through ONE service and queries it through ANOTHER, proving the two
containers and the shared vector DB cooperate over the network.

Prerequisites — the stack from Lesson 3 must be running:
    docker compose -f chapter_4/l3/docker-compose.test.yaml up -d --build

Run it from the host (services published on localhost):
    pytest chapter_4/l4/test_integration.py -v

Env overrides: INGESTION_URL, QUERY_URL, RAG_API_KEY, SAMPLE_PDF_DIR.
"""

from __future__ import annotations

import os
import time

import httpx
import pytest

INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8081")
QUERY_URL = os.getenv("QUERY_URL", "http://localhost:8080")
SAMPLE_PDF_DIR = os.getenv("SAMPLE_PDF_DIR", "pdf/")  # reuse an existing PDF

HEADERS = {"X-API-Key": os.getenv("RAG_API_KEY", "dev-key")}
POLL_TIMEOUT_S = 180
POLL_INTERVAL_S = 3


@pytest.fixture(scope="session")
def http() -> httpx.Client:
    with httpx.Client(headers=HEADERS, timeout=30) as client:
        yield client


def test_services_are_healthy(http: httpx.Client) -> None:
    """Both services answer /health before we test the flow."""
    for name, base in (("ingestion", INGESTION_URL), ("query", QUERY_URL)):
        r = http.get(f"{base}/health")
        assert r.status_code == 200, f"{name} unhealthy: {r.status_code}"


def test_ingest_then_query(http: httpx.Client) -> None:
    """Ingest via the ingestion service, then query via the query service.

    The only thing connecting the two is the shared chromadb container —
    so a passing test proves networking + the inter-service contract.
    """
    # 1. Kick off ingestion (202 + job id) on the INGESTION service.
    r = http.post(f"{INGESTION_URL}/ingest", json={"source_dir": SAMPLE_PDF_DIR})
    assert r.status_code == 202, r.text
    job_id = r.json()["job_id"]

    # 2. Poll the job until it completes.
    elapsed = 0
    record = None
    while elapsed < POLL_TIMEOUT_S:
        record = http.get(f"{INGESTION_URL}/ingest/jobs/{job_id}").json()
        if record["status"] in ("completed", "failed"):
            break
        time.sleep(POLL_INTERVAL_S)
        elapsed += POLL_INTERVAL_S

    assert record is not None and record["status"] == "completed", (
        f"ingestion did not complete: {record}"
    )
    assert record["result"]["total_chunks"] > 0

    # 3. Query via the QUERY service — it reads the same chromadb.
    r = http.post(f"{QUERY_URL}/query", json={"question": "What is this document about?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"]
    assert body["sources"], "query returned no sources — DB not shared?"
