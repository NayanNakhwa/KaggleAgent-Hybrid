"""Mind engine: the LLM client that talks to the Ollama server running on Kaggle.

The model is passed per call, so the UI can hot-swap models without restarting anything.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol

import httpx
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama

from core.config import get_settings


class LLMClient(Protocol):
    """Anything that can answer a chat. Tests use a fake implementation."""

    def complete(self, messages: Sequence[BaseMessage], model: str) -> str: ...


class OllamaEngine:
    def __init__(self, base_url: str | None = None, temperature: float = 0.2, timeout: float = 300.0):
        self.base_url = base_url or get_settings().ollama_url
        self.temperature = temperature
        self.timeout = timeout
        self._clients: dict[str, ChatOllama] = {}

    def _client(self, model: str) -> ChatOllama:
        if model not in get_settings().allowed_models:
            raise ValueError(f"model '{model}' is not in the allowed list")
        if model not in self._clients:
            self._clients[model] = ChatOllama(
                model=model,
                base_url=self.base_url,
                temperature=self.temperature,
                client_kwargs={"timeout": self.timeout},
            )
        return self._clients[model]

    def complete(self, messages: Sequence[BaseMessage], model: str) -> str:
        return str(self._client(model).invoke(list(messages)).content)

    def stream(self, messages: Sequence[BaseMessage], model: str) -> Iterator[str]:
        """Yield text tokens as Ollama produces them. Used for live token streaming."""
        for chunk in self._client(model).stream(list(messages)):
            if chunk.content:
                yield str(chunk.content)

    def installed_models(self) -> list[str]:
        """Models currently present in the Ollama store (GET /api/tags)."""
        response = httpx.get(f"{self.base_url}/api/tags", timeout=10)
        response.raise_for_status()
        return [m["model"] for m in response.json().get("models", [])]
