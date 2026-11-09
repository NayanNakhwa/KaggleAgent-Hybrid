"""Specialized worker agents.

A worker runs a bounded tool loop. Each LLM reply must be one JSON object:
``{"tool": name, "args": {...}}`` to call a tool, or ``{"final": "..."}`` to finish.
A JSON action protocol works with any Ollama model, including ones without native tool calling.
Each role sees only its allowed skills, so a researcher cannot edit files.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from core.llm import LLMClient
from core.mcp_loader import SkillRegistry

ROLE_PROMPTS: dict[str, str] = {
    "coder": (
        "You write and edit code. Make every change with file_editor diff patches, never by rewriting "
        "whole files. After editing, run linter on the file and fix what it reports."
    ),
    "executor": (
        "You run commands and report exact results. Use bash_terminal for shell work and python_repl "
        "for quick checks. Never invent output. Quote the real output in your final answer."
    ),
    "researcher": (
        "You find and summarise documentation. Use web_docs to search or download pages and "
        "file_explorer to find local references. Cite the URL of every source you use."
    ),
}

# Role -> skills it may call. Enforced in run_worker, not just in the prompt.
ROLE_SKILLS: dict[str, tuple[str, ...]] = {
    "coder": ("file_editor", "file_explorer", "linter", "python_repl"),
    "executor": ("bash_terminal", "python_repl"),
    "researcher": ("web_docs", "file_explorer"),
}

PROTOCOL = """ROLE: WORKER
{role_prompt}

You work one step at a time. Reply with EXACTLY ONE JSON object and nothing else.
- To call a tool:  {"tool": "<name>", "args": {...}}
- When finished:   {"final": "<concise result for the superagent>"}

Available tools:
{tools}
"""

MAX_OBSERVATION_CHARS = 4000


@dataclass
class WorkerResult:
    ok: bool
    output: str
    steps: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "output": self.output, "steps": self.steps}


def extract_json(text: str, required_keys: Sequence[str]) -> dict[str, Any] | None:
    """Return the first JSON object in ``text`` that contains one of ``required_keys``.

    Models often wrap JSON in prose or code fences, so this scans for braces and decodes
    from each one instead of requiring the whole reply to be valid JSON.
    """
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and any(key in obj for key in required_keys):
            return obj
    return None


def run_worker(
    role: str,
    task: str,
    llm: LLMClient,
    model: str,
    registry: SkillRegistry,
    max_steps: int = 6,
) -> WorkerResult:
    """Execute one subtask with a bounded think-act-observe loop."""
    if role not in ROLE_SKILLS:
        raise ValueError(f"unknown role '{role}'")
    allowed = [name for name in ROLE_SKILLS[role] if name in registry]
    system = PROTOCOL.replace("{role_prompt}", ROLE_PROMPTS[role]).replace(
        "{tools}", registry.describe(allowed) or "(no tools available)"
    )
    history: list[BaseMessage] = [SystemMessage(system), HumanMessage(f"Task:\n{task}")]
    steps: list[dict[str, Any]] = []

    for _ in range(max_steps):
        reply = llm.complete(history, model)
        action = extract_json(reply, ("tool", "final"))
        if action is None:
            history += [
                AIMessage(reply),
                HumanMessage("That was not a valid JSON action. Reply with exactly one JSON object."),
            ]
            continue
        if "final" in action:
            return WorkerResult(ok=True, output=str(action["final"]), steps=steps)

        name = str(action.get("tool", ""))
        args = action.get("args", {})
        if name not in allowed:
            observation = (
                f"ERROR: tool '{name}' is not available to the {role} role. "
                f"Allowed: {', '.join(allowed) or 'none'}"
            )
        else:
            observation = registry.call(name, args)
        steps.append({"tool": name, "args": args, "observation": observation[:500]})
        history += [AIMessage(reply), HumanMessage(f"Observation:\n{observation[:MAX_OBSERVATION_CHARS]}")]

    return WorkerResult(ok=False, output="Step budget exhausted before a final answer.", steps=steps)
