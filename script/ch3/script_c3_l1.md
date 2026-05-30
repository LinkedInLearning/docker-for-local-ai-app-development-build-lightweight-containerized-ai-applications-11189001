# Chapter 3 — Lesson 1: Designing Images for Change

Welcome to Chapter 3.

[CLICK]

By now we understand *why* we want to develop AI applications inside containers, and we've worked through the **Docker workflow** — building, running, and sharing images. With that foundation in place, we can start focusing on the **development lifecycle** of an AI application.

That lifecycle runs in three stages — **prototype**, **test**, and **deploy**. In this chapter we focus on the first stage: the **prototype**, where we build a containerized development environment that will enable us to start prototype our RAG application in a reproducible environment. Testing comes in Chapter 4, and preparing for production in Chapter 5.

We begin with a strategy lesson on designing a development image for the prototyping stage of the AI application.

[CLICK]

Here's the reality of development: we start with a set of requirements, but those requirements **change**. We add a library, bump a version, pull in a new model, and restructure the project. During a prototype, this happens often.

Every one of those changes means rebuilding the image. So the real question for this lesson is: how do we structure the image so that rebuilds stay **fast** as the requirements keep moving?

[CLICK]

We covered the build cache in Chapter 2, so here’s a quick reminder.

Docker builds images layer by layer, from top to bottom. It reuses cached layers as long as nothing changes. But once a layer changes, Docker rebuilds that layer and everything after it.

This gives us an important rule for fast rebuilds: the position of a change in the Dockerfile matters. Changes near the top trigger more rebuilds, while changes near the bottom affect less.

So, when possible, we place things that rarely change at the top, and things we change often at the bottom.

[CLICK]

Map that onto what we're building. Our RAG development image has roughly three tiers of stability:

* **Rarely changes** — the base OS, system packages, the language runtime, shell setup.
* **Changes sometimes** — the Python dependencies in `requirements.txt`.
* **Changes constantly** — our own project code.

Order the Dockerfile to match: system setup first, dependencies in the middle, project code last. The further down a change lives, the faster the rebuild.

[CLICK]

There’s one more useful idea to preview.

If the stable part of the environment rarely changes, we don’t need to rebuild it every time.

Instead, we can split the setup into two images: a base image with the heavy, stable tooling, and a dev image built on top of it with only the project-specific parts. The base image is built once and reused, while the dev image is rebuilt as the project evolves.

[CLICK]

Designing for change is not premature optimization — during a prototype, where requirements move fastest, it's the difference between a rebuild you wait through and a rebuild you don't notice.

Stable at the top, volatile at the bottom, and let the layers caching do the rest.

[CLICK]

Let's now pivot to VSCode and review the RAG prototype Dockerfile settings. 

---

> **🎬 LIVE WALKTHROUGH — pivot to VS Code.**
> Switch to VS Code and open the RAG project's `docker/` folder. Show
> `Dockerfile_Base` and `Dockerfile_Dev` (side by side if you can). This is the
> base/dev split from the previous slide, made real.

Let's make this concrete — this is exactly how the RAG project's own images are built. I'll switch over to VS Code and open the `docker/` folder.

First, **`Dockerfile_Base`** — the foundation tier:

```dockerfile
FROM ubuntu:22.04
ARG QUARTO_VER="1.7.32"
ENV QUARTO_VER=$QUARTO_VER
COPY install_quarto.sh install_dependencies.sh setting_git.sh settings/
RUN bash ./settings/install_dependencies.sh
RUN bash ./settings/install_quarto.sh $QUARTO_VER
```

This is the most stable layer of the whole stack. It starts from `ubuntu:22.04`, installs the system dependencies and shell setup, and adds Quarto. Notice what's *not* here: no Python packages, no project code. That's deliberate. This image is built **once**, pushed to a registry as `python-base`, and reused — we almost never rebuild it.

Now **`Dockerfile_Dev`** — the volatile tier we rebuild as the prototype evolves:

```dockerfile
FROM docker.io/rkrispin/python-base:0.0.4
ARG PYTHON_VER="3.11"
ARG VENV_NAME="my_project"
ARG RUFF_VER="0.12.0"
ENV HF_HOME=/opt/hf-cache
COPY install_uv.sh requirements.txt cache_docling_models.py settings/
RUN bash ./settings/install_uv.sh $VENV_NAME $PYTHON_VER $RUFF_VER
RUN mkdir -p $HF_HOME \
    && /opt/$VENV_NAME/bin/python ./settings/cache_docling_models.py
```

The very first line is the whole point: it builds `FROM` the `python-base` image we just looked at. It does **not** reinstall the OS or Quarto — that work is already baked into the base.

What the dev image *adds* is the project-specific tier. The build args at the top let us pin the **Python version**, the **virtual-environment name**, and the **Ruff** linter version without editing the file. `install_uv.sh` sets up the Python environment with `uv`; we install our `requirements.txt`; and we pre-download the Docling and HuggingFace models into `HF_HOME` so the first run isn't slow. These are the pieces that move as the prototype changes — so they live in the dev image, never in the base.

So that's the principle in practice: a heavy, stable **base** built once, and a lighter **dev** image — `FROM` that base — that we rebuild all day. Stable on top, volatile on the bottom.

Back to the slides.

---

In the next lesson, we move from a single image to **multiple containers**, and introduce Docker Compose to orchestrate the RAG environment.
