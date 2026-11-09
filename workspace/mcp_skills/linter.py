"""Automatic linter: runs ruff to report and auto-fix syntax and style problems in one file."""

from __future__ import annotations

import os
import subprocess
import sys

from core.paths import safe_path

SKILL_NAME = "linter"
DESCRIPTION = (
    "Run ruff on one Python file in the workspace. Applies safe automatic fixes first, then reports "
    "remaining problems. Use it after every edit to catch syntax errors."
)
PARAMETERS = {
    "type": "object",
    "properties": {"path": {"type": "string", "description": "Python file path relative to the workspace."}},
    "required": ["path"],
}


def run(path: str) -> str:
    target = safe_path(path)
    if not target.is_file() or target.suffix != ".py":
        return f"ERROR: {path} is not a Python file in the workspace"
    env = {**os.environ, "NO_COLOR": "1", "RUFF_NO_CACHE": "1"}
    base = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--no-cache",
        "--color",
        "never",
        "--output-format",
        "concise",
    ]
    before = target.read_text(encoding="utf-8")
    fix = subprocess.run(base + ["--fix", str(target)], capture_output=True, text=True, timeout=60, env=env)
    if fix.returncode == 2:  # ruff uses exit code 2 for usage or configuration errors
        return f"ERROR: ruff failed: {fix.stderr.strip()}"
    changed = target.read_text(encoding="utf-8") != before
    check = subprocess.run(base + [str(target)], capture_output=True, text=True, timeout=60, env=env)
    report = check.stdout.strip() or "no lint problems remain"
    note = "auto-fixes applied" if changed else "no auto-fixes needed"
    return f"{note}\n{report}"
