# Chapter 5 — Lesson 6: Best Practices & Going Live

Our image is built, hardened, portable, and published. The last column is **operability** — keeping it reliable once it's running — and **validation** before it ships. This lesson ties the chapter together and closes the course.

[CLICK]

Start with **runtime guardrails**. A container with no limits can consume the whole host. In production you cap it and tell the platform how to handle failure:

```bash
docker run --memory 1g --cpus 1.5 --restart unless-stopped \
  --read-only myuser/rag-query:0.1.0
```

[CLICK]

Then **graceful shutdown and health**. Handle `SIGTERM` so in-flight work finishes when the platform stops the container, and add a `HEALTHCHECK` so the orchestrator knows when it's actually ready — not just started:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
```

[CLICK]

Before shipping, **validate the built artifact** — the real production image, not a dev shell. Run it, hit `/health`, send a real query, and scan it. This is different from Chapter 4's integration tests: those checked *behavior*; this checks the *image you're about to ship*.

[CLICK]

All of this belongs in **CI** so it happens on every change, not by memory. A production pipeline is: build → scan → test → publish.

[CLICK]

Wired into the project's existing workflow, the key steps look like this:

```yaml
# .github/workflows/main.yml (excerpt)
- run: docker build -f docker/Dockerfile_Query -t rag-query:${{ github.sha }} .
- run: docker scout cves --exit-code --only-severity critical,high rag-query:${{ github.sha }}
- run: pytest tests/
- run: docker buildx build --platform linux/amd64,linux/arm64 \
         -t myuser/rag-query:${{ github.ref_name }} --push docker/
```

A failing scan or test stops the publish.

[CLICK]

Now the recap. The readiness checklist from Lesson 1 — every column, checked off: **size** (multi-stage), **security** (non-root, pinned, scanned), **portability** (buildx), **distribution** (versioned + published), **operability** (limits, health, CI).

[CLICK]

And honesty about scope. This course did **not** cover orchestration at scale — Kubernetes, autoscaling — or a full observability stack. Those are the natural next steps once your images are production-ready, which now they are.

[CLICK]

That's the journey: from "why containers" in Chapter 1, through building, developing, and testing, to production-ready AI images here.

That's the course. Thank you.
