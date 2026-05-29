# Chapter 1 — Lesson 4: Containerized Development Workflow for AI Applications

> **Learning goal:** Outline the end-to-end containerized workflow — spec,
> development, test, deployment — and map each stage to the chapters that
> follow.

Lesson 3 left us with a **container strategy**: identify the services,
define their requirements, then decide how to package them across
development, test, and deployment. This lesson answers the obvious next
question — **how do we actually execute that plan?**

This is the workflow we'll follow for the rest of the course, from the
first idea to a system running in production. Each stage maps to a later
chapter, so think of this lesson as the map for everything that follows.

---

## 0. The shape of the workflow

```
  Spec  →  Development  →  Test  →  Deployment
  (ch2)      (ch3)        (ch4)      (ch5)
```

Four stages. The same containerized environment carries through all of
them — that's the whole point. Containers are not a thing you bolt on at
the end to "ship it"; they're how you develop and test in the first
place.

---

## 1. Start with a spec

Before writing code or building an image, work **with your AI
code-generation tool** to turn the project scope into a clear
requirements document. The output is a **project spec**.

A good spec covers:

| Part                     | What it captures                                         |
| ------------------------ | -------------------------------------------------------- |
| **Environment settings** | Language version, libraries, system packages             |
| **Infrastructure**       | Services (e.g. the vector DB), ports, volumes            |
| **Architecture**         | The services from Lesson 3 and how they connect          |
| **Implementation stages**| How the system gets built, step by step                  |

Writing the spec *with* an AI tool is fast and iterative: you describe
the scope, the tool drafts structure, you refine. The point isn't to
generate code yet — it's to converge on a written plan everyone (you,
your team, and the tooling) can build against.

> The spec is the single source of truth. Every container we build later
> traces back to a requirement written here.

---

## 2. The spec builds the dev image

One section of the spec matters most right now: the **development
environment requirements**. These describe exactly what the dev
environment needs — and they become the recipe for the **development
image**.

That recipe runs through the core Docker workflow:

```
requirements  →  Dockerfile  →  docker build  →  image  →  docker run  →  container
```

* **requirements** — what the environment needs (from the spec)
* **Dockerfile** — the build instructions
* **image** — a reproducible, shareable snapshot
* **container** — the running environment you actually work in

We'll spend all of **Chapter 2 (Docker 101)** on this workflow — how to
write a Dockerfile, build an image, run a container, and the best
practices that keep images small, fast, and safe.

---

## 3. Stage 1 — Development  → Chapter 3

Following the Lesson 3 strategy, development starts with **two
containers**:

| Container               | Role                                                       |
| ----------------------- | ---------------------------------------------------------- |
| **ChromaDB**            | Vector database — stores embeddings, serves similarity search |
| **Python dev container**| Where we prototype the ingestion and query pipelines       |

The dev container does double duty for ingestion and query while we're
still iterating — no premature splitting.

The key technique: we develop **inside** the containerized environment
using **VS Code** and the **Dev Containers extension**. The editor
attaches to the running container, so we write and run code in the exact
environment defined by the spec. The "it works on my machine" gap
disappears, because *the machine is the container*.

This **prototype stage** is the focus of **Chapter 3**.

---

## 4. Stage 2 — Test  → Chapter 4

Once the prototype works, we move it toward something production-shaped.
Three steps:

1. **Functionalize** — turn exploratory prototype code into clean,
   reusable functions. Make it robust.
2. **Test** — verify the components behave correctly and predictably.
3. **Split into separate containers** — one for the **ingestion
   pipeline**, one for the **query pipeline** (the vector DB is already
   its own container).

```
   ┌─ ingestion ─┐   ┌─ vector DB ─┐   ┌─ query ─┐
   │  container  │   │  container  │   │ container│
   └─────────────┘   └─────────────┘   └──────────┘
```

Splitting them out lets us test in an environment **much closer to
production**, where the real question is no longer "does the code run?"
but "do the components actually **connect**?" — networking, access, and
port settings between services.

This **testing stage** is the focus of **Chapter 4**.

---

## 5. Stage 3 — Deployment  → Chapter 5

The last step before production is to **optimize the container for each
service** — lean, secure, production-ready images. Those optimized
containers are exactly what we ship.

From there, deployment is **gradual**, not big-bang:

1. Onboard system components into the production environment one at a
   time.
2. Test as you go.
3. Repeat until the system is fully deployed.

This **deployment stage** is the focus of **Chapter 5**.

---

## 6. Why this matters

Notice what threads through every stage: **the container**. We don't
write code on the host and containerize it at the end. We:

* **develop** inside containers,
* **test** inside containers,
* **deploy** the same containers.

That continuity is what makes the behavior predictable from a laptop all
the way to production — the promise we made back in Lesson 1, now turned
into a concrete workflow.

---

## What's next

That wraps up Chapter 1. We've made the case for containers (L1), mapped
our example RAG system (L2), planned a container strategy (L3), and laid
out the workflow that puts it into practice (L4).

**Chapter 2 — Docker 101** zooms into the fundamentals behind Stage 0:
how requirements become a Dockerfile, an image, and a running container,
plus the best practices that keep your images production-ready.
