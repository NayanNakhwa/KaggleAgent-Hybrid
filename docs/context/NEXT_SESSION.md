# Next session guide

Last updated: 2026-11-13

This file has four parts:
- Part 1: End a session (save, push, make the snapshot).
- Part 2: Start a new session (what to upload, what to paste, first checks).
- Part 3: What the assistant does in the new session (the plan).
- Part 4: Common problems and fixes.

Read HANDOFF.md (state) and PROJECT_SCOPE.md (scope and plan) too.

---

## Part 1: End a session

Do this at the end of every session. The next session only sees committed files.

### Step 1.1: Check that tests and style pass

Window: current PowerShell. Prompt must start with `(.venv)`. Folder: repo root.

```powershell
ruff check .
pytest -v
```

Expected: "All checks passed!" and "37 passed, 2 skipped". If something else shows, stop and tell the assistant.

### Step 1.2: Save and push the work

Window: same. Folder: repo root.

```powershell
git status
git add -A
git commit -m "Describe what changed in one line"
git push origin phase-b-cli
git status
```

What each line does:
- `git status` shows what changed.
- `git add -A` stages all changed files.
- `git commit` saves them with a message. Change the message to describe your change.
- `git push origin phase-b-cli` uploads the work branch to GitHub.
- The last `git status` should say "nothing to commit, working tree clean".

If `git commit` says "nothing to commit", that is fine: there was nothing new to save.

Never push to `master` directly. Work stays on `phase-b-cli` until Phase E.

### Step 1.3: Make the snapshot

Window: same. Run this AFTER Step 1.2, so the zip includes the latest commit.

```powershell
git archive --format=zip --output kagent-snapshot.zip HEAD
python -c "import zipfile; z=zipfile.ZipFile('kagent-snapshot.zip'); print(len(z.namelist()), 'files'); print([n for n in z.namelist() if 'context' in n])"
Move-Item -Force kagent-snapshot.zip "$HOME\Downloads\kagent-snapshot.zip"
```

Expected: a file count (about 44), and a list that includes `docs/context/HANDOFF.md`, `docs/context/NEXT_SESSION.md`, and `docs/context/PROJECT_SCOPE.md`. If the PROJECT_SCOPE line is missing, the docs were not committed. Go back to Step 1.2.

### Step 1.4: Save the chat

If your chat tool can export or copy the chat, save it as `chathub-chat.md` in Downloads. It helps the next session see what was tried.

---

## Part 2: Start a new session

### Step 2.1: Open a new chat

Use any account. Open a new chat with the assistant.

### Step 2.2: Upload the files

Upload these from your Downloads folder:
1. `kagent-snapshot.zip` (required)
2. `chathub-chat.md` (optional, if you saved it in Step 1.4)

### Step 2.3: Paste the starter prompt

Copy everything between the lines below and paste it as your first message.

---
I am continuing the KaggleAgent-Hybrid project. The attached kagent-snapshot.zip has the latest committed code and docs. If chathub-chat.md is attached, it is the chat from the last session.

Read docs/context/HANDOFF.md first, then docs/context/NEXT_SESSION.md, then docs/context/PROJECT_SCOPE.md. Read each file in raw form. If you cannot read a file in raw form, say so and ask me to paste Get-Content output.

Follow the working rules in HANDOFF.md. I am learning to code: explain each step, give full files, and wait for my pasted output before the next step. Never ask for real tokens or passwords.

First, tell me: the current branch, the newest commit, what is verified, and what is untested. Then give Part 2 step 2.4 from NEXT_SESSION.md.
---

### Step 2.4: Run the first checks

Use a NEW PowerShell window. Activate the venv first, then run from the repo root. (If you have not yet unzipped the snapshot into the repo, the repo itself is the source of truth; the snapshot is a copy for the assistant.)

```powershell
.\.venv\Scripts\Activate.ps1
git log --oneline -3
git status
git branch --show-current
```

Paste the full output into the new chat.

---

## Part 3: What the assistant does in the new session

The plan, in order. The assistant should follow it unless you say otherwise.

### Step 3.1: Re-test Ctrl+C with the server fix (2 windows)

Window 1 (server). Keep it open:

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_LLM = "fake"
$env:KAGENT_TOKEN = "local-dev-test"
$env:KAGENT_FAKE_DELAY = "3"
uvicorn core.server:make_app --factory --host 127.0.0.1 --port 8000
```

Window 2 (client):

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_TOKEN = "local-dev-test"
python -m client.cli
```

At `you>`, type `write a short hello world script`, press Enter, then press Ctrl+C within 3 seconds.

Expected:
- Window 2 prints "interrupted. Closing the connection..." and returns to the shell prompt.
- Window 1 shows no traceback after that.

Paste the full output of both windows. Then stop the server with Ctrl+C in window 1.

Also test the wrong token in window 2: `$env:KAGENT_TOKEN = "wrong-token-test"` then `python -m client.cli`. Expected: "auth failed" once.

### Step 3.2: Re-run the tests

Window 2, with `(.venv)`, repo root. `KAGENT_FAKE_DELAY` should not be set in this window (open a new window if unsure):

```powershell
pytest -v
```

Expected: 37 passed, 2 skipped.

### Step 3.3: Phase C (Streamlit UI)

The assistant will give the full files for the `ui/` folder and the steps to run them. In short:
- `ui/app.py`: a Streamlit page with a model dropdown, a chat box, the plan, worker and judge lines, and the answer.
- Reuses `client/protocol.py` and the same server.
- Reads the token only from the `KAGENT_TOKEN` environment variable. Never from a text box that stores it.
- Run with `streamlit run ui/app.py` in a new window, with the server running in another window.

### Step 3.4: Phase D and E

Later. Details are in PROJECT_SCOPE.md.

---

## Part 4: Common problems and fixes

| What you see | What to do |
|---|---|
| `.\.venv\Scripts\Activate.ps1` is blocked (execution policy) | Tell the assistant. Do not change system policy without asking. |
| `(.venv)` is not shown | Run `.\.venv\Scripts\Activate.ps1` from the repo root. |
| `uvicorn` not found | The venv is not active. Activate it, then try again. |
| "Address already in use" on port 8000 | An old server is still running. Close its window, or press Ctrl+C in it. |
| "LF will be replaced by CRLF" warning | Harmless. Ignore it. |
| `pytest` shows 2 skipped | Expected on Windows (Linux-only bash tests). |
| `git push` is rejected | Run `git pull` first, then tell the assistant before pushing again. |
| The client says "auth failed" but you expected success | Check that `KAGENT_TOKEN` in the client window matches the server window. |
| `KAGENT_FAKE_DELAY` is still set in a window | Close that window and open a new one. The delay is for manual tests only. |

## Part 5: Rules for the assistant (summary)

- Read HANDOFF.md first. Do not trust summaries. Ask for `Get-Content` output when unsure.
- One step at a time. Wait for the user's pasted output.
- Full files only. Explain each file in plain language.
- Never ask for real tokens, passwords, or keys.
- Ask before push, delete, or merge.
