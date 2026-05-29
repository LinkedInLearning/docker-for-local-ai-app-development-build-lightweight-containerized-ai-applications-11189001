#!/usr/bin/env bash
#
# Chapter 2 / Lesson 4 — example registry script.
#
# Tags the `demo:0.1` image from Lesson 3 for your Docker Hub namespace and
# pushes it, then prints the command others would use to pull it.
#
# Prerequisites:
#   - the `demo:0.1` image exists (build it with `bash chapter_2/l3/build.sh`)
#   - you are logged in:  docker login
#
# Usage (from the repository root):
#
#   DOCKER_USER=your-dockerhub-username bash chapter_2/l4/registry.sh
#
set -euo pipefail

: "${DOCKER_USER:?Set DOCKER_USER to your Docker Hub username, e.g. DOCKER_USER=myuser}"

LOCAL_IMAGE="demo:0.1"
REMOTE_IMAGE="${DOCKER_USER}/demo:0.1"

echo "Tagging ${LOCAL_IMAGE} -> ${REMOTE_IMAGE}"
docker tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE}"

echo "Pushing ${REMOTE_IMAGE} to Docker Hub"
docker push "${REMOTE_IMAGE}"

echo ""
echo "Done. Anyone can now pull it with:"
echo "    docker pull ${REMOTE_IMAGE}"
