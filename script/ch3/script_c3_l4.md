# Chapter 3 — Lesson 4: Developing Inside the Container

The environment is ready. Compose brings up our services, and the dev container connects our editor to them. Now we can start developing the application.

This lesson is about the day-to-day loop of writing code inside the container, with an AI assistant alongside. Before we pivot to VSCode let's discuss about the development workflow.

[CLICK]

Working inside the container changes one thing fundamentally: there is no gap between writing code and running it. The interpreter, the libraries, the database — everything the code needs is already here. You import a library and it's the pinned version. You connect to ChromaDB and with the right network settings.

That tight loop is what makes a containerized prototype productive. You're not maintaining a local environment *and* a container environment — there's only one, and it's the one that ships.

[CLICK]

AI coding assistants fit naturally into this workflow. Tools like Claude Code or in-editor assistants run in the same workspace and can see the same files. They’re great at setting up a basic structure for a module, writing initial functions, generating tests, and explaining unfamiliar code.

But the design is still yours. These tools work best when you already know what to build and how the pieces fit together — which is exactly the strategy work we did in Chapters 1 and 3. You define the architecture; the assistant speeds up implementation.

[CLICK]

A couple of practices keep a prototype from turning into a mess.

**Develop in modules, not in one giant script.** Our RAG code is split by responsibility — parsing, chunking, embedding, storing, retrieving — each a small importable piece. Small modules are easier to test, easier to reason about, and easier to ask an assistant to change without breaking everything else.

**Validate as you go, interactively.** Two tools shine here: **notebooks** for stepping through a pipeline cell by cell, and an **interactive dashboard** for exercising the whole thing end to end. Let's look at both.

[CLICK]

Let's switch to VS Code — running in the dev container — and walk through the real project.

[SWITCH TO VS CODE]

First, the module layout under `rag/`. Each stage of the pipeline is its own module: `ingestion/pdf_parser.py`, `ingestion/chunker.py`, `ingestion/embedder.py`, `store.py` for the vector database, and `retrieval/chain.py` for querying. None of these is an application by itself — they're building blocks we compose.

[CLICK]

Now the **ingestion notebook**, `notebooks/01_pdf_ingestion.ipynb`. Because we're in the container, the Jupyter kernel is the container's interpreter — the same one our modules will run under.

I'll step through the cells: load a PDF, parse it into elements, chunk those elements, embed the chunks, and store them in ChromaDB. The notebook is where we *develop and verify* the pipeline a stage at a time — inspecting the output of each step before wiring them together. If a chunking parameter looks wrong, I change it and re-run just that cell.

[CLICK]

Notice what's happening across the boundary: the notebook runs in the `python` container, and the `store` step writes to the `chromadb` container over the network we set up in Lesson 2. The whole multi-container environment is exercised from one notebook cell.

[CLICK]

Once the pipeline works, we test the full application through the **Streamlit dashboard** in `clients/streamlit_app.py`. From the integrated terminal:

```bash
bash clients/run_streamlit.sh
```

That launches Streamlit on port 8501. Because the dev container forwards that port, VS Code pops it open in the browser on the host.

[CLICK]

In the app, I can upload a PDF, watch it get parsed, chunked, embedded, and stored — the same pipeline from the notebook, now driven through a UI — and then ask questions and get answers with sources. This is the interactive dashboard standing in for a real user, letting us feel the whole system end to end before any of it is "productionized."

[CLICK]

That's the development loop: small modules, an AI assistant to accelerate them, notebooks to validate each stage, and a dashboard to exercise the whole. All of it inside the container, against the real database.

We now have a working prototype. In the final lesson of this chapter, we'll step back and cover the best practices that keep a containerized development environment maintainable as the project grows.
