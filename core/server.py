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

Environment
  KAGENT_TOKEN  required; the shared secret
  KAGENT_LLM    "fake" (scripted FakeLLM, no Ollama) or "ollama" (default, needs OLLAMA_HOST)
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

try:
    from starlette.websockets import WebSocketDisconnected

    # Starlette can raise either class when the client has gone away.
    DISCONNECT_ERRORS = (WebSocketDisconnect, WebSocketDisconnected)
except ImportError:  # older Starlette versions only have WebSocketDisconnect
    DISCONNECT_ERRORS = (WebSocketDisconnect,)

Emit = Callable[[dict], Awaitable[None]]
ChatFn = Callable[[str, str, Emit], Awaitable[str]]

CHUNK_SIZE = 40
FAKE_ANSWER = "Fake answer: the pipeline ran end to end."


async def fake_chat(request: str, model: str, emit: Emit) -> str:
    """Canned events, used only by the Phase B unit tests."""
    await emit({"type": "plan", "subtasks": [{"role": "executor", "task": "Compute the requested result"}]})
    await emit({"type": "worker", "role": "executor", "result": "fake worker result"})
    await emit({"type": "judge", "ok": True, "feedback": ""})
    return FAKE_ANSWER


async def _send_error(ws: WebSocket, message: str) -> None:
    """Send an error if the client is still connected. Otherwise do nothing."""
    try:
        await ws.send_json({"type": "error", "message": message})
    except Exception:
        # The socket is already closed, so there is nobody to tell.
        return


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

    try:
        answer = await chat_fn(request, model, emit)
        for i in range(0, len(answer), CHUNK_SIZE):
            await ws.send_json({"type": "chunk", "text": answer[i : i + CHUNK_SIZE]})
        await ws.send_json({"type": "answer_done", "text": answer})
        await ws.send_json({"type": "chat_done"})
    except DISCONNECT_ERRORS:
        # The client closed the connection during the turn. Stop quietly.
        return
    except Exception as exc:
        await _send_error(ws, f"agent failed: {exc}")


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
        except DISCONNECT_ERRORS:
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
            except DISCONNECT_ERRORS:
                return
            except ValueError:
                await _send_error(ws, "invalid JSON")
                continue
            try:
                await _handle(ws, msg, chat_fn, models, skills)
            except DISCONNECT_ERRORS:
                return

    return app


def make_app() -> FastAPI:
    """Entry point: uvicorn core.server:make_app --factory"""
    from core.config import get_settings
    from core.graph_chat import make_graph_chat
    from core.mcp_loader import load_skills_from_dir
    from core.superagent import build_graph

    token = os.environ.get("KAGENT_TOKEN") or None
    mode = os.environ.get("KAGENT_LLM", "ollama")
    settings = get_settings()

    if mode == "fake":
        from core.fake_llm import FakeLLM

        llm = FakeLLM()
        models = ["fake"]
    elif mode == "ollama":
        from core.llm import OllamaEngine

        llm = OllamaEngine()
        models = list(settings.allowed_models)
    else:
        raise RuntimeError(f"KAGENT_LLM must be 'fake' or 'ollama', got {mode!r}")

    registry = load_skills_from_dir(settings.skills_dir)
    graph = build_graph(llm, registry, settings)
    return create_app(make_graph_chat(graph), models, registry.names(), token)
