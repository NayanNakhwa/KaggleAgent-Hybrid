"""Smart directory explorer: regex search over workspace files, ranked by relevance."""

from __future__ import annotations

import re

from core.config import get_settings

SKILL_NAME = "file_explorer"
DESCRIPTION = (
    "Search workspace files with a regular expression. Returns matching files ranked by hit count, "
    "with the matching lines. Optionally filter by a glob such as '*.py'."
)
PARAMETERS = {
    "type": "object",
    "properties": {
        "pattern": {"type": "string", "description": "Python regular expression."},
        "glob": {"type": "string", "description": "File glob, default '*'."},
        "max_results": {"type": "integer", "description": "Max files to return, default 10."},
    },
    "required": ["pattern"],
}

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules"}


def run(pattern: str, glob: str = "*", max_results: int = 10) -> str:
    root = get_settings().workspace_root
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return f"ERROR: invalid regex: {exc}"
    scored: list[tuple[int, str, list[str]]] = []
    for path in root.rglob(glob):
        if not path.is_file() or SKIP_DIRS.intersection(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits = [f"{n}: {line.strip()}" for n, line in enumerate(text.splitlines(), 1) if regex.search(line)]
        if hits:
            # Rank by hit count, then by filename depth so shallow files win ties.
            scored.append((len(hits), path.relative_to(root).as_posix(), hits[:5]))
    if not scored:
        return "no matches"
    scored.sort(key=lambda item: (-item[0], item[1].count("/"), item[1]))
    blocks = [
        f"{rel} ({count} hits)\n    " + "\n    ".join(lines) for count, rel, lines in scored[:max_results]
    ]
    return "\n".join(blocks)
