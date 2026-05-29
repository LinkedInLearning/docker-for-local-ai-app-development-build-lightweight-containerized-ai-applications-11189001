# Chapter 5 · Lesson 4 — Multi-Platform Builds with Buildx · Demo Runbook

> Recording guide for the buildx demo. The full lesson `README.md` /
> `script_c5_l4.md` / `slides_c5_l4.html` are authored separately; this is the
> hands-on steps to run on screen.

Demo asset files in this folder:

| File | Role |
| ---- | ---- |
| `Dockerfile` | tiny, dependency-free demo image (slim, non-root) |
| `app.py` | prints the CPU architecture it runs on |
| `buildx_demo.sh` | the scripted walk-through (steps 1–3 below) |

**Why a tiny image?** A multi-arch build of the real `rag-ingestion` image
(torch, Docling) emulates for a long time and can hit *missing-wheel* errors on
an architecture — a great talking point, but painful on camera. This image
builds in seconds on every arch. **The commands are identical for the real
image** — just swap the `-f`/context, e.g.
`docker buildx build --platform linux/amd64,linux/arm64 -f chapter_5/l2/Dockerfile_Ingestion .`

All commands run from the **repository root**.

## 0. Prerequisite — emulators

Docker Desktop already includes them. On plain Linux, install once:

```bash
docker run --privileged --rm tonistiigi/binfmt --install all
```

## 1. Create a multi-platform builder

The default `docker` driver can't build multi-arch; the `docker-container`
driver can.

```bash
docker buildx create --name multiarch --driver docker-container --use --bootstrap
docker buildx inspect --bootstrap        # lists supported platforms (incl. emulated)
```

## 2. Build each architecture and run it

```bash
# amd64
docker buildx build --platform linux/amd64 --load -t rag-demo:amd64 chapter_5/l4
docker run --rm --platform linux/amd64 rag-demo:amd64     # -> x86_64

# arm64 (native on Apple Silicon, emulated on x86)
docker buildx build --platform linux/arm64 --load -t rag-demo:arm64 chapter_5/l4
docker run --rm --platform linux/arm64 rag-demo:arm64     # -> aarch64
```

The architecture in each line of output changes — same source, two binaries.

## 3. The catch: one tag, many arches = a manifest list

`--load` puts a single image in your local store, so you can't `--load` a
multi-arch build. Combining both architectures under **one tag** produces a
**manifest list**, and that only lives in a registry — which is Lesson 5.

```bash
# This is the bridge to publishing (it needs --push, see Lesson 5):
# docker buildx build --platform linux/amd64,linux/arm64 -t USER/rag-demo:0.1.0 --push chapter_5/l4
```

## Or just run the script

```bash
bash chapter_5/l4/buildx_demo.sh
```

## Talking points

- One Dockerfile → binaries for many CPU architectures.
- Develop on Apple Silicon (arm64), deploy to x86 cloud (amd64) — buildx covers both.
- Emulation (QEMU) is convenient but slow; native builders are faster.
- A multi-arch tag is a **manifest list**; `docker pull` auto-selects the caller's arch.
- AI caveat: not every dependency publishes wheels for every arch (e.g. some
  native/torch builds) — multi-platform isn't free for heavy images.
