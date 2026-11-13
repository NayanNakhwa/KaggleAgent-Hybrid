# Next session guide

Last updated: 2026-11-13

This file explains how to end a session, how to start the next one, and how the assistant should guide you.

## Part 1: End of a session (make the snapshot)

Use the current PowerShell window. Make sure the prompt starts with `(.venv)`. Run from the repo root:
`D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid`

1. Check the tests and style. Stop if either fails.

```powershell
ruff check .
pytest -v
```

2. Save the changes to Git, push the branch, then check that the push worked.

```powershell
git status
git add docs/context
git commit -m "Update context docs: handoff, next-session guide"
git push origin phase-b-cli
git status
```

Notes:
- The code changes from this session are already committed in `8e19112`. This step only commits the docs in `docs/context`.
- If `git commit` says "nothing to commit", the files were already saved. That is fine.
- Push goes to `phase-b-cli`, the work branch. Never push to `master` directly.

3. Make the snapshot. It contains only committed files, so run it after the push.

```powershell
git archive --format=zip --output kagent-snapshot.zip HEAD
python -c "import zipfile; z=zipfile.ZipFile('kagent-snapshot.zip'); print(len(z.namelist()), 'files'); print([n for n in z.namelist() if 'context' in n])"
Move-Item -Force kagent-snapshot.zip "$HOME\Downloads\kagent-snapshot.zip"
```

The last line moves the zip to your Downloads folder. The `print` line should list `docs/context/HANDOFF.md` and `docs/context/NEXT_SESSION.md`. If it does not, stop and tell the assistant.

4. Save the chat. If your chat tool can export or copy the chat, save it as `chathub-chat.md` in Downloads. The next session needs it.

## Part 2: Start a new session

1. Open a new chat with the assistant, in any account.
2. Upload `kagent-snapshot.zip`. Also upload `chathub-chat.md` if you saved it.
3. Paste the starter prompt below.
4. Run the check below and paste its full output.

Starter prompt (copy everything between the lines):

---
I am continuing the KaggleAgent-Hybrid project. The attached kagent-snapshot.zip has the latest code and docs. Read docs/context/HANDOFF.md first, then docs/context/NEXT_SESSION.md. Follow the working rules in HANDOFF.md. I am learning to code: explain each step and give full files. Never ask for real tokens or passwords. If chathub-chat.md is attached, it is the chat from the last session. Start by saying what you read and what the current state is. Then give the first step.
---

First check (run in the current PowerShell window, prompt starts with `(.venv)`, repo root):

```powershell
git log --oneline -3
git status
git branch --show-current
```

## Part 3: How the assistant should guide you

- Start from the current state in HANDOFF.md. Name the commit and the next step.
- Explain each step in plain language: what it does and why.
- Give PowerShell in one block per set of commands. Say which window, whether `(.venv)` is needed, and the folder.
- Wait for your pasted output before the next step.
- Say "untested" for anything you have not confirmed.
- Give full files when a file changes. Do not give partial snippets.
- Ask before any push, delete, or merge.
- Never ask for or store real tokens or passwords.

## Part 4: Local test (two windows)

Window 1 runs the server. Keep it open.

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_LLM = "fake"
$env:KAGENT_TOKEN = "local-dev-test"
$env:KAGENT_FAKE_DELAY = "3"
uvicorn core.server:make_app --factory --host 127.0.0.1 --port 8000
```

Window 2 runs the client:

```powershell
.\.venv\Scripts\Activate.ps1
$env:KAGENT_TOKEN = "local-dev-test"
python -m client.cli
```

Type `write a short hello world script`, then press Ctrl+C within 3 seconds. Expected: window 2 prints "interrupted" and window 1 shows no traceback. To test the wrong token, set `$env:KAGENT_TOKEN = "wrong-token-test"` in window 2 and expect "auth failed" once.

Stop the server with Ctrl+C in window 1 when done. Set `KAGENT_FAKE_DELAY` to nothing (or close the window) for normal runs.

## Part 5: Known caveats

- Some file reads in earlier sessions returned summaries instead of the raw file text. The assistant must not rely on a summary. If it needs exact code, it asks you to paste `Get-Content <file>`.
- The snapshot only includes committed files. Changes that are not committed will not appear in the next session.
