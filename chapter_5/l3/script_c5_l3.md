# Chapter 5 — Lesson 3: Securing Production Images

Our image is smaller. Now let's make it **safe**. Security in a container image comes down to three habits: reduce the attack surface, run with least privilege, and scan for known vulnerabilities.

[CLICK]

Start with the biggest, easiest win: **don't run as root.** By default a container process is root, and a process that escapes a root container is root on concerns it shouldn't reach. Create an unprivileged user and switch to it:

```dockerfile
RUN useradd --create-home --uid 10001 appuser
USER appuser
```

[CLICK]

**Pin the base image.** `FROM python:3.11-slim` floats — the tag moves under you. For a reproducible, verifiable build, pin by **digest**:

```dockerfile
FROM python:3.11-slim@sha256:<digest>
```

And prefer a minimal base — `slim` or `distroless` — so there's simply less in the image to attack.

[CLICK]

**Keep secrets out of the image.** API keys and tokens must never be baked into a layer — layers are cached, shared, and pushed. Pass them at runtime instead, and verify nothing leaked:

```bash
docker history --no-trunc rag-query:0.1.0   # no keys should appear here
```

[CLICK]

**Drop what you don't need.** Use `--no-install-recommends`, clean the apt lists in the same layer, and at runtime add a **read-only root filesystem** and **drop Linux capabilities**:

```bash
docker run --read-only --cap-drop ALL rag-query:0.1.0
```

[CLICK]

Now **scan**. A scanner reads your image's packages and reports known CVEs:

```bash
docker scout cves rag-query:0.1.0
# or:  trivy image --severity HIGH,CRITICAL rag-query:0.1.0
```

[CLICK]

A scan is only useful if you act on it. Bump the offending base image or dependency to a fixed version, rebuild, and **re-scan** to prove the CVE is gone. That loop — scan, fix, re-scan — is the habit.

[CLICK]

The AI-specific trap: never bake `OPENAI_API_KEY` or downloaded **model weights** into the image. Show the leak with `docker history`, then inject the key at runtime and mount or download weights as data — not as a baked layer.

[CLICK]

The image is now smaller **and** hardened: non-root, pinned, secret-free, scanned.

Next: making it run anywhere — multi-platform builds.
