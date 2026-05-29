# Chapter 4 — Lesson 5: Testing Best Practices for Multi-Container Apps

We've split the prototype into services, orchestrated them, and tested the end-to-end flow. This final lesson of the chapter steps back to the practices that keep a multi-container application reliable and reproducible.

[CLICK]

Start with the shape of your testing — the **testing pyramid**, mapped onto containers.

At the base, **unit tests**. Each module in isolation, no containers at all — our chunker, our retriever, tested directly. They're fast, so there are many of them.

Above that, **service tests**. One container in isolation, checking its routes and contracts behave.

Then **integration tests** — the whole stack together, the ingest-to-query flow we built in Lesson 4. Fewer of these, because they're slower and need everything running.

At the top, **smoke tests**. A handful of sanity calls you run right after a deploy: is each service answering `/health`, can I ingest and query once.

The rule: lots of fast unit tests at the bottom, a few expensive integration tests at the top.

[CLICK]

Second practice: **health and readiness checks**, everywhere.

We added a healthcheck to the database in Lesson 3. The same idea belongs on every service — a `HEALTHCHECK` in the Dockerfile or compose, hitting `/health`. It's what gates startup ordering, what an orchestrator uses to decide a container is ready for traffic, and what tells you *which* service is down when something breaks.

[CLICK]

Third: **manage your test data.**

Integration tests need data, and that data must be predictable. Use a small, fixed sample document — not a 500-page report that makes every test run slow. Give each test run a **fresh, ephemeral** database collection so runs don't contaminate each other. And tear it down afterward — `docker compose down -v` removes the volumes too, so the next run starts clean.

Reproducibility is the goal: the same test, run twice, gives the same result.

[CLICK]

Fourth: **run the whole stack in CI.**

This is what ties it together. In your pipeline, bring the stack up, run the tests against it, tear it down.

```yaml
- run: docker compose -f docker-compose.test.yaml up -d --build
- run: pytest chapter_4/l4/test_integration.py
- run: docker compose -f docker-compose.test.yaml down -v
```

Because the stack is defined in a Compose file and the images are pinned, the environment in CI is the same one you ran locally — and close to production. Every change gets tested against the real multi-container topology, automatically.

[CLICK]

So, the four practices: a testing pyramid weighted toward fast unit tests; health checks on every service; disciplined, ephemeral test data; and the full stack exercised in CI.

[CLICK]

That closes Chapter 4. We took a single-container prototype, split it into dedicated services — a lean query image and a heavy ingestion image — orchestrated them with Compose, and tested that they cooperate over the network in an environment close to production.

But "close to production" is not production. Our images aren't optimized for size or security, we haven't deployed anywhere, and there's no scaling or real observability.

That's Chapter 5: **preparing the application for production** — optimizing the containers, deploying to a server or the cloud, and validating the system in its target environment.
