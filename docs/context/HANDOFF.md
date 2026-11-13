# Handoff

Last updated: 2026-11-13

## Project
KaggleAgent-Hybrid is a hybrid agent system. The UI and server run on the user's Windows 11 laptop. Ollama runs on a Kaggle GPU and connects to the laptop through a tunnel (Phase D).

- Local path: D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid
- Python 3.11.13 in .venv. Activate with: .\.venv\Scripts\Activate.ps1
- Shell: PowerShell in VS Code.
- GitHub: https://github.com/NayanNakhwa/KaggleAgent-Hybrid

## Branches
| Branch | Commit | Status |
|---|---|---|
| master | 19b8bea | Phase A complete. Default branch on GitHub. Changes only through the final pull request. |
| phase-b | f1e5bc5 | Phase B server. On origin. |
| phase-b-cli | see `git log -1` | Current work branch. Pushed to origin. |

Work lives on phase-b-cli until a pull request merges it into master (Phase E).
Commit at the time of writing: 8e19112, plus the commit made after this handoff. Run `git log -1` to confirm.

## Done and verified by the user
- `ruff check .`: passed (earlier session).
- Fake-mode server starts. Token auth works.
- Wrong token: prints "auth failed" once. Token is not printed. (2026-11-13)
- Chat in fake mode: plan, worker, judge and answer panels render. (2026-11-13)
- Ctrl+C during a chat turn: CLI printed "interrupted. Closing the connection; the server may still finish the current turn." Test used `KAGENT_FAKE_DELAY=3`. (2026-11-13)
- `pytest -v`: 37 passed, 2 skipped. Run before the server fix below. (2026-11-13)

## Changed in code, not yet verified
- `core/server.py`: `_chat` has a new `except WebSocketDisconnect: return` block. This stops the traceback when the client disconnects mid-turn.
  - The server log was clean after one Ctrl+C run with this fix (2026-11-13).
  - The CLI's "interrupted" line did not appear in the last paste. Re-run the Ctrl+C test to confirm.
  - `pytest -v` has not been re-run since this fix.
- Test delay: `KAGENT_FAKE_DELAY` (seconds, default 0) in `core/config.py` and `core/fake_llm.py`. Use it only for manual Ctrl+C tests. Never set it in real runs.

## Not yet done or untested
- Ollama mode (`KAGENT_LLM=ollama`): untested.
- Real token: not set up. It belongs only in Kaggle Secrets, never in the repo or in chat.
- Kaggle notebook, tunnel and handshake: not started (Phase D).
- Persist: returns a stub until Phase E.
- Interrupts from client to server: not implemented.

## Known gaps and small bugs
1. FIXED: doubled "auth failed" message.
2. VERIFIED: Ctrl+C during a chat turn prints a message and exits (2026-11-13, with the delay).
3. Chat answers are sent as 40-character chunks after synthesis, not as live tokens. Live tokens come in Phase D.
4. Worker events do not include the worker's output text, so the CLI cannot show it.
5. PARTLY FIXED: a client disconnect mid-turn no longer logs a traceback (see above). The graph thread still runs to the end of the turn. Add cancellation before Phase D sends interrupts.
6. Auth failure is `{"type":"error","message":"auth failed"}` followed by close code 1008. Documented in ARCHITECTURE.md.

## Next steps (in order)
1. Run `ruff check .` and `pytest -v`. Expect 37 passed, 2 skipped. Then commit, push to phase-b-cli, and make the snapshot (see NEXT_SESSION.md).
2. Re-run the Ctrl+C test and confirm "interrupted" plus a clean server log.
3. Phase C: Streamlit web UI. It reuses `client/protocol.py` and the same server.
4. Phase D: Kaggle notebook running Ollama, tunnel, handshake, and live token streaming. Needs a server change for gap 3.
5. Phase E: persist generated skills to a branch, README, final polish, then a pull request from phase-b-cli into master.

## Working rules (follow these)
- The user is still learning to code. Explain each step in plain language: what it does and why.
- Give full files, not partial snippets. When a file changes, give the whole file.
- Every PowerShell block must say which window to use (current or new), whether `.venv` must be active (prompt starts with `(.venv)`), and the folder to run from (repo root).
- One code block per set of commands, in the order to run them. The user pastes the full output after each step.
- Say "untested" until the user confirms a result.
- Never ask for, accept, or store real tokens or passwords. Local dev token: `local-dev-test` (fake mode, localhost only).
- Ask before any push, delete, merge, or other destructive action.
- Use branches. Do not commit to master directly.
- The user does not want to choose between options. Pick the best option, state it in one line, and proceed.
- Keep each reply small enough to finish. Do not cut off code.
- If the assistant has not read a file in raw form, it must say so and ask the user to paste `Get-Content <file>` output.

## How to resume in a new chat
See docs/context/NEXT_SESSION.md.
