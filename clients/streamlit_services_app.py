"""Streamlit client for the multi-container RAG stack (Chapter 4).

Unlike clients/streamlit_app.py — which imports the rag/ modules and runs the
pipeline in-process — this app is a thin HTTP client. It talks to the two
dedicated services over the network:

    * ingestion service   POST /ingest, GET /ingest/jobs/{id}
    * query service       POST /query,  GET /documents

That decoupling is the point: in Chapter 4 the services run as separate
containers, and this UI exercises them exactly the way any external client
would. Use it to smoke-test the running stack and to drive the end-to-end
ingest -> query flow by hand.

Run it (from the project root):
    bash clients/run_streamlit_services.sh

Point it at the services with env vars (defaults assume published ports on
localhost):
    INGESTION_URL  (default http://localhost:8081)
    QUERY_URL      (default http://localhost:8080)
    RAG_API_KEY    (optional; sent as the X-API-Key header)
"""

from __future__ import annotations

import os
import time

import httpx
import streamlit as st

DEFAULT_INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8081")
DEFAULT_QUERY_URL = os.getenv("QUERY_URL", "http://localhost:8080")
DEFAULT_API_KEY = os.getenv("RAG_API_KEY", "")

POLL_INTERVAL_S = 2
POLL_TIMEOUT_S = 180


# ── HTTP helpers ─────────────────────────────────────────────────────────

def _headers() -> dict[str, str]:
    key = st.session_state.get("api_key", "")
    return {"X-API-Key": key} if key else {}


def _ingestion_url() -> str:
    return st.session_state.get("ingestion_url", DEFAULT_INGESTION_URL).rstrip("/")


def _query_url() -> str:
    return st.session_state.get("query_url", DEFAULT_QUERY_URL).rstrip("/")


def check_health(base_url: str) -> tuple[bool, str]:
    """GET {base}/health. Returns (ok, human-readable detail)."""
    try:
        r = httpx.get(f"{base_url.rstrip('/')}/health", headers=_headers(), timeout=5)
        if r.status_code == 200:
            body = r.json()
            return True, f"{body.get('status', 'ok')} · docs={body.get('documents', '?')}"
        return False, f"HTTP {r.status_code}"
    except httpx.HTTPError as e:
        return False, f"unreachable ({type(e).__name__})"


def start_ingestion(source_dir: str, chunking_method: str, chunk_size: int,
                    chunk_overlap: int, keep_tables_intact: bool) -> str:
    """POST /ingest on the ingestion service. Returns the job_id (202 body)."""
    r = httpx.post(
        f"{_ingestion_url()}/ingest",
        headers=_headers(),
        json={
            "source_dir": source_dir,
            "chunking_method": chunking_method,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "keep_tables_intact": keep_tables_intact,
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["job_id"]


def poll_job(job_id: str) -> dict:
    """GET /ingest/jobs/{id} until the job reaches a terminal state."""
    deadline = POLL_TIMEOUT_S
    elapsed = 0
    while elapsed < deadline:
        r = httpx.get(
            f"{_ingestion_url()}/ingest/jobs/{job_id}",
            headers=_headers(),
            timeout=10,
        )
        r.raise_for_status()
        record = r.json()
        yield record
        if record["status"] in ("completed", "failed"):
            return
        time.sleep(POLL_INTERVAL_S)
        elapsed += POLL_INTERVAL_S


def list_documents() -> list[dict]:
    """GET /documents on the query service."""
    r = httpx.get(f"{_query_url()}/documents", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


def ask(question: str, top_k: int | None = None) -> dict:
    """POST /query on the query service."""
    body: dict = {"question": question}
    if top_k:
        body["top_k"] = top_k
    r = httpx.post(f"{_query_url()}/query", headers=_headers(), json=body, timeout=120)
    r.raise_for_status()
    return r.json()


# ── UI ───────────────────────────────────────────────────────────────────

def init_session_state() -> None:
    ss = st.session_state
    ss.setdefault("ingestion_url", DEFAULT_INGESTION_URL)
    ss.setdefault("query_url", DEFAULT_QUERY_URL)
    ss.setdefault("api_key", DEFAULT_API_KEY)
    ss.setdefault("messages", [])


def render_sidebar() -> None:
    st.sidebar.title("RAG services")

    # ── Connection ───────────────────────────────────────────────
    with st.sidebar.expander("Connection", expanded=True):
        st.session_state.ingestion_url = st.text_input(
            "Ingestion service URL", st.session_state.ingestion_url
        )
        st.session_state.query_url = st.text_input(
            "Query service URL", st.session_state.query_url
        )
        st.session_state.api_key = st.text_input(
            "API key (X-API-Key)", st.session_state.api_key, type="password"
        )
        if st.button("Check health"):
            for label, url in (
                ("ingestion", _ingestion_url()),
                ("query", _query_url()),
            ):
                ok, detail = check_health(url)
                (st.success if ok else st.error)(f"{label}: {detail}")

    # ── Ingestion ────────────────────────────────────────────────
    with st.sidebar.expander("Ingest documents", expanded=True):
        source_dir = st.text_input("Source dir (in ingestion container)", "pdf/")
        method = st.selectbox("Chunking", ["recursive", "semantic", "by_title"])
        size = st.slider("Chunk size", 200, 4000, 1000, 100)
        overlap = st.slider("Chunk overlap", 0, 1000, 200, 50)
        keep_tables = st.checkbox("Keep tables intact", value=True)
        if st.button("Ingest"):
            _run_ingestion(source_dir, method, size, overlap, keep_tables)

    # ── Documents in the store ───────────────────────────────────
    with st.sidebar.expander("Documents in the store"):
        if st.button("Refresh document list"):
            try:
                docs = list_documents()
                if not docs:
                    st.caption("No documents in the collection yet.")
                for d in docs:
                    st.caption(f"· {d['file']} ({d['chunks']} chunks)")
            except httpx.HTTPError as e:
                st.error(f"Could not reach query service: {e}")


def _run_ingestion(source_dir, method, size, overlap, keep_tables) -> None:
    try:
        job_id = start_ingestion(source_dir, method, size, overlap, keep_tables)
    except httpx.HTTPError as e:
        st.sidebar.error(f"Ingestion request failed: {e}")
        return

    with st.status(f"Ingestion job `{job_id}`", expanded=True) as status:
        last = None
        for record in poll_job(job_id):
            last = record
            prog = record.get("progress") or {}
            if prog:
                status.update(
                    label=f"{record['status']} — "
                    f"{prog.get('chunks_done', 0)}/{prog.get('chunks_total', 0)} chunks"
                )
            else:
                status.update(label=f"status: {record['status']}")

        if last and last["status"] == "completed":
            result = last.get("result") or {}
            status.update(
                state="complete",
                label=f"Done — {result.get('documents_ingested', 0)} doc(s), "
                f"{result.get('total_chunks', 0)} chunks",
            )
        else:
            msg = (last or {}).get("error_message", "unknown error")
            status.update(state="error", label=f"Failed — {msg}")


def render_main() -> None:
    st.title("RAG Q&A — multi-service")
    st.caption(
        f"ingestion: `{_ingestion_url()}`  ·  query: `{_query_url()}`  "
        "— this UI talks to both over HTTP."
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                _render_sources(msg.get("sources", []))
                meta = msg.get("metadata")
                if meta:
                    st.caption(
                        f"{meta.get('provider', '')} · `{meta.get('model', '')}` · "
                        f"{meta.get('latency_ms', 0)} ms"
                    )

    question = st.chat_input("Ask a question about the ingested documents...")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Querying the query service..."):
            try:
                result = ask(question)
            except httpx.HTTPError as e:
                err = f"Query failed: {e}"
                st.error(err)
                st.session_state.messages.append(
                    {"role": "assistant", "content": err, "sources": []}
                )
                return

        st.markdown(result["answer"])
        _render_sources(result.get("sources", []))
        meta = result.get("metadata") or {}
        st.caption(
            f"{meta.get('provider', '')} · `{meta.get('model', '')}` · "
            f"{meta.get('latency_ms', 0)} ms"
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result.get("sources", []),
            "metadata": meta,
        })


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for s in sources:
            header = f"**{s.get('file', '?')}** · page {s.get('page', '?')}"
            if s.get("section"):
                header += f" · _{s['section']}_"
            st.markdown(header)
            st.caption(s.get("excerpt", ""))


def main() -> None:
    st.set_page_config(page_title="RAG services", page_icon=":link:", layout="wide")
    init_session_state()
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
