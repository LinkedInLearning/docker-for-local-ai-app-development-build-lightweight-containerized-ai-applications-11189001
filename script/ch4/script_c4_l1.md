# Chapter 4 — Lesson 1: From One Container to Many

Welcome to Chapter 4. In Chapter 3 we built a working prototype of our RAG application — and everything ran inside **one** container. Ingestion, query, and all of our code shared a single image and a single process.

That was perfect for prototyping. It is the wrong shape for production. This chapter is about the move from that single container to **one dedicated container per service**, and testing them together in an environment close to production.

[CLICK]

The principle is simple: **one responsibility per container.**

A container should do one job and do it well. When we cram the whole application into one container, we lose the things containers are good at — and we tie together parts of the system that have nothing in common.

[CLICK]

Why split? Five reasons.

**Independent scaling.** Our two pipelines have completely different load profiles. Ingestion is bursty and CPU-heavy — parsing a 500-page PDF and embedding it is a batch job. Query is steady and latency-sensitive — a user waiting for an answer. In one container, you can't scale them separately. Split apart, you can run one ingestion worker and five query replicas.

**Failure isolation.** If a giant document ties up ingestion, query keeps answering. One service's problem doesn't become the whole system's problem.

**Independent deployment.** Fix the query prompt and redeploy the query service in seconds — without rebuilding the heavy Docling parsing stack.

**Right-sized images.** Each image carries only what its service needs. The query image doesn't need a PDF parser; the ingestion image doesn't need the web framework's query routes. Smaller images are faster to ship and have a smaller attack surface.

**Clear boundaries.** Separate services mean separate secrets, separate network exposure, separate resource limits.

[CLICK]

So what are the services in our RAG system?

Three of them. **Ingestion** — parse, chunk, embed, store. **Query** — retrieve, rerank, call the LLM, answer. And the **vector database**, ChromaDB, which has been its own container since Chapter 3.

The nice thing is our prototype already drew the line for us. Look at the API endpoints: `POST /ingest` and the job endpoints belong to ingestion; `POST /query` and `/documents` belong to query. The seam is already there — we're just going to cut along it.

[CLICK]

Here's the destination for this chapter.

Two application services — ingestion on one port, query on another — plus the database, all running as separate containers wired together on one network. A client talks to each service over HTTP.

[CLICK]

And that's what "testing near production" means. Instead of one process where everything can reach everything by virtue of being in the same memory space, we now have separate containers that must talk over a network — with hostnames, ports, and access rules.

That's exactly where the interesting bugs live, and exactly the bugs a single-container prototype hides. By running this topology now, we surface them while they're cheap to fix.

[CLICK]

So the plan for the chapter: in Lesson 2 we build a dedicated image for each service. In Lesson 3 we orchestrate them with Compose. In Lesson 4 we test the whole thing end to end. And in Lesson 5 we cover the testing practices that keep it reliable.

Let's start by giving each service its own image.
