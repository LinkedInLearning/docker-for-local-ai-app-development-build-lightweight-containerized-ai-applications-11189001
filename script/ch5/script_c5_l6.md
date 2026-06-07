# Chapter 5 — Lesson 6: Best Practices & Going Live

At this point, our image is built, hardened, portable, and published.

Let's focus on  **operability** — what keeps it stable once it’s running — and **validation** before it reaches production. This lesson brings everything together and closes the course.

[CLICK]

Start with **runtime guardrails**.

A container without limits can consume all available host resources. In production, we define clear boundaries and restart behavior:

```bash id="a91k3d"
docker run --memory 1g --cpus 1.5 --restart unless-stopped \
  --read-only myuser/rag-query:0.1.0
```

[CLICK]

Next, **graceful shutdown and health checks**.

Containers should handle `SIGTERM` so in-flight requests can complete cleanly when the platform stops them.

We also define a `HEALTHCHECK` so the orchestrator can distinguish between “started” and “ready”:

```dockerfile id="h2m8qz"
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
```

[CLICK]

Before releasing anything, we **validate the final artifact**.

This means running the actual production image — not a development environment — and checking the essentials: the service starts, `/health` responds, a real query works, and the image passes a security scan.

This is different from Chapter 4 integration tests. Those verified service behavior in a composed system. Here we verify the **image itself**, as it will be shipped.

[CLICK]

All of this belongs in **CI**, so it runs automatically on every change.

A production pipeline typically follows this flow: build → scan → test → publish.

[CLICK]

In a real workflow, that looks like this:

```yaml id="c7k2v9"
# .github/workflows/main.yml (excerpt)
- run: docker build -f docker/Dockerfile_Query -t rag-query:${{ github.sha }} .
- run: docker scout cves --exit-code --only-severity critical,high rag-query:${{ github.sha }}
- run: pytest tests/
- run: docker buildx build --platform linux/amd64,linux/arm64 \
         -t myuser/rag-query:${{ github.ref_name }} --push docker/
```

If any step fails, the image is not published.

[CLICK]

Let’s step back.

The readiness checklist from Lesson 1 is now complete:

* **Size** → multi-stage builds
* **Security** → non-root, pinned, scanned
* **Portability** → multi-platform builds
* **Distribution** → versioned and published images
* **Operability** → limits, health checks, CI validation

[CLICK]

One final note on scope.

This course focused on making AI applications **production-ready at the image and container level**. It did not cover orchestration at scale (like Kubernetes) or full observability platforms. Those come next, once the foundation is solid.

[CLICK]

And that’s the journey — from understanding why containers matter, to building, testing, and finally preparing production-ready AI systems.

Thanks for following along.
