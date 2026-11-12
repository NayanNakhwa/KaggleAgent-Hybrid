from fastapi.testclient import TestClient

from core.config import Settings
from core.fake_llm import FakeLLM
from core.graph_chat import make_graph_chat
from core.mcp_loader import SkillRegistry
from core.server import create_app
from core.superagent import build_graph

TOKEN = "test-token"


def test_real_graph_streams_events_through_websocket():
    graph = build_graph(FakeLLM(), SkillRegistry(), Settings())
    client = TestClient(create_app(make_graph_chat(graph), ["fake"], [], TOKEN))

    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "auth", "token": TOKEN})
        assert ws.receive_json()["type"] == "auth_ok"
        ws.send_json({"type": "chat", "request": "hello", "model": "fake"})

        types = []
        answer = None
        while True:
            message = ws.receive_json()
            types.append(message["type"])
            if message["type"] == "answer_done":
                answer = message["text"]
            if message["type"] == "chat_done":
                break

    assert types[0] == "plan"
    assert "judge" in types
    assert "answer" not in types  # the answer event is consumed by the adapter
    assert answer and "Fake answer" in answer
    assert types[-2:] == ["answer_done", "chat_done"]
