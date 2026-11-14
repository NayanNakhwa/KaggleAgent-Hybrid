# Next session guide

Last updated: 2026-11-14 (end of session 4)

Parts:
- Part 1: End of a session (checks, commit, push, snapshot, chat save, raw paste list, final reply)
- Part 2: Start of a session (what to upload, starter prompt, first checks, upload fixes)
- Part 3: The plan for the next sessions (Phase C done, Phase D, Phase E, batched)
- Part 4: How the assistant must guide you
- Part 5: Common problems and fixes

Read HANDOFF.md (state) and PROJECT_SCOPE.md (scope and plan) too.

---

## Part 1: End of a session

The final reply of every session must include these items, in this order:
1. Output of the previous session (what the user pasted, short).
2. Updated docs for the next session (full files).
3. Summary of this session.
4. Commit and push commands (checks first, then commit and push).
5. New snapshot commands (run after the push).
6. Raw text the user must paste into the next chat (Get-Content block).
7. Starter prompt for the next chat (same text as in Part 2, Step 2.3).

The user runs the commands and pastes the output. The next session sees only committed files.

### Step 1.1: Checks (must pass before commit)

Window: current PowerShell. The prompt shows `(.venv)`. Folder: repo root.

```powershell
ruff check .
pytest -v
