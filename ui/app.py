"""Streamlit browser UI for the KAgent WebSocket server.

Run from the repo root, with KAGENT_TOKEN set in the same terminal:
    streamlit run ui/app.py

The token is read from the environment only. The page never shows or stores it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Streamlit adds the ui/ folder to sys.path, not the repo root.
# Add the root so the shared client package can be imported.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402
from websockets.exceptions import WebSocketException  # noqa: E402
from websockets.sync.client import connect  # noqa: E402

from client import protocol  # noqa: E402
from client.protocol import ProtocolError, TurnState  # noqa: E402

DEFAULT_URL = "ws://127.0.0.1:8000/ws"


class UIError(Exception):
    """A message to show in the page. It never contains the token."""


def server_url() -> str:
    return os.environ.get("KAGENT_URL", DEFAULT_URL)


def _recv(ws: Any) -> dict[str, Any]:
    return protocol.decode(ws.recv())


def open_authenticated(ws: Any, token: str) -> None:
    ws.send(protocol.auth_message(token))
    reply = _recv(ws)
    if reply["type"] == "auth_ok":
        return
    if reply["type"] == "error":
        raise UIError(str(reply.get("message", "authentication failed")))
    raise UIError(f"unexpected reply to auth: {reply['type']}")


def request_list(ws: Any, kind: str) -> list[str]:
    ws.send(protocol.encode({"type": kind}))
    reply = _recv(ws)
    if reply["type"] == "error":
        raise UIError(f"server error: {reply.get('message', 'unknown')}")
    if reply["type"] != kind:
        raise UIError(f"unexpected reply to {kind}: {reply['type']}")
    items = reply.get(kind)
    if not isinstance(items, list):
        raise UIError(f"malformed {kind} reply")
    return [str(item) for item in items]


def run_turn(ws: Any, request: str, model: str) -> tuple[TurnState, list[dict[str, Any]]]:
    """Send one chat request and read events until the turn ends."""
    ws.send(protocol.chat_message(request, model))
    state = TurnState()
    events: list[dict[str, Any]] = []
    while not state.done:
        event = _recv(ws)
        state.apply(event)
        events.append(event)
    return state, events


def fetch_catalog(url: str, token: str) -> tuple[list[str], list[str]]:
    """Return (models, skills) from the server."""
    try:
        with connect(url) as ws:
            open_authenticated(ws, token)
            return request_list(ws, "models"), request_list(ws, "skills")
    except ProtocolError as exc:
        raise UIError(f"protocol error: {exc}") from exc
    except (OSError, WebSocketException) as exc:
        raise UIError(f"connection error: {exc}") from exc


def send_chat(url: str, token: str, request: str, model: str) -> list[dict[str, Any]]:
    """Run one turn. Errors become an 'error' event so they show in the chat."""
    try:
        with connect(url) as ws:
            open_authenticated(ws, token)
            _, events = run_turn(ws, request, model)
            return events
    except UIError as exc:
        return [{"type": "error", "message": str(exc)}]
    except ProtocolError as exc:
        return [{"type": "error", "message": f"protocol error: {exc}"}]
    except (OSError, WebSocketException) as exc:
        return [{"type": "error", "message": f"connection error: {exc}"}]


def plan_rows(subtasks: Any) -> list[dict[str, Any]]:
    if not isinstance(subtasks, list):
        return []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(subtasks, start=1):
        if isinstance(item, dict):
            rows.append(
                {
                    "#": index,
                    "Role": str(item.get("role", "?")),
                    "Task": str(item.get("task", "")),
                }
            )
    return rows


def worker_text(event: dict[str, Any]) -> str:
    status = "ok" if event.get("ok") is True else "failed"
    return f"worker {event.get('id', '?')} ({event.get('role', '?')}): {status}"


def judge_text(event: dict[str, Any]) -> str:
    verdict = "accepted" if event.get("accepted") is True else "rejected"
    return f"judge {event.get('id', '?')}: {verdict}"


def render_turn(events: list[dict[str, Any]]) -> None:
    for event in events:
        kind = event.get("type")
        if kind == "plan":
            rows = plan_rows(event.get("subtasks"))
            if rows:
                st.table(rows)
        elif kind == "worker":
            st.text(worker_text(event))
        elif kind == "judge":
            st.text(judge_text(event))
        elif kind == "answer_done":
            text = event.get("text")
            st.markdown(text if isinstance(text, str) else "")
        elif kind == "error":
            st.error(str(event.get("message", "unknown error")))


def main() -> None:
    st.set_page_config(page_title="KAgent", layout="wide")
    st.title("KAgent")

    token = os.environ.get("KAGENT_TOKEN", "")
    if not token:
        st.error(
            "KAGENT_TOKEN is not set. Set it in the terminal that runs Streamlit, "
            "then restart Streamlit."
        )
        st.stop()

    url = server_url()
    try:
        models, skills = fetch_catalog(url, token)
    except UIError as exc:
        st.error(str(exc))
        st.stop()
    if not models:
        st.error("The server reported no models.")
        st.stop()

    with st.sidebar:
        st.caption(f"Server: {url}")
        model = st.selectbox("Model", models)
        st.subheader("Skills")
        for name in skills:
            st.text(name)

    if "history" not in st.session_state:
        st.session_state.history = []
    for turn in st.session_state.history:
        with st.chat_message("user"):
            st.text(turn["request"])
        with st.chat_message("assistant"):
            render_turn(turn["events"])

    request = st.chat_input("Ask KAgent to write, check or explain code")
    if request:
        with st.chat_message("user"):
            st.text(request)
        with st.chat_message("assistant"):
            with st.spinner("Working on it..."):
                events = send_chat(url, token, request, model)
            render_turn(events)
        st.session_state.history.append({"request": request, "events": events})


if __name__ == "__main__":
    main()
