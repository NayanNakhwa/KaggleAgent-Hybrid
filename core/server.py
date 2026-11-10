"""FastAPI WebSocket backend. One endpoint: /ws.

Protocol
  1. First message must be {"type": "auth", "token": "..."}. The token is compared with
     KAGENT_TOKEN in constant time. If KAGENT_TOKEN is unset, every client is refused.
  2. After auth the client may send:
       {"type": "models"}
       {"type": "skills"}
       {"type": "chat", "request": "...", "model": "..."}
       {"type": "persist"}   (stub until Phase E)
  3. A chat reply sends plan/worker/judge events, then chunk messages, answer_done, chat_done.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

Emit = Callable[[dict], Awaitable[None]]
ChatFn = Callable[[str, str, Emit], Awaitable[str]]

CHUNK_SIZE = 40
FAKE_ANSWER = "Fake answer: the pipeline ran end to end."


async def fake_chat(request: str, model: str, emit: Emit) -> str:
    """Stands in for the Phase A graph. Sends the same event shapes the real graph will."""
    await emit({"type": "plan", "subtasks": [{"role": "executor", "task": "Compute the requested result"}]})
    await emit({"type": "worker", "role": "executor", "result": "fake worker result"})
    await emit({"type": "judge", "ok": True, "feedback": ""})
    return FAKE_ANSWER


async def _chat(ws: WebSocket, msg: dict, chat_fn: ChatFn, models: list[str]) -> None:
    request = msg.get("request")
    model = msg.get("model")
    if not isinstance(request, str) or not request.strip():
        await ws.send_json({"type": "error", "message": "request must be a non-empty string"})
        return
    if model not in models:
        await ws.send_json({"type": "error", "message": f"unknown model: {model}"})
        return

    async def emit(event: dict) -> None:
        await ws.send_json(event)

    answer = await chat_fn(request, model, emit)
    for i in range(0, len(answer), CHUNK_SIZE):
        await ws.send_json({"type": "chunk", "text": answer[i : i + CHUNK_SIZE]})
    await ws.send_json({"type": "answer_done", "text": answer})
    await ws.send_json({"type": "chat_done"})


async def _handle(ws: WebSocket, msg: object, chat_fn: ChatFn, models: list[str], skills: list[str]) -> None:
    kind = msg.get("type") if isinstance(msg, dict) else None
    if kind == "models":
        await ws.send_json({"type": "models", "models": models})
    elif kind == "skills":
        await ws.send_json({"type": "skills", "skills": skills})
    elif kind == "persist":
        await ws.send_json({"type": "persist_pending", "message": "Persist is implemented in Phase E."})
    elif kind == "chat" and isinstance(msg, dict):
        await _chat(ws, msg, chat_fn, models)
    else:
        await ws.send_json({"type": "error", "message": f"unknown message type: {kind}"})


def create_app(chat_fn: ChatFn, models: list[str], skills: list[str], token: str | None) -> FastAPI:
    app = FastAPI()

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        if not token:
            await ws.send_json({"type": "error", "message": "server has no KAGENT_TOKEN set"})
            await ws.close(code=1008)
            return

        try:
            first = await ws.receive_json()
        except WebSocketDisconnect:
            return
        except ValueError:
            first = None

        supplied = None
        if isinstance(first, dict) and first.get("type") == "auth":
            supplied = first.get("token")
        if not isinstance(supplied, str) or not hmac.compare_digest(supplied.encode(), token.encode()):
            await ws.send_json({"type": "error", "message": "auth failed"})
            await ws.close(code=1008)
            return
        await ws.send_json({"type": "auth_ok"})

        while True:
            try:
                msg = await ws.receive_json()
            except WebSocketDisconnect:
                return
            except ValueError:
                await ws.send_json({"type": "error", "message": "invalid JSON"})
                continue
            await _handle(ws, msg, chat_fn, models, skills)

    return app


def make_app() -> FastAPI:
    """Entry point: uvicorn core.server:make_app --factory"""
    token = os.environ.get("KAGENT_TOKEN") or None
    if os.environ.get("KAGENT_LLM") == "fake":
        return create_app(fake_chat, ["fake"], [], token)
    raise RuntimeError("Only KAGENT_LLM=fake works so far. The real graph is connected in the next step.")
