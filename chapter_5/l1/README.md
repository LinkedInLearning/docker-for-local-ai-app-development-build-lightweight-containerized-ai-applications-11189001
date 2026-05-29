# Chapter 5 — Lesson 1: What "Production-Ready" Means

> **Learning goal:** define production-readiness for a containerized app (size,
> security, portability, distribution, operability) and baseline your current
> images against that bar.

Chapter 4 left us with a multi-container application that **runs and passes its
tests**. But "runs on my machine and in CI" is not "ready for production." This
chapter takes those images the last mile; this lesson defines the target and
measures where we stand.

---

## 1. A working image is not a production image

The gap between the two is a checklist — five things a production image gets
right that a prototype usually doesn't:

| Column | Why it matters |
| ------ | -------------- |
| **Size** | faster pulls, cheaper storage, smaller attack surface |
| **Security** | minimal surface, no baked secrets, no known CVEs, least privilege |
| **Portability** | runs on the CPU architecture you deploy to |
| **Distribution** | versioned and published to a registry |
| **Operability** | resource limits, health, graceful shutdown, observability |

Each remaining lesson in the chapter attacks one column.

---

## 2. Baseline before you change anything

You can't improve what you don't measure. Look at the images Chapter 4 produced:

```bash
docker images rag-ingestion rag-query      # starting size
docker history rag-ingestion:0.1.0         # which layers dominate
dive rag-ingestion:0.1.0                    # wasted space, layer by layer
docker scout quickview rag-ingestion:0.1.0  # CVE count at a glance
```

The heavy ingestion image (Docling, torch) is large and has a wide surface —
that's our starting point, and what the rest of the chapter improves.

> `dive` and `docker scout` are separate tools; `scout` ships with Docker
> Desktop. Install `dive` from its releases page if you want the layer explorer.

---

## 3. The chapter map

| Lesson | Column it attacks |
| ------ | ----------------- |
| 2 — Multi-stage builds | size |
| 3 — Securing images | security |
| 4 — Multi-platform builds | portability |
| 5 — Publishing | distribution |
| 6 — Best practices & going live | operability + validation |

We re-measure as we go, so each gain is visible.

---

Next: the single biggest lever on size — **multi-stage builds**.
