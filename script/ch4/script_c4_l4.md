# Chapter 4 — Lesson 4: Networking, Health & Integration Testing

The stack is running. But running is not the same as working.

In this lesson, we'll review how separate services communicate, why health checks matter, and what an integration test should validate in a multi-container application. The hands-on exercises, commands, and expected outputs are provided in this lesson's README.

[CLICK]

Let's start with service communication.

In our prototype, everything ran in a single process, so components could call each other directly. Now they run in separate containers and communicate over a network.

The ingestion service and query service don't talk to each other directly. Instead, they share state through the database. Ingestion writes vectors to ChromaDB, and query reads them back.

That database becomes the contract between the two services.

Both services reach the database using its service name, `chromadb`, on port `8000`. Docker Compose handles the networking and service discovery for us, so there's no need to manage IP addresses.

[CLICK]

Next, health and readiness.

Each service exposes a `/health` endpoint. These endpoints help us verify that a service is ready before it begins handling requests.

We already saw one example in Lesson 3, where a database health check controlled the startup order of the stack.

The same pattern applies to application services. Health endpoints provide a simple way to verify availability and are commonly used by load balancers and orchestration platforms to determine whether traffic should be routed to a service.

[CLICK]

Now let's look at integration testing.

An integration test validates that multiple services work together correctly.

For our RAG application, a typical test begins by ingesting a document through the ingestion service. Once processing completes, the query service retrieves information from that document and generates a response.

If the expected answer is returned, we've verified several things at once:

* The services can communicate over the network.
* Both services can access the shared database.
* The ingestion workflow completed successfully.
* The query workflow can retrieve and use the stored information.

In other words, we've validated the complete workflow across service boundaries.

The README for this lesson walks through this process step by step, including manual testing with `curl`, verifying service-name DNS, and running an automated integration test with `pytest`.

[CLICK]

That's the core idea behind multi-container testing.

We're not just checking that individual containers start successfully. We're verifying that independent services can communicate, share data, and complete real application workflows together.

In the final lesson of this chapter, we'll step back and review the testing practices that help keep multi-container applications reliable and reproducible.
