"""Streamlit UI for uploading PDFs and querying them via the rag/ pipeline.

Run inside the dev container:
    streamlit run clients/streamlit_app.py --server.address 0.0.0.0 --server.port 8501

VS Code's dev container will auto-forward port 8501 to the host browser.
"""

from __future__ import annotations

import logging
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chromadb
import streamlit as st

from rag.config import Settings, load_config
from rag.ingestion.chunker import chunk_elements
from rag.ingestion.embedder import get_embedder
from rag.ingestion.pdf_parser import parse_pdf
from rag.retrieval.chain import query_rag
from rag.store import ChromaStore

PDF_LIBRARY_DIR = ROOT / "pdf"
CHUNKING_METHODS = ["recursive", "semantic", "by_title"]
RERANK_METHODS = ["cross-encoder", "none"]

MODE_AD_HOC = "ad_hoc"
MODE_EXISTING = "existing"
MODE_LABELS = {
    MODE_AD_HOC: "Upload & query (per-session collection)",
    MODE_EXISTING: "Connect to existing ChromaDB collection",
}


def _load_config_or_stop() -> Settings:
    try:
        return load_config()
    except FileNotFoundError as e:
        st.error(
            f"Config file not found: {e}. "
            "Create `config/settings.yaml` (see docs/development_plan.md §5.1)."
        )
        st.stop()


def _collection_names(client) -> list[str]:
    """Return sorted collection names from a ChromaDB client.

    Robust across ChromaDB versions: ``list_collections()`` returns name
    strings in some releases and ``Collection`` objects in others (which
    aren't orderable, so ``sorted()`` on them raises). Normalize to names
    before sorting.
    """
    names = [
        c if isinstance(c, str) else c.name
        for c in client.list_collections()
    ]
    return sorted(names)


def list_chromadb_collections(config: Settings) -> list[str]:
    """Return names of all collections currently on the ChromaDB server."""
    client = chromadb.HttpClient(
        host=config.chromadb.host, port=config.chromadb.port
    )
    return _collection_names(client)


@st.cache_data(show_spinner=False, ttl=60)
def summarize_chromadb(host: str, port: int) -> dict[str, list[dict]]:
    """Summarize what is already stored in ChromaDB and ready to query.

    Returns a mapping of ``collection_name -> [{file, label, chunks}, ...]``,
    aggregating chunks by their ``source_file`` metadata so each document
    shows the file it was loaded from and its human-friendly label.

    Cached (short TTL) because it runs on every rerun; call
    ``summarize_chromadb.clear()`` after ingesting/removing data.
    """
    client = chromadb.HttpClient(host=host, port=port)
    summary: dict[str, list[dict]] = {}
    for name in _collection_names(client):
        collection = client.get_collection(name)
        total = collection.count()

        docs: dict[str, dict] = {}
        for offset in range(0, total, 100):
            batch = collection.get(
                include=["metadatas"], limit=100, offset=offset
            )
            for meta in batch["metadatas"]:
                source = (meta or {}).get("source_file", "unknown")
                if source not in docs:
                    docs[source] = {
                        "file": source,
                        "label": (meta or {}).get("label", ""),
                        "chunks": 0,
                    }
                docs[source]["chunks"] += 1
        summary[name] = list(docs.values())
    return summary




def init_session_state(base_config: Settings) -> None:
    ss = st.session_state
    if "session_id" not in ss:
        ss.session_id = uuid.uuid4().hex[:12]
    if "mode" not in ss:
        ss.mode = MODE_AD_HOC
    if "existing_collection" not in ss:
        ss.existing_collection = None
    if "messages" not in ss:
        ss.messages = []
    if "ingested_files" not in ss:
        ss.ingested_files = {}
    if "config_overrides" not in ss:
        chat_model = base_config.providers[
            base_config.active.chat_provider
        ].models.chat
        ss.config_overrides = {
            "embedding_provider": base_config.active.embedding_provider,
            "chat_provider": base_config.active.chat_provider,
            "temperature": (
                chat_model.temperature
                if chat_model and chat_model.temperature is not None
                else 0.0
            ),
            "max_tokens": (
                chat_model.max_tokens
                if chat_model and chat_model.max_tokens
                else 2048
            ),
            "chunking_method": base_config.chunking.method,
            "chunk_size": base_config.chunking.chunk_size,
            "chunk_overlap": base_config.chunking.chunk_overlap,
            "keep_tables_intact": base_config.chunking.keep_tables_intact,
            "do_ocr": False,
            "do_table_structure": True,
            "top_k": base_config.retrieval.top_k,
            "score_threshold": base_config.retrieval.score_threshold,
            "rerank_method": (
                base_config.retrieval.rerank_model
                if base_config.retrieval.rerank
                else "none"
            ),
        }


def session_collection_name() -> str:
    if st.session_state.mode == MODE_EXISTING:
        return (
            st.session_state.existing_collection
            or "financial_reports"
        )
    return f"streamlit_{st.session_state.session_id}"


def build_session_config() -> Settings:
    config = load_config()
    ov = st.session_state.config_overrides

    config.active.embedding_provider = ov["embedding_provider"]
    config.active.chat_provider = ov["chat_provider"]
    config.chromadb.collection_name = session_collection_name()

    config.chunking.method = ov["chunking_method"]
    config.chunking.chunk_size = ov["chunk_size"]
    config.chunking.chunk_overlap = ov["chunk_overlap"]
    config.chunking.keep_tables_intact = ov["keep_tables_intact"]

    config.retrieval.top_k = ov["top_k"]
    config.retrieval.score_threshold = ov["score_threshold"]
    config.retrieval.rerank = ov["rerank_method"] != "none"
    config.retrieval.rerank_model = ov["rerank_method"]

    chat_model = config.providers[ov["chat_provider"]].models.chat
    if chat_model is not None:
        chat_model.temperature = ov["temperature"]
        chat_model.max_tokens = ov["max_tokens"]

    return config


def reset_session() -> None:
    """Reset chat. In ad-hoc mode, also drops the per-session collection."""
    if st.session_state.mode == MODE_AD_HOC:
        config = build_session_config()
        try:
            client = chromadb.HttpClient(
                host=config.chromadb.host, port=config.chromadb.port
            )
            client.delete_collection(name=session_collection_name())
        except Exception:
            pass
        st.session_state.session_id = uuid.uuid4().hex[:12]
        st.session_state.ingested_files = {}
        summarize_chromadb.clear()  # dropped collection must leave the overview
    st.session_state.messages = []


def ingest_pdf(
    path: Path,
    source_label: str | None = None,
    doc_label: str | None = None,
) -> int:
    config = build_session_config()
    ov = st.session_state.config_overrides
    source_file = source_label or path.name
    # Human-friendly label stored with every chunk; defaults to the file name.
    label = doc_label or source_file
    embed_provider = config.active.embedding_provider
    embed_model_name = config.providers[
        embed_provider
    ].models.embedding.name

    with st.status(f"Ingesting `{source_file}`", expanded=True) as status:
        # Stage 1 — parse
        ocr_label = "OCR on" if ov["do_ocr"] else "OCR off"
        ts_label = (
            "table-structure on"
            if ov["do_table_structure"]
            else "table-structure off"
        )
        status.update(label=f"Parsing PDF ({ocr_label}, {ts_label})...")
        st.write(f"**1. Parse** — Docling, {ocr_label}, {ts_label}")
        t0 = time.time()

        def _on_parse_stage(msg: str) -> None:
            st.write(f"&nbsp;&nbsp;&nbsp;· {msg}")

        elements = parse_pdf(
            path,
            do_ocr=ov["do_ocr"],
            do_table_structure=ov["do_table_structure"],
            status_callback=_on_parse_stage,
        )
        st.write(
            f"&nbsp;&nbsp;&nbsp;{len(elements)} elements in "
            f"{time.time() - t0:.1f}s"
        )

        # Stage 2 — chunk
        status.update(label="Chunking...")
        st.write(
            f"**2. Chunk** — `{config.chunking.method}`, "
            f"size={config.chunking.chunk_size}, "
            f"overlap={config.chunking.chunk_overlap}, "
            f"keep_tables_intact={config.chunking.keep_tables_intact}"
        )
        t0 = time.time()
        chunks = chunk_elements(
            elements,
            method=config.chunking.method,
            chunk_size=config.chunking.chunk_size,
            chunk_overlap=config.chunking.chunk_overlap,
            keep_tables_intact=config.chunking.keep_tables_intact,
        )
        st.write(
            f"&nbsp;&nbsp;&nbsp;{len(chunks)} chunks in "
            f"{time.time() - t0:.1f}s"
        )

        if not chunks:
            status.update(state="error", label="No chunks produced")
            return 0

        # Stage 3 — embed + store (batched, with progress bar)
        status.update(
            label=f"Embedding {len(chunks)} chunks via {embed_provider}..."
        )
        st.write(
            f"**3. Embed + store** — `{embed_provider}` "
            f"(`{embed_model_name}`) → ChromaDB collection "
            f"`{config.chromadb.collection_name}`"
        )
        embedder = get_embedder(config)
        store = ChromaStore(config)

        progress = st.progress(0.0, text="0 / ? chunks embedded")

        def _on_progress(done: int, total: int) -> None:
            progress.progress(
                done / total, text=f"{done} / {total} chunks embedded"
            )

        t0 = time.time()
        n = store.ingest_chunks(
            chunks,
            embedder,
            source_file=source_file,
            label=label,
            progress_callback=_on_progress,
        )
        progress.empty()
        st.write(
            f"&nbsp;&nbsp;&nbsp;{n} vectors stored in "
            f"{time.time() - t0:.1f}s"
        )

        status.update(
            state="complete",
            label=f"Done — {n} chunks ingested from `{source_file}` "
                  f"(label: {label})",
        )
    summarize_chromadb.clear()  # stored-data overview must reflect the new doc
    return n


def remove_source(filename: str) -> None:
    config = build_session_config()
    store = ChromaStore(config)
    store.delete_by_source(filename)
    st.session_state.ingested_files.pop(filename, None)
    summarize_chromadb.clear()  # overview must reflect the removal


def delete_document(collection_name: str, source_file: str) -> int:
    """Delete every chunk of ``source_file`` from a specific collection.

    Targets the given collection by name (independent of the current
    session's collection), so it works for the persistent collections the
    notebooks populate as well as ad-hoc session ones. Returns the number
    of chunks removed.
    """
    config = load_config()
    config.chromadb.collection_name = collection_name
    store = ChromaStore(config)
    deleted = store.count_by_source(source_file)
    store.delete_by_source(source_file)
    # Keep session bookkeeping and the cached overview in sync.
    st.session_state.ingested_files.pop(source_file, None)
    summarize_chromadb.clear()
    return deleted


def delete_collection(collection_name: str) -> None:
    """Delete an entire collection (all documents/vectors) from ChromaDB.

    Removes the whole collection by name — this is irreversible. If the
    current session is connected to this collection, reset that reference.
    """
    config = load_config()
    client = chromadb.HttpClient(
        host=config.chromadb.host, port=config.chromadb.port
    )
    client.delete_collection(name=collection_name)
    # If we just deleted the collection the session was pointed at, clear it.
    if st.session_state.get("existing_collection") == collection_name:
        st.session_state.existing_collection = None
    summarize_chromadb.clear()


def ask(question: str) -> dict:
    config = build_session_config()
    response = query_rag(question=question, config=config)
    md = response.metadata
    return {
        "answer": response.answer,
        "sources": [
            {
                "file": s.file,
                "page": s.page,
                "section": s.section,
                "excerpt": s.excerpt,
            }
            for s in response.sources
        ],
        "provider": md.provider if md else "",
        "model": md.model if md else "",
        "latency_ms": md.latency_ms if md else 0,
    }


def render_sidebar(base_config: Settings) -> None:
    ov = st.session_state.config_overrides
    has_session_data = bool(st.session_state.ingested_files)
    in_existing_mode = st.session_state.mode == MODE_EXISTING

    st.sidebar.title("RAG Settings")

    # ── Mode selector ────────────────────────────────────────────
    mode_label = st.sidebar.radio(
        "Mode",
        options=[MODE_LABELS[MODE_AD_HOC], MODE_LABELS[MODE_EXISTING]],
        index=0 if st.session_state.mode == MODE_AD_HOC else 1,
        help=(
            "**Upload & query**: each Streamlit session gets a fresh, "
            "ephemeral ChromaDB collection. Uploaded PDFs are dropped when "
            "you reset the session.\n\n"
            "**Connect to existing**: query a persistent collection in "
            "your ChromaDB container (the one the notebooks populate)."
        ),
    )
    new_mode = (
        MODE_AD_HOC
        if mode_label == MODE_LABELS[MODE_AD_HOC]
        else MODE_EXISTING
    )
    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        st.rerun()

    st.sidebar.divider()

    # ── Providers & models (shown in both modes) ─────────────────
    with st.sidebar.expander("Providers & models", expanded=True):
        embedding_options = sorted(
            n for n, p in base_config.providers.items()
            if p.models.embedding is not None
        )
        chat_options = sorted(
            n for n, p in base_config.providers.items()
            if p.models.chat is not None
        )

        current_embed = ov["embedding_provider"]
        if not in_existing_mode and has_session_data:
            st.selectbox(
                "Embedding provider",
                embedding_options,
                index=embedding_options.index(current_embed),
                disabled=True,
                help="Reset session to change embedding provider.",
            )
        else:
            ov["embedding_provider"] = st.selectbox(
                "Embedding provider",
                embedding_options,
                index=embedding_options.index(current_embed),
            )
            if in_existing_mode:
                st.caption(
                    ":warning: Pick the same embedding provider that "
                    "populated this collection. Mismatched embeddings "
                    "return irrelevant results."
                )

        ov["chat_provider"] = st.selectbox(
            "Chat provider",
            chat_options,
            index=chat_options.index(ov["chat_provider"]),
        )

        embed_model = base_config.providers[
            ov["embedding_provider"]
        ].models.embedding.name
        chat_model = base_config.providers[
            ov["chat_provider"]
        ].models.chat.name
        st.caption(f"Embedding model: `{embed_model}`")
        st.caption(f"Chat model: `{chat_model}`")

        ov["temperature"] = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=float(ov["temperature"]),
            step=0.05,
        )
        ov["max_tokens"] = st.number_input(
            "Max tokens",
            min_value=128,
            max_value=8192,
            value=int(ov["max_tokens"]),
            step=128,
        )

    # ── Ingestion-only controls (ad-hoc mode) ────────────────────
    if not in_existing_mode:
        with st.sidebar.expander("PDF parsing"):
            ov["do_ocr"] = st.checkbox(
                "Enable OCR",
                value=bool(ov["do_ocr"]),
                help=(
                    "Optical Character Recognition. Only needed for scanned "
                    "PDFs or pages where text is baked into images. Digital "
                    "PDFs (like SEC 10-Q filings) don't need it."
                ),
            )
            ov["do_table_structure"] = st.checkbox(
                "Detect table structure (TableFormer)",
                value=bool(ov["do_table_structure"]),
                help=(
                    "Run Docling's TableFormer model on every table. "
                    "Slow on CPU — ~10–30s per table. Off = tables come "
                    "out as plain text."
                ),
            )

        with st.sidebar.expander("Chunking"):
            ov["chunking_method"] = st.selectbox(
                "Method",
                CHUNKING_METHODS,
                index=CHUNKING_METHODS.index(ov["chunking_method"]),
            )
            ov["chunk_size"] = st.slider(
                "Chunk size",
                min_value=200,
                max_value=4000,
                value=int(ov["chunk_size"]),
                step=100,
            )
            ov["chunk_overlap"] = st.slider(
                "Chunk overlap",
                min_value=0,
                max_value=1000,
                value=int(ov["chunk_overlap"]),
                step=50,
            )
            ov["keep_tables_intact"] = st.checkbox(
                "Keep tables intact",
                value=bool(ov["keep_tables_intact"]),
            )
            if has_session_data:
                st.caption(
                    "Already-ingested chunks aren't re-chunked when "
                    "these change."
                )

    # ── Retrieval (shown in both modes) ──────────────────────────
    with st.sidebar.expander("Retrieval"):
        ov["top_k"] = st.slider(
            "Top-K",
            min_value=1,
            max_value=20,
            value=int(ov["top_k"]),
        )
        ov["rerank_method"] = st.selectbox(
            "Rerank method",
            RERANK_METHODS,
            index=RERANK_METHODS.index(ov["rerank_method"]),
            help="LLM rerank is not implemented yet.",
        )
        ov["score_threshold"] = st.slider(
            "Score threshold",
            min_value=0.0,
            max_value=1.0,
            value=float(ov["score_threshold"]),
            step=0.05,
        )

    # ── Mode-specific bottom section ─────────────────────────────
    if in_existing_mode:
        _render_existing_collection_section(base_config)
    else:
        _render_pdf_library_section()
        _render_session_section()


def _render_existing_collection_section(base_config: Settings) -> None:
    with st.sidebar.expander("ChromaDB collection", expanded=True):
        try:
            collections = list_chromadb_collections(base_config)
        except Exception as e:
            st.error(f"Could not reach ChromaDB at "
                     f"`{base_config.chromadb.host}:{base_config.chromadb.port}`: {e}")
            return

        if not collections:
            st.caption("No collections found on the ChromaDB server.")
            st.caption(
                "Tip: run a notebook (e.g. `notebooks/02_pdf_ingestion.ipynb`) "
                "to populate one, then refresh."
            )
            return

        current = st.session_state.existing_collection
        if current not in collections:
            current = collections[0]
        selected = st.selectbox(
            "Collection",
            collections,
            index=collections.index(current),
        )
        st.session_state.existing_collection = selected

        try:
            config = build_session_config()
            store = ChromaStore(config)
            docs = store.list_documents()
        except Exception as e:
            st.caption(f"Could not load collection info: {e}")
            return

        total_chunks = sum(d["chunks"] for d in docs)
        st.caption(f"**{total_chunks}** vectors across **{len(docs)}** document(s)")
        for d in docs[:15]:
            label = d.get("label") or "—"
            st.caption(f"· {d['file']} · _{label}_ ({d['chunks']} chunks)")
        if len(docs) > 15:
            st.caption(f"… and {len(docs) - 15} more")

        if st.button("Clear chat", key="clear_chat_existing"):
            st.session_state.messages = []
            st.rerun()


def _render_pdf_library_section() -> None:
    with st.sidebar.expander("PDF library"):
        if not PDF_LIBRARY_DIR.exists():
            st.caption("No `pdf/` folder found.")
            return
        pdfs = sorted(PDF_LIBRARY_DIR.glob("*.pdf"))
        if not pdfs:
            st.caption("No PDFs in `pdf/`.")
            return
        for pdf in pdfs:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            already = pdf.name in st.session_state.ingested_files
            st.caption(f"{pdf.name} · {size_mb:.1f} MB")
            doc_label = st.text_input(
                "Label",
                value=pdf.stem,
                key=f"label_{pdf.name}",
                disabled=already,
                help="Human-friendly name stored with the document "
                     "(used for display and metadata filtering).",
            )
            clicked = st.button(
                "Done" if already else "Ingest",
                key=f"ingest_{pdf.name}",
                disabled=already,
            )
            if clicked:
                try:
                    n = ingest_pdf(pdf, doc_label=doc_label or None)
                    st.session_state.ingested_files[pdf.name] = n
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")


def _render_session_section() -> None:
    with st.sidebar.expander("Session", expanded=True):
        st.caption(f"Collection: `{session_collection_name()}`")
        if st.session_state.ingested_files:
            for fname, n in list(st.session_state.ingested_files.items()):
                cols = st.columns([3, 1])
                cols[0].caption(f"{fname} — {n} chunks")
                if cols[1].button("Remove", key=f"remove_{fname}"):
                    remove_source(fname)
                    st.rerun()
        else:
            st.caption("No documents ingested yet.")

        if st.button("Reset session"):
            reset_session()
            st.rerun()


def render_stored_data_overview(base_config: Settings) -> None:
    """Show what is already stored in ChromaDB and ready to query.

    Runs on app load so users immediately see which files were loaded and
    under what label, across every collection on the ChromaDB server.
    """
    with st.expander("📚 Data already available in ChromaDB", expanded=True):
        try:
            summary = summarize_chromadb(
                base_config.chromadb.host, base_config.chromadb.port
            )
        except Exception as e:
            st.warning(
                f"Could not reach ChromaDB at "
                f"`{base_config.chromadb.host}:{base_config.chromadb.port}`: {e}"
            )
            return

        # Only collections that actually hold documents are interesting.
        populated = {name: docs for name, docs in summary.items() if docs}
        if not populated:
            st.caption(
                "No documents stored yet. Ingest a PDF here, or run "
                "`notebooks/01_pdf_ingestion.ipynb` to populate a collection."
            )
            return

        for name, docs in populated.items():
            _render_collection_header(name, docs)
            for d in docs:
                _render_document_row(name, d)


def _render_collection_header(collection_name: str, docs: list[dict]) -> None:
    """Collection title row with a confirm-then-delete control for the whole
    collection (all its documents/vectors)."""
    total_chunks = sum(d["chunks"] for d in docs)
    pending_key = f"confirm_delete_collection::{collection_name}"

    cols = st.columns([8, 2])
    cols[0].markdown(
        f"**`{collection_name}`** — {len(docs)} document(s), "
        f"{total_chunks} chunks"
    )

    if st.session_state.get(pending_key):
        # Second step: confirm or cancel dropping the entire collection.
        cols[0].warning(
            f"Delete the **entire** `{collection_name}` collection "
            f"({total_chunks} chunks)? This cannot be undone."
        )
        c1, c2 = cols[1].columns(2)
        if c1.button("✓", key=f"yes_{pending_key}", help="Confirm delete"):
            delete_collection(collection_name)
            st.session_state.pop(pending_key, None)
            st.toast(f"Deleted collection '{collection_name}'.")
            st.rerun()
        if c2.button("✗", key=f"no_{pending_key}", help="Cancel"):
            st.session_state.pop(pending_key, None)
            st.rerun()
    else:
        # First step: arm the confirmation.
        if cols[1].button(
            "🗑️ Collection",
            key=f"del_{pending_key}",
            help=f"Delete the entire '{collection_name}' collection",
        ):
            st.session_state[pending_key] = True
            st.rerun()


def _render_document_row(collection_name: str, doc: dict) -> None:
    """One document row in the overview, with a confirm-then-delete control."""
    source = doc["file"]
    label = doc.get("label") or "—"
    pending_key = f"confirm_delete::{collection_name}::{source}"

    cols = st.columns([4, 3, 1, 1])
    cols[0].caption(f"📄 {source}")
    cols[1].caption(f"🏷️ {label}")
    cols[2].caption(f"{doc['chunks']} chunks")

    if st.session_state.get(pending_key):
        # Second step: confirm or cancel.
        c1, c2 = cols[3].columns(2)
        if c1.button("✓", key=f"yes_{pending_key}", help="Confirm delete"):
            n = delete_document(collection_name, source)
            st.session_state.pop(pending_key, None)
            st.toast(f"Deleted {n} chunks of '{source}' from '{collection_name}'.")
            st.rerun()
        if c2.button("✗", key=f"no_{pending_key}", help="Cancel"):
            st.session_state.pop(pending_key, None)
            st.rerun()
    else:
        # First step: arm the confirmation.
        if cols[3].button(
            "🗑️",
            key=f"del_{pending_key}",
            help=f"Delete '{source}' from '{collection_name}'",
        ):
            st.session_state[pending_key] = True
            st.rerun()


def render_main() -> None:
    st.title("RAG Q&A")

    in_existing_mode = st.session_state.mode == MODE_EXISTING

    if in_existing_mode:
        collection = st.session_state.existing_collection
        st.caption(
            f"**Connect to existing** mode · "
            f"Collection: `{collection or '<pick one in the sidebar>'}`"
        )
    else:
        st.caption(
            f"**Upload & query** mode · "
            f"Session `{st.session_state.session_id}` · "
            f"{len(st.session_state.ingested_files)} document(s) ingested"
        )

    # What's already stored and ready to query, shown on load.
    render_stored_data_overview(base_config=load_config())

    # Upload widget only in ad-hoc mode
    if not in_existing_mode:
        uploaded = st.file_uploader(
            "Upload a PDF",
            type=["pdf"],
            help=(
                "Each upload is parsed, chunked, embedded, and added to "
                "your per-session collection."
            ),
        )
        if uploaded is not None:
            if uploaded.name in st.session_state.ingested_files:
                st.info(f"`{uploaded.name}` is already in this session.")
            else:
                doc_label = st.text_input(
                    "Label",
                    value=Path(uploaded.name).stem,
                    key=f"upload_label_{uploaded.name}",
                    help="Human-friendly name stored with the document "
                         "(used for display and metadata filtering).",
                )
                if st.button("Ingest", key=f"upload_ingest_{uploaded.name}"):
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp:
                        tmp.write(uploaded.getvalue())
                        tmp_path = Path(tmp.name)
                    try:
                        n = ingest_pdf(
                            tmp_path,
                            source_label=uploaded.name,
                            doc_label=doc_label or None,
                        )
                        st.session_state.ingested_files[uploaded.name] = n
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to ingest: {e}")
                    finally:
                        tmp_path.unlink(missing_ok=True)

    # Chat history (both modes)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(_md(msg["content"]))
            if msg["role"] == "assistant":
                _render_sources(msg.get("sources", []))
                meta = msg.get("metadata")
                if meta:
                    st.caption(
                        f"{meta['provider']} · `{meta['model']}` · "
                        f"{meta['latency_ms']} ms"
                    )

    # Readiness check differs by mode
    if in_existing_mode:
        if not st.session_state.existing_collection:
            st.info(
                "Pick a collection from the **ChromaDB collection** "
                "sidebar to start."
            )
            return
    else:
        if not st.session_state.ingested_files:
            st.info(
                "Upload a PDF or pick one from the **PDF library** "
                "sidebar to start."
            )
            return

    question = st.chat_input("Ask a question about your documents...")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(_md(question))

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = ask(question)
            except Exception as e:
                err = f"Error: {e}"
                st.error(err)
                st.session_state.messages.append(
                    {"role": "assistant", "content": err, "sources": []}
                )
                return

        st.markdown(_md(result["answer"]))
        _render_sources(result["sources"])
        st.caption(
            f"{result['provider']} · `{result['model']}` · "
            f"{result['latency_ms']} ms"
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "metadata": {
                "provider": result["provider"],
                "model": result["model"],
                "latency_ms": result["latency_ms"],
            },
        })


def _md(text: str) -> str:
    """Make free text safe for st.markdown.

    Streamlit renders ``$...$`` as LaTeX math, so dollar amounts in answers
    (e.g. "$25.2 billion ... $71.5 billion") get swallowed into a math span
    and rendered with characters stacked. Escaping ``$`` keeps them literal.
    """
    return (text or "").replace("$", "\\$")


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for s in sources:
            header = f"**{s['file']}** · page {s['page']}"
            if s.get("section"):
                header += f" · _{s['section']}_"
            st.markdown(_md(header))
            st.caption(_md(s["excerpt"]))


def main() -> None:
    st.set_page_config(
        page_title="RAG Q&A",
        page_icon=":page_facing_up:",
        layout="wide",
    )
    # Surface Docling's progress messages in the Streamlit terminal.
    # basicConfig is a no-op if the root logger already has handlers,
    # so this is safe to call on every rerun.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    base_config = _load_config_or_stop()
    init_session_state(base_config)
    render_sidebar(base_config)
    render_main()


if __name__ == "__main__":
    main()
