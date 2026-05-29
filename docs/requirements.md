# Course Requirements

> A living checklist of everything a learner needs to follow the **Docker for
> Local AI** course — accounts, software, and credentials. Add a row whenever a
> lesson introduces a new prerequisite; keep the **Where in the course** column
> pointing at the first lesson that needs it.

_Last updated: 2026-05-29._

Legend — **Status**: ✅ confirmed required · 🔲 to confirm · ⬜ optional / nice-to-have.

---

## 1. Accounts & services

| Requirement | Why it's needed | Where in the course | How to get it | Status |
| ----------- | --------------- | ------------------- | ------------- | ------ |
| **Docker Hub account** | Authenticated pulls of base images (avoids anonymous rate limits), and pushing/sharing your own images. | Chapter 2 · L4 (working with registries); Chapter 5 · L5 (publish to Docker Hub) | Free sign-up at [hub.docker.com](https://hub.docker.com) → then `docker login` | ✅ |

---

## 2. Software

| Requirement | Why it's needed | Where in the course | How to get it | Status |
| ----------- | --------------- | ------------------- | ------------- | ------ |
| **Docker Engine / Docker Desktop** | Build and run every image and container in the course. | All chapters | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) | ✅ |

---

## 3. Credentials & secrets

| Requirement | Why it's needed | Where in the course | How to get it | Status |
| ----------- | --------------- | ------------------- | ------------- | ------ |
| _(none tracked yet)_ | | | | |

---

## Backlog — candidates to confirm

Prerequisites the course material appears to use but that are **not yet
confirmed/triaged** into the tables above. Promote them (with a real
**Where in the course** reference) as the relevant lessons are finalized:

- Code editor — **VS Code** (used for the live `docker build` demo in Ch2 · L3 and Dev Containers in Ch3).
- **VS Code Dev Containers** extension (Chapter 3 — developing inside the container).
- **Git** (cloning the course repo; general workflow).
- **Python 3.11** on the host (only if running anything outside containers).
- LLM **API keys** — e.g. `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` (RAG application chapters).

> Note: keep secrets (API keys, tokens) **out of images and out of git** — see
> `chapter_2/l6` and `.env.example` at the repo root.
