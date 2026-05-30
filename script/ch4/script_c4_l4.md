# Chapter 4 — Lesson 4: Networking, Health & Integration Testing

The stack is running. But running is not the same as working. This lesson tests that our separate containers actually cooperate — the thing a single-container prototype could never reveal. We'll work through it on the slides; the full hands-on — every command and its output — lives in this lesson's README.

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

For the full hands-on, see this lesson's README. It walks through the ingest-and-query flow with curl, proving service-name DNS from inside the query container, and the automated `pytest` integration test — each command with its expected output.

[CLICK]

That's the heart of multi-container testing: not "does each container start," but "do the containers work *together*" — networking, the shared-database contract, and the full ingest-to-query path across service boundaries.

In the final lesson, we'll step back and cover the testing practices that keep a multi-container app reliable — the testing pyramid, fixtures, and running all of this in CI.
