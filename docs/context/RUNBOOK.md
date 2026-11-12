# Runbook

Run all commands from the repo root in PowerShell.

## Setup
.\.venv\Scripts\Activate.ps1

## Lint and tests
ruff check .
pytest -v

Expected: All checks passed. pytest shows 36 passed and 2 skipped (Linux-only bash tests).

## Fake-mode server (Terminal 1, leave running)
.\.venv\Scripts\Activate.ps1
$env:KAGENT_LLM = "fake"
$env:KAGENT_TOKEN = "local-dev-test"
uvicorn core.server:make_app --factory --host 127.0.0.1 --port 8000

Stop with Ctrl+C.

## Rich CLI (Terminal 2)
.\.venv\Scripts\Activate.ps1
$env:KAGENT_TOKEN = "local-dev-test"
python -m client.cli

Inside the CLI: type a request, or use /models, /skills, /help, /quit.
Optional: python -m client.cli --model fake

Wrong-token check:
$env:KAGENT_TOKEN = "wrong-token-test"
python -m client.cli
Expected: authentication failed message, no token shown.

## Smoke test
$env:KAGENT_TOKEN = "local-dev-test"
python scripts\smoke_ws.py

## Git: sync and snapshot
git pull
git status
git archive --format=zip --output="$env:USERPROFILE\Desktop\kagent-snapshot.zip" HEAD

Note: git archive only includes committed files. Commit and push first.

## Git: commit and push docs (this session)
git add docs/context
git status
git commit -m "Update context docs for CLI milestone"
git push
git log --oneline -4

## Not yet available
- Ollama mode on Kaggle: needs the Phase D notebook and tunnel.
- Real token: needs Kaggle Secrets setup in Phase D.
