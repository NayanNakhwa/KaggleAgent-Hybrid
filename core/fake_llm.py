"""Scripted fake LLM. Lets the whole pipeline run with no Ollama and no GPU.

Enable it on the server with KAGENT_LLM=fake. It replies according to the role in the system prompt.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from langchain_core.messages import BaseMessage

FAKE_ANSWER = "Fake answer: the pipeline ran end to end."


class FakeLLM:
    def complete(self, messages: Sequence[BaseMessage], model: str) -> str:
        system = str(messages[0].content) if messages else ""
        if "ROLE: PLANNER" in system:
            return json.dumps({"subtasks": [{"role": "executor", "task": "Compute the requested result"}]})
        if "ROLE: JUDGE" in system:
            return '{"ok": true, "feedback": ""}'
        if "ROLE: SYNTHESIZER" in system:
            return FAKE_ANSWER
        return '{"final": "fake worker result"}'
