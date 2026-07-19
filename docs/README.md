# Documentation

Reference documentation for this project, ordered by the path most users follow:
**set up the environment → understand the system → run it**.

| # | Document | Covers |
| - | -------- | ------ |
| 01 | [`01_settings.md`](01_settings.md) | **Setup & configuration.** Running the project in a VS Code Dev Container — requirements, launching, environment variables (`.env` / provider API keys), the `config/settings.yaml` schema, ChromaDB storage & persistence, and how to verify the environment. |
| 02 | [`02_rag.md`](02_rag.md) | **System overview.** What RAG is, the architecture of the `rag/` package (ingestion vs. query pipelines with ChromaDB as the contract between them), a map of the modules, and a summary of the core functions. |
| 03 | [`03_rag_cli.md`](03_rag_cli.md) | **Command-line usage.** Running the ingest and query pipelines from the command line inside the development container. |

## Suggested reading order

1. **Start with [`01_settings.md`](01_settings.md)** to get the containers up and
   your API keys in place.
2. **Read [`02_rag.md`](02_rag.md)** for how the RAG system is put together and
   which module does what.
3. **Use [`03_rag_cli.md`](03_rag_cli.md)** to ingest a document and ask questions
   from the command line.

Files are numbered so they sort in this order; keep the prefix when adding new
docs (e.g. `04_...`).
