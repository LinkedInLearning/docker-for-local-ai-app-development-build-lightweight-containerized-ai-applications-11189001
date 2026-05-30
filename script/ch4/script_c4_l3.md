# Chapter 4 — Lesson 3: Orchestrating the Stack with Compose

We have two service images and the database image. This lesson wires them into one running stack with Docker Compose — the topology the application will have in production. Concepts on slides, then we bring the stack up in the terminal.

[CLICK]

We already used Compose in Chapter 3, so the tool is familiar. But this is a different *kind* of Compose file, and the difference matters.

The Chapter 3 file was a **development** compose. It bind-mounted our source code into the container and ran `sleep infinity` so we could attach an editor and live-edit.

This file is a **test** compose. There's no source mount and no `sleep infinity`. Each container runs its real command against the **built image** — the exact artifact that would ship. We're testing the thing we'd deploy, not a development shell.

[CLICK]

The stack has three services on a shared network: `ingestion` on port 8081, `query` on port 8080, and `chromadb` on 8000.

First, `build`. Instead of pulling a prebuilt image, the two app services build from the Dockerfiles we wrote in Lesson 2, and tag the result. Compose can build as well as run.

Second — and this is new — a **healthcheck** on the database, and `depends_on` with `condition: service_healthy` on the two app services.

[CLICK]

Why the healthcheck? `depends_on` on its own only waits for a container to *start*, not to be *ready*. A database container can be "started" a full second or two before it's actually accepting connections.

The healthcheck closes that gap. We tell Compose how to ask the database "are you ready?" — here, by hitting its heartbeat endpoint — and the app services wait until that check passes before they start. No more race where ingestion comes up and immediately fails because the database isn't listening yet.

[CLICK]

Let's bring it up.

[SWITCH TO TERMINAL]

From the project root, one command builds the images and starts all three containers:

```bash
docker compose -f chapter_4/l3/docker-compose.test.yaml up -d --build
```

Compose builds the two service images, starts the database, waits for its healthcheck, then starts ingestion and query.

[CLICK]

Let's confirm the stack is healthy:

```bash
docker compose -f chapter_4/l3/docker-compose.test.yaml ps
```

Three services, all up — and the database shows `healthy`, not just `running`.

[CLICK]

A quick look at one service's logs to confirm it started cleanly:

```bash
docker compose -f chapter_4/l3/docker-compose.test.yaml logs query
```

[CLICK]

And a first smoke test from the multi-service Streamlit client, which talks to both services over HTTP:

```bash
bash clients/run_streamlit_services.sh
```

In the sidebar, I'll click **Check health** — both the ingestion and query services respond. The stack is alive and reachable.

[CLICK]

The whole system is now running as separate containers, exactly as it would in production. But "running" isn't "working" — we haven't proven the services can actually cooperate.

In the next lesson, we test that: networking between the containers, health and readiness, and the end-to-end flow of ingesting through one service and querying through the other.
