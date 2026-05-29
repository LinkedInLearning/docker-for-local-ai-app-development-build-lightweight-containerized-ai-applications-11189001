# Chapter 5 — Lesson 5: Publishing to a Registry

The **distribution** column. A production image has to live somewhere a deploy target can pull it from — a server, an orchestrator, a CI runner. That somewhere is a **registry**.

We covered the basics of pulling and pushing back in Chapter 2. This lesson is about publishing *for production*.

[CLICK]

There are several registries — **Docker Hub** is the default, GitHub's **GHCR** ties into GitHub Actions, and every cloud has its own. Wherever it goes, the image is named `registry/namespace/repository:tag`, and the namespace is yours.

[CLICK]

The most important production habit is **tagging strategy**. Push an **immutable version** — `0.1.0`, or the git commit SHA — never just `latest`. `latest` is a *moving* tag: it silently changes, so "which build is in production?" becomes unanswerable. Version tags are how you roll back with confidence.

[CLICK]

The everyday push: log in, tag for your namespace, push. Docker uploads only the layers the registry doesn't already have:

```bash
docker login
docker tag rag-demo:0.1.0 myuser/rag-demo:0.1.0
docker push myuser/rag-demo:0.1.0
```

[CLICK]

This is where multi-platform meets publishing. `buildx --push` builds for every platform **and** publishes the manifest list in a single step — no intermediate `--load`:

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t myuser/rag-demo:0.1.0 --push chapter_5/l4
```

[CLICK]

Inspect what you published — one tag, multiple architectures — then pull it back and watch Docker select the right one:

```bash
docker buildx imagetools inspect myuser/rag-demo:0.1.0
docker pull myuser/rag-demo:0.1.0
```

[CLICK]

For production you also care about **provenance** — proving an image is the build you think it is. Every image has a content **digest** (`@sha256:...`) that pins an exact build, and tools like cosign or `docker scout` can **sign** images and attach attestations so consumers can verify them.

[CLICK]

The AI note: large images make publishing slower and bump into registry **storage** and **pull-rate** limits. With multi-gigabyte AI images, tag hygiene and layer caching matter more, not less.

[CLICK]

Our image is now built, hardened, portable, and published.

Last lesson: operating it in production — and the best practices that tie the chapter together.
