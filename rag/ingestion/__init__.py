"""RAG ingestion package.

`embedder` is import-safe everywhere — it carries no Docling dependency — so it
is imported eagerly. The Docling-backed `pdf_parser` and `chunker` symbols are
resolved lazily (PEP 562 ``__getattr__``) so a process without Docling
installed (the lean query image) can ``import rag.ingestion`` for the embedder
alone without triggering a Docling import. Accessing `parse_pdf`, `chunk_elements`,
etc. still works wherever Docling *is* installed.
"""

from rag.ingestion.embedder import embed_documents_batched, get_embedder

__all__ = [
    "get_embedder",
    "embed_documents_batched",
    "parse_pdf",
    "ParsedElement",
    "chunk_elements",
    "Chunk",
]

# Symbol -> submodule that defines it. These submodules import Docling, so they
# are only loaded on first access rather than at package import time.
_LAZY_EXPORTS = {
    "parse_pdf": "rag.ingestion.pdf_parser",
    "ParsedElement": "rag.ingestion.pdf_parser",
    "chunk_elements": "rag.ingestion.chunker",
    "Chunk": "rag.ingestion.chunker",
}


def __getattr__(name: str):
    module_path = _LAZY_EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, name)
