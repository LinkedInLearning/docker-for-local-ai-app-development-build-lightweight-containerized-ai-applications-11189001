#!/usr/bin/env bash
#
# Chapter 5 / Lesson 4 — multi-platform build demo with buildx.
#
# Builds the tiny demo image (./Dockerfile) for amd64 and arm64, then runs each
# so the reported CPU architecture proves buildx produced the right binary.
#
# Prerequisites:
#   - Docker Desktop (ships the QEMU emulators). On plain Linux, install them once:
#       docker run --privileged --rm tonistiigi/binfmt --install all
#
# Usage (from the repository root):
#
#   bash chapter_5/l4/buildx_demo.sh
#
set -euo pipefail

IMAGE="${IMAGE:-rag-demo}"
CONTEXT="chapter_5/l4"

echo "== 1. A multi-platform-capable builder =="
# The default 'docker' driver can't do multi-arch; the docker-container driver can.
docker buildx create --name multiarch --driver docker-container --use --bootstrap 2>/dev/null \
  || docker buildx use multiarch
docker buildx inspect --bootstrap | grep -i "platforms" || true

echo ""
echo "== 2. Build + load the amd64 variant, then run it =="
docker buildx build --platform linux/amd64 --load -t "${IMAGE}:amd64" "${CONTEXT}"
docker run --rm --platform linux/amd64 "${IMAGE}:amd64"

echo ""
echo "== 3. Build + load the arm64 variant, then run it =="
docker buildx build --platform linux/arm64 --load -t "${IMAGE}:arm64" "${CONTEXT}"
docker run --rm --platform linux/arm64 "${IMAGE}:arm64"

echo ""
echo "Each run printed a different architecture — same source, two binaries."
echo "Combining both arches under ONE tag makes a manifest list, which must be"
echo "pushed to a registry. That is Lesson 5 (publish_demo.sh)."
