#!/usr/bin/env bash
#
# Chapter 5 / Lesson 5 — publish to Docker Hub.
#
# Publishes the Lesson 4 demo image (chapter_5/l4) to Docker Hub two ways: a
# single-arch tag+push, then a multi-arch manifest list built and pushed in one
# step with buildx.
#
# Prerequisites:
#   - log in first (interactive):  docker login
#   - the multi-platform builder from Lesson 4 exists (buildx_demo.sh), or:
#       docker buildx create --name multiarch --driver docker-container --use --bootstrap
#
# Usage (from the repository root):
#
#   DOCKER_USER=your-dockerhub-username bash chapter_5/l5/publish_demo.sh
#
set -euo pipefail

: "${DOCKER_USER:?Set DOCKER_USER to your Docker Hub username, e.g. DOCKER_USER=myuser}"

IMAGE="${IMAGE:-rag-demo}"
VERSION="${VERSION:-0.1.0}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
CONTEXT="chapter_5/l4"          # reuse the Lesson 4 demo image
REPO="${DOCKER_USER}/${IMAGE}"

echo "== 1. Single-arch: build for this machine, tag, and push =="
docker buildx build --load -t "${IMAGE}:${VERSION}" "${CONTEXT}"
# Tag with the namespace a registry will accept (an immutable version, not 'latest').
docker tag "${IMAGE}:${VERSION}" "${REPO}:${VERSION}"
docker push "${REPO}:${VERSION}"

echo ""
echo "== 2. Multi-arch: build BOTH platforms and push as one manifest list =="
docker buildx build --platform "${PLATFORMS}" -t "${REPO}:${VERSION}" --push "${CONTEXT}"

echo ""
echo "== 3. Inspect the published manifest list — one tag, multiple arches =="
docker buildx imagetools inspect "${REPO}:${VERSION}"

echo ""
echo "== 4. Pull it back (Docker auto-selects this machine's architecture) =="
docker pull "${REPO}:${VERSION}"

echo ""
echo "Published: ${REPO}:${VERSION}"
echo "Others pull it with:  docker pull ${REPO}:${VERSION}"
