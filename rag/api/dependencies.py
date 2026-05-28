import os
from functools import lru_cache
from typing import TYPE_CHECKING

from rag.config import Settings, load_config
from rag.ingestion.embedder import get_embedder
from rag.store import ChromaStore

if TYPE_CHECKING:
    from rag.api.jobs.registry import JobRegistry


@lru_cache
def get_api_keys() -> tuple[str, ...]:
    """Parse RAG_API_KEYS env var into a tuple of non-empty stripped keys.

    Returns:
        Tuple of keys. Empty tuple if the env var is unset/empty.

    Notes:
        Cached for process lifetime. Tests that need to change keys must
        call `get_api_keys.cache_clear()`.
    """
    raw = os.environ.get("RAG_API_KEYS", "")
    return tuple(k.strip() for k in raw.split(",") if k.strip())


@lru_cache
def get_config() -> Settings:
    return load_config()


@lru_cache
def get_store() -> ChromaStore:
    return ChromaStore(get_config())


@lru_cache
def get_embedder_instance():
    return get_embedder(get_config())


@lru_cache
def get_job_registry() -> "JobRegistry":
    """Process-wide singleton JobRegistry.

    Cached for process lifetime. Tests that need a fresh registry
    must call `get_job_registry.cache_clear()` (and accept that any
    in-flight BackgroundTasks holding the old reference will write
    to the old, now-orphaned registry).
    """
    from rag.api.jobs.registry import JobRegistry
    return JobRegistry.from_env()
