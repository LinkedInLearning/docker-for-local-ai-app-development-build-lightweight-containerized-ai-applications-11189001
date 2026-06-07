# Chapter 5 — Lesson 3: Securing Production Images

Our image is smaller. Now let’s make it **secure**.

[CLICK]

Container security comes down to three core practices: reduce the attack surface, run with least privilege, and continuously scan for vulnerabilities.

[CLICK]

Start with the simplest and most important change: **don’t run as root**.

By default, containers run as root. If a process escapes the container, it inherits those privileges on the host — which is exactly what we want to avoid.

We fix this by creating a non-root user and switching to it:

```dockerfile
RUN useradd --create-home --uid 10001 appuser
USER appuser
```

[CLICK]

Next, **pin the base image**.

A tag like `python:3.11-slim` can change over time, which breaks reproducibility. For fully deterministic builds, pin the image by digest:

```dockerfile
FROM python:3.11-slim@sha256:<digest>
```

Whenever possible, use minimal base images like `slim` or `distroless` to reduce what’s included by default.

[CLICK]

Next, **keep secrets out of the image**.

API keys and tokens must never be baked into layers. Once included, they are cached, shared, and pushed to registries.

Instead, pass them at runtime and verify they are not present in the image history:

```bash
docker history --no-trunc rag-query:0.1.0   # ensure no secrets appear
```

[CLICK]

Next, **minimize what’s installed and what’s exposed**.

During builds, avoid unnecessary packages using the `--no-install-recommends` flag, and clean up package caches in the same layer.

At runtime, you can further harden the container by using a read-only filesystem and removing Linux capabilities:

```bash
docker run --read-only --cap-drop ALL rag-query:0.1.0
```

[CLICK]

Now, **scan the image**.

A vulnerability scanner inspects installed packages and reports known CVEs:

```bash
docker scout cves rag-query:0.1.0
# or: trivy image --severity HIGH,CRITICAL rag-query:0.1.0
```

[CLICK]

Scanning is only useful if it leads to action. When you find a CVE, upgrade the affected dependency or base image, rebuild, and re-scan.

That loop — scan, fix, re-scan — is the workflow you want to build into your process.

[CLICK]

One important AI-specific rule: never bake secrets or model assets into the image.

That includes API keys like `OPENAI_API_KEY` and large model weights. You can verify leaks using `docker history`, then move those values to runtime configuration or external storage.

[CLICK]

At this point, the image is both smaller and safer: it runs as a non-root user, is pinned for reproducibility, contains no secrets, and is continuously scanable.

Next, we’ll make it portable across environments with multi-platform builds.
