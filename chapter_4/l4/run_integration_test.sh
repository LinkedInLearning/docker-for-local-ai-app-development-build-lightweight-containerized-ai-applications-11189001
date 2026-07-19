#!/usr/bin/env bash
#
# Chapter 4 · Lesson 4 — end-to-end integration test, no venv required.
#
# A pure `curl` + `python3` (standard library only) version of
# test_integration.py: it ingests a document through the INGESTION service and
# queries it through the QUERY service, proving the two containers cooperate
# over the shared ChromaDB — the thing a single-container prototype can't show.
#
# Prerequisite — the Lesson 3 stack must be running:
#   docker compose -f chapter_4/l3/docker-compose.test.yaml up -d --build
#
# Run (from the project root):
#   bash chapter_4/l4/run_integration_test.sh                       # whole pdf/ folder
#   bash chapter_4/l4/run_integration_test.sh --pdf pdf/report.pdf  # one file
#   bash chapter_4/l4/run_integration_test.sh --dir pdf/sample      # a folder under pdf/
#
# Env overrides (same as test_integration.py):
#   INGESTION_URL, QUERY_URL, RAG_API_KEY, SAMPLE_PDF_DIR
#   POLL_TIMEOUT_S  (default 300) — raise it for a large / multi-PDF corpus,
#                   since Docling parses on CPU (e.g. POLL_TIMEOUT_S=900).
#   POLL_INTERVAL_S (default 15) — how often to poll/print progress.

set -u

INGESTION_URL="${INGESTION_URL:-http://localhost:8081}"
QUERY_URL="${QUERY_URL:-http://localhost:8080}"
API_KEY="${RAG_API_KEY:-dev-key}"
SAMPLE_PDF_DIR="${SAMPLE_PDF_DIR:-pdf/}"
POLL_TIMEOUT_S="${POLL_TIMEOUT_S:-300}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-15}"
QUESTION="What is this document about?"

# Repo root (so staging/listing work regardless of the caller's cwd). The
# ingestion container mounts <repo>/pdf at /app/pdf, so any source_dir we send
# must be a path under `pdf/` (e.g. "pdf/sample").
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

usage() {
  cat <<EOF
Usage: bash chapter_4/l4/run_integration_test.sh [--pdf FILE | --dir DIR]

  --pdf FILE   Ingest a single PDF. It is copied into a temp folder under the
               mounted pdf/ so the ingestion container can read it, then removed
               when the test finishes.
  --dir  DIR   Ingest every *.pdf in DIR. DIR must live under the repo's pdf/
               folder — the only path the ingestion container can see — e.g.
               --dir pdf/sample.
  -h, --help   Show this help.

  With no argument, ingests \$SAMPLE_PDF_DIR (default: pdf/ — the whole folder).
  Other env: INGESTION_URL, QUERY_URL, RAG_API_KEY, POLL_TIMEOUT_S (300),
  POLL_INTERVAL_S (15).
EOF
}

PDF_FILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pdf) PDF_FILE="${2:?--pdf needs a file path}"; shift 2 ;;
    --dir) SAMPLE_PDF_DIR="${2:?--dir needs a directory}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1"; echo; usage; exit 1 ;;
  esac
done

command -v curl    >/dev/null 2>&1 || { echo "needs 'curl'"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "needs 'python3' (stdlib only) for JSON parsing"; exit 1; }

pass() { echo "  PASS  $1"; }
fail() { echo "  FAIL  $1"; exit 1; }
# Read JSON from stdin and print a field: jget "<expr on dict d>"
jget() { python3 -c "import sys,json; d=json.load(sys.stdin); print($1)" 2>/dev/null; }

# --pdf: stage the single file into a temp folder under pdf/ so the container
# can read it, and remove that folder when we exit (pass, fail, or ctrl-c).
staged_note=""
if [ -n "$PDF_FILE" ]; then
  [ -f "$PDF_FILE" ] || fail "--pdf file not found: $PDF_FILE"
  stage_host="$PROJECT_ROOT/pdf/.integration-test"
  SAMPLE_PDF_DIR="pdf/.integration-test"
  mkdir -p "$stage_host"
  rm -f "$stage_host"/*.pdf 2>/dev/null || true
  cp "$PDF_FILE" "$stage_host"/ || fail "could not stage $PDF_FILE into $stage_host"
  trap 'rm -rf "$stage_host"' EXIT
  staged_note="  (staged from --pdf $PDF_FILE)"
fi

# Host path matching the container source_dir, for listing the PDFs on screen.
host_dir="$PROJECT_ROOT/$SAMPLE_PDF_DIR"
pdf_files=""
for f in "$host_dir"/*.pdf; do
  [ -e "$f" ] || continue
  pdf_files="${pdf_files:+$pdf_files, }$(basename "$f")"
done
[ -n "$pdf_files" ] || pdf_files="(can't list from here; container reads /app/$SAMPLE_PDF_DIR)"

echo "====================================================================="
echo "  RAG stack — end-to-end integration test (no venv)"
echo "====================================================================="
echo "  Ingest a PDF through the ingestion service, then query it through the"
echo "  query service. The two containers share nothing but ChromaDB, so a"
echo "  pass proves they cooperate over the network — networking works and the"
echo "  ingest-writes / query-reads contract through the shared DB holds."
echo ""
echo "  ingestion : $INGESTION_URL"
echo "  query     : $QUERY_URL"
echo "  source    : $SAMPLE_PDF_DIR   (files: $pdf_files)$staged_note"
echo "  poll      : up to ${POLL_TIMEOUT_S}s, every ${POLL_INTERVAL_S}s"
echo "  api key   : $API_KEY"
echo "====================================================================="

echo ""
echo "[1/4] Health — both services answer /health before we send real traffic"
for pair in "ingestion|$INGESTION_URL" "query|$QUERY_URL"; do
  name="${pair%%|*}"; base="${pair##*|}"
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$base/health")
  [ "$code" = "200" ] \
    && pass "$name /health -> 200" \
    || fail "$name /health -> ${code:-no response} (is the stack up? is the host port free? see Lesson 3 README §6)"
done

echo ""
echo "[2/4] Ingest — POST /ingest {\"source_dir\":\"$SAMPLE_PDF_DIR\"} on the ingestion service (:8081)"
resp=$(curl -s --max-time 30 -X POST "$INGESTION_URL/ingest" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d "{\"source_dir\":\"$SAMPLE_PDF_DIR\"}")
job_id=$(printf '%s' "$resp" | jget "d.get('job_id','')")
[ -n "$job_id" ] || fail "no job_id in ingest response: $resp"
pass "job accepted (202), job_id=$job_id"

echo ""
echo "[3/4] Poll — wait for the ingestion job to reach 'completed'"
echo "  ingesting : $SAMPLE_PDF_DIR  ($pdf_files)"
echo "  timeout   : ${POLL_TIMEOUT_S}s max, polling every ${POLL_INTERVAL_S}s  (Docling parses on CPU)"
elapsed=0; status=""; chunks=0
while [ "$elapsed" -lt "$POLL_TIMEOUT_S" ]; do
  rec=$(curl -s --max-time 10 -H "X-API-Key: $API_KEY" "$INGESTION_URL/ingest/jobs/$job_id")
  status=$(printf '%s' "$rec" | jget "d.get('status','')")
  echo "  ... status=${status:-?}  (${elapsed}s / ${POLL_TIMEOUT_S}s)"
  case "$status" in
    completed)
      chunks=$(printf '%s' "$rec" | jget "(d.get('result') or {}).get('total_chunks',0)")
      if [ "${chunks:-0}" -gt 0 ]; then
        pass "completed — $chunks new chunks written to ChromaDB"
      else
        echo "  NOTE  0 new chunks — this document is already stored, so the"
        echo "        re-embed was skipped. The query step below is the real check:"
        echo "        it proves the data is present and queryable."
      fi
      break ;;
    failed)
      fail "ingestion failed: $(printf '%s' "$rec" | jget "d.get('error_message','?')")" ;;
  esac
  sleep "$POLL_INTERVAL_S"; elapsed=$((elapsed + POLL_INTERVAL_S))
done
[ "$status" = "completed" ] || fail "did not complete within ${POLL_TIMEOUT_S}s (last status=${status:-none}); raise POLL_TIMEOUT_S or ingest fewer PDFs"

echo ""
echo "[4/4] Query — POST /query on the query service (:8080); expect an answer WITH sources"
echo "  question  : \"$QUESTION\""
q=$(curl -s --max-time 60 -X POST "$QUERY_URL/query" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\"}")
answer=$(printf '%s' "$q" | jget "(d.get('answer') or '')[:200]")
nsrc=$(printf '%s' "$q" | jget "len(d.get('sources') or [])")
[ -n "$answer" ]       || fail "empty answer: $q"
[ "${nsrc:-0}" -gt 0 ] || fail "query returned no sources — is the DB shared? $q"
pass "answer received, backed by $nsrc source(s)"
echo "  answer    : ${answer}"

echo ""
echo "====================================================================="
echo "  RESULT: PASSED"
echo "  ingest (:8081) -> shared chromadb -> query (:8080)"
echo "  '$SAMPLE_PDF_DIR' -> $chunks new chunk(s) (0 = already stored) -> query returned $nsrc source(s)"
echo "====================================================================="
