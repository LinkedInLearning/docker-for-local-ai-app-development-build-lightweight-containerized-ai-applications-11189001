#!/usr/bin/env bash
#
# Chapter 2 / Lesson 5 — example run script.
#
# Starts the image built in Lesson 3 as a detached container with a
# published port, a friendly name, and an auto-restart policy.
#
# Usage (from the repository root):
#
#   bash chapter_2/l5/run.sh           # start the container
#   bash chapter_2/l5/run.sh stop      # stop & remove the container
#
set -euo pipefail

IMAGE="demo:0.1"
NAME="rag-api"
HOST_PORT=8080
CTR_PORT=8080

case "${1:-up}" in
  up|start)
    echo "Starting container '${NAME}' from image '${IMAGE}'"
    docker run -d \
      --name "${NAME}" \
      --restart unless-stopped \
      -p "${HOST_PORT}:${CTR_PORT}" \
      "${IMAGE}"
    echo ""
    echo "Container started. The FastAPI app is now published on the host:"
    echo "  open  http://localhost:${HOST_PORT}/        # JSON from the app"
    echo "  open  http://localhost:${HOST_PORT}/docs    # auto-generated Swagger UI"
    echo ""
    echo "Other handy commands:"
    echo "  curl http://localhost:${HOST_PORT}/"
    echo "  docker logs -f ${NAME}"
    echo "  docker exec -it ${NAME} bash"
    ;;
  down|stop)
    echo "Stopping and removing container '${NAME}'"
    docker rm -f "${NAME}" >/dev/null
    echo "Done."
    ;;
  *)
    echo "Usage: $0 [up|down]"
    exit 1
    ;;
esac
