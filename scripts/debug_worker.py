"""Diagnostic for step D.4. Not part of the app. Do not commit.

Runs one coder worker against the real model and prints each reply.
Tools are stubs with fixed text, so tool results are not real.
Prints no URL and no token.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import BaseMessage

from core.config import get_settings
from core.llm import OllamaEngine
from core.workers import run_worker

TASK = "Write a Python function named add that returns the sum of two numbers a and b."


class StubRegistry:
    """Stands in for the skill registry. Every tool returns fixed text."""

    NAMES = ("file_editor", "file_explorer", "linter", "python_repl")

    def __contains__(self, name: object) -> bool:
        return name in self.NAMES

    def describe(self, names: Sequence[str]) -> str:
        return "\n".join(f"- {name}: (stub for debugging)" for name in names)

    def call(self, name: str, args: Any) -> str:
        return f"(stub result from {name}) args={args}"


class TracingLLM:
    """Wraps the real LLM and prints each reply on one line."""

    def __init__(self, inner: OllamaEngine) -> None:
        self.inner = inner
        self.count = 0

    def complete(self, messages: Sequence[BaseMessage], model: str) -> str:
        self.count += 1
        reply = self.inner.complete(messages, model)
        one_line = " ".join(reply.split())
        print(f"reply {self.count}: {one_line[:200]}")
        return reply


def main() -> int:
    settings = get_settings()
    model = settings.default_model
    llm = TracingLLM(OllamaEngine())
    print(f"model: {model}")
    result = run_worker(
        role="coder",
        task=TASK,
        llm=llm,
        model=model,
        registry=StubRegistry(),
        max_steps=settings.max_worker_steps,
    )
    print(f"RESULT ok={result.ok} tool_steps={len(result.steps)} replies={llm.count}")
    print(f"output: {' '.join(result.output.split())[:200]}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
