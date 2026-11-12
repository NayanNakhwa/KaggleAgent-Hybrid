"""Pure wire-protocol helpers. No network or terminal I/O, so tests need no server."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


class ProtocolError(Exception):
    """A server message was not valid JSON or not an object with a string 'type'."""


def encode(message: dict[str, Any]) -> str:
    return json.dumps(message)


def decode(raw: str | bytes) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"invalid JSON from server: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("type"), str):
        raise ProtocolError("server message must be a JSON object with a string 'type'")
    return data


def auth_message(token: str) -> str:
    return encode({"type": "auth", "token": token})


def chat_message(request: str, model: str) -> str:
    return encode({"type": "chat", "request": request, "model": model})


@dataclass
class TurnState:
    """Accumulates the events of one chat turn until it finishes."""

    plan: list[dict[str, Any]] = field(default_factory=list)
    workers: list[dict[str, Any]] = field(default_factory=list)
    judgements: list[dict[str, Any]] = field(default_factory=list)
    chunk_count: int = 0
    answer: str | None = None
    error: str | None = None
    done: bool = False

    def apply(self, event: dict[str, Any]) -> None:
        kind = event.get("type")
        if kind == "plan":
            subtasks = event.get("subtasks")
            items = subtasks if isinstance(subtasks, list) else []
            self.plan = [item for item in items if isinstance(item, dict)]
        elif kind == "worker":
            self.workers.append(event)
        elif kind == "judge":
            self.judgements.append(event)
        elif kind == "chunk":
            self.chunk_count += 1
        elif kind == "answer_done":
            text = event.get("text")
            self.answer = text if isinstance(text, str) else ""
        elif kind == "chat_done":
            self.done = True
        elif kind == "error":
            message = event.get("message")
            self.error = message if isinstance(message, str) else "unknown error"
            self.done = True
