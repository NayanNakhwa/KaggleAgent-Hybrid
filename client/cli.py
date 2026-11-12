"""Rich terminal client for the KAgent WebSocket server.

Run from the repo root with KAGENT_TOKEN set in this terminal:
    python -m client.cli
    python -m client.cli --model fake
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

from client import protocol
from client.protocol import ProtocolError, TurnState

DEFAULT_URL = "ws://127.0.0.1:8000/ws"
HELP_TEXT = "Type a request and press Enter. Commands: /models, /skills, /help, /quit"
INTERRUPT_TEXT = (
    "interrupted. Closing the connection; the server may still finish the current turn."
)


class ClientError(Exception):
    """A user-facing failure: bad token, unknown model, or unexpected server reply."""


class Session:
    """One connection. ws is any object with send(str) and recv() returning str."""

    def __init__(self, ws: Any, console: Console) -> None:
        self.ws = ws
        self.console = console

    def _recv(self) -> dict[str, Any]:
        return protocol.decode(self.ws.recv())

    def authenticate(self, token: str) -> None:
        self.ws.send(protocol.auth_message(token))
        reply = self._recv()
        if reply["type"] == "auth_ok":
            return
        if reply["type"] == "error":
            raise ClientError(str(reply.get("message", "authentication failed")))
        raise ClientError(f"unexpected reply to auth: {reply['type']}")

    def _request_list(self, kind: str) -> list[str]:
        self.ws.send(protocol.encode({"type": kind}))
        reply = self._recv()
        if reply["type"] == "error":
            raise ClientError(f"server error: {reply.get('message', 'unknown')}")
        if reply["type"] != kind:
            raise ClientError(f"unexpected reply to {kind}: {reply['type']}")
        items = reply.get(kind)
        if not isinstance(items, list):
            raise ClientError(f"malformed {kind} reply")
        return [str(item) for item in items]

    def models(self) -> list[str]:
        return self._request_list("models")

    def skills(self) -> list[str]:
        return self._request_list("skills")

    def chat(self, request: str, model: str) -> TurnState:
        self.ws.send(protocol.chat_message(request, model))
        state = TurnState()
        while not state.done:
            event = self._recv()
            state.apply(event)
            self._show(event)
        return state

    def _show(self, event: dict[str, Any]) -> None:
        kind = event.get("type")
        if kind == "plan":
            table = Table(title="Plan")
            table.add_column("#", justify="right")
            table.add_column("Role")
            table.add_column("Task", overflow="fold")
            for index, item in enumerate(event.get("subtasks") or [], start=1):
                if isinstance(item, dict):
                    role = escape(str(item.get("role", "?")))
                    task = escape(str(item.get("task", "")))
                    table.add_row(str(index), role, task)
            self.console.print(table)
        elif kind == "worker":
            status = "[green]ok[/]" if event.get("ok") is True else "[red]failed[/]"
            worker_id = escape(str(event.get("id", "?")))
            role = escape(str(event.get("role", "?")))
            self.console.print(f"  worker {worker_id} ({role}): {status}")
        elif kind == "judge":
            verdict = "[green]accepted[/]" if event.get("accepted") is True else "[yellow]rejected[/]"
            judged_id = escape(str(event.get("id", "?")))
            self.console.print(f"  judge {judged_id}: {verdict}")
        elif kind == "answer_done":
            text = event.get("text")
            self.console.print(Panel(Markdown(text if isinstance(text, str) else ""), title="Answer"))
        elif kind == "error":
            self.console.print(f"[red]error:[/] {escape(str(event.get('message', 'unknown')))}")


def pick_model(models: list[str], requested: str | None) -> str:
    if not models:
        raise ClientError("server reported no models")
    if requested is None:
        return models[0]
    if requested not in models:
        raise ClientError(f"model '{requested}' is not available; server has: {', '.join(models)}")
    return requested


def run_repl(session: Session, console: Console, model: str) -> None:
    console.print(f"Connected. Model: [bold]{escape(model)}[/]")
    console.print(HELP_TEXT)
    while True:
        try:
            line = console.input("[bold green]you>[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return
        if not line:
            continue
        if line in ("/quit", "/exit"):
            return
        try:
            if line == "/help":
                console.print(HELP_TEXT)
            elif line == "/models":
                for name in session.models():
                    marker = " (current)" if name == model else ""
                    console.print(f"  {escape(name)}{marker}")
            elif line == "/skills":
                for name in session.skills():
                    console.print(f"  {escape(name)}")
            elif line.startswith("/"):
                console.print(f"[yellow]unknown command:[/] {escape(line)}")
            else:
                session.chat(line, model)
        except ClientError as exc:
            console.print(f"[red]{escape(str(exc))}[/]")
        except KeyboardInterrupt:
            # Ctrl+C while waiting on the server. The socket state is unknown,
            # so leave the REPL and let main() close the connection.
            console.print(f"\n[yellow]{INTERRUPT_TEXT}[/]")
            return


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="kagent", description="Terminal client for KAgent.")
    parser.add_argument("--url", default=os.environ.get("KAGENT_URL", DEFAULT_URL))
    parser.add_argument("--model", default=None, help="defaults to the first model the server reports")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    console = Console()
    token = os.environ.get("KAGENT_TOKEN", "")
    if not token:
        console.print("[red]KAGENT_TOKEN is not set.[/] Set it in this terminal and try again.")
        return 2
    try:
        with connect(args.url) as ws:
            session = Session(ws, console)
            session.authenticate(token)
            model = pick_model(session.models(), args.model)
            run_repl(session, console, model)
    except ClientError as exc:
        console.print(f"[red]{escape(str(exc))}[/]")
        return 1
    except ProtocolError as exc:
        console.print(f"[red]protocol error:[/] {escape(str(exc))}")
        return 1
    except (OSError, WebSocketException) as exc:
        console.print(f"[red]connection error:[/] {escape(str(exc))}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
