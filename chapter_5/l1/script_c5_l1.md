# Chapter 5 — Lesson 1: What "Production-Ready" Means

Chapter 4 left us with a multi-container application that **runs and passes its tests**. That is a real milestone — but "runs on my machine and in CI" is not the same as "ready for production."

This chapter takes those images the last mile. This first lesson defines what *production-ready* actually means, and measures where our images stand against that bar.

[CLICK]

A **working** image is not a **production** image. The difference is a checklist — five things a production image gets right that a prototype usually doesn't.

[CLICK]

First, **size**. Smaller images pull faster, cost less to store, and expose a smaller attack surface. A multi-gigabyte image is slow to deploy and full of things an attacker could use.

[CLICK]

Second, **security**. A minimal surface, no secrets baked into layers, no known vulnerabilities, and least privilege — not running as root.

[CLICK]

Third, **portability**. The image has to run on the CPU architecture you deploy to. An image built only for your laptop's architecture may not run on the server.

[CLICK]

Fourth, **distribution**. A production image is **versioned** and **published** to a registry, so a deploy target can pull exactly the build you intend.

[CLICK]

Fifth, **operability**. Once it's running, it needs resource limits, health checks, graceful shutdown, and a way to observe it.

[CLICK]

Before we fix anything, let's **measure**. You can't improve what you don't baseline:

```bash
docker images rag-ingestion rag-query     # how big are we starting?
docker history rag-ingestion:0.1.0        # which layers dominate?
dive rag-ingestion:0.1.0                   # wasted space, layer by layer
docker scout quickview rag-ingestion:0.1.0 # CVE count at a glance
```

The heavy ingestion image is large and has a wide surface. That's our starting point.

[CLICK]

Each remaining lesson attacks one column of that checklist — size, security, portability, distribution, operability — and we re-measure to prove the gain.

Next: the single biggest lever on size — multi-stage builds.
