# Runbook

All commands run in PowerShell from the repo root with `.venv` active.

## Activate
```powershell
cd "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
```

## Checks
```powershell
ruff check .
pytest -v
pytest -rs    # shows why tests were skipped
```
Expected on Windows: all checks passed, 23 passed, 2 skipped.

## Start the server (Window 1, leave it running)
```powershell
$env:KAGENT_TOKEN = "local-dev-test"
$env:KAGENT_LLM = "fake"
uvicorn core.server:make_app --factory --port 8000
```
Ready when the output shows `Uvicorn running on http://127.0.0.1:8000`.
Stop with Ctrl+C.

## Smoke test (Window 2)
```powershell
$env:KAGENT_TOKEN = "local-dev-test"
python scripts/smoke_ws.py
```
Environment variables are per window. Set them in every window that needs them.

## Git
```powershell
git status
git branch --show-current
git log --oneline -5
```

Commit and push the docs on `phase-b-cli` (run only after the user confirms):
```powershell
git add docs/context
git commit -m "Add project context docs and handoff"
git push -u origin phase-b-cli
```

Make a snapshot to share with the next session:
```powershell
git archive --format=zip --output="$env:USERPROFILE\Desktop\kagent-snapshot.zip" HEAD
```

## Common problems
| Symptom | Cause | Fix |
|---|---|---|
| `skills:` is empty | Server started outside the repo root | `cd` to the repo root and restart |
| Auth refused | Token differs between windows | Set `KAGENT_TOKEN` in the same window as the command |
| `ModuleNotFoundError: core` | Wrong folder or `.venv` not active | Activate `.venv` and run from the repo root |
| Port 8000 in use | An old server is still running | Ctrl+C the old window, or use another port and set `KAGENT_URL` |
| Bash tests skipped | Windows | Expected |
