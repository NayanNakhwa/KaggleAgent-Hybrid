# Next session guide

Last updated: 2026-11-13

Parts:
- Part 1: End of a session (checks, commit, push, snapshot, chat save, starter prompt)
- Part 2: Start of a session (what to upload, starter prompt, first checks)
- Part 3: The plan for the next session (what the assistant does)
- Part 4: How the assistant must guide you
- Part 5: Common problems and fixes

Read HANDOFF.md (state) and PROJECT_SCOPE.md (scope and plan) too.

---

## Part 1: End of a session

The final reply of every session must include these six items, in this order:
1. Output of the previous session (what the user pasted, short).
2. Updated docs for the next session (full files).
3. Summary of this session.
4. Commit and push commands.
5. New snapshot commands (run after the push).
6. Starter prompt for the next chat.

The user does the commands and pastes the output. The next session only sees committed files.

### Step 1.1: Checks (must pass before commit)

Window: current PowerShell. Prompt starts with `(.venv)`. Folder: repo root.

```powershell
ruff check .
pytest -v
```

Expected: "All checks passed!" and "37 passed, 2 skipped". If not, stop and paste the output.

### Step 1.2: Check what will be committed

```powershell
git status
git diff --stat
```

Read the list. Only expected files should appear. If a file appears that you did not change on purpose, stop and ask.

### Step 1.3: Commit and push

Only after 1.1 and 1.2 look right. Window: same.

```powershell
git add -A
git commit -m "Short description of the change"
git push origin phase-b-cli
git status
```

Expected: the push succeeds, and the last line says "nothing to commit, working tree clean".

Notes:
- Use `git add -A` only when the `git status` list is correct.
- Commit messages should say what changed, for example "Add Streamlit UI shell". Do not write "verified" unless the test was run and confirmed.
- Never push to `master`.

### Step 1.4: Make the snapshot

Window: same. Run AFTER the push, so the zip includes the latest commit.

```powershell
git archive --format=zip --output kagent-snapshot.zip HEAD
python -c "import zipfile; z=zipfile.ZipFile('kagent-snapshot.zip'); print(len(z.namelist()), 'files'); print([n for n in z.namelist() if 'context' in n])"
Move-Item -Force kagent-snapshot.zip "$HOME\Downloads\kagent-snapshot.zip"
```

Expected: a file count (about 44 or more), and the list includes `docs/context/HANDOFF.md`, `docs/context/NEXT_SESSION.md`, `docs/context/PROJECT_SCOPE.md`, and `docs/context/README.md`. If one is missing, the docs were not committed. Go back to Step 1.3.

### Step 1.5: Save the chat

Export or copy the chat, and save it as `chathub-chat.md` in Downloads. If your tool cannot export, paste the most important parts into the new chat instead.

---

## Part 2: Start of a session

### Step 2.1: Open a new chat

Any account. New chat.

### Step 2.2: Upload

From Downloads:
1. `kagent-snapshot.zip` (required)
2. `chathub-chat.md` (optional)

### Step 2.3: Paste the starter prompt

Use the starter prompt in the final reply of the last session. It is the same every time.

### Step 2.4: First checks

Window: NEW PowerShell. Folder: repo root.

```powershell
cd "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
git branch --show-current
git log --oneline -5
git status
git ls-files docs/context
```

Expected: the branch is `phase-b-cli`. `git status` says "nothing to commit" (or lists changes you know about). `git ls-files docs/context` lists all four docs files. Paste the full output into the new chat.

---

## Part 3: The plan for the next session

The assistant follows this order unless you say otherwise.

### Step 3.1: Confirm the state

Check the output of Step 2.4 against HANDOFF.md. If the newest commit is not `ea2db92` or a newer one, stop and ask.

### Step 3.2: Run the checks on the unpushed commit

Window: current, `(.venv)`, repo root.

```powershell
ruff check .
pytest -v
```

Expected: "All checks passed!" and 37 passed, 2 skipped.

### Step 3.3: Push ea2db92 (ask the user first)

The assistant asks for confirmation, then gives:

```powershell
git push origin phase-b-cli
git status
```

### Step 3.4: Re-run the Ctrl+C test (2 windows)

Window 1, server. Keep it open:

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_LLM = "fake"
$env:KAGENT_TOKEN = "local-dev-test"
$env:KAGENT_FAKE_DELAY = "3"
uvicorn core.server:make_app --factory --host 127.0.0.1 --port 8000
```

Window 2, client. New window, so it has no leftover settings:

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_TOKEN = "local-dev-test"
python -m client.cli
```

At `you>`, type `write a short hello world script`, press Enter, then press Ctrl+C within 3 seconds.

Expected:
- Window 2: "interrupted. Closing the connection..." then the shell prompt.
- Window 1: no traceback after that point.

Paste the full output of both windows. Then stop the server (Ctrl+C in window 1).

Then the wrong-token check, in window 2 (new window):

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_TOKEN = "wrong-token-test"
python -m client.cli
```

Expected: "auth failed" once.

### Step 3.5: Phase C, Streamlit UI

After 3.4 is confirmed, the assistant gives the full files for `ui/` and the run steps. Plan: PROJECT_SCOPE.md, section 7.

### Step 3.6: Phases D and E

Later. See PROJECT_SCOPE.md, sections 8 and 9.

---

## Part 4: How the assistant must guide you

- Start from HANDOFF.md. Name the newest commit and the next step.
- Explain each step in plain language: what it does and why.
- One PowerShell block per set of commands. Say which window (new or current), whether `(.venv)` must show, and the folder.
- Wait for pasted output before the next step.
- Say "untested" until the user shows output.
- Give full files when a file changes. Do not give partial snippets.
- Before writing commit instructions, check `git log` and `git status` output. Do not assume what was committed.
- Ask before any push, delete, merge, or amend.
- Never ask for, store, or repeat real tokens or passwords.
- Keep replies short enough to finish. Do not cut off code.

---

## Part 5: Common problems and fixes

| What you see | What to do |
|---|---|
| `.\.venv\Scripts\Activate.ps1` is blocked (execution policy) | Tell the assistant. Do not change system policy without asking. |
| `(.venv)` is not shown | Run `.\.venv\Scripts\Activate.ps1` from the repo root. |
| `uvicorn` not found | The venv is not active. Activate it and try again. |
| "Address already in use" on port 8000 | An old server is still running. Press Ctrl+C in its window, or close it. |
| "LF will be replaced by CRLF" | Harmless. Ignore it. |
| pytest shows 2 skipped | Expected on Windows (Linux-only bash tests). |
| `git push` is rejected | Run `git pull` first, then ask the assistant before pushing again. |
| Client says "auth failed" but you expected success | The `KAGENT_TOKEN` in the client window must match the server window. |
| `KAGENT_FAKE_DELAY` still set in a window | Close that window and open a new one. The delay is for manual tests only. |
| `Copy-Item` fails with "cannot find path" | The file in Downloads has a different name, such as `HANDOFF (1).md`. Paste the error. |
| Browser renames downloads | Rename to the exact name before copying. |
