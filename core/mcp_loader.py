"""Hot-plug skill loader (MCP-compatible tool registry).

Every ``*.py`` file in ``workspace/mcp_skills/`` is imported with importlib at startup and
registered as a skill. Files whose names start with an underscore are ignored.
A skill module must define:

    SKILL_NAME: str     unique snake_case identifier shown to agents
    DESCRIPTION: str    one-paragraph purpose, shown to the LLM
    PARAMETERS: dict    JSON Schema object describing the keyword arguments of run()
    def run(**kwargs) -> str

A broken skill is logged and skipped. It does not stop other skills from loading.
``registry.mcp_tool_specs()`` returns the MCP ``tools/list`` shape, so the same registry can be
served over the Model Context Protocol.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core.config import REPO_ROOT, get_settings

log = logging.getLogger("kagent.skills")

# Skills import ``core.*``, so the repo root must be importable.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SKILL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
REQUIRED_ATTRS = ("SKILL_NAME", "DESCRIPTION", "PARAMETERS", "run")
MAX_OUTPUT_CHARS = 20_000


class SkillLoadError(Exception):
    """A skill file is malformed or conflicts with another skill."""


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    parameters: dict[str, Any]
    run: Callable[..., str]
    source: Path


class SkillRegistry:
    """Holds the active skills and dispatches calls to them."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self.load_errors: dict[str, str] = {}

    def __contains__(self, name: object) -> bool:
        return name in self._skills

    def clear(self) -> None:
        self._skills.clear()
        self.load_errors.clear()

    def register(self, skill: Skill) -> None:
        if skill.name in self._skills:
            raise SkillLoadError(f"duplicate skill name '{skill.name}' in {skill.source.name}")
        self._skills[skill.name] = skill

    def names(self) -> list[str]:
        return sorted(self._skills)

    def describe(self, names: list[str] | None = None) -> str:
        """Human/LLM-readable tool listing for prompts."""
        chosen = names if names is not None else self.names()
        lines = []
        for name in chosen:
            skill = self._skills.get(name)
            if skill is None:
                continue
            lines.append(
                f"- {skill.name}: {skill.description}\n"
                f"  arguments (JSON Schema): {json.dumps(skill.parameters)}"
            )
        return "\n".join(lines)

    def mcp_tool_specs(self) -> list[dict[str, Any]]:
        """Tool descriptors in the MCP ``tools/list`` format."""
        return [
            {"name": s.name, "description": s.description, "inputSchema": s.parameters}
            for s in self._skills.values()
        ]

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        """Run a skill. Always returns text, so the agent can read and recover from errors."""
        skill = self._skills.get(name)
        if skill is None:
            return f"ERROR: unknown tool '{name}'"
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            return "ERROR: arguments must be a JSON object"
        try:
            output = skill.run(**arguments)
        except TypeError as exc:
            return f"ERROR: bad arguments for {name}: {exc}"
        except Exception as exc:  # noqa: BLE001 - skills are untrusted plugins; report, don't crash
            log.exception("skill %s failed", name)
            return f"ERROR: {type(exc).__name__}: {exc}"
        text = str(output)
        if len(text) > MAX_OUTPUT_CHARS:
            text = text[:MAX_OUTPUT_CHARS] + "\n...[truncated]"
        return text


def _skill_from_module(module: Any, path: Path) -> Skill:
    missing = [attr for attr in REQUIRED_ATTRS if not hasattr(module, attr)]
    if missing:
        raise SkillLoadError(f"missing {', '.join(missing)}")
    name = module.SKILL_NAME
    if not isinstance(name, str) or not SKILL_NAME_RE.match(name):
        raise SkillLoadError(f"invalid SKILL_NAME {name!r}")
    if not callable(module.run):
        raise SkillLoadError("run must be callable")
    if not isinstance(module.PARAMETERS, dict) or module.PARAMETERS.get("type") != "object":
        raise SkillLoadError("PARAMETERS must be a JSON Schema object")
    return Skill(
        name=name,
        description=" ".join(str(module.DESCRIPTION).split()),
        parameters=module.PARAMETERS,
        run=module.run,
        source=path,
    )


def _load_skill_file(path: Path) -> Skill:
    spec = importlib.util.spec_from_file_location(f"kagent_skills.{path.stem}", path)
    if spec is None or spec.loader is None:
        raise SkillLoadError("cannot create an import spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # syntax and import errors surface here
    return _skill_from_module(module, path)


def load_skills_from_dir(
    skill_dir: Path | str | None = None, registry: SkillRegistry | None = None
) -> SkillRegistry:
    """Scan the skill folder and (re)register every valid skill.

    Call it again after adding a file to hot-load that skill without restarting the server.
    """
    skill_dir = Path(skill_dir) if skill_dir else get_settings().skills_dir
    registry = registry or SkillRegistry()
    registry.clear()
    if not skill_dir.is_dir():
        log.warning("skill directory %s does not exist", skill_dir)
        return registry
    for path in sorted(skill_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            registry.register(_load_skill_file(path))
            log.info("loaded skill %s", path.stem)
        except Exception as exc:  # noqa: BLE001 - one bad plugin must not block the rest
            registry.load_errors[path.name] = f"{type(exc).__name__}: {exc}"
            log.error("skipping %s: %s", path.name, exc)
    return registry
