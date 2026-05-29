#!/usr/bin/env bash
#
# Chapter 2 / Lesson 7 — guided tour of the management commands.
#
# Assumes the `demo:0.1` image from Lesson 3 exists and a container
# named `demo` is running (start it with `bash chapter_2/l5/run.sh`).
#
# This script does NOT modify anything — it just prints the most
# common inspection commands and their output, in order, so you can
# read along.
#
set -euo pipefail

NAME="demo"

hr() { printf '\n--- %s ---\n' "$*"; }

hr "docker ps  (running containers)"
docker ps

hr "docker ps -a  (all containers, incl. stopped)"
docker ps -a

hr "docker images"
docker images

hr "docker logs --tail 20 ${NAME}"
docker logs --tail 20 "${NAME}" || true

hr "docker inspect ${NAME}  (env vars only)"
docker inspect "${NAME}" | jq '.[0].Config.Env' 2>/dev/null \
    || docker inspect "${NAME}" | head -n 40

hr "docker stats --no-stream ${NAME}"
docker stats --no-stream "${NAME}"

hr "docker system df  (disk usage summary)"
docker system df
