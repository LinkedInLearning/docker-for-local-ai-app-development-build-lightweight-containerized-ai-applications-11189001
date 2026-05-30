# Chapter 4 — Lesson 1: From One Container to Many

Welcome to Chapter 4.

[CLICK]

In Chapter 3 we learned how to set up a prototype development environment for developing an AI application. We saw the moving pieces of the RAG system working inside a notebook, running inside a fully containerized development environment with Dev Containers.

That was perfect for prototyping. It is the wrong shape for production. This chapter is about the move from that single container to **one dedicated container per service**, and testing them together in an environment close to production.

[CLICK]

The principle is simple: **one responsibility per container.**

A container should do one job and do it well. When we put the whole application into one container, we lose the benefits of containers — and we tightly couple parts of the system that don’t belong together.

[CLICK]

Why split? Five reasons.

First, **Independent scaling.** Our two pipelines have completely different load profiles. Ingestion is CPU-heavy. For example,  parsing a 500-page PDF and embedding it is a batch job. Query is steady and latency-sensitive — as a user waiting for an answer. In one container, you can't scale them separately. Split apart, you can run one ingestion worker and five query replicas.

Next is **Failure isolation.** If a giant document ties up ingestion, query keeps answering. One service's problem doesn't become the whole system's problem.

Independent deployment. You can fix the query prompt and update the query service in seconds, without rebuilding the heavier Docling parsing stack.

**Right-sized images.** Each image carries only what its service needs. The query image doesn't need a PDF parser; the ingestion image doesn't need a web framework. Smaller images are faster to ship and have a smaller attack surface.

Last but not least **Clear boundaries.** Separate services mean separate secrets, separate network exposure, separate resource limits.

[CLICK]

Here's the destination for this chapter: three services, wired together on one network.

Two application services — **ingestion**, which parses, chunks, embeds, and stores, on one port; and **query**, which retrieves, reranks, calls the LLM, and generates the answer, on another — plus the **vector database**, ChromaDB, which has already been running as its own container since Chapter 3. A client talks to each service over HTTP.


[CLICK]

The good news is we don't have to guess where to cut — the prototype already drew the line for us.

Look at the API endpoints. The ingestion routes — `POST /ingest` and `GET /ingest/jobs` — sit on one side; the query routes — `POST /query`, `GET /documents`, and `GET /config` — on the other. They already partition cleanly, so we just cut along that seam: each service owns its own routes.

[CLICK]

Running those services as separate containers is what we mean by **testing near production**. Instead of one process where everything can reach everything by virtue of being in the same memory space, we now have separate containers that must talk over a network — with hostnames, ports, and access rules.

That's exactly where the interesting bugs live, and exactly the bugs a single-container prototype hides. By running this topology now, we surface them while they're cheap to fix.

[CLICK]

So the plan for this chapter is to build each service in its own container and test it.


