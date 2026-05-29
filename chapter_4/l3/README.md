# Chapter 4 — Lesson 3: Orchestrating the Stack with Compose

> **Learning goal:** Orchestrate the per-service containers into one running
> stack with Compose, configured like production.

We have two service images and the database image. This lesson wires them into
one running stack with Docker Compose — the topology the app will have in
production. Concepts first, then a hands-on bring-up. The
`docker-compose.test.yaml` for this lesson is in this folder.

---

## 1. A *test* compose, not a *dev* compose

We used Compose in Chapter 3, but this is a different kind of file:

| | Chapter 3 dev compose | This test compose |
| --- | --- | --- |
| Source code | Bind-mounted into the container | Baked into the image |
| Command | `sleep infinity` (attach + live-edit) | the service's real `CMD` |
| Image | A dev image you develop in | The **built artifact** you'd ship |
| Purpose | Iterate on code | Test the thing you'd deploy |

We're testing the artifact, not a development shell.

---

## 2. The stack

Three services on a shared network — `ingestion` (8081), `query` (8080),
`chromadb` (8000):

```yaml
services:
  ingestion:
    build: { context: ., dockerfile: chapter_4/l2/Dockerfile_Ingestion }
    image: rag-ingestion:0.1.0
    ports: ["8081:8081"]
    environment:
      - CHROMA_HOST=chromadb
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on: { chromadb: { condition: service_healthy } }
    networks: [rag-net]

  query:
    build: { context: ., dockerfile: chapter_4/l2/Dockerfile_Query }
    image: rag-query:0.1.0
    ports: ["8080:8080"]
    environment:
      - CHROMA_HOST=chromadb
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on: { chromadb: { condition: service_healthy } }
    networks: [rag-net]

  chromadb:
    image: chromadb/chroma:1.3.5
    volumes: ["./chroma_data:/chroma/chroma"]
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v2/heartbeat')"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks: [rag-net]
```

Two things are new:

* **`build:`** — the app services build from the Lesson 2 Dockerfiles and tag
  the result. Compose builds as well as runs.
* **`healthcheck` + `depends_on: service_healthy`** — see below.

---

## 3. Why a healthcheck

`depends_on` on its own only waits for a container to **start**, not to be
**ready**. A database is often "started" a second or two before it accepts
connections — long enough for an app service to come up, try to connect, and
crash.

The healthcheck closes the gap: we tell Compose how to ask the database "are
you ready?" (here, its heartbeat endpoint), and the app services wait until
that check passes. No more startup race.

> The probe is a Python one-liner, not `curl`: the off-the-shelf
> `chromadb/chroma` image is minimal and has no `curl`, but it does have the
> Python that runs Chroma itself — so we reuse what's already inside the image.

---

## 4. Hands-on: bring it up

From the project root:

```bash
# Build images and start all three containers
docker compose -f chapter_4/l3/docker-compose.test.yaml up -d --build

# Confirm the stack — db should read "healthy", not just "running"
docker compose -f chapter_4/l3/docker-compose.test.yaml ps

# Check a service started cleanly
docker compose -f chapter_4/l3/docker-compose.test.yaml logs query
```

Then a first smoke test from the multi-service Streamlit client, which talks
to both services over HTTP:

```bash
bash clients/run_streamlit_services.sh
```

In the sidebar, click **Check health** — both services should respond.

Tear down (removing volumes) when done:

```bash
docker compose -f chapter_4/l3/docker-compose.test.yaml down -v
```

---

## What's next

The system is running as separate containers — but "running" isn't "working."
**Lesson 4** tests that the containers actually cooperate: networking, health
and readiness, and the end-to-end ingest → query flow.
