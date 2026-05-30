# Chapter 4 — Lesson 5: Testing Best Practices for Multi-Container Applications

We've split the prototype into services, orchestrated them with Compose, and verified the end-to-end workflow.

In this final lesson, we'll step back and review the practices that help keep a multi-container application reliable and reproducible.

[CLICK]

Let's start with the testing pyramid.

At the base are **unit tests**. These test individual components in isolation, without containers. They're fast, so we can have lots of them.

Next are **service tests**, which validate a single service running in its own container.

Above that are **integration tests**, where multiple services run together and we verify workflows such as ingesting a document and querying it.

At the top are **smoke tests**—a small set of checks that confirm the system is up and responding.

The goal is simple: many fast tests at the bottom and fewer expensive tests at the top.

[CLICK]

Second, add health checks everywhere.

In Lesson 3, we added a health check to ChromaDB. The same pattern applies to every service.

Health checks help control startup order, allow orchestrators to determine when a service is ready, and make troubleshooting much easier when something goes wrong.

[CLICK]

Third, manage your test data carefully.

Integration tests should use small, predictable datasets. A short sample document is better than a large report that slows every test run.

Each test should also use a fresh, temporary database collection so runs don't affect one another.

When the tests finish, clean everything up. Commands such as `docker compose down -v` remove both containers and volumes so the next run starts from a known state.

The goal is reproducibility: the same test should produce the same result every time.

[CLICK]

Fourth, run the full stack in CI.

Bring up the services, run the tests, and tear everything down when the job finishes.

```yaml
- run: docker compose -f docker-compose.test.yaml up -d --build
- run: pytest chapter_4/l4/test_integration.py
- run: docker compose -f docker-compose.test.yaml down -v
```

Because the stack is defined in Compose and the images are versioned, CI runs in the same environment you tested locally and one that closely resembles production.

Every change is validated against the real multi-container architecture before it moves forward.

[CLICK]

To summarize, four practices help keep multi-container applications reliable:

* Fast unit tests
* Health checks on every service
* Predictable and disposable test data
* Running the full stack in CI

[CLICK]

That concludes Chapter 4.

We started with a single-container prototype and transformed it into a multi-service application. We created dedicated images for ingestion and query, orchestrated them with Docker Compose, and tested them together in an environment that closely resembles production.

But we're not production-ready yet.

Our images can still be optimized, security can be improved, and we haven't prepared the application to run in its target environment.

That's the focus of Chapter 5: preparing the application for production by optimizing containers, validating the environment, and getting the system ready to run reliably at scale.
