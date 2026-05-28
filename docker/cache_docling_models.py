"""Pre-download Docling layout/TableFormer models and the cross-encoder reranker.

Run at image-build time so the models are baked into the dev image and the
container never has to download them on first ingestion or first query.

Models cache into ``$HF_HOME`` (set in ``Dockerfile_Dev`` to ``/opt/hf-cache``).
"""

from __future__ import annotations

import os
import sys

print(f"HF_HOME = {os.environ.get('HF_HOME', '<unset>')}")
print(f"Python  = {sys.executable}")


def _download_docling_models() -> None:
    """Pre-download Docling layout + TableFormer models.

    Tries the official ``download_models`` helper first, then falls back
    to the ``docling-tools`` CLI. If both fail, raises so the image build
    fails loudly instead of silently shipping un-cached models.
    """
    try:
        from docling.utils.model_downloader import download_models
    except ImportError:
        download_models = None

    if download_models is not None:
        print("Downloading Docling models via docling.utils.model_downloader...")
        download_models()
        print("Docling model download complete.")
        return

    print("download_models() unavailable; trying docling-tools CLI...")
    import subprocess
    subprocess.check_call(["docling-tools", "models", "download"])
    print("docling-tools CLI completed.")


def _download_cross_encoder() -> None:
    """Pre-download the cross-encoder reranker used by retrieval."""
    print("Downloading sentence-transformers cross-encoder...")
    from sentence_transformers import CrossEncoder
    CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    print("Cross-encoder download complete.")


if __name__ == "__main__":
    _download_docling_models()
    _download_cross_encoder()
    print("All models pre-cached.")
