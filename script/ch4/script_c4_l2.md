# Chapter 4 — Lesson 2: Dedicated Images per Service

In the last lesson we decided to split the prototype into one container per service. This lesson builds the images. We'll cover the design on slides, then switch to the terminal and build both.

The packaging decision: **two dedicated images** — one for ingestion, one for query — each with its own Dockerfile and its own dependency set.

[CLICK]

Start with dependencies, because that's where the split pays off.

The ingestion service parses PDFs. That means **Docling**, and Docling pulls in a large stack — vision models, parsing libraries, system graphics libraries. It's heavy.

The query service never parses anything. It retrieves context and calls an LLM. It needs the web framework and the LLM client libraries — and that's about it.

So we write two requirements files. `requirements-ingestion.txt` carries Docling and the embedding stack. `requirements-query.txt` is lean — FastAPI, the LangChain clients, the ChromaDB client. The biggest single difference is that Docling is simply absent from the query image.

[CLICK]

Next, the entry points. Today our routes all live in one FastAPI app. To serve only half the routes per image, we split them.

We move the route definitions into two routers — one for ingestion, one for query — and create two small app modules. `ingestion_app.py` mounts only the ingestion router. `query_app.py` mounts only the query router. Both keep `/health`.

```python
# rag/api/query_app.py
from fastapi import FastAPI
from rag.api.routes import query
app = FastAPI(title="RAG Query")
app.include_router(query.router)
```

This matters for more than tidiness: because the query app never imports the ingestion module, it never imports Docling. The lean image is lean *because the code says so*.

[CLICK]

Now the Dockerfiles. They follow every best practice from Chapter 2 — pinned base, dependencies copied before code, exec-form `CMD`. The only differences are the requirements file, the entry-point module, and the port.

The query Dockerfile is short. The ingestion Dockerfile adds a couple of system libraries that Docling needs, and points at the ingestion app on port 8081.

Let's build them.

[SWITCH TO TERMINAL]

I'm at the project root. First the lean query image:

```bash
docker build -f chapter_4/l2/Dockerfile_Query -t rag-query:0.1.0 .
```

[CLICK]

Now the heavy ingestion image:

```bash
docker build -f chapter_4/l2/Dockerfile_Ingestion -t rag-ingestion:0.1.0 .
```

This one takes longer — that's Docling and its dependencies installing.

[CLICK]

Now the payoff. Let's compare the two images:

```bash
docker images | grep rag-
```

The query image is a fraction of the size of the ingestion image. That difference is almost entirely the parsing stack the query service doesn't carry. Every time we deploy the query service, that's the weight we *don't* ship — faster pulls, faster starts, smaller attack surface.

[CLICK]

Two images, each right-sized for its job. Notice we reused everything from earlier chapters: the layer ordering from Chapter 3, the best practices from Chapter 2. The only new idea is splitting one app into two service entry points.

In the next lesson, we stop building images one at a time and orchestrate all three containers — ingestion, query, and the database — into one running stack with Compose.
