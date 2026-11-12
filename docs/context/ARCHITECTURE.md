# Architecture

## Components
| Path | Role |
|---|---|
| core/superagent.py | LangGraph superagent: plan, worker fan-out, judge, retry, synthesize. |
| core/workers.py | Worker execution, role gate, step budget. |
| core/mcp_loader.py | Loads skills from workspace/mcp_skills/. Skips the template and bad files. |
| core/config.py | Settings from environment variables. |
| core/llm.py | Ollama client (OllamaEngine). |
| core/fake_llm.py | Scripted FakeLLM for offline tests and fake mode. |
| core/graph_chat.py | Runs the graph in a thread and forwards events to the WebSocket. |
| core/server.py | FastAPI WebSocket server at /ws with token auth. |
| client/protocol.py | Pure wire helpers and TurnState. No I/O. |
| client/cli.py | Rich terminal client, synchronous websockets. |
| scripts/smoke_ws.py | End-to-end WebSocket smoke test. |
| tests/ | pytest suite. test_cli.py uses a scripted fake socket. |

## Environment variables
| Name | Default | Notes |
|---|---|---|
| KAGENT_TOKEN | none | Required. Server refuses everyone if unset. Client reads it from env only. |
| KAGENT_LLM | ollama | fake or ollama. Any other value raises RuntimeError. |
| KAGENT_URL | ws://127.0.0.1:8000/ws | Used by the client and smoke test. |

## WebSocket protocol (confirmed from a live dump, fake mode)
Every message is a JSON object with a string "type". All messages are flat, with no nested "data" wrapper.

Auth (first message required):
- Client sends: {"type":"auth","token":"..."}
- Success: {"type":"auth_ok"}
- Failure: {"type":"error","message":"auth failed"}, then close with code 1008.

Models and skills:
- Client sends: {"type":"models"} returns {"type":"models","models":["fake"]}
- Client sends: {"type":"skills"} returns {"type":"skills","skills":["bash_terminal","file_editor","file_explorer","linter","python_repl","web_docs"]}

Chat:
- Client sends: {"type":"chat","request":"...","model":"fake"}
- Server sends, in order:
  - {"type":"plan","subtasks":[{"role":"executor","task":"..."}]}
  - {"type":"worker","id":"r1-0","role":"executor","ok":true}
  - {"type":"judge","id":"r1-0","accepted":true}
  - {"type":"chunk","text":"..."} (40 characters per chunk)
  - {"type":"answer_done","text":"full answer"}
  - {"type":"chat_done"}
- Errors (bad JSON, unknown type, unknown model, agent failure): {"type":"error","message":"..."}

Persist: {"type":"persist"} returns a pending stub until Phase E.

## Graph flow
plan -> fan-out to workers -> judge each result -> retry failed rounds up to a limit -> synthesize -> answer.
Unresolved items are marked when rounds run out.
