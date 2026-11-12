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
| master | 19b8bea | Phase A complete. Not touched since. Default branch on GitHub. |
| phase-b | f1e5bc5 | Phase B server. Verified by user. On origin. |
| phase-b-cli | 6530bd6, then this session's docs commit | Current work branch. Rich CLI added and verified by user in fake mode. Pushed to origin. |

Work lives on phase-b-cli until a pull request merges it into master.

## Done and verified by the user
- ruff check .: All checks passed.
- pytest -v: 36 passed, 2 skipped. The 2 skips are the Linux-only bash tests, expected on Windows.
- Fake-mode server starts. Token auth works.
- Wire format confirmed from a live dump (see ARCHITECTURE.md).
- Rich CLI (client/) in fake mode: connects, authenticates, shows plan table, worker and judge lines, answer panel, /models, /skills, /quit.
- Wrong token: refused with "authentication failed: auth failed". The token is not printed.
- CLI tests: 13 pass, using a scripted fake socket.

## Not yet done or untested
- Ollama mode (KAGENT_LLM=ollama): untested.
- Real token: not set up. It belongs only in Kaggle Secrets, never in the repo or chat.
- Kaggle notebook, tunnel, and handshake: not started (Phase D).
- Persist: returns a stub until Phase E.
- Interrupts: not implemented.

## Known gaps and small bugs
1. The wrong-token message reads "authentication failed: auth failed" (doubled). Fix in client/cli.py, Session.authenticate: print only the server message.
2. Ctrl+C during a running chat turn is not caught. It only works at the input prompt. Fix in run_repl or main.
3. Chat answers are sent as 40-character chunks after synthesis finishes, not as live tokens. Live tokens come in Phase D.
4. Worker events do not include the worker output text, so the CLI cannot show it.
5. If a client disconnects mid-run, the worker thread keeps running until the graph finishes. Add cancellation before the CLI sends interrupts.
6. Server auth failure is {"type":"error","message":"auth failed"} followed by close code 1008. This is now documented in ARCHITECTURE.md.

## Next steps (in order)
1. Phase C: Streamlit web UI. It reuses client/protocol.py and the same server. Fold in known gaps 1 and 2 as a small first step.
2. Phase D: Kaggle notebook running Ollama, tunnel, handshake, and live token streaming. Server change needed for gap 3.
3. Phase E: persist generated skills to a branch, README, final polish, then a pull request from phase-b-cli into master.

## Working rules (follow these)
- Give step-by-step PowerShell commands. The user pastes the full output after each step.
- The assistant cannot run Kaggle, Ollama, or the user's laptop. Verification is the user's runs.
- Say "untested" until the user confirms a result.
- Never ask for, accept, or store real tokens or passwords in chat. Local dev token: local-dev-test (fake mode, localhost only).
- Ask before any push, delete, merge, or other destructive action.
- Give full files or replace whole functions, not partial snippets. Replies must not be cut off, so keep each reply small enough to finish.
- Use branches. Do not commit to master directly.
- The user does not want to choose between options. Pick the best option, state it in one line, and proceed.

## How to resume in a new chat
1. In PowerShell, from the repo root:
   git pull
   git archive --format=zip --output="$env:USERPROFILE\Desktop\kagent-snapshot.zip" HEAD
2. Upload kagent-snapshot.zip to the new chat.
3. Paste this HANDOFF.md, or say "read docs/context in the zip".
4. Paste the output of the last step you ran.
