# Chapter 3 — Lesson 1: Designing Images for Change

Welcome to Chapter 3. We've learned *why* containers matter and *how* the Docker workflow works. Now we start building — this chapter is about prototyping our RAG application inside a containerized development environment.

We begin with a strategy lesson.

[CLICK]

Here's the reality of development: we start with a set of requirements, but those requirements **change**. We add a library, bump a version, pull in a new model, restructure the project. During a prototype, this happens many times a day.

Every one of those changes means rebuilding the image. So the real question for this lesson is: how do we structure the image so that rebuilds stay **fast** as the requirements keep moving?

[CLICK]

Let's recall how an image is built. Docker reads the Dockerfile top to bottom and turns most instructions into a **layer** — a read-only filesystem change stacked on top of the previous one.

The key property is the **build cache**. On a rebuild, Docker walks down the layers and reuses each one as long as nothing above it has changed. The moment it hits an instruction whose inputs changed, that layer and **every layer after it** are rebuilt from scratch.

[CLICK]

That cascade is the whole game. One principle follows from it:

> Put the things that rarely change at the **top**, and the things that change constantly at the **bottom**.

We want the volatile parts — the parts we touch every hour — to live in the last possible layer, so a change there invalidates as little as possible.

[CLICK]

The classic example is dependency installation versus source code.

```dockerfile
# Fragile — code copied before dependencies
COPY . .
RUN pip install -r requirements.txt
```

Here, editing a single line of code changes the `COPY . .` layer, which invalidates the `pip install` below it. Every code change reinstalls every dependency.

```dockerfile
# Cache-friendly — dependencies first, code last
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

Now `pip install` only re-runs when `requirements.txt` actually changes. Editing code only rebuilds the cheap final `COPY` — a sub-second rebuild instead of a multi-minute one.

[CLICK]

Map that onto what we're building. Our RAG development image has roughly three tiers of stability:

* **Rarely changes** — the base OS, system packages, the language runtime, shell setup.
* **Changes sometimes** — the Python dependencies in `requirements.txt`.
* **Changes constantly** — our own project code.

Order the Dockerfile to match: system setup first, dependencies in the middle, project code last. The further down a change lives, the cheaper the rebuild.

[CLICK]

There's one more move worth previewing. If the stable tier almost never changes, why rebuild it at all?

We can split the work into **two images**: a *base image* that carries the heavy, stable tooling, and a *dev image* built `FROM` that base, carrying only the project-specific pieces. The base is built once and reused; day-to-day we only rebuild the thin dev layer on top.

We'll come back to that split in detail in Lesson 5. For now, the takeaway is the mindset.

[CLICK]

Designing for change is not premature optimization — during a prototype, where requirements move fastest, it's the difference between a rebuild you wait through and a rebuild you don't notice.

Stable at the top, volatile at the bottom, and let the cache do the rest.

In the next lesson, we move from a single image to **multiple containers**, and introduce Docker Compose to orchestrate the RAG environment.
