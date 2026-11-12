# Decisions

Each decision is final unless new information requires a change. Record any change here with the date.

## D1. Git branches
- Work on feature branches. Phase B is on `phase-b`. Docs and the CLI are on `phase-b-cli`.
- GitHub's default branch is `master`, which the user calls "main". Merge to `master` through a pull request once a phase is verified.
- Date: 2026-11-12.

## D2. CLI scope (first version)
- Chat with live events: plan, worker, judge, streamed answer, and done.
- Commands: `/models` and `/skills`, which call the server's `models` and `skills` messages.
- Commands: `/quit` to exit.
- Not included: `persist` (stub until Phase E), and interrupts (need server cancellation first).
- Reason: this covers everything the server can do now, and avoids features the server cannot back yet.

## D3. CLI libraries
- Use `rich` for rendering and `websockets` (sync client, same as `scripts/smoke_ws.py`) for the connection.
- Add both to `requirements.txt` with versions matching what is installed in `.venv`. Check the installed versions with `pip show rich websockets` before pinning.
- Reason: `websockets` is already in use, and `rich` is the standard terminal rendering library for Python.

## D4. CLI configuration
- Read `KAGENT_URL` (default `ws://127.0.0.1:8000/ws`) and `KAGENT_TOKEN` from the environment.
- Never accept a token as a command-line argument, because it would stay in shell history.
- Model: default to the first model returned by the server. Override with `--model`.

## D5. CLI file layout
- `client/__init__.py`
- `client/protocol.py`: message builders and event formatting. No network code, so it is easy to test.
- `client/cli.py`: `main()`, the input loop, and the Rich rendering.
- `tests/test_cli.py`: tests for `protocol.py`, and one test that runs the CLI against the real server in fake mode.

## D6. Process
- Full files only, not partial snippets.
- Tests are written first for each new piece, then the code.
- The user runs the tests and reports results. Say "untested" until the user confirms.

## D7. Secrets
- Local dev token: `local-dev-test`, fake mode, localhost only.
- Real token: Kaggle Secrets only. Never in code, docs, or chat.
