# Handoff

Last updated: 2026-11-12

## Project
KaggleAgent-Hybrid is a hybrid agent system. The UI and server run on the user's Windows 11 laptop. Ollama runs on a Kaggle GPU and connects to the laptop through a tunnel.

- Local path: D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid
- Python 3.11.13 in .venv. Activate with: .\.venv\Scripts\Activate.ps1
- Shell: PowerShell in VS Code.

## Branches
| Branch | Commit | Status |
|---|---|---|
| master | 19b8bea | Phase A complete. Default branch on GitHub. Changes only through the final pull request. |
| phase-b | f1e5bc5 | Phase B server. Verified by user. On origin. |
| phase-b-cli | 7e64ce8 | Current work branch. Pushed to origin. Holds the latest project files. |

Work lives on phase-b-cli until a pull request merges it into master.

## Done and verified by the user
- ruff check .: All checks passed.
- pytest -v: 37 passed, 2 skipped. The 2 skips are the Linux-only bash tests, expected on Windows.
- Fake-mode server starts. Token auth works.
- Wire format confirmed from a live dump (see ARCHITECTURE.md).
- Rich CLI (client/) in fake mode: connects, authenticates, shows plan table, worker and judge lines, answer panel, /models, /skills, /quit.
- Wrong token: refused with "auth failed". The token is not printed.
- CLI tests: pass, using a scripted fake socket.

## Done, committed and pushed, not yet verified on the laptop
- Auth error text fixed in client/cli.py (no more "auth failed: auth failed").
- Ctrl+C during a chat turn is caught. The CLI prints a message and closes the connection. Needs a manual check (see NEXT_SESSION.md).

## Not yet done or untested
- Ollama mode (KAGENT_LLM=ollama): untested.
- Real token: not set up. It belongs only in Kaggle Secrets, never in the repo or chat.
- Kaggle notebook, tunnel, and handshake: not started (Phase D).
- Persist: returns a stub until Phase E.
- Interrupts to the server: not implemented.

## Known gaps and small bugs
1. FIXED and pushed: doubled "auth failed" message.
2. FIXED and pushed, untested on laptop: Ctrl+C during a chat turn.
3. Chat answers are sent as 40-character chunks after synthesis finishes, not as live tokens. Live tokens come in Phase D.
4. Worker events do not include the worker output text, so the CLI cannot show it.
5. If a client disconnects mid-run, the worker thread keeps running until the graph finishes. Add cancellation before the CLI sends interrupts.
6. Server auth failure is {"type":"error","message":"auth failed"} followed by close code 1008. Documented in ARCHITECTURE.md.

## Next steps (in order)
1. Manual check of Ctrl+C and the auth message on the laptop (fake mode).
2. Phase C: Streamlit web UI. It reuses client/protocol.py and the same server.
3. Phase D: Kaggle notebook running Ollama, tunnel, handshake, and live token streaming. Server change needed for gap 3.
4. Phase E: persist generated skills to a branch, README, final polish, then a pull request from phase-b-cli into master.

## Working rules (follow these)
- The user is still learning to code. Explain each step in plain language: what it does and why.
- Give full files, not partial snippets. When a file changes, give the whole file.
- Every PowerShell command block must say:
  - which window to use: the current one, or a new one;
  - whether .venv must be active (prompt starts with (.venv));
  - the folder to run from (the repo root).
- Use one code block per set of commands, in the order to run them. The user pastes the full output after each step.
- The assistant cannot run Kaggle, Ollama, or the user's laptop. Verification is the user's runs.
- Say "untested" until the user confirms a result.
- Never ask for, accept, or store real tokens or passwords in chat. Local dev token: local-dev-test (fake mode, localhost only).
- Ask before any push, delete, merge, or other destructive action.
- Use branches. Do not commit to master directly.
- The user does not want to choose between options. Pick the best option, state it in one line, and proceed.
- Keep each reply small enough to finish. Do not cut off code.

## How to resume in a new chat
See docs/context/NEXT_SESSION.md.
