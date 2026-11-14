"""Tests for the Streamlit UI helpers. No server and no browser needed."""

import json

import pytest

from ui import app
from ui.app import (
    UIError,
    judge_text,
    open_authenticated,
    plan_rows,
    request_list,
    run_turn,
    send_chat,
    worker_text,
)


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


class FakeConnect:
    """Stands in for websockets connect(url) used as a context manager."""

    def __init__(self, ws):
        self.ws = ws

    def __call__(self, url):
        return self

    def __enter__(self):
        return self.ws

    def __exit__(self, *exc):
        return False


def dumps(obj):
    return json.dumps(obj)


def test_open_authenticated_sends_token_and_accepts_ok():
    ws = FakeWS([dumps({"type": "auth_ok"})])
    open_authenticated(ws, "local-dev-test")
    assert ws.sent == [{"type": "auth", "token": "local-dev-test"}]


def test_wrong_token_shows_only_server_message():
    ws = FakeWS([dumps({"type": "error", "message": "auth failed"})])
    with pytest.raises(UIError) as info:
        open_authenticated(ws, "secret-value")
    assert str(info.value) == "auth failed"
    assert "secret-value" not in str(info.value)


def test_request_list_returns_models():
    ws = FakeWS([dumps({"type": "models", "models": ["fake"]})])
    assert request_list(ws, "models") == ["fake"]
    assert ws.sent == [{"type": "models"}]


def test_run_turn_collects_events_in_order():
    ws = FakeWS(
        [
            dumps({"type": "plan", "subtasks": [{"role": "executor", "task": "Compute"}]}),
            dumps({"type": "worker", "id": "r1-0", "role": "executor", "ok": True}),
            dumps({"type": "judge", "id": "r1-0", "accepted": True}),
            dumps({"type": "answer_done", "text": "Fake answer."}),
            dumps({"type": "chat_done"}),
        ]
    )
    state, events = run_turn(ws, "Say hi", "fake")
    assert ws.sent == [{"type": "chat", "request": "Say hi", "model": "fake"}]
    assert state.answer == "Fake answer." and state.done
    assert [event["type"] for event in events] == [
        "plan",
        "worker",
        "judge",
        "answer_done",
        "chat_done",
    ]


def test_plan_rows_skips_bad_items():
    rows = plan_rows([{"role": "executor", "task": "Compute"}, "bad"])
    assert rows == [{"#": 1, "Role": "executor", "Task": "Compute"}]
    assert plan_rows("nope") == []


def test_worker_and_judge_text():
    assert worker_text({"id": "r1-0", "role": "executor", "ok": True}) == (
        "worker r1-0 (executor): ok"
    )
    assert judge_text({"id": "r1-0", "accepted": False}) == "judge r1-0: rejected"


def test_send_chat_turns_connection_error_into_error_event(monkeypatch):
    def refuse(url):
        raise OSError("connection refused")

    monkeypatch.setattr(app, "connect", refuse)
    events = send_chat("ws://127.0.0.1:1/ws", "tok", "hi", "fake")
    assert events == [{"type": "error", "message": "connection error: connection refused"}]


def test_send_chat_auth_failure_hides_token(monkeypatch):
    ws = FakeWS([dumps({"type": "error", "message": "auth failed"})])
    monkeypatch.setattr(app, "connect", FakeConnect(ws))
    events = send_chat("ws://127.0.0.1:8000/ws", "secret-value", "hi", "fake")
    assert events == [{"type": "error", "message": "auth failed"}]
    assert "secret-value" not in repr(events)
