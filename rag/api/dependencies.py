import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
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


DEFAULT_MAX_UPLOAD_MB: int = 50
DEFAULT_ALLOWED_UPLOAD_DIR: str = "pdf/"
ENV_MAX_UPLOAD_MB: str = "RAG_API_MAX_UPLOAD_MB"
ENV_ALLOWED_UPLOAD_DIR: str = "RAG_API_ALLOWED_UPLOAD_DIR"


@dataclass(frozen=True)
class UploadSettings:
    """Resolved upload limits for the running process.

    Attributes:
        max_upload_mb: Maximum aggregate body size for ingestion routes.
            Validated >= 1 at construction.
        max_upload_bytes: Convenience: max_upload_mb * 1024 * 1024.
        allowed_upload_dir: Absolute, resolved path under which all
            `source_dir` values must live. resolve_under() enforces this.
    """

    max_upload_mb: int
    max_upload_bytes: int
    allowed_upload_dir: str


@lru_cache
def get_upload_settings() -> UploadSettings:
    """Read RAG_API_MAX_UPLOAD_MB and RAG_API_ALLOWED_UPLOAD_DIR from
    the environment, validate, and return an UploadSettings instance.

    Raises:
        RuntimeError: if either env var is set to an unparseable value,
            so the process fails LOUD at startup (called from lifespan).
    """
    raw_mb = os.environ.get(ENV_MAX_UPLOAD_MB, "").strip()
    if raw_mb:
        try:
            mb = int(raw_mb)
        except ValueError as exc:
            raise RuntimeError(
                f"{ENV_MAX_UPLOAD_MB} must be a positive integer, "
                f"got {raw_mb!r}"
            ) from exc
        if mb < 1:
            raise RuntimeError(
                f"{ENV_MAX_UPLOAD_MB} must be >= 1, got {mb}"
            )
    else:
        mb = DEFAULT_MAX_UPLOAD_MB

    raw_dir = (
        os.environ.get(ENV_ALLOWED_UPLOAD_DIR, "").strip()
        or DEFAULT_ALLOWED_UPLOAD_DIR
    )
    # Resolve to absolute. We do NOT require it to exist here — the
    # lifespan emits a warning if it doesn't, and resolve_under() will
    # 403 at request time. Keeping the env var stable at startup even
    # if the directory is mounted late is desirable.
    allowed_abs = str(Path(raw_dir).resolve(strict=False))

    return UploadSettings(
        max_upload_mb=mb,
        max_upload_bytes=mb * 1024 * 1024,
        allowed_upload_dir=allowed_abs,
    )
