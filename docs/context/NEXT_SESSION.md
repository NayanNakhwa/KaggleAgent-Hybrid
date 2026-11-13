# Next session guide

Last updated: 2026-11-13 (end of session 3)

Parts:
- Part 1: End of a session (checks, commit, push, snapshot, chat save, final reply)
- Part 2: Start of a session (what to upload, starter prompt, first checks)
- Part 3: The plan for the next sessions (Phase C, D, E, batched)
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

The user runs the commands and pastes the output. The next session sees only committed files.

### Step 1.1: Checks (must pass before commit)

Window: current PowerShell. The prompt shows `(.venv)`. Folder: repo root.

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

Expected for a docs-only session: only the changed files under `docs/context/` appear. If a file appears that you did not change on purpose, stop and ask.

### Step 1.3: Commit and push

Only after 1.1 and 1.2 look right. Window: same.

```powershell
git add -A
git commit -m "Update handoff, next session guide and project scope"
git push origin phase-b-cli
git status -sb
```

Expected: the push succeeds, and `git status -sb` shows `## phase-b-cli...origin/phase-b-cli` with nothing listed below it.

Notes:
- Use `git add -A` only when the `git status` list is correct.
- Commit messages say what changed. Do not write "verified" unless the test was run and confirmed.
- Never push to `master`.

### Step 1.4: Make the snapshot

Window: same. Run AFTER the push, so the zip includes the latest commit.

```powershell
git archive --format=zip --output kagent-snapshot.zip HEAD
python -c "import zipfile; z=zipfile.ZipFile('kagent-snapshot.zip'); print(len(z.namelist()), 'files'); print([n for n in z.namelist() if 'context' in n])"
Move-Item -Force kagent-snapshot.zip "$HOME\Downloads\kagent-snapshot.zip"
```

Expected: a file count (about 45 or more). The list includes `docs/context/HANDOFF.md`, `docs/context/NEXT_SESSION.md`, `docs/context/PROJECT_SCOPE.md` and `docs/context/README.md`. If one is missing, the docs were not committed. Go back to Step 1.3.

### Step 1.5: Save the chat

Export or copy the chat and save it as `chathub-chat.md` in Downloads. If the tool cannot export, paste the most important parts into the new chat.

---

## Part 2: Start of a session

### Step 2.1: Open a new chat

New chat.

### Step 2.2: Upload

From Downloads:
1. `kagent-snapshot.zip` (required)
2. `chathub-chat.md` (optional)

### Step 2.3: Paste the starter prompt

Use the starter prompt in the final reply of the last session.

### Step 2.4: First checks

Window: NEW PowerShell. Folder: repo root. Run this in one block:

```powershell
cd "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
git branch --show-current
git --no-pager log --oneline -5
git status -sb
git ls-files docs/context
python -m pip show streamlit
```

Expected:
- Branch: `phase-b-cli`.
- Newest commit: the docs commit from the end of session 3. If the hash is different, paste the output and wait.
- `git status -sb`: `## phase-b-cli...origin/phase-b-cli` with nothing listed.
- `git ls-files docs/context`: four files.
- `pip show streamlit`: either a version or "WARNING: Package(s) not found". Both are fine. The Phase C steps handle it.

Paste the full output into the new chat.

---

## Part 3: The plan for the next sessions

The assistant follows this order. Each phase has batched steps. The user pastes the output of one whole block, and the assistant then moves on.

### Phase C: Streamlit web UI (next)

Goal: a browser page that does what the CLI does, in fake mode.

Design (decided, do not re-ask):
- Files: `ui/__init__.py`, `ui/app.py`, `tests/test_ui.py`. Run with `streamlit run ui/app.py`.
- Reuse `client/protocol.py` for decoding and turn-state logic.
- Synchronous WebSocket client, same style as the CLI.
- The token comes only from the `KAGENT_TOKEN` environment variable. The page never asks for it and never stores it.
- Page parts: model dropdown (from the server), skills list, chat box, plan table, worker and judge lines, answer, error box.
- Branch: stay on `phase-b-cli`.
- Add `streamlit` to `requirements.txt` only after `pip show` shows the installed version. Pin to that version.

Step C.1: The assistant gives the full files and the run block. The user runs the block in window 1 (current, `(.venv)`, repo root):

```powershell
python -m pip install streamlit
python -m pip show streamlit
ruff check .
pytest -v
```

Expected: streamlit version shown, "All checks passed!", and 37 + new tests passed, 2 skipped.

Step C.2: Browser test. Window 2 (server, leave open):

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_LLM = "fake"
$env:KAGENT_TOKEN = "local-dev-test"
uvicorn core.server:make_app --factory --host 127.0.0.1 --port 8000
```

Window 3 (UI, new window):

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_TOKEN = "local-dev-test"
streamlit run ui/app.py
```

Open the URL shown (usually http://localhost:8501). Send `write a short hello world script`. Paste a screenshot description or the text of the page, and the window 3 output.

Done when: the browser shows the plan, worker, judge and answer, and a wrong token shows an error box in the page.

### Phase D: Kaggle notebook, Ollama, tunnel, live tokens

Goal: the agent uses a real model on Kaggle, reached from the laptop.

Design (decided):
- Kaggle notebook installs Ollama, pulls one allowed model (`qwen2.5-coder:7b` by default), and starts Ollama on localhost.
- Tunnel: `cloudflared` quick tunnel. The notebook prints a public URL. The URL changes on every notebook run.
- Handshake: `scripts/check_ollama.py` checks the URL's `/api/tags` before the server starts.
- Token: the real `KAGENT_TOKEN` lives only in Kaggle Secrets and in the laptop's PowerShell window. Never in the repo, the docs, or the chat.
- Server change: live tokens (streaming call in `core/llm.py`, small change in `core/server.py`).
- Cancellation: a stop signal that the graph checks between steps. The client disconnect sets it.
- Worker output text added to worker events, so the CLI and UI can show it.

Steps (the assistant gives all files in one reply, the user runs them in order):

D.1 (user, browser): Confirm you have a Kaggle account. Kaggle may ask for phone verification before internet and GPU are allowed. In a new notebook, turn on Internet and set the accelerator to GPU. Add a Kaggle Secret named `KAGENT_TOKEN`. Type the real value yourself. Do not paste it in the chat.

D.2 (user, Kaggle notebook): Run the cells the assistant provides: install Ollama, start it, pull the model, install cloudflared, start the quick tunnel, print the public URL.

D.3 (user, laptop window 1): Run the handshake script with the URL:

```powershell
$env:OLLAMA_HOST = "<URL printed by the notebook>"
python scripts/check_ollama.py
```

D.4 (laptop, new window): Start the server with `KAGENT_LLM=ollama`. Run the CLI. Send one request. Check live tokens and the answer.

D.5: Unit tests for the streaming helper and for cancellation (with a fake Ollama client). Run `ruff check .` and `pytest -v`.

Done when: a real model answers a request from the laptop through the tunnel, tokens arrive live, and a disconnect stops the graph before the next step.

### Phase E: Finish

Goal: persist generated skills, README, docs, pull request.

Steps:

E.1 Persist: the assistant proposes one design at the start of Phase E. Default: a persist request writes the accepted skill to `workspace/mcp_skills/generated/` and commits it to a new branch named `generated-skills`. Any push needs the user's confirmation.

E.2 README.md at the repo root: setup, run in fake mode, run with Kaggle, test commands. Full file.

E.3 Docs: update HANDOFF, NEXT_SESSION, PROJECT_SCOPE, ARCHITECTURE, RUNBOOK if they changed. Run `ruff check .` and `pytest -v`.

E.4 Pull request: after the user confirms, push `phase-b-cli`. The user opens a pull request on GitHub from `phase-b-cli` into `master` and merges it.

Done when: the pull request is merged and the docs say so.

---

## Part 4: How the assistant must guide you

- Start from HANDOFF.md. Name the newest commit and the next step.
- Explain each step in plain language: what it does and why.
- Batch the commands for a phase into blocks, in order. Say which window, whether `(.venv)` must show, and the folder.
- Wait for pasted output before calling anything verified.
- Give full files when a file changes.
- Before writing commit instructions, check `git log` and `git status` output.
- Ask before any push, delete, merge, or amend.
- Never ask for, store, or repeat real tokens or passwords.
- Keep replies short enough to finish.

---

## Part 5: Common problems and fixes

| What you see | What to do |
|---|---|
| `.\.venv\Scripts\Activate.ps1` is blocked (execution policy) | Paste the error. Do not change system policy without asking. |
| `(.venv)` is not shown | Run `.\.venv\Scripts\Activate.ps1` from the repo root. |
| `uvicorn` or `streamlit` not found | The venv is not active. Activate it and try again. |
| "Address already in use" on port 8000 or 8501 | An old server is still running. Press Ctrl+C in its window, or close it. |
| Git output stops at `(END)` | Press `q`. Use `git --no-pager ...` next time. |
| "LF will be replaced by CRLF" | Harmless. Ignore it. |
| pytest shows 2 skipped | Expected on Windows (Linux-only bash tests). |
| `git push` is rejected | Run `git pull` first, then ask the assistant before pushing again. |
| Client says "auth failed" but you expected success | `KAGENT_TOKEN` in the client window must match the server window. |
| `KAGENT_FAKE_DELAY` still set in a window | Close that window and open a new one. |
| Kaggle notebook has no internet | Turn on Internet in the notebook settings. Phone verification may be needed. |
| Tunnel URL stopped working | Notebook sessions end. Start the notebook again and use the new URL. |
| Browser renames downloads | Rename to the exact name before copying. |
