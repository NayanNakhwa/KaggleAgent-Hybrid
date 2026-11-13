# Project scope and plan

Last updated: 2026-11-13 (end of session 3)

## 1. Goal

KaggleAgent-Hybrid is a hybrid coding agent. You type a request on your Windows laptop. A planner splits it into subtasks. Workers do the subtasks with tools (Python, files, shell, web docs, linter). A judge checks each result and asks for a retry if needed. A synthesizer writes the final answer.

The language model (Ollama) runs on a free Kaggle GPU. The laptop talks to it through a tunnel. You get a large model without owning a GPU.

## 2. Architecture

```
Laptop (Windows 11)                            Kaggle notebook (GPU)
-----------------------------                  ----------------------
Client (Rich CLI now, Streamlit later)         Ollama (model server)
        |                                              ^
        v  WebSocket /ws + token                       |
Server (FastAPI, core/server.py)  ---- tunnel ---------+   (Phase D)
        |
        v
LangGraph: plan -> worker fan-out -> judge -> retry -> synthesize -> answer
        |
        v
Skills (tools) in workspace/mcp_skills/
```

Phase B runs everything on the laptop in fake mode. No Ollama, no Kaggle, no tunnel yet.

## 3. Components

| Part | File or folder | Purpose |
|---|---|---|
| Server | `core/server.py` | WebSocket endpoint `/ws`. Checks the token. Routes messages. |
| Config | `core/config.py` | All settings from environment variables. |
| Graph | `core/superagent.py` | The agent graph. |
| Chat bridge | `core/graph_chat.py` | Sends graph events to the WebSocket as they happen. |
| LLM (real) | `core/llm.py` | Talks to Ollama. |
| LLM (fake) | `core/fake_llm.py` | Scripted answers for tests and manual runs. |
| Skills loader | `core/mcp_loader.py`, `core/workers.py` | Finds and loads skills. New skill files are picked up (hot-plug). |
| Skills (tools) | `workspace/mcp_skills/*.py` | python_repl, linter, file_explorer, file_editor, bash_terminal, web_docs. |
| Paths | `core/paths.py` | Safe paths inside the workspace. |
| CLI client | `client/cli.py`, `client/protocol.py` | Rich terminal client. `protocol.py` holds pure helpers. |
| UI (Phase C) | `ui/app.py` | Streamlit browser page. Not built yet. |
| Tests | `tests/` | pytest tests. |
| Docs | `docs/context/` | Handoff, next-session guide, this file, README index. Also ARCHITECTURE, DECISIONS, RUNBOOK. |
| Smoke script | `scripts/smoke_ws.py` | Quick WebSocket check. |
| Handshake (Phase D) | `scripts/check_ollama.py` | Checks the Ollama URL before the server starts. Not built yet. |

## 4. Protocol (client to server)

First message must be auth: `{"type":"auth","token":"..."}`.

| Client sends | Server replies |
|---|---|
| `{"type":"models"}` | `{"type":"models","models":[...]}` |
| `{"type":"skills"}` | `{"type":"skills","skills":[...]}` |
| `{"type":"chat","request":"...","model":"..."}` | `plan`, `worker`, `judge` events, then `chunk` messages, `answer_done`, `chat_done` |
| `{"type":"persist"}` | `persist_pending` (stub until Phase E) |

Auth failure: `{"type":"error","message":"auth failed"}`, then close code 1008.

Phase D adds live token messages and worker output text. The exact format is decided in Phase D and documented in ARCHITECTURE.md.

## 5. Settings (environment variables)

| Name | Default | Meaning |
|---|---|---|
| `KAGENT_TOKEN` | none (refuses everyone) | Shared secret. Same value in server and client windows. Local dev: `local-dev-test`. |
| `KAGENT_LLM` | `ollama` | `fake` for scripted answers, `ollama` for the real model. |
| `KAGENT_FAKE_DELAY` | `0` | Seconds to wait in each fake call. Manual Ctrl+C tests only. |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Where Ollama listens. Phase D sets it to the tunnel URL. |
| `KAGENT_DEFAULT_MODEL` | `qwen2.5-coder:7b` | Model used when none is chosen. |
| `KAGENT_MAX_ROUNDS` | `2` | Plan-work-judge rounds allowed. |
| `KAGENT_MAX_SUBTASKS` | `4` | Max subtasks from the planner. |
| `KAGENT_MAX_WORKER_STEPS` | `6` | Max tool steps per worker. |
| `KAGENT_WORKSPACE` | `workspace/` | Folder the tools may touch. |
| `KAGENT_SKILLS_DIR` | `workspace/mcp_skills/` | Folder with skill files. |

Allowed models (real mode): `qwen2.5-coder:7b`, `deepseek-coder:6.7b`, `llama3.1:8b`.

## 6. Phases and status

| Phase | Goal | Status |
|---|---|---|
| A | Core agent graph and skills, tested | Complete. On `master`. |
| B | WebSocket server and Rich CLI, fake mode | Complete (2026-11-13). Ctrl+C and auth checks verified on `ea2db92`. |
| C | Streamlit web UI | Next. Steps in NEXT_SESSION.md, Part 3. |
| D | Kaggle notebook with Ollama, tunnel, handshake, live tokens, cancellation | Not started. |
| E | Persist skills to a branch, README, polish, pull request to `master` | Not started. |

## 7. Phase C plan (Streamlit UI)

Goal: a browser page that does what the CLI does.

Design (decided, do not re-ask):
- File: `ui/app.py`. Run with `streamlit run ui/app.py`.
- Reuse `client/protocol.py` for decoding and turn-state logic.
- Synchronous WebSocket client, same style as the CLI.
- Token comes only from the `KAGENT_TOKEN` environment variable. The page never asks for it and never stores it.
- Page parts: model dropdown (from the server), skills list, chat box, plan table, worker and judge lines, answer, error box.
- Tests: a small test that the helpers build correct messages, using the scripted-socket pattern from `tests/test_cli.py`.
- Add `streamlit` to `requirements.txt` only after checking the version in the user's `.venv`.

Done when: a request sent in the browser shows the same events as the CLI, in fake mode.

## 8. Phase D plan (Kaggle, Ollama, tunnel)

Goal: the agent uses a real model on Kaggle.

Design (decided):
- Kaggle notebook installs Ollama, pulls one allowed model, starts Ollama on localhost.
- Tunnel: `cloudflared` quick tunnel (no account needed). The notebook prints a public URL. The laptop sets it as `OLLAMA_HOST`.
- Handshake: the laptop checks `/api/tags` before the server starts.
- Token: the real `KAGENT_TOKEN` lives only in Kaggle Secrets and in the laptop environment. Never in the repo, the docs, or the chat.
- Server change: live tokens instead of 40-character chunks. Needs a streaming call in `core/llm.py` and a small change in `core/server.py`.
- Cancellation: when a client disconnects, the graph stops at the next step. Needed before interrupts.
- Worker output text in worker events.

Done when: a real model answers a request from the laptop through the tunnel, with live tokens.

## 9. Phase E plan (finish)

- Persist: generated skills saved to a new branch (not `master`). Needs the user's confirmation before any push.
- README at the repo root: setup, run, test.
- Polish: `ruff check .` and `pytest -v` pass. Context docs updated.
- Pull request from `phase-b-cli` into `master`. The user does the merge.

## 10. Safety rules (never break)

- No real token, password or key in the repo, the docs, or the chat.
- The server refuses everyone when `KAGENT_TOKEN` is not set.
- The token is compared in constant time.
- Tools stay inside the workspace folder (`core/paths.py`).
- The web tool refuses private addresses.
- Nothing is pushed, deleted, merged or amended without the user's confirmation.

## 11. Decisions log

| Date | Decision | Reason |
|---|---|---|
| 2026-11-12 | Work on `phase-b-cli`, not `master` | Keeps `master` as the stable Phase A line. |
| 2026-11-13 | `KAGENT_FAKE_DELAY` added, default 0 | Makes Ctrl+C testable by hand. Off in tests and normal runs. |
| 2026-11-13 | Disconnect during a turn is quiet, not an error | Avoids a traceback on Ctrl+C. |
| 2026-11-13 | Snapshot is `git archive HEAD` | Only committed work reaches the next session. |
| 2026-11-13 | Phase D tunnel is `cloudflared` quick tunnel | No account needed. Simple for a beginner. |
| 2026-11-13 | All work stays on `phase-b-cli` until Phase E | One branch to track. Pull request to `master` at the end. |
| 2026-11-13 | Worker output text added in Phase D, with streaming | UI changes happen once. |
