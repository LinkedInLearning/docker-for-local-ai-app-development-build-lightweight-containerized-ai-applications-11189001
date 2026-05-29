# Chapter 5 · Lesson 5 — Publishing to a Registry (Docker Hub) · Demo Runbook

> Recording guide for the publishing demo. The full lesson `README.md` /
> `script_c5_l5.md` / `slides_c5_l5.html` are authored separately; this is the
> hands-on steps to run on screen.

This lesson reuses the **Lesson 4 demo image** (`chapter_5/l4/`) — we built it
multi-platform, now we publish it. Demo asset in this folder:

| File | Role |
| ---- | ---- |
| `publish_demo.sh` | the scripted walk-through (steps 2–5 below) |

**Registry:** Docker Hub (`docker.io`). The same flow works for GHCR — just log
in to `ghcr.io` and namespace the tag `ghcr.io/<user>/rag-demo`.

All commands run from the **repository root**. Set your Docker Hub username:

```bash
export DOCKER_USER=your-dockerhub-username
```

## 1. Log in (interactive — run this yourself before the script)

```bash
docker login
# username + an access token (preferred over a password; revocable)
```

## 2. Single-arch: tag and push (the everyday case)

```bash
docker buildx build --load -t rag-demo:0.1.0 chapter_5/l4
docker tag rag-demo:0.1.0 "$DOCKER_USER/rag-demo:0.1.0"
docker push "$DOCKER_USER/rag-demo:0.1.0"
```

## 3. Multi-arch: build both platforms and push as one manifest list

`buildx --push` builds and publishes in a single step — no `--load` needed.

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t "$DOCKER_USER/rag-demo:0.1.0" --push chapter_5/l4
```

## 4. Inspect the published manifest list

One tag, multiple architectures — `docker pull` later picks the right one.

```bash
docker buildx imagetools inspect "$DOCKER_USER/rag-demo:0.1.0"
```

## 5. Pull it back

```bash
docker pull "$DOCKER_USER/rag-demo:0.1.0"
docker run --rm "$DOCKER_USER/rag-demo:0.1.0"
```

## Or just run the script

```bash
docker login
DOCKER_USER=your-dockerhub-username bash chapter_5/l5/publish_demo.sh
```

## Talking points

- **Tagging strategy** — push an **immutable version** (`0.1.0`, or a git SHA),
  not just `latest`. `latest` is a *moving* tag: it silently changes and makes
  "which build is running in prod?" unanswerable.
- **Layers are deduplicated** over the network — only layers the registry lacks
  are uploaded (same caching idea as builds).
- **`buildx --push`** is the bridge from Lesson 4: build multi-arch *and*
  publish the manifest list in one command.
- **Provenance** — the image digest (`@sha256:...`) identifies an exact build;
  signing/attestations (cos: cosign, `docker scout`) let consumers verify it.
- **AI note** — large images make push/pull slow and bump up against registry
  storage and pull-rate limits; tag hygiene matters more, not less.
