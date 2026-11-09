"""Sandboxed persistent bash session.

One bash process is kept alive, so working directory and environment variables persist between
calls. Output is framed with a sentinel line that carries the exit code. Each command has a
timeout. A timeout restarts the session.
"""

from __future__ import annotations

import subprocess
import threading
import uuid

from core.config import get_settings

SKILL_NAME = "bash_terminal"
DESCRIPTION = (
    "Run a shell command in a persistent bash session rooted in the workspace. Working directory and "
    "variables persist between calls. Returns stdout, stderr and the exit code."
)
PARAMETERS = {
    "type": "object",
    "properties": {
        "command": {"type": "string", "description": "Bash command to run."},
        "timeout": {"type": "integer", "description": "Seconds before the command is killed, default 60."},
    },
    "required": ["command"],
}

_lock = threading.Lock()
_session: "_BashSession | None" = None


class _BashSession:
    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            ["bash", "--noprofile", "--norc"],
            cwd=get_settings().workspace_root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env={
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "HOME": str(get_settings().workspace_root),
                "LANG": "C.UTF-8",
            },
        )

    def run(self, command: str, timeout: int) -> str:
        marker = f"__KAGENT_DONE_{uuid.uuid4().hex}__"
        # Stderr is merged into stdout via 2>&1 inside the shell, so ordering is preserved.
        payload = f"{command}\n__rc=$?; echo; echo {marker}:$__rc\n"
        self.proc.stdin.write(payload)
        self.proc.stdin.flush()
        chunks: list[str] = []
        result: list[str] = []

        def reader() -> None:
            for line in self.proc.stdout:
                if line.startswith(marker):
                    result.append(line.strip().split(":")[-1])
                    return
                chunks.append(line)

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self.close()
            return f"ERROR: command timed out after {timeout}s; session was restarted (state lost)"
        output = "".join(chunks).rstrip()
        return f"{output}\n[exit code {result[0] if result else '?'}]"

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()


def _get_session() -> _BashSession:
    global _session
    if _session is None or _session.proc.poll() is not None:
        _session = _BashSession()
    return _session


def run(command: str, timeout: int = 60) -> str:
    if not command.strip():
        return "ERROR: empty command"
    timeout = max(1, min(int(timeout), 600))
    with _lock:
        session = _get_session()
        return session.run(command, timeout)
