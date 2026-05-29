# Chapter 5 — Lesson 3: Securing Production Images

> **Learning goal:** reduce attack surface and run with least privilege
> (non-root, pinned base, no baked secrets), and scan for and triage
> vulnerabilities.

The image is smaller; now make it **safe**. Container-image security is three
habits: shrink the attack surface, run with least privilege, and scan for known
vulnerabilities.

---

## 1. Run as non-root

A container process is root by default. Create an unprivileged user and switch:

```dockerfile
RUN useradd --create-home --uid 10001 appuser
USER appuser
```

---

## 2. Pin the base, keep it minimal

A floating tag (`python:3.11-slim`) moves under you. Pin by **digest** for a
reproducible, verifiable build, and prefer a minimal base:

```dockerfile
FROM python:3.11-slim@sha256:<digest>
```

`slim` or `distroless` means less in the image to attack.

---

## 3. Keep secrets out of layers

API keys and tokens must never be baked in — layers are cached, shared, and
pushed. Pass them at runtime and verify nothing leaked:

```bash
docker run -e OPENAI_API_KEY rag-query:0.1.0          # injected, not baked
docker history --no-trunc rag-query:0.1.0             # no secret should appear
```

---

## 4. Drop what you don't need

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```

At runtime, tighten further:

```bash
docker run --read-only --cap-drop ALL rag-query:0.1.0
```

---

## 5. Scan, fix, re-scan

A scanner reports known CVEs in your image's packages:

```bash
docker scout cves rag-query:0.1.0
# or:  trivy image --severity HIGH,CRITICAL rag-query:0.1.0
```

Act on it: bump the offending base or dependency to a fixed version, rebuild,
and **re-scan** to prove the CVE is gone. That loop is the habit.

> We lead with `docker scout` (bundled with Docker Desktop); `trivy` is the
> common CI alternative.

---

## 6. AI note

Never bake `OPENAI_API_KEY` or downloaded **model weights** into the image.
Confirm the leak with `docker history`, then inject the key at runtime and treat
weights as mounted/downloaded data — not a baked layer.

---

Next: making the image run anywhere — **multi-platform builds with Buildx**.
