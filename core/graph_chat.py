"""Adapter: runs the Phase A superagent graph and forwards its events to the WebSocket server."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from typing import Any

from core.superagent import stream_events

Emit = Callable[[dict[str, Any]], Awaitable[None]]


def make_graph_chat(graph) -> Callable[[str, str, Emit], Awaitable[str]]:
    """Return a chat function for the server. stream_events is synchronous, so it runs in a thread."""

    async def graph_chat(request: str, model: str, emit: Emit) -> str:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        done = object()

        def run() -> None:
            try:
                for event in stream_events(graph, request, model):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
            except Exception as exc:  # passed to the async side and re-raised there
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, done)

        threading.Thread(target=run, daemon=True).start()

        answer = ""
        while True:
            item = await queue.get()
            if item is done:
                break
            if isinstance(item, Exception):
                raise item
            if item.get("type") == "answer":
                answer = str(item.get("text", ""))  # sent later as chunks, not as a plan/worker event
                continue
            await emit(item)
        return answer

    return graph_chat
