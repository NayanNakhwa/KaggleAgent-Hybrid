# Next session guide

Last updated: 2026-11-17 (end of session 5)

Parts:
- Part 1: End of a session (checks, commit, push, snapshot, raw paste, starter prompt)
- Part 2: Start of a session (upload, starter prompt, first checks, upload fixes)
- Part 3: The plan (Phase D from step D.4, then Phase E)
- Part 4: How the assistant must work
- Part 5: Common problems and fixes

Read HANDOFF.md first, then PROJECT_SCOPE.md.

---

## Part 1: End of a session

The final reply of every session includes these items, in this order:
1. Output of the previous session (short).
2. Updated docs for the next session (full files, nothing cut off).
3. Summary of this session.
4. Commit and push commands.
5. New snapshot command (after the push).
6. Raw text to paste into the next chat (Get-Content blocks).
7. Starter prompt for the next chat.

The next session sees only committed files. Anything not pushed does not reach it.

### Step 1.1: Checks (must pass before commit)

Window: current PowerShell, `(.venv)` showing, repo root.

```powershell
ruff check .
pytest -v
```

Expected: "All checks passed!" and "45 passed, 2 skipped". If not, stop and paste the output.

### Step 1.2: Check what will be committed

```powershell
git status
git --no-pager diff --stat
```

Expected: only the seven files in `docs/context/`, and `scripts/check_ollama.py` if it is still untracked. Any other file: stop and ask.

### Step 1.3: Commit and push the docs

Only after 1.1 and 1.2 look right. Window: same.

```powershell
git add docs/context
git commit -m "Update context docs for session 5 (Phase D tunnel and handshake)"
git push origin phase-b-cli
git --no-pager log --oneline -3
git status -sb
```

Expected: the push succeeds. `git status -sb` shows `## phase-b-cli...origin/phase-b-cli` and nothing below it.

### Step 1.4: Optional, commit the handshake script

Recommended, because this file passed step D.3. Run this block only if you agree. Window: same.

```powershell
git add scripts/check_ollama.py
git commit -m "Add Ollama handshake check script (Phase D.3)"
git push origin phase-b-cli
git --no-pager log --oneline -3
git status -sb
```

Expected: the same as Step 1.3.

### Step 1.5: Make the snapshot

Window: same. Run after the last push, so the zip includes the latest commit.

```powershell
git archive --format=zip --output "$HOME\Downloads\kagent-snapshot.zip" HEAD
python -c "import zipfile,os; z=zipfile.ZipFile(os.path.expanduser('~/Downloads/kagent-snapshot.zip')); n=z.namelist(); print(len(n),'files'); print([x for x in n if 'context' in x or 'check_ollama' in x])"
```

Expected: a file count (49 or more). The list shows the seven `docs/context/` files. It shows `check_ollama.py` only if Step 1.4 was run.

### Step 1.6: Raw text for the next chat

Run these three blocks in the repo root, one at a time, and keep the output for the next chat. Each block is pasted as a separate message if the output is long.

Block A:
```powershell
Get-Content -Encoding UTF8 docs\context\HANDOFF.md
Get-Content -Encoding UTF8 docs\context\NEXT_SESSION.md
```

Block B:
```powershell
Get-Content -Encoding UTF8 docs\context\PROJECT_SCOPE.md
Get-Content -Encoding UTF8 docs\context\RUNBOOK.md
```

Block C:
```powershell
Get-Content -Encoding UTF8 docs\context\ARCHITECTURE.md
Get-Content -Encoding UTF8 docs\context\DECISIONS.md
```

Upload `kagent-snapshot.zip` from Downloads in the new chat. `chathub-chat.md` is optional.

### Step 1.7: Starter prompt

The same text is in Part 2, Step 2.3.

---

## Part 2: Start of a session

### Step 2.1: Open a new chat

### Step 2.2: Upload

From Downloads:
1. `kagent-snapshot.zip` (required).
2. `chathub-chat.md` (optional). Skip it if the upload fails or the chat summarizes it. See Step 2.5.

### Step 2.3: First message (starter prompt)

Paste this as the first message, then paste the Block A, B and C output from Part 1, Step 1.6.

```text
Continue the KaggleAgent-Hybrid project. Attached: kagent-snapshot.zip (and chathub-chat.md, optional).

Rules:
1. Read docs/context/HANDOFF.md, NEXT_SESSION.md and PROJECT_SCOPE.md. My pasted Get-Content text is the source of truth. Tell me the line count of each file you read. If you can only give a summary, say so and ask me to paste the raw text again.
2. Start from NEXT_SESSION.md, Part 3, step D.4 (worker failure with the real model).
3. Explain each step in plain language. Give full files, not snippets. Batch the commands for each step into one PowerShell block, and say which window, whether (.venv) must show, and the folder.
4. Keep Kaggle cell output short: one line per step.
5. Do not say "verified" until I paste output. Do not push, delete, merge or amend without my confirmation.
6. Never ask for, store or repeat a real token, password or tunnel URL.
```

### Step 2.4: First checks

Window: NEW PowerShell. Folder: repo root. Run this one block:

```powershell
cd "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
git branch --show-current
git --no-pager log --oneline -3
git status -sb
git ls-files docs/context
(Get-Content docs\context\HANDOFF.md).Count
(Get-Content docs\context\NEXT_SESSION.md).Count
(Get-Content docs\context\PROJECT_SCOPE.md).Count
```

Expected:
- Branch: `phase-b-cli`.
- Newest commit: the session 5 docs commit (and the script commit if Step 1.4 was run).
- `git status -sb`: in sync with origin, nothing listed.
- `git ls-files docs/context`: seven files.

Paste the full output into the new chat.

### Step 2.5: If the upload or reading fails

The chat sometimes summarizes an uploaded file instead of giving the raw text. Try these in order:
1. Start a new chat. Upload only `kagent-snapshot.zip`. Leave out `chathub-chat.md`. The chat export is large and is the most likely file to be summarized. The committed docs and your pasted Get-Content text carry the state.
2. Paste the Block A, B and C output from Part 1, Step 1.6. Each block can be its own message.
3. Check the zip before upload. Step 1.5 must list the seven `docs/context/` files.
4. Do not rename files. Browsers may add " (1)" to a download. Rename it to the exact name.
5. If the assistant still summarizes, reply: "Summary is not allowed. Use the pasted raw text." If it still fails, paste the files again in smaller parts.

---

## Part 3: The plan

Phase status:

| Phase | Status |
|---|---|
| A | Complete (on `master`) |
| B | Complete |
| C | Complete (browser test 2026-11-14) |
| D | In progress. D.1 to D.3 done. D.4 next. |
| E | Not started |

### Phase D: Kaggle notebook, Ollama, tunnel, live tokens

Goal: the laptop agent uses the real model through the tunnel, with live tokens and cancellation.

Done so far:
- D.1 Notebook `kagent-ollama`: private, GPU T4 x2, Internet On.
- D.2 Notebook cells 1 to 3 pass (code in RUNBOOK.md). Cell 3 uses `--http-host-header localhost:11434`.
- D.3 Laptop handshake: `python scripts\check_ollama.py` prints OK through the tunnel.

#### D.4: Worker failure with the real model (next)

Goal: a simple request gets worker ok and judge accepted with `qwen2.5-coder:7b`.

Known facts:
- The planner returned role `coder`. Fake mode uses role `executor`.
- Both worker rounds failed. The judge rejected both.
- The server window showed only the connection, no error text.

Steps:
1. Notebook: run cell 4 from RUNBOOK.md (diagnostic). Paste its output.
2. Laptop window 1 (server): after one failed request, copy the last 30 lines of the server output. Paste them.
3. Assistant: read `core/workers.py`, `core/superagent.py` and `core/llm.py` from the snapshot zip. Report line counts. Find the role check and the reason for `failed`.
4. Assistant: give the fix as full files with tests. The fix comes from the code, not a guess.
5. User: run `ruff check .` and `pytest -v`, restart the server, and send the same request in the CLI. Paste the CLI output.

Done when: the CLI shows worker ok and judge accepted, and the answer comes from the model.

#### D.5: Live tokens, worker output text, cancellation

Design (decided):
- Chat uses `OllamaEngine.stream()` from `core/llm.py`, so tokens arrive live.
- Worker events include the worker's output text. The field name is set in this step and written to ARCHITECTURE.md.
- A client disconnect sets a cancel flag. The graph checks it between steps and stops.
- The Streamlit UI gets a cancel button.

Steps:
1. Assistant lists the files it will change, in one message.
2. Assistant gives each changed file in full. Files likely: `core/superagent.py`, `core/workers.py`, `core/graph_chat.py`, `core/server.py`, `client/protocol.py`, `client/cli.py`, `ui/app.py`, and tests. Long files are split across replies, announced first.
3. User: run `ruff check .` and `pytest -v`. Paste the output.
4. User: fake mode test with `KAGENT_FAKE_DELAY=2` and Ctrl+C. Paste the server log tail.

Done when: tokens show in the CLI as they arrive, Ctrl+C stops the turn at the next step with no traceback in the server log, and tests pass.

#### D.6: End-to-end test with the real model

Steps:
1. Restart the notebook (cell 3 gives a new tunnel URL). Run the handshake: `python scripts\check_ollama.py`.
2. Window 1: server with `KAGENT_LLM=ollama` and the new `OLLAMA_HOST`.
3. Window 2: CLI. Send one request.
4. Window 3: UI with `streamlit run ui/app.py` (`KAGENT_TOKEN=local-dev-test`). Send one request.
5. Paste the output of each window (short).

Done when: the CLI and the UI both answer through the tunnel, and tokens arrive live.

#### D.7: Close Phase D

1. Stop the server (Ctrl+C) and stop the Kaggle session.
2. Add a token check in front of Ollama. Decision: add it now, because the tunnel URL is open to anyone who has it. The Kaggle side runs a small proxy that checks a header, and the laptop sends the header from `KAGENT_TOKEN`. The real token goes into Kaggle Secrets. The user confirms the token is set before the assistant writes code.
3. Update the docs.

### Phase E: Finish

Goal: persist generated skills, README, docs, and a pull request into `master`.

Steps:
- E.1 Persist: a request writes the accepted skill to `workspace/mcp_skills/generated/` and commits it to a new branch `generated-skills`. Any push needs the user's confirmation.
- E.2 README.md at the repo root: setup, fake run, Kaggle run, tests. Full file.
- E.3 Docs: update all context files. Run `ruff check .` and `pytest -v`.
- E.4 Notebook: decide at this point whether to delete the old output that contains a tunnel URL. The notebook stays private.
- E.5 Pull request: after your confirmation, push `phase-b-cli`. You open the pull request from `phase-b-cli` into `master` on GitHub and merge it.

Done when: the pull request is merged and the docs say so.

---

## Part 4: How the assistant must work

- Start from HANDOFF.md. Name the newest commit and the next step.
- Read files in raw form from the paste. Give the line count of each file. If a tool gives a summary, say so and ask for the raw text.
- Explain each step in plain language: what it does and why.
- Batch the commands for one step into one PowerShell block. Say which window, whether `(.venv)` must show, and the folder.
- Put each PowerShell command on its own line. Do not join an environment assignment and a `python` command on one line.
- Use `git --no-pager` for log and show.
- Kaggle cells print one line per step. Ask for full logs only when a step fails.
- Give full files when a file changes. Do not cut off code. If a file is long, say so first and split it across replies.
- Check `git log` and `git status` output before writing commit instructions.
- Use `git add <paths>`, not `git add -A`, unless the status list is checked.
- Ask before any push, delete, merge or amend. The user's end-of-session request confirms only the docs commit and push.
- Never ask for, store, or repeat real tokens, passwords or tunnel URLs.
- Say "untested" until the user pastes output. Do not say "verified" before that.
- Use branches. Never commit to `master`.
- Keep each reply small enough to finish.

---

## Part 5: Common problems and fixes

| What you see | What to do |
|---|---|
| `.\.venv\Scripts\Activate.ps1` is blocked (execution policy) | Paste the error. Do not change system policy without asking. |
| `(.venv)` is not shown | Run `.\.venv\Scripts\Activate.ps1` from the repo root. |
| `uvicorn` or `streamlit` not found | The venv is not active. Activate it and try again. |
| `ParserError: Unexpected token 'python'` | Put `$env:...` and `python ...` on separate lines. |
| `can't open file 'scripts\check_ollama.py'` | The file is missing. Create it from the code in the chat, then run again. |
| "Address already in use" on 8000 or 8501 | An old server is running. Press Ctrl+C in its window. |
| Tunnel test gives `403 Forbidden` | Ollama rejects the Host header. Use cell 3 with `--http-host-header localhost:11434`. Check `tunnel.log` for `http-host-header`. |
| Notebook test gives `Name or service not known` right after cell 3 | Wait 45 seconds and run cell 3 again. It creates a new URL. |
| `Tunnel URL: None` | Cell 3 did not find the URL in 60 seconds. Look at `/kaggle/working/tunnel.log` (cell 4 prints only matching lines). |
| Chat shows workers "failed" | Step D.4. Do not change the code until D.4 begins. |
| Kaggle `ollama.log` has nbconvert or debugger warnings | These come from the notebook tool, not Ollama. Use cell 4 to filter. |
| Client says "auth failed" | `KAGENT_TOKEN` in the client window must match the server window. |
| Chat says it read a file but gives a summary | Step 2.5. Start a new chat and paste the raw text. |
| Git output stops at `(END)` | Press `q`. Use `git --no-pager` next time. |
| "LF will be replaced by CRLF" | Harmless. Ignore it. |
| pytest shows 2 skipped | Expected on Windows (Linux-only bash tests). |
| `git push` is rejected | Run `git pull` first, then ask the assistant before pushing again. |
| Kaggle notebook has no internet | Turn on Internet in Settings. Phone verification may be needed. |
| Tunnel stopped working | The notebook session ended. Run cell 3 again and update `OLLAMA_HOST`. |
