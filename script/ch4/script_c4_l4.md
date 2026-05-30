# Chapter 4 — Lesson 4: Networking, Health & Integration Testing

The stack is running. But running is not the same as working. This lesson tests that our separate containers actually cooperate — the thing a single-container prototype could never reveal. Concepts on slides, then we test it in the terminal.

[CLICK]

First, how the services talk.

In our prototype, everything was in one process, so any part could call any other directly. Now they're separate containers, and they communicate over the network.

The ingestion service and the query service **don't call each other**. They share state through the database. Ingestion writes vectors to ChromaDB; query reads them back. The database is the contract between them.

Both services reach the database by its **service name** — `chromadb`, port 8000 — the Compose DNS we saw in Chapter 3. No IP addresses.

[CLICK]

Second, health and readiness.

Each service exposes a `/health` endpoint. We use it two ways: the database's healthcheck gates startup, as we saw in Lesson 3, and we can hit each service's `/health` directly to confirm it's ready before sending real traffic.

This is also what a load balancer or orchestrator uses in production to decide whether to route to a container — so building it now means we're already production-shaped.

[CLICK]

Third, the **integration test**.

Here's the flow that only a multi-container setup can exercise. Ingest a document by calling `POST /ingest` on the **ingestion** service. Poll its job until it completes. Then ask a question by calling `POST /query` on the **query** service. If the answer comes back with sources from the document we just ingested, we've proven something big.

We've proven that two independent containers, talking only through a shared database over the network, cooperate correctly. Networking works. The shared-state contract works. The services are genuinely integrated.

[CLICK]

Let's run it.

[SWITCH TO TERMINAL]

First, a manual walk-through with curl. Ingest, against the ingestion service on 8081:

```bash
curl -X POST localhost:8081/ingest \
  -H "X-API-Key: dev-key" -d '{"source_dir":"pdf/"}'
```

That returns a job ID. Once it's done, query — against the query service on 8080:

```bash
curl -X POST localhost:8080/query \
  -H "X-API-Key: dev-key" -d '{"question":"What is this document about?"}'
```

The answer comes back with sources. Two different containers, one coherent result.

[CLICK]

And to prove the networking directly — from *inside* the query container, reach the database by service name. The image is lean and has no curl, so we use the Python it already ships:

```bash
docker compose -f chapter_4/l3/docker-compose.test.yaml exec query \
  python -c "import urllib.request; print(urllib.request.urlopen('http://chromadb:8000/api/v2/heartbeat').status)"
```

The hostname is `chromadb`, not localhost — service-name DNS at work.

[CLICK]

Doing this by hand is fine for exploring, but we want it automated and repeatable. That's the integration test:

```bash
pytest chapter_4/l4/test_integration.py -v
```

It runs that same ingest-to-query flow automatically — checking both services are healthy and asserting the answer comes back with sources — a test we can run on every change.

You can also drive this interactively from the Streamlit client — ingest from the sidebar, watch the job complete, then ask a question in the chat. Same flow, human-friendly.

[CLICK]

That's the heart of multi-container testing: not "does each container start," but "do the containers work *together*." We just verified networking, the shared-database contract, and the full ingest-to-query path across service boundaries.

In the final lesson, we'll step back and cover the testing practices that keep a multi-container app reliable — the testing pyramid, fixtures, and running all of this in CI.
