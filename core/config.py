"""Runtime configuration.

Every host, model list, and limit comes from environment variables with safe defaults.
Nothing secret or machine-specific is hard-coded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    """Immutable settings snapshot. Build a new one with get_settings()."""

    workspace_root: Path = field(
        default_factory=lambda: Path(os.getenv("KAGENT_WORKSPACE", REPO_ROOT / "workspace")).resolve()
    )
    skills_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("KAGENT_SKILLS_DIR", REPO_ROOT / "workspace" / "mcp_skills")
        ).resolve()
    )
    # Ollama runs on the Kaggle side, bound to localhost.
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    default_model: str = field(default_factory=lambda: os.getenv("KAGENT_DEFAULT_MODEL", "qwen2.5-coder:7b"))
    # Only these models can be selected. Keeps the UI dropdown and the server in agreement.
    allowed_models: tuple[str, ...] = ("qwen2.5-coder:7b", "deepseek-coder:6.7b", "llama3.1:8b")
    max_rounds: int = field(default_factory=lambda: _env_int("KAGENT_MAX_ROUNDS", 2))
    max_subtasks: int = field(default_factory=lambda: _env_int("KAGENT_MAX_SUBTASKS", 4))
    max_worker_steps: int = field(default_factory=lambda: _env_int("KAGENT_MAX_WORKER_STEPS", 6))
    # Seconds to sleep in each FakeLLM call. 0 in production and tests; set to 2-3 for Ctrl+C testing.
    fake_delay: int = field(default_factory=lambda: _env_int("KAGENT_FAKE_DELAY", 0))


def get_settings() -> Settings:
    """Return a fresh settings snapshot. Reading env on each call keeps tests simple."""
    return Settings()
