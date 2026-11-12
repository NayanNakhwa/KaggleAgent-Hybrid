# Architecture

## Components
- `core/config.py`: `Settings` and `get_settings()`. Reads environment variables. Defaults: workspace `workspace/`, skills `workspace/mcp_skills/`, Ollama `http://127.0.0.1:11434`, default model `qwen2.5-coder:7b`, allowed models `qwen2.5-coder:7b`, `deepseek-coder:6.7b`, `llama3.1:8b`, max rounds 2, max subtasks 4, max worker steps 6.
- `core/llm.py`: `OllamaEngine` with `complete` and `stream`.
- `core/fake_llm.py`: deterministic fake LLM for tests and fake mode.
- `core/mcp_loader.py`: skill registry. Loads every `*.py` in `workspace/mcp_skills/` except names starting with `_`. Each skill defines `SKILL_NAME`, `DESCRIPTION`, `PARAMETERS`, and `run(**kwargs) -> str`. Broken skills are skipped. Output is capped at 20,000 characters.
- `core/superagent.py`: the LangGraph-style pipeline. `stream_events(graph, request, model)` is synchronous. Nodes: plan, worker fan-out, judge, retry, synthesize.
- `core/graph_chat.py`: runs `stream_events` in a thread and forwards each event to the async WebSocket side. Final `answer` events are held and sent as chunks.
- `core/server.py`: FastAPI WebSocket at `/ws`. `make_app()` is the factory. `KAGENT_LLM=fake` uses the fake LLM. `KAGENT_LLM=ollama` uses `OllamaEngine`.
- `scripts/smoke_ws.py`: manual smoke test. Reads `KAGENT_URL` (default `ws://127.0.0.1:8000/ws`) and `KAGENT_TOKEN`.

## WebSocket protocol (as of Phase B)
The first message must be auth. The server compares the token with `hmac.compare_digest` against `KAGENT_TOKEN`. If the server has no token set, it refuses every client.

Client to server:
| type | fields | notes |
|---|---|---|
| `auth` | `token` | must be the first message |
| `models` | none | returns the model list |
| `skills` | none | returns the skill names |
| `chat` | `request`, `model` | starts a run |
| `persist` | not yet defined | stub until Phase E |

Server to client, as observed in the smoke test:
| type | fields | notes |
|---|---|---|
| `auth_ok` | none | |
| `models` | `models` (list) | fake mode returns `['fake']` |
| `skills` | `skills` (list) | |
| `plan` | `subtasks` (list of `role`, `task`) | |
| `worker` | `id`, `role`, `ok` | output text not included |
| `judge` | `id`, `accepted` | |
| `chunk` | `text` | answer text in pieces |
| `answer_done` | `text` | full answer |
| `chat_done` | none | run finished |

Error message types are not confirmed. Check `core/server.py` before the CLI relies on them.

## Planned: Rich CLI client (`client/`)
See `DECISIONS.md` for the chosen design.

## Planned deployment
Laptop runs the UI and server. Kaggle runs Ollama on a GPU. A tunnel connects them. Real token lives only in Kaggle Secrets. Tunnel details are chosen in Phase D.
