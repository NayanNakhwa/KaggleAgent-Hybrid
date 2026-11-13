# Project scope and plan

Last updated: 2026-11-13

## 1. Goal

KaggleAgent-Hybrid is a hybrid coding agent. You type a request on your Windows laptop. A planning agent splits it into subtasks. Worker agents do the tasks with tools (Python, files, shell, web docs, linter). A judge checks each result and retries if needed. A synthesizer writes the final answer.

The language model (Ollama) runs on a free Kaggle GPU. The laptop talks to it through a tunnel. This means you can use a large model without owning a GPU.

## 2. Architecture

```
Laptop (Windows 11)                          Kaggle notebook (GPU)
---------------------------------            ----------------------
Client (Rich CLI now, Streamlit later)       Ollama (local model server)
        |                                           ^
        v  WebSocket /ws + token                    |
Server (FastAPI, core/server.py)  ---- tunnel ------+   (Phase D)
        |
        v
LangGraph agent: plan -> worker fan-out -> judge -> retry -> synthesize -> answer
        |
        v
Skills (tools) in workspace/mcp_skills/
```

Phase B runs everything on the laptop in fake mode. No Ollama, no Kaggle, no tunnel yet.

## 3. Components and where they live

| Part | Folder or file | Purpose |
|---|---|---|
| Server | `core/server.py` | WebSocket endpoint `/ws`. Checks the token. Routes messages. |
| Config | `core/config.py` | All settings from environment variables. |
| Graph | `core/superagent.py` | The agent graph (plan, worker, judge, retry, synthesize). |
| Chat bridge | `core/graph_chat.py` | Sends graph events to the WebSocket as they happen. |
| LLM (real) | `core/llm.py` | Talks to Ollama. |
| LLM (fake) | `core/fake_llm.py` | Scripted answers for tests and manual runs. |
| Skills loader | `core/mcp_loader.py`, `core/workers.py` | Finds and loads skills. Hot-plug: new skill files are picked up. |
| Skills (tools) | `workspace/mcp_skills/*.py` | python_repl, linter, file_explorer, file_editor, bash_terminal, web_docs. |
| Paths | `core/paths.py` | Safe paths inside the workspace. |
| CLI client | `client/cli.py`, `client/protocol.py` | Rich terminal client. `protocol.py` holds pure message helpers. |
| Tests | `tests/` | pytest tests for backend, CLI, graph and server. |
| Docs | `docs/context/` | Handoff, next-session guide, architecture, decisions, runbook, this file. |
| Smoke script | `scripts/smoke_ws.py` | Quick WebSocket check. |

## 4. Protocol (client to server)

First message must be auth: `{"type":"auth","token":"..."}`. Then:

| Client sends | Server replies |
|---|---|
| `{"type":"models"}` | `{"type":"models","models":[...]}` |
| `{"type":"skills"}` | `{"type":"skills","skills":[...]}` |
| `{"type":"chat","request":"...","model":"..."}` | `plan`, `worker`, `judge` events, then `chunk` messages, `answer_done`, `chat_done` |
| `{"type":"persist"}` | `persist_pending` (stub until Phase E) |

Auth failure: `{"type":"error","message":"auth failed"}` then close code 1008.

## 5. Settings (environment variables)

| Name | Default | Meaning |
|---|---|---|
| `KAGENT_TOKEN` | none (refuses everyone) | Shared secret. Set in the server and the client window. Local dev: `local-dev-test`. |
| `KAGENT_LLM` | `ollama` | `fake` for scripted answers, `ollama` for the real model. |
| `KAGENT_FAKE_DELAY` | `0` | Seconds to wait in each fake call. Manual Ctrl+C tests only. |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Where Ollama listens. |
| `KAGENT_DEFAULT_MODEL` | `qwen2.5-coder:7b` | Model used when none is chosen. |
| `KAGENT_MAX_ROUNDS` | `2` | How many plan-work-judge rounds are allowed. |
| `KAGENT_MAX_SUBTASKS` | `4` | Max subtasks from the planner. |
| `KAGENT_MAX_WORKER_STEPS` | `6` | Max tool steps for one worker. |
| `KAGENT_WORKSPACE` | `workspace/` | Folder the tools can touch. |
| `KAGENT_SKILLS_DIR` | `workspace/mcp_skills/` | Folder with skill files. |

Allowed models (real mode): `qwen2.5-coder:7b`, `deepseek-coder:6.7b`, `llama3.1:8b`.

## 6. Phases and status

| Phase | Goal | Status |
|---|---|---|
| A | Core agent graph and skills, tested | Complete. On `master`. |
| B | WebSocket server and Rich CLI, fake mode | Mostly complete. Ctrl+C re-test pending. |
| C | Streamlit web UI | Next. |
| D | Kaggle notebook with Ollama, tunnel, handshake, live tokens | Not started. |
| E | Persist skills to a branch, README, polish, pull request to `master` | Not started. |

## 7. Phase C plan (Streamlit UI)

Goal: a browser page that does what the CLI does.

Design (chosen; no need to pick again):
- File: `ui/app.py`. Run with `streamlit run ui/app.py`.
- Reuse `client/protocol.py` for decoding and for the turn state logic.
- Use a synchronous WebSocket client, the same style as the CLI.
- Token comes only from the `KAGENT_TOKEN` environment variable. The page never asks for it and never stores it.
- Page parts: model dropdown (from the server), skills list, chat box, plan table, worker and judge lines, answer, and an error box.
- Tests: a small test that the page helpers build correct messages, using the existing scripted-socket pattern.
- Add `streamlit` to `requirements.txt` only after a version check with the user's `.venv`.

Done when: the user sends a request in the browser and sees the same events as in the CLI, with fake mode running.

## 8. Phase D plan (Kaggle, Ollama, tunnel)

Goal: the agent uses a real model on Kaggle.

Design (chosen):
- Kaggle notebook installs Ollama, pulls one allowed model, and starts Ollama on localhost.
- Tunnel: `cloudflared` quick tunnel. It needs no account. The notebook prints a public URL. The laptop uses that URL as `OLLAMA_HOST`.
- Handshake: the notebook prints its URL and a check value. The laptop tests `/api/tags` before starting the server.
- Token: the real `KAGENT_TOKEN` lives only in Kaggle Secrets and on the laptop environment. Never in the repo, the docs, or the chat.
- Server change for gap 3: send answer text as live tokens instead of 40-character chunks. This needs a streaming LLM call in `core/llm.py` and a small change in `core/server.py`.
- Gap 5 (cancellation): when a client disconnects, the graph should stop at the next step. Needed before interrupts are sent.

Done when: a real model answers a request from the laptop, through the tunnel, with live tokens.

## 9. Phase E plan (finish)

- Persist: generated skills are saved to a new branch (not `master`). Needs a confirmation from the user before any push.
- README at the repo root: setup, run, test.
- Final polish: `ruff check .` and `pytest -v` pass. Context docs updated.
- Pull request from `phase-b-cli` into `master`. The user does the merge after confirming.

## 10. Safety rules (never break these)

- No real token, password or key in the repo, the docs, or the chat.
- The server refuses everyone when `KAGENT_TOKEN` is not set.
- The token is compared in constant time.
- Tools stay inside the workspace folder (path checks in `core/paths.py`).
- Web tool refuses private addresses.
- Nothing is pushed, deleted, or merged without the user's confirmation.

## 11. Decisions log (short)

| Date | Decision | Reason |
|---|---|---|
| 2026-11-12 | Work on `phase-b-cli`, not `master` | Keeps `master` as the stable Phase A line. |
| 2026-11-13 | `KAGENT_FAKE_DELAY` added, default 0 | Makes Ctrl+C testable by hand. Off in tests and normal runs. |
| 2026-11-13 | Disconnect during a turn is quiet, not an error | Avoids a traceback when the user presses Ctrl+C. |
| 2026-11-13 | Snapshot is `git archive HEAD` | Only committed work reaches the next session. |
| 2026-11-13 | Phase D tunnel is `cloudflared` quick tunnel | No account needed. Simple for a beginner. |
