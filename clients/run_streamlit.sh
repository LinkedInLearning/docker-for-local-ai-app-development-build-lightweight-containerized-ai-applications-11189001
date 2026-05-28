#!/usr/bin/env bash
#
# Launch the Streamlit RAG app inside the dev container.
#
# Usage (from anywhere in the project):
#   bash clients/run_streamlit.sh
#
# Env overrides:
#   STREAMLIT_PORT (default: 8501)
#   STREAMLIT_ADDR (default: 0.0.0.0)

set -euo pipefail

PORT="${STREAMLIT_PORT:-8501}"
ADDR="${STREAMLIT_ADDR:-0.0.0.0}"

# Run from the project root regardless of where the script was invoked.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "==> Launching Streamlit"
echo "    app:  clients/streamlit_app.py"
echo "    addr: $ADDR:$PORT"
echo "    cwd:  $PROJECT_ROOT"
echo ""

exec streamlit run clients/streamlit_app.py \
    --server.address "$ADDR" \
    --server.port "$PORT"
