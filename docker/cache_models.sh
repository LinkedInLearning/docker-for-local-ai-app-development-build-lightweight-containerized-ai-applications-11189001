#!/usr/bin/env bash
#
# Pre-download Docling models (layout + TableFormer) and the cross-encoder
# reranker into the HuggingFace cache *at runtime*, so the next PDF
# ingestion and the first query don't have to download anything.
#
# Where models land:
#   - Inside the container they go to $HF_HOME (defaults to
#     /root/.cache/huggingface).
#   - The docker-compose bind mount maps that path to the host's
#     ~/.cache/huggingface, so the models persist across
#     `docker compose down` / `up`.
#
# How to use:
#   1. Open a shell in the dev container (VS Code: "Terminal" inside the
#      attached devcontainer, OR from host: `docker compose exec python bash`).
#   2. Run:    bash docker/cache_models.sh
#   3. Wait ~2-5 minutes (depending on connection speed; ~330 MB total).
#   4. Done. Next Streamlit ingestion will skip the download step.

set -euo pipefail

VENV_BIN=/opt/python-3.11-dev/bin

if [[ ! -x "$VENV_BIN/python" ]]; then
    echo "ERROR: expected Python venv at $VENV_BIN — is this running inside the dev container?" >&2
    exit 1
fi

CACHE_DIR="${HF_HOME:-$HOME/.cache/huggingface}"
echo "==> HuggingFace cache target: $CACHE_DIR"
mkdir -p "$CACHE_DIR"

echo ""
echo "==> Pre-downloading Docling layout + TableFormer models..."
if "$VENV_BIN/docling-tools" models download; then
    echo "    Downloaded via docling-tools CLI."
else
    echo "    docling-tools CLI failed; falling back to Python API..."
    "$VENV_BIN/python" -c "from docling.utils.model_downloader import download_models; download_models()"
    echo "    Downloaded via docling.utils.model_downloader."
fi

echo ""
echo "==> Pre-downloading sentence-transformers cross-encoder..."
"$VENV_BIN/python" - <<'PY'
from sentence_transformers import CrossEncoder
CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("    Cross-encoder downloaded.")
PY

echo ""
echo "==> Cache summary:"
du -sh "$CACHE_DIR/hub" 2>/dev/null || echo "    (hub subdir not present yet)"
ls "$CACHE_DIR/hub" 2>/dev/null | head -20 || true

echo ""
echo "==> Done. Restart Streamlit if it's running so the new cache is picked up."
