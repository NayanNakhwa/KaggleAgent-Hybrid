"""Path guard. Every file operation an agent performs must go through safe_path()."""

from __future__ import annotations

import os
from pathlib import Path

from core.config import get_settings


def safe_path(relative: str | os.PathLike[str]) -> Path:
    """Resolve a path inside the workspace or raise PermissionError.

    Rejects absolute paths, ``..`` escapes, and symlinks that point outside the workspace,
    because resolve() follows symlinks before the containment check.
    """
    root = get_settings().workspace_root
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise PermissionError(f"path escapes workspace: {relative}")
    return candidate
