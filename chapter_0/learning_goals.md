# Course Learning Goals

> Every lesson opens with a learning goal that completes the sentence:
> **"With this content, you will be able to…"**
> Each goal is also reproduced at the top of its lesson `README.md`. This page
> is the course-level index; keep it in sync when a lesson is added or its
> goal changes. See [naming_convention.md](naming_convention.md) for structure.

---

## Chapter 1 — Introduction to Docker for AI Applications

| Lesson | Title | With this content, you will be able to… |
| ------ | ----- | --------------------------------------- |
| 1 | Why Docker Containers? | **explain** why containerization matters for software in general and for AI applications in particular, and **describe** how containers provide reproducible environments across the development lifecycle. |
| 2 | Introduction to RAG | **describe** the components of a Retrieval-Augmented Generation (RAG) system and **frame** them as discrete services that can later be containerized. |
| 3 | Container Strategy | **evaluate** whether an AI application's services should be packaged into one container or many, based on its architecture and target production environment. |
| 4 | Containerized Development Workflow for AI Applications | **outline** the end-to-end containerized workflow — spec, development, test, deployment — and **map** each stage to the chapters that follow. |

## Chapter 2 — Docker Workflow and Best Practices

| Lesson | Title | With this content, you will be able to… |
| ------ | ----- | --------------------------------------- |
| 1 | The Docker Workflow | **describe** the four-step Docker workflow (requirements → Dockerfile → build → run) and **distinguish** an image from a container. |
| 2 | Core Dockerfile Commands | **write** a Dockerfile using the core instructions (`FROM`, `ARG`, `ENV`, `WORKDIR`, `RUN`, `COPY`, `EXPOSE`, `CMD`) to define an image's environment. |
| 3 | docker build | **build** an image from a Dockerfile, and **use** the build context, `.dockerignore`, and layer cache to make builds correct and fast. |
| 4 | Working with Registries | **pull and push** images to a registry, **tag** them for a namespace, and **share** an image via Docker Hub. |
| 5 | docker run | **run, manage, and inspect** containers from an image using the everyday `docker run` flags and lifecycle commands. |
| 6 | Dockerfile Best Practices | **apply** Dockerfile best practices to produce images that are smaller, faster to build, more reproducible, and more secure. |
| 7 | Managing Containers and Images | **list, inspect, debug, and clean up** Docker images, containers, volumes, and networks using the `docker` CLI. |

## Chapter 3 — Building a Containerized AI Development Environment

| Lesson | Title | With this content, you will be able to… |
| ------ | ----- | --------------------------------------- |
| 1 | Designing Images for Change | **structure** a Docker image so the elements most likely to change sit in the last layers, and **use** the build cache to keep rebuilds fast as requirements evolve. |
| 2 | Docker Compose | **use** Docker Compose to define and orchestrate the multi-container RAG environment (a Python dev container and a ChromaDB container), and **bring it up, verify, and tear it down** from the terminal. |
| 3 | Dev Containers | **configure** a VS Code Dev Container that attaches your editor to the containerized environment — with project-level extensions and mounts — backed by Docker Compose. |
| 4 | Developing Inside the Container | **develop** the RAG application inside the dev container — writing modules and **validating** them with notebooks and a Streamlit dashboard — with an AI coding assistant in the loop. |
| 5 | Development Environment Best Practices | **apply** best practices for a containerized development environment: version and tag images, script the builds, split a base image from a project dev image, and start new projects from a GitHub template. |

## Chapter 4 — Testing Containerized AI Applications

| Lesson | Title | With this content, you will be able to… |
| ------ | ----- | --------------------------------------- |
| 1 | From One Container to Many | **explain** why a multi-container, one-service-per-container architecture beats a single prototype container, and **identify** the RAG services to split out. |
| 2 | Dedicated Images per Service | **build** a dedicated, right-sized image for each service, each with its own Dockerfile and dependency set. |
| 3 | Orchestrating the Stack with Compose | **orchestrate** the per-service containers into one running stack with Compose, configured like production. |
| 4 | Networking, Health & Integration Testing | **validate** the multi-container system end to end — service-name networking, health gating, and an integration test across both services and the shared vector DB. |
| 5 | Testing Best Practices for Multi-Container Apps | **apply** testing best practices that keep a multi-container app reliable and reproducible — the testing pyramid mapped onto containers, ephemeral test data, and CI. |

## Chapter 5 — Preparing AI Applications for Production with Docker

| Lesson | Title | With this content, you will be able to… |
| ------ | ----- | --------------------------------------- |
| 1 | What "Production-Ready" Means | **define** production-readiness for a containerized app (size, security, portability, distribution, operability) and **baseline** your current images against that bar. |
| 2 | Slimming Images with Multi-Stage Builds | **use** multi-stage builds, a minimal base, and `.dockerignore` to ship only runtime artifacts, and **quantify** the size reduction. |
| 3 | Securing Production Images | **reduce** attack surface and run with least privilege (non-root, pinned base, no baked secrets), and **scan** for and triage vulnerabilities. |
| 4 | Multi-Platform Builds with Buildx | **build** images that run on multiple CPU architectures (amd64/arm64) from one source using Buildx and BuildKit. |
| 5 | Publishing to a Registry | **version, tag, and publish** images to a registry — including a multi-arch manifest — with a sound tagging strategy and image provenance. |
| 6 | Best Practices & Going Live | **apply** the operational practices that keep a published image reliable (resource limits, health, graceful shutdown) and **validate** the production artifact in a build → scan → test → push pipeline. |
