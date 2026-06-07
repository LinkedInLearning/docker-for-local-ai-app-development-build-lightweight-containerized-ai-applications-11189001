# Chapter 5 — Lesson 4: Multi-Platform Builds with Buildx

In this lesson we will focus on **portability**.

In practice, we often develop on one architecture and deploy on another. Apple Silicon machines use `arm64`, while most cloud environments still run `amd64`. The image has to work across both.

[CLICK]

The issue is straightforward but important.

An image built for one architecture may not run on another. At best, it falls back to slow emulation. At worst, it fails completely. Either way, you only discover the problem when you try to run it in a different environment.

[CLICK]

To solve this, we use **Buildx**, Docker’s extended build system powered by BuildKit.

The default builder only targets your local architecture. Buildx, using the `docker-container` driver, can build for multiple platforms:

```bash id="q8k1m2"
docker buildx create --name multiarch --driver docker-container --use --bootstrap
docker buildx inspect --bootstrap
```

[CLICK]

Once the builder is set up, we can build for multiple architectures from a single Dockerfile:

```bash id="p2m8v7"
docker buildx build --platform linux/amd64,linux/arm64 -t rag-demo:0.1.0 .
```

One source, multiple architectures.

[CLICK]

So how does this work?

On a different architecture than the host, Docker uses **emulation** via QEMU, which is included with Docker Desktop. This makes cross-platform builds easy, but slower. At scale, teams often prefer native builders per architecture for performance.

[CLICK]

When you build multiple platforms under one tag, Docker produces a **manifest list**. This is a single image name that points to multiple architecture-specific images.

When you pull the image, Docker automatically selects the correct version for your machine.

The course main image we build with this method, let's go to VScode and see the execution file.

[CLICK]

Let’s make this visible with a small demo image that prints its architecture:

```bash id="l9w3xq"
docker buildx build --platform linux/amd64 --load -t rag-demo:amd64 chapter_5/l4
docker run --rm --platform linux/amd64 rag-demo:amd64    # x86_64

docker buildx build --platform linux/arm64 --load -t rag-demo:arm64 chapter_5/l4
docker run --rm --platform linux/arm64 rag-demo:arm64    # aarch64
```

Same code, different architectures — confirmed at runtime.

[CLICK]

One important caveat for AI workloads: multi-platform builds are not always seamless.

Many heavy dependencies don’t publish prebuilt binaries for every architecture. In those cases, builds may fall back to slow source compilation or fail entirely.

[CLICK]

At this point, our image is portable across architectures. But there’s an important detail: a multi-architecture image only exists as a **manifest list**, and that lives in a registry.

Next, we’ll look at publishing images so they can be shared and deployed consistently.
