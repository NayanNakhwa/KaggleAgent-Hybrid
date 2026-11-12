# Handoff

## Project
KaggleAgent-Hybrid: a hybrid agent system. The user interface and server run on the laptop. Ollama runs on a Kaggle GPU and connects to the laptop through a tunnel.

- Repo: https://github.com/NayanNakhwa/KaggleAgent-Hybrid (public while in development)
- Default branch on GitHub: `master` (this is the "main" branch)
- Local path: `D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid`
- Environment: Windows 11, PowerShell, VS Code, Python 3.11.13 in `.venv`
- Activate before any command: `.\.venv\Scripts\Activate.ps1`

## Branch state
| Branch | Commit | Status |
|---|---|---|
| `master` | `19b8bea` | Phase A complete |
| `phase-b` | `f1e5bc5` | Phase B server, verified by user, pushed to origin |
| `phase-b-cli` | from `phase-b` | Current branch. Holds the docs commit. No CLI code yet. |

## Done
- **Phase A:** Superagent graph (`core/superagent.py`): plan, worker fan-out, judge, retry, synthesize. Skill loader (`core/mcp_loader.py`). Config (`core/config.py`). Ollama client (`core/llm.py`).
- **Phase B (server):** WebSocket server at `/ws` (`core/server.py`) with token auth, the real graph adapter (`core/graph_chat.py`), fake LLM mode (`core/fake_llm.py`), and smoke test (`scripts/smoke_ws.py`).
- **Verified by the user:**
  - `ruff check .` is clean.
  - `pytest -v`: 23 passed, 2 skipped. The 2 skips are the Linux-only bash tests and are expected on Windows.
  - Server starts, and auth works.
  - Smoke test in fake mode: `auth_ok`, `models` returns `['fake']`, `skills` returns the 6 real skills, and the full chat event sequence ends with `chat_done`.
- **Pushed:** `phase-b` is on origin (`d10eedf` and `f1e5bc5`).

## Not done
- **Rich CLI client** (`client/`): not started. The decisions are in `DECISIONS.md`.
- **Ollama mode** (`KAGENT_LLM=ollama`): untested.
- **Real token:** not yet set up. It belongs only in Kaggle Secrets.

## Known gaps
- Chat answers are sent as chunks after synthesis finishes, not as live tokens. Live tokens are planned for Phase D.
- `persist` returns a stub until Phase E.
- Worker events do not include the worker output text.
- If a WebSocket client disconnects mid-run, the worker thread keeps running until the graph finishes. Fine for now. Add cancellation before the CLI sends interrupts.
- Auth failure response type is not documented here. Check `core/server.py` before relying on it.

## Next steps
1. Commit and push the docs (see `RUNBOOK.md`). Push only after the user confirms.
2. Build the Rich CLI on `phase-b-cli`, following `DECISIONS.md`.
3. Phase C: Streamlit web UI.
4. Phase D: Kaggle notebook with Ollama, tunnel, handshake, and live token streaming.
5. Phase E: Persist Workspace (generated skills pushed to a branch), README, final polish.

## Working rules
- Give step-by-step PowerShell commands. The user pastes the full output after each step.
- The assistant cannot run Kaggle, Ollama, or the user's laptop. Verification is the user's runs.
- Say "untested" until the user confirms a result.
- Never ask for or accept real tokens or passwords in chat. Local dev token: `local-dev-test` (fake mode, localhost only).
- Ask before any push, delete, or other destructive action.
- Give full files or replace whole functions, not partial snippets.
- Use branches. Do not commit to `master` directly.
- The user does not want to choose between options. Pick the best option, state it in one line, and proceed.

## How to start the next session
1. Create a fresh snapshot of the repo:
   ```powershell
   git archive --format=zip --output="$env:USERPROFILE\Desktop\kagent-snapshot.zip" HEAD
   ```
2. Upload `kagent-snapshot.zip` to the new chat.
3. Paste the current `HANDOFF.md` text, or say "read docs/context in the zip."
4. Paste the output of the step you ran last.
