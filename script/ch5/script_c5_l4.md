# Chapter 5 — Lesson 4: Multi-Platform Builds with Buildx

The next column is **portability**. Here's the everyday reality: you develop on one CPU architecture and deploy on another. Apple Silicon laptops are `arm64`; a lot of cloud runs `amd64`; some cloud is ARM. The image has to match where it runs.

[CLICK]

The problem is concrete. An image built only for `amd64` either won't start on an `arm64` host, or it silently runs under emulation and crawls. Build for the wrong architecture and you find out in production.

[CLICK]

The tool is **Buildx**, Docker's interface to the BuildKit engine. The default `docker` builder can only build for your current architecture; a **`docker-container`** builder can build for many:

```bash
docker buildx create --name multiarch --driver docker-container --use --bootstrap
docker buildx inspect --bootstrap        # lists the platforms it can target
```

[CLICK]

With that builder, one source builds for many platforms — you just name them:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t rag-demo:0.1.0 .
```

One Dockerfile, two binaries.

[CLICK]

How does it build `arm64` on an `amd64` machine? **Emulation** — QEMU, bundled with Docker Desktop. It's convenient and it works, but it's slow. For speed at scale you'd use **native builders** for each architecture instead.

[CLICK]

When you build for several platforms under one tag, the result is a **manifest list** — a single name that points at one image per architecture. A plain `docker pull` then automatically picks the right one for the machine doing the pulling.

[CLICK]

The demo uses a tiny image that prints the architecture it's running on, so the point is visible:

```bash
docker buildx build --platform linux/amd64 --load -t rag-demo:amd64 chapter_5/l4
docker run --rm --platform linux/amd64 rag-demo:amd64    # -> x86_64
docker buildx build --platform linux/arm64 --load -t rag-demo:arm64 chapter_5/l4
docker run --rm --platform linux/arm64 rag-demo:arm64    # -> aarch64
```

Same source, two architectures, proven by the output.

[CLICK]

The AI catch: multi-platform isn't free for heavy images. Not every dependency publishes wheels for every architecture — some native or torch builds will fail or fall back to a slow source compile under emulation. Worth knowing before you promise an ARM build.

[CLICK]

Our image is now portable. But notice: a multi-arch image under one tag is a manifest list, and that only lives in a **registry**.

Next: publishing.
