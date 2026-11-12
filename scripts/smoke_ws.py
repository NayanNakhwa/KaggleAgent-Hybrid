"""Smoke test for the running server. Reads KAGENT_TOKEN from the environment, never from the code."""

import json
import os
import sys

from websockets.sync.client import connect

URL = os.environ.get("KAGENT_URL", "ws://127.0.0.1:8000/ws")
TOKEN = os.environ.get("KAGENT_TOKEN")


def send(ws, message: dict) -> None:
    ws.send(json.dumps(message))


def recv(ws) -> dict:
    return json.loads(ws.recv())


def main() -> None:
    if not TOKEN:
        sys.exit("Set KAGENT_TOKEN in this window first.")

    with connect(URL) as ws:
        send(ws, {"type": "auth", "token": TOKEN})
        print("auth:", recv(ws))

        send(ws, {"type": "models"})
        print("models:", recv(ws))

        send(ws, {"type": "skills"})
        print("skills:", recv(ws))

        send(ws, {"type": "chat", "request": "hello", "model": "fake"})
        while True:
            message = recv(ws)
            print("chat:", message)
            if message["type"] == "chat_done":
                break


if __name__ == "__main__":
    main()
