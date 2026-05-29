from __future__ import annotations

import os
from pathlib import Path


class PathNotAllowedError(ValueError):
    """Raised by resolve_under() when the candidate path resolves
    outside the allowed root, does not exist, or escapes via symlink.
    """

    def __init__(self, candidate: str, allowed_root: str, reason: str) -> None:
        self.candidate = candidate
        self.allowed_root = allowed_root
        self.reason = reason
        super().__init__(
            f"Path '{candidate}' rejected: {reason} "
            f"(allowed root: '{allowed_root}')"
        )


def resolve_under(
    candidate: str | os.PathLike[str],
    allowed_root: str | os.PathLike[str],
    *,
    must_exist: bool = True,
) -> Path:
    """Resolve `candidate` and verify it is a real descendant of
    `allowed_root`, following symlinks on both sides.

    Args:
        candidate: User-supplied path (relative or absolute). If
            relative, resolved against the current working directory
            BEFORE the allowed-root check — callers that want stricter
            behavior should pre-join with `allowed_root` themselves.
        allowed_root: The single directory under which `candidate`
            must resolve. May be absolute or relative; resolved
            against cwd if relative.
        must_exist: If True (default), the resolved candidate AND the
            allowed_root must both exist on disk. If False, only
            allowed_root must exist (candidate may be a future write
            target). Phase 3 always passes `must_exist=True` since
            `/ingest` reads from an existing directory.

    Returns:
        The fully-resolved, absolute, symlink-free Path of the
        candidate. Safe to hand to file-system operations.

    Raises:
        PathNotAllowedError: candidate resolves outside allowed_root,
            does not exist (when `must_exist=True`), or allowed_root
            itself does not exist. Reason field is one of:
              - "allowed_root_missing"
              - "candidate_missing"
              - "outside_allowed_root"
              - "symlink_escapes_root"   (kept distinct for log clarity)
    """
    root_resolved = Path(allowed_root).resolve(strict=False)
    if not root_resolved.exists():
        raise PathNotAllowedError(
            str(candidate), str(allowed_root), reason="allowed_root_missing"
        )
    root_real = Path(os.path.realpath(root_resolved))

    candidate_resolved = Path(candidate).resolve(strict=False)
    if must_exist and not candidate_resolved.exists():
        raise PathNotAllowedError(
            str(candidate), str(allowed_root), reason="candidate_missing"
        )
    candidate_real = Path(os.path.realpath(candidate_resolved))

    try:
        common = Path(os.path.commonpath([str(root_real), str(candidate_real)]))
    except ValueError:
        raise PathNotAllowedError(
            str(candidate), str(allowed_root), reason="outside_allowed_root"
        )

    if common != root_real:
        # Distinguish a symlink escape from a plainly-outside path. The
        # candidate's *named* location (lexical abspath, symlinks NOT
        # followed) being inside root while its realpath lands outside
        # means an in-root symlink pointed elsewhere -> symlink_escapes_root.
        # Compare both sides lexically so this holds even when the root is
        # itself reached through a symlink.
        reason = "outside_allowed_root"
        candidate_abs = os.path.abspath(candidate)
        root_abs = os.path.abspath(allowed_root)
        try:
            Path(candidate_abs).relative_to(root_abs)
        except ValueError:
            pass
        else:
            reason = "symlink_escapes_root"
        raise PathNotAllowedError(str(candidate), str(allowed_root), reason=reason)

    return candidate_real
