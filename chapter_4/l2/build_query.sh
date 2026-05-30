#!/usr/bin/env bash
#
# Chapter 4 · Lesson 2 — build the LEAN query-service image.
#
# Builds chapter_4/l2/Dockerfile_Query. The Dockerfile COPYs from repo-root
# paths (rag/, config/, chapter_4/l2/requirements-query.txt), so the build
# context must be the repository root. This script cd's there itself, so you
# can run it from anywhere:
#
#   bash chapter_4/l2/build_query.sh
#
set -euo pipefail

IMAGE_NAME="rag-query"
IMAGE_TAG="0.1.0"
DOCKERFILE="chapter_4/l2/Dockerfile_Query"

# Run from the repository root (two levels up from this script).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "Building ${IMAGE_NAME}:${IMAGE_TAG} from ${DOCKERFILE} (context: ${REPO_ROOT})"

docker build \
    -f "${DOCKERFILE}" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    .

echo ""
echo "Done. Image:"
docker images | grep "^${IMAGE_NAME} " || docker images "${IMAGE_NAME}:${IMAGE_TAG}"
