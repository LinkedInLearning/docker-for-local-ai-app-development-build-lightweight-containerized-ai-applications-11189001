# Chapter 4 — Lesson 1: From One Container to Many

Welcome to Chapter 4.

In Chapter 3, we built a containerized development environment for our AI application. We integrate our development environment with the Dev Containers to prototype a RAG system and run all its components inside a single development container.

That setup was ideal for prototyping. But it's not how we want to run the application in production. In this chapter, we'll split the application into dedicated services and test them together in an environment that more closely resembles production.

[CLICK]

The guiding principle is simple: one responsibility per container in production.

A container should do one job and do it well. When we put an entire application into a single container, we lose many of the benefits of containers and tightly couple components that should remain independent.

[CLICK]

Why split the application? Five reasons.

First, independent scaling. The ingestion and query pipelines have very different workloads. Ingestion is CPU-intensive, while query is latency-sensitive. When they run as separate services, we can scale each one independently.

Second, failure isolation. If ingestion gets tied up processing a large document, query can continue serving requests.

Third, independent updates. We can update the query service without rebuilding the heavier ingestion stack.

Fourth, right-sized images. Each image contains only the dependencies it needs, making images smaller, faster to distribute, and easier to secure.

Finally, clear boundaries. Separate services allow us to manage networking, secrets, and resource limits independently.

[CLICK]

Here's the architecture we'll build in this chapter.

The system consists of three services connected on a shared network: an ingestion service, a query service, and vector database, which has been running as its own container since Chapter 3. Clients communicate with the services over HTTP.

[CLICK]

The good news is that we don't have to guess where to split the application. The prototype already defines the boundaries.

If we look at the API, the ingestion routes—`POST /ingest` and the ingestion job endpoints—belong to one service. The query routes—`POST /query`, `GET /documents`, and `GET /config`—belong to another.

The separation is already there. We're simply turning those logical boundaries into separate services.

[CLICK]

Running services in separate containers is what we mean by testing near production.

Instead of a single process where everything shares the same environment, we now have services communicating over a network using hostnames, ports, and access rules.

That's where many real-world issues appear. By testing this architecture now, we find and fix those issues before they reach production.

[CLICK]

So the plan for this chapter is simple: build each service in its own container and test them together as a complete system.
