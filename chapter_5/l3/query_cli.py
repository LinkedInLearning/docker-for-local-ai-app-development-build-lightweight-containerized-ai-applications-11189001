"""Chapter 5 · Lesson 3 — recordable demo entry point for the query image.

The point of this CLI is to give the hardened image something real to run so the
security demo proves the locked-down runtime still works — not just that it
builds. It mirrors the Lesson 2 `ingest_cli.py` style.

Three modes, all chosen so they run with NO API keys and NO vector DB (so the
demo is self-contained and reproducible on any machine):

    python query_cli.py --check          # import the query stack, print versions
    python query_cli.py --whoami         # print the runtime user (prove non-root)
    python query_cli.py --secret-check   # show whether OPENAI_API_KEY is present

`--secret-check` is the security beat: it reports only whether the key is *set*
in the environment (never its value), demonstrating that credentials are
injected at runtime rather than baked into the image.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from importlib.metadata import PackageNotFoundError, version


def _ver(pkg: str) -> str:
    try:
        return version(pkg)
    except PackageNotFoundError:
        return "not installed"


def check() -> int:
    """Import the query stack and report versions — a build smoke test."""
    import chromadb  # noqa: F401

    # Touch the project query pipeline so a broken COPY/import fails loudly here.
    from rag.retrieval import query_rag  # noqa: F401

    print("query runtime OK")
    print(f"  chromadb              {_ver('chromadb')}")
    print(f"  sentence-transformers {_ver('sentence-transformers')}")
    print(f"  langchain-openai      {_ver('langchain-openai')}")
    return 0


def whoami() -> int:
    """Print the runtime user — proves the image runs as a non-root user."""
    try:
        user = getpass.getuser()
    except Exception:
        user = "unknown"
    print(f"running as: {user} (uid={os.getuid()}, gid={os.getgid()})")
    if os.getuid() == 0:
        print("  WARNING: running as root — least privilege not applied.")
    return 0


def secret_check() -> int:
    """Report whether the API key is present, WITHOUT printing its value.

    A baked-in secret would be visible in `docker history`; a runtime-injected
    one shows up here only when you pass `-e OPENAI_API_KEY`.
    """
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        print(f"OPENAI_API_KEY is set (length {len(key)}) — injected at runtime.")
    else:
        print("OPENAI_API_KEY is NOT set — pass it at runtime with -e OPENAI_API_KEY.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RAG query demo (import check + security probes)."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="Import the query stack and print versions (default).",
    )
    group.add_argument(
        "--whoami",
        action="store_true",
        help="Print the runtime user (prove non-root).",
    )
    group.add_argument(
        "--secret-check",
        action="store_true",
        help="Report whether OPENAI_API_KEY is set (never prints its value).",
    )
    args = parser.parse_args(argv)

    if args.whoami:
        return whoami()
    if args.secret_check:
        return secret_check()
    return check()


if __name__ == "__main__":
    sys.exit(main())
