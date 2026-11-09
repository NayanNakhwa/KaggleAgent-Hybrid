"""Structured file editor: applies unified diff patches instead of rewriting whole files."""

from __future__ import annotations

import re

from core.paths import safe_path

SKILL_NAME = "file_editor"
DESCRIPTION = (
    "Apply a unified diff patch to one file inside the workspace. Use this for every edit. "
    "Hunks must match the current file content exactly, including whitespace."
)
PARAMETERS = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "File path relative to the workspace."},
        "patch": {"type": "string", "description": "Unified diff with @@ hunk headers."},
    },
    "required": ["path", "patch"],
}

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@")


def apply_unified_diff(original: str, patch: str) -> str:
    """Apply one file's unified diff. Raises ValueError if any context line does not match."""
    src = original.splitlines(keepends=True)
    out: list[str] = []
    pos = 0  # index into src
    lines = patch.splitlines()
    i = 0
    while i < len(lines) and not lines[i].startswith("@@"):
        i += 1  # skip ---/+++ headers
    if i == len(lines):
        raise ValueError("patch contains no hunks (@@ lines)")
    while i < len(lines):
        match = HUNK_RE.match(lines[i])
        if not match:
            i += 1
            continue
        start = max(int(match.group(1)) - 1, 0)
        if start < pos:
            raise ValueError("hunks overlap or are out of order")
        out.extend(src[pos:start])
        pos = start
        i += 1
        while i < len(lines) and not lines[i].startswith("@@"):
            line = lines[i]
            tag, body = (line[:1], line[1:]) if line else (" ", "")
            if tag == "\\":  # "\ No newline at end of file"
                i += 1
                continue
            if tag not in (" ", "-", "+"):
                raise ValueError(f"bad patch line: {line!r}")
            if tag in (" ", "-"):
                if pos >= len(src) or src[pos].rstrip("\r\n") != body:
                    expected = body
                    actual = src[pos].rstrip("\r\n") if pos < len(src) else "<end of file>"
                    raise ValueError(
                        f"context mismatch at line {pos + 1}: expected {expected!r}, found {actual!r}"
                    )
                if tag == " ":
                    out.append(src[pos])
                pos += 1
            else:  # "+"
                out.append(body + "\n")
            i += 1
    out.extend(src[pos:])
    return "".join(out)


def run(path: str, patch: str) -> str:
    target = safe_path(path)
    if not target.is_file():
        return f"ERROR: {path} does not exist. Create it with bash_terminal first."
    original = target.read_text(encoding="utf-8")
    try:
        updated = apply_unified_diff(original, patch)
    except ValueError as exc:
        return f"ERROR: patch rejected, file unchanged: {exc}"
    target.write_text(updated, encoding="utf-8")
    return f"patched {path} ({len(original.splitlines())} -> {len(updated.splitlines())} lines)"
