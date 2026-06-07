# Chapter 5 — Lesson 5: Publishing to a Registry

Let's focus now on **distribution**.

A production image needs to live somewhere that other systems can pull from — a CI pipeline, a server, or an orchestrator. That place is a **registry**.

We already saw basic push and pull operations in Chapter 2. In this lesson, we focus on publishing images the way production systems expect them to be published.

[CLICK]

There are several registries. 

**Docker Hub** is the default, GitHub’s **GHCR** integrates with CI pipelines, and every cloud provider offers its own.

Regardless of where you push, the naming follows the same pattern:

`registry/namespace/repository:tag`

The key part is the namespace — that’s where ownership lives.

[CLICK]

The most important production practice is **tagging strategy**.

Always push immutable versions like `0.1.0` or a git commit SHA. Avoid using `latest`.


[CLICK]

The standard workflow is simple: authenticate, tag, and push.

Docker uploads only layers that don’t already exist in the registry:

```bash id="n4p2x8"
docker login
docker tag rag-demo:0.1.0 myuser/rag-demo:0.1.0
docker push myuser/rag-demo:0.1.0
```

[CLICK]

This is where multi-platform builds connect to publishing.

With Buildx, you can build and publish in one step. The `--push` flag builds for all platforms and publishes a single manifest list:

```bash id="k7v1m3"
docker buildx build --platform linux/amd64,linux/arm64 \
  -t myuser/rag-demo:0.1.0 --push chapter_5/l4
```

No intermediate load step needed.

[CLICK]

We can inspect what we published:

```bash id="x1q8zd"
docker buildx imagetools inspect myuser/rag-demo:0.1.0
docker pull myuser/rag-demo:0.1.0
```

One tag now represents multiple architectures, and Docker automatically selects the right one at pull time.

[CLICK]

In production, there’s one more concern: **provenance**.

Every image has a content digest (`sha256:...`) that uniquely identifies the exact build. This allows you to pin and reproduce a specific image precisely.

Tools like **Docker Scout** or image signing tools like **cosign** add verification on top, so you can confirm an image was built from a trusted source and hasn’t been modified.

[CLICK]

One AI-specific consideration: large model images are expensive to distribute.

They take longer to push and pull, and they can hit registry storage and bandwidth limits. That makes tag discipline and layer reuse even more important in AI workloads.

[CLICK]

At this point, the image is built, secured, portable, and published.

In the final chapter, we move from publishing to **operating** these containers in production — and tie everything together into a complete production workflow.
