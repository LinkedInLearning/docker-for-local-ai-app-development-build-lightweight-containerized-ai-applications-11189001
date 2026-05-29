#!/usr/bin/env bash
#
# Chapter 2 / Lesson 3 — example build script.
#
# Builds the minimal Dockerfile from chapter_2/l2 with a tagged name.
# Run from the repository root:
#
#   bash chapter_2/l3/build.sh
#
set -euo pipefail

IMAGE_NAME="demo"
IMAGE_TAG="0.1"
CONTEXT_DIR="chapter_2/l2"

echo "Building ${IMAGE_NAME}:${IMAGE_TAG} from context ${CONTEXT_DIR}"

docker build \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    "${CONTEXT_DIR}"

echo ""
echo "Image built. Layers:"
docker history "${IMAGE_NAME}:${IMAGE_TAG}"
