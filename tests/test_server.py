import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from core.server import create_app, fake_chat

TOKEN = "test-token"


def make_client(token: str | None = TOKEN) -> TestClient:
    return TestClient(create_app(fake_chat, ["fake"], ["file_editor"], token))


def authenticate(ws, token: str = TOKEN) -> dict:
    ws.send_json({"type": "auth", "token": token})
    return ws.receive_json()


def test_wrong_token_is_refused_and_closed():
    with make_client().websocket_connect("/ws") as ws:
        assert authenticate(ws, "wrong")["type"] == "error"
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_server_without_token_refuses_everyone():
    with make_client(token=None).websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "error"


def test_models_and_skills():
    with make_client().websocket_connect("/ws") as ws:
        assert authenticate(ws)["type"] == "auth_ok"
        ws.send_json({"type": "models"})
        assert ws.receive_json() == {"type": "models", "models": ["fake"]}
        ws.send_json({"type": "skills"})
        assert ws.receive_json() == {"type": "skills", "skills": ["file_editor"]}


def test_chat_streams_events_then_answer():
    with make_client().websocket_connect("/ws") as ws:
        authenticate(ws)
        ws.send_json({"type": "chat", "request": "hello", "model": "fake"})
        types = []
        while True:
            message = ws.receive_json()
            types.append(message["type"])
            if message["type"] == "chat_done":
                break
        assert types[:3] == ["plan", "worker", "judge"]
        assert "chunk" in types
        assert types[-2:] == ["answer_done", "chat_done"]


def test_unknown_model_is_an_error():
    with make_client().websocket_connect("/ws") as ws:
        authenticate(ws)
        ws.send_json({"type": "chat", "request": "hello", "model": "nope"})
        assert ws.receive_json()["type"] == "error"
