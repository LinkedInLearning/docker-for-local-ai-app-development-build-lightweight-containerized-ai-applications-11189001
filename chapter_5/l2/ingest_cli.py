"""Chapter 5 · Lesson 2 — recordable demo entry point for the ingestion image.

The point of this CLI is to give the multi-stage build something real to run so
the recorded demo proves the slimmed runtime image actually works — not just
that it builds.

Two modes, both chosen so they run with NO API keys and NO vector DB (so the
demo is self-contained and reproducible on any machine):

    python ingest_cli.py --check          # import the stack, print versions
    python ingest_cli.py --pdf pdf/<f>    # parse + chunk a PDF, print counts

`parse_pdf` and `chunk_elements` are fully offline (Docling parsing + text
splitting). Embedding and storage need a provider key and a running ChromaDB,
so they are intentionally left out of the demo path; the dependencies are still
in the image, which is what keeps it honestly "heavy".
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version


def _ver(pkg: str) -> str:
    try:
        return version(pkg)
    except PackageNotFoundError:
        return "not installed"


def check() -> int:
    """Import the ingestion stack and report versions — a build smoke test."""
    import docling  # noqa: F401
    import langchain_text_splitters  # noqa: F401

    # Touch the project pipeline so a broken COPY/import fails loudly here.
    from rag.ingestion import chunk_elements, parse_pdf  # noqa: F401

    print("ingestion runtime OK")
    print(f"  docling                 {_ver('docling')}")
    print(f"  langchain-text-splitters {_ver('langchain-text-splitters')}")
    print(f"  sentence-transformers   {_ver('sentence-transformers')}")
    print(f"  chromadb                {_ver('chromadb')}")
    return 0


def ingest(pdf_path: str) -> int:
    """Run the offline part of the pipeline: parse a PDF, then chunk it."""
    from rag.ingestion import chunk_elements, parse_pdf

    print(f"Parsing {pdf_path} ...")
    elements = parse_pdf(pdf_path, status_callback=lambda m: print(f"  · {m}"))
    chunks = chunk_elements(elements)
    print(
        f"Done: {len(elements)} parsed elements -> {len(chunks)} chunks "
        f"(method=recursive)."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RAG ingestion demo (parse + chunk).")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="Import the stack and print versions (default).",
    )
    group.add_argument(
        "--pdf",
        metavar="PATH",
        help="Parse and chunk this PDF (runs offline, no keys needed).",
    )
    args = parser.parse_args(argv)

    if args.pdf:
        return ingest(args.pdf)
    return check()


if __name__ == "__main__":
    sys.exit(main())
