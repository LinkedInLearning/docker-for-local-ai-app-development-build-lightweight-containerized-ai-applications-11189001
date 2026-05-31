# Chapter 5 — Lesson 1: What “Production-Ready” Means

In Chapter 4, we ended with a multi-container application that runs and passes tests. That’s an important milestone — but “it runs locally and in CI” is not the same as “production-ready.”

In this chapter, we take those images the last mile. 

In this first lesson, we define what “production-ready” actually means and use it as a baseline to evaluate where we are today.

[CLICK]

A working image is not a production image. 

[CLICK]

The difference comes down to a small set of properties — a checklist that production images get right, but prototypes often miss.

[CLICK]

First, size. Smaller images pull faster, cost less to store, and reduce the attack surface. Large images are slow to deploy and often include unnecessary dependencies.

[CLICK]

Second, security. That means minimizing what’s inside the image, avoiding embedded secrets, and running with least privilege — not as root.

[CLICK]

Third, portability. The image must run on the target infrastructure. If it only works on your local architecture, it won’t reliably run elsewhere.

[CLICK]

Fourth, distribution. Production images are versioned and stored in a registry so we can consistently pull the exact build we intend to run.

[CLICK]

Fifth, operability. Once running, the container should support health checks, resource limits, graceful shutdown, and observability.

[CLICK]

Before we improve anything, we need a baseline. The first step is to measure where we are today:

```bash
docker images rag-ingestion rag-query     # image sizes
docker history rag-ingestion:0.1.0        # layer breakdown
dive rag-ingestion:0.1.0                  # wasted space per layer
docker scout quickview rag-ingestion:0.1.0 # vulnerability snapshot
```

The ingestion image is heavy, and both images have a broad surface area. That becomes our starting point.

[CLICK]

Each of the remaining lessons in this chapter targets one item in this checklist — size, security, portability, distribution, and operability — and we’ll re-measure after each step to see the improvement.

Next up: the biggest immediate win for image size — multi-stage builds.
