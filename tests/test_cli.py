"""Tests for the terminal client, using a scripted fake socket (no server needed)."""

import io
import json

import pytest
from rich.console import Console

from client import protocol
from client.cli import ClientError, Session, pick_model, run_repl
from client.protocol import ProtocolError, TurnState


class FakeWS:
    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def send(self, raw):
        self.sent.append(json.loads(raw))

    def recv(self):
        if not self.replies:
            raise AssertionError("no more scripted replies")
        return self.replies.pop(0)


def make_console():
    return Console(file=io.StringIO(), width=100, force_terminal=False, color_system=None)


def dumps(obj):
    return json.dumps(obj)


def test_decode_accepts_typed_object():
    assert protocol.decode('{"type":"models","models":["fake"]}')["models"] == ["fake"]


@pytest.mark.parametrize("raw", ["not json", '{"models": []}', "[1, 2]"])
def test_decode_rejects_bad_messages(raw):
    with pytest.raises(ProtocolError):
        protocol.decode(raw)


def test_turn_state_collects_full_turn():
    state = TurnState()
    for event in [
        {"type": "plan", "subtasks": [{"role": "executor", "task": "Compute"}]},
        {"type": "worker", "id": "r1-0", "role": "executor", "ok": True},
        {"type": "judge", "id": "r1-0", "accepted": True},
        {"type": "chunk", "text": "Fake"},
        {"type": "answer_done", "text": "Fake answer."},
        {"type": "chat_done"},
    ]:
        state.apply(event)
    assert state.plan == [{"role": "executor", "task": "Compute"}]
    assert len(state.workers) == 1 and len(state.judgements) == 1
    assert state.chunk_count == 1
    assert state.answer == "Fake answer."
    assert state.error is None and state.done is True


def test_turn_state_error_finishes_turn():
    state = TurnState()
    state.apply({"type": "error", "message": "unknown model"})
    assert state.error == "unknown model" and state.done is True


def test_turn_state_ignores_bad_plan_shape():
    state = TurnState()
    state.apply({"type": "plan", "subtasks": "nope"})
    assert state.plan == []


def test_authenticate_ok_sends_token():
    ws = FakeWS([dumps({"type": "auth_ok"})])
    Session(ws, make_console()).authenticate("local-dev-test")
    assert ws.sent == [{"type": "auth", "token": "local-dev-test"}]


def test_authenticate_rejected_shows_only_server_message():
    ws = FakeWS([dumps({"type": "error", "message": "auth failed"})])
    with pytest.raises(ClientError) as info:
        Session(ws, make_console()).authenticate("secret-value")
    assert str(info.value) == "auth failed"
    assert "secret-value" not in str(info.value)


class InterruptedSession:
    def chat(self, request, model):
        raise KeyboardInterrupt


def test_ctrl_c_during_chat_leaves_repl_cleanly(monkeypatch):
    console = make_console()
    monkeypatch.setattr(console, "input", lambda *args, **kwargs: "hello")
    run_repl(InterruptedSession(), console, "fake")
    assert "interrupted" in console.file.getvalue()


def test_models_and_skills():
    ws = FakeWS(
        [
            dumps({"type": "models", "models": ["fake"]}),
            dumps({"type": "skills", "skills": ["linter"]}),
        ]
    )
    session = Session(ws, make_console())
    assert session.models() == ["fake"]
    assert session.skills() == ["linter"]


def test_chat_runs_full_turn_and_renders_answer():
    ws = FakeWS(
        [
            dumps({"type": "plan", "subtasks": [{"role": "executor", "task": "Compute"}]}),
            dumps({"type": "worker", "id": "r1-0", "role": "executor", "ok": True}),
            dumps({"type": "judge", "id": "r1-0", "accepted": True}),
            dumps({"type": "chunk", "text": "Fake answer"}),
            dumps({"type": "answer_done", "text": "Fake answer."}),
            dumps({"type": "chat_done"}),
        ]
    )
    console = make_console()
    state = Session(ws, console).chat("Say hi", "fake")
    assert ws.sent == [{"type": "chat", "request": "Say hi", "model": "fake"}]
    assert state.answer == "Fake answer."
    output = console.file.getvalue()
    assert "Compute" in output and "Fake answer." in output


def test_chat_error_event_ends_turn():
    ws = FakeWS([dumps({"type": "error", "message": "unknown model"})])
    console = make_console()
    state = Session(ws, console).chat("hi", "nope")
    assert state.error == "unknown model"
    assert "unknown model" in console.file.getvalue()


def test_pick_model_default_override_and_unknown():
    assert pick_model(["fake", "other"], None) == "fake"
    assert pick_model(["fake", "other"], "other") == "other"
    with pytest.raises(ClientError, match="not available"):
        pick_model(["fake"], "nope")
