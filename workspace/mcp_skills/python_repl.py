"""Dynamic Python REPL: runs a snippet in a fresh interpreter with a hard timeout.

Snippets run in a separate process, never inside the server, so a crash, infinite loop or
os.exit() cannot take down the backend.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from core.config import get_settings

SKILL_NAME = "python_repl"
DESCRIPTION = (
    "Run a Python snippet in a separate interpreter rooted in the workspace and return stdout and "
    "stderr. Use it to test logic quickly. Each call starts fresh, so variables do not persist."
)
PARAMETERS = {
    "type": "object",
    "properties": {
        "code": {"type": "string", "description": "Python source to run."},
        "timeout": {"type": "integer", "description": "Seconds before the run is killed, default 20."},
    },
    "required": ["code"],
}


def run(code: str, timeout: int = 20) -> str:
    timeout = max(1, min(int(timeout), 120))
    root = get_settings().workspace_root
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=root, encoding="utf-8") as fh:
        fh.write(code)
        script = Path(fh.name)
    try:
        proc = subprocess.run(
            [sys.executable, "-I", str(script)],  # -I: isolated mode, ignores user env and site hooks
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: snippet timed out after {timeout}s"
    finally:
        script.unlink(missing_ok=True)
    out = proc.stdout.rstrip()
    err = proc.stderr.rstrip()
    return f"stdout:\n{out or '(empty)'}\nstderr:\n{err or '(empty)'}\nexit code: {proc.returncode}"
