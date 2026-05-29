#!/usr/bin/env bash
#
# Launch the multi-service RAG Streamlit client (Chapter 4).
#
# This UI is a thin HTTP client of the two dedicated services — it does NOT
# import the rag/ modules. Point it at the running stack with env vars.
#
# Usage (from anywhere in the project):
#   bash clients/run_streamlit_services.sh
#
# Env overrides:
#   INGESTION_URL   (default: http://localhost:8081)
#   QUERY_URL       (default: http://localhost:8080)
#   RAG_API_KEY     (optional; sent as X-API-Key)
#   STREAMLIT_PORT  (default: 8502 — avoids clashing with the Ch3 app on 8501)
#   STREAMLIT_ADDR  (default: 0.0.0.0)

set -euo pipefail

PORT="${STREAMLIT_PORT:-8502}"
ADDR="${STREAMLIT_ADDR:-0.0.0.0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "==> Launching multi-service Streamlit client"
echo "    app:        clients/streamlit_services_app.py"
echo "    addr:       $ADDR:$PORT"
echo "    ingestion:  ${INGESTION_URL:-http://localhost:8081}"
echo "    query:      ${QUERY_URL:-http://localhost:8080}"
echo ""

exec streamlit run clients/streamlit_services_app.py \
    --server.address "$ADDR" \
    --server.port "$PORT"
