# HANDOFF - KaggleAgent-Hybrid

Last updated: end of session 7.
Branch: phase-b-cli. Never commit to master.

## 1. Current state

- Repo: https://github.com/NayanNakhwa/KaggleAgent-Hybrid
- Local path: D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid
- Branch: phase-b-cli
- Origin head: 15c877f "Add Ollama handshake check script (Phase D.3)".
- Session 7 changed no application code. It only changed the two context docs.
- Uncommitted in the working copy: docs/context/HANDOFF.md and docs/context/NEXT_SESSION.md
  (the session 7 versions replace them once committed).
- Untracked files that must never be committed:
  - scripts/debug_worker.py (scratch diagnostic)
  - workspace/example.py (old file, deleted in concept, still on disk)
  - workspace/scratch_target.py (test file for Experiment A)

Phase status:

| Phase | State |
| --- | --- |
| A | done |
| B | done |
| C | done |
| D.1 config + settings | done |
| D.2 Kaggle notebook + tunnel | done |
| D.3 handshake check script | done |
| D.4 worker run with the real model | in progress, session 8 continues here |
| D.5 live tokens, worker output text, cancellation | not started |
| D.6 end-to-end CLI + UI with the real model | not started |
| D.7 token check in front of Ollama | not started |
| E persistence, README, docs, PR | not started |

What works today:

- Server, CLI and WebSocket plumbing run end to end with the fake model.
- The worker loop works with stub tools (session 6 debug run: RESULT ok=True tool_steps=2 replies=3).
- Real Ollama is reachable through the Kaggle tunnel (handshake check passed in session 7).
- The real model produces a plan with subtasks and the run does not crash.

What does not work: with the real model and the real skill registry, the worker does not
produce a correct result. In session 7 the worker reported "ok" but the file was not
changed. See section 3.

## 2. Verified by the user (pasted output only)

Nothing outside this list is verified. Everything else is inference from code or notes.

Session 6 (carried forward):

1. Kaggle cell 4 at that time: api calls 19, error lines 0, all displayed calls status 200.
2. Server window during the real run: WebSocket /ws accepted, connection open. No tool logs, no traceback.
3. CLI real run in session 6: plan with 1 coder subtask, worker r1-0 failed, judge rejected,
   worker r2-0 failed, judge rejected, answer written from model knowledge.
4. check_ollama.py printed OK in session 6.
5. Stub-registry debug run: RESULT ok=True tool_steps=2 replies=3. Stub tools always
   succeed, so this proves the loop, not the tools.
6. Line counts from the session 6 snapshot: HANDOFF 115, NEXT_SESSION 308,
   PROJECT_SCOPE 148, RUNBOOK 55, core/workers.py 124, core/superagent.py 232,
   core/llm.py 56, core/mcp_loader.py 170, core/config.py 52, core/server.py 167.

Session 7 (pasted output):

7. Step 2.2 in W3: .venv active, Python 3.11.13, top commit 15c877f, matching origin.
   git status showed M on the two docs and ?? on scripts/debug_worker.py and workspace/example.py.
8. Line counts of the context docs at start of session 7 (Get-Content .Count):
   HANDOFF.md 226, NEXT_SESSION.md 249, PROJECT_SCOPE.md 148.
9. Kaggle notebook kagent-ollama, run in session 7:
   - cell 1: zstd OK, ollama OK, cloudflared OK
   - cell 2: Ollama running True, model pull OK
   - cell 3: tunnel URL found, notebook test OK
   - cell 4: api calls 8, error lines 0 (GET /api/tags rows, one POST /api/pull at 41.73s)
10. Step 3.2 handshake in a new W1-style window: "OK: Ollama is reachable and has qwen2.5-coder:7b."
11. Experiment A (step 3.3), request sent twice on one connection (user error, see gap 19):
    - Plan: 1 subtask, role executor (session 6 showed coder).
    - worker r1-0 (executor): ok
    - judge r1-0: rejected
    - worker r2-0 (executor): failed
    - judge r2-0: rejected
    - CLI answer mentioned a Windows Subsystem for Linux (WSL) optional component error.
12. Server window during Experiment A: WebSocket /ws accepted, connection open, no tool logs.
13. scratch_target.py after Experiment A (Get-Content): unchanged, 6 lines, no docstrings.
14. Step 3.3b read-only checks:
    - line count: 6
    - Select-String for triple quotes in scratch_target.py: no output (no docstrings)
    - bash resolves to C:\Users\nayan\AppData\Local\Microsoft\WindowsApps\bash.exe
    - Select-String for "executor|coder|ROLE_SKILLS|bash_terminal" over core and
      workspace\mcp_skills: NO OUTPUT. This contradicts the session 6 reading and is
      not explained yet (gap 16).

## 3. Findings

### 3.1 Session 6 chain (still valid)

1. Role gate is not the cause. coder is present in ROLE_SKILLS (session 6 reading).
2. run_worker has one ok=False exit: "Step budget exhausted before a final answer."
3. Invalid JSON consumes a step, and the model is told nothing about why.
4. _judge returns rejected immediately when ok=False, without calling the model.
5. file_editor takes path + patch and edits existing files only. On a missing file it returns
   "ERROR: <path> does not exist. Create it with bash_terminal first."
6. The coder role has file_editor, file_explorer, linter, python_repl. No bash_terminal.
7. The coder prompt asks for unified diff patches. Creating a file needs @@ -0,0 +1,N @@,
   which the real tool refuses.

### 3.2 What session 7 changed

- The planner chose role executor, not coder. The role the planner picks changes between runs.
- Experiment A did not give a clean answer. My rule table in the session 7 plan had no row for
  "worker ok, file unchanged" other than "different bug, paste everything". That is the result we got.
  So the new-file hypothesis is neither confirmed nor rejected.
- The worker reported ok without changing the file. The worker does not check that its own edit
  happened, or the check is not visible to us. Server logs show no tool calls, so we cannot see what
  the worker did (gap 7).
- The answer text points at WSL. Hypothesis H1 (unconfirmed): the executor runs a shell command
  through bash, bash resolves to a Windows app alias (WindowsApps\bash.exe), the command fails
  on Windows, and the worker still reports ok.

### 3.3 Hypotheses, ranked

- H1: executor uses a shell tool that fails on Windows and the worker does not notice. Check:
  find the executor role in the code and see which tool it uses. Check bash with wsl --list.
- H2: the worker edits nothing and the model simply says it did. Check: tool-call trace (needs
  logging, gap 7).
- H3: the planner's role choice differs per run, so the session 6 coder result does not apply to
  executor. Check: run the same request again and compare roles.

### 3.4 Separate bug

_judge does bool(verdict.get("ok")). The string "false" becomes True. Gap 14. Safe to fix
independently of D.4 because it is a one-line parse change with a test.

## 4. Untested or not built

- The D.4 fix. Not written. Blocked until the cause is confirmed.
- Creating a file through file_editor. Unverified whether the loader accepts a schema change.
- client/* and ui/app.py against the real model. Only the CLI ran for real.
- Cancellation of a running worker (D.5).
- Live token streaming end to end (D.5).
- Anything behind a token in front of Ollama (D.7).
- Persisting generated skills to the generated-skills branch (Phase E).
- scripts/debug_worker.py is local only, untracked, not part of the app.
- PROJECT_SCOPE.md still lists Phase D as "Not started". Stale. Fix in the session 8 docs pass.

## 5. Known gaps

1. No confirmed cause for the D.4 worker failure.
2. No test covers "worker runs out of budget" or "worker says ok with no change".
3. _judge has no unit test, which is why gap 14 survived.
4. Invalid JSON gives the model no corrective message; it just loses a step.
5. The coder prompt and the coder's skills disagree (prompt says bash_terminal, role has none).
6. file_editor cannot create files, so writing a new file is unreachable for roles without bash_terminal.
7. The server logs no tool calls or tool errors, so failures are invisible server-side.
8. The UI has not been run against the real model.
9. No cancellation path (D.5).
10. No token check in front of Ollama (D.7).
11. Generated skills are not persisted anywhere yet (Phase E).
12. RUNBOOK.md has no Kaggle cell text. Cells 1-4 exist only in the notebook. Phase E.3 item.
13. core/paths.py and core/config.py have not been read raw this session.
14. Judge boolean bug: bool(verdict.get("ok")) treats "false" as True.
15. scripts/debug_worker.py is untracked scratch that looks like app code. Never commit it.
16. Select-String for ROLE_SKILLS / executor / coder / bash_terminal returned no lines in step 3.3b.
    Unexplained. Re-check with a simpler command before trusting any code location.
17. A worker reports ok even when the file did not change. The success check is missing or wrong.
18. The CLI does not show why the judge rejected a round.
19. Two requests were sent on one connection in Experiment A. Not a code bug, but it doubles
    any file edit. One request per run from now on.

## 6. Next steps (session 8, in order)

A. Start-of-session checks (NEXT_SESSION.md Part 2).
B. Kaggle cells 1-4 again, one line per cell. New tunnel URL every run.
C. Handshake check in W3 (step 3.2 again).
D. Read-only checks: wsl --list, Get-ChildItem of core and workspace\mcp_skills, and a retry of the
   Select-String from gap 16. Paste all output.
E. Raw code reads: core\workers.py, the role map (ROLE_SKILLS and wherever it lives), and the executor
   skill files. Paste with Get-Content. The chat cannot read the repo directly.
F. Decide the cause from the raw code and the step D output. Then write the fix as full files.
G. Judge bug fix (gap 14) with tests. Strict boolean parsing: True, "true", 1 accepted;
   "false", "no", 0, missing rejected.
H. ruff check . then pytest -v. Two Windows skips are expected.
I. Restart the server (W1), send ONE request in W2, confirm the worker returns a final answer and
   the file changes if the request asks for a change.
J. Only after I passes: D.5.

## 7. Decisions carried forward

- Hybrid by design. Planning and judging use the local model path; the heavy model sits on Kaggle
  behind a tunnel. Nothing needs a paid API key.
- Ollama on Kaggle, reached through cloudflared. Cell 3 must pass --http-host-header localhost:11434
  or requests return 403. Every cell 3 run gives a new URL.
- Model allow-list stays narrow: qwen2.5-coder:7b (default), deepseek-coder:6.7b, llama3.1:8b.
- Secrets never travel. No token, password or tunnel URL is asked for, stored, echoed or written into
  docs, commits or snapshots. The tunnel URL is typed by the user with Read-Host.
- Tool contract: file_editor(path, patch) for edits; tools return strings; errors start with ERROR:.
  The model sees them.
- Role map is closed: a role gets exactly the skills in ROLE_SKILLS. The coder does not get
  bash_terminal. Adding it would be the lazy fix and it widens what the model can do on the host.
- Fix the tool, not the prompt, when the prompt and the tool disagree.
- Experiments before fixes. Results decide the fix.
- One request per CLI run.
- Docs are the source of truth. Full files only, never snippets.
- git add <paths>, never git add -A. Commit before snapshot, because the snapshot comes from HEAD.
- Snapshots go outside the repo folder, so they cannot be committed by accident.

## 8. Session log

Session 1-2 (Phase A/B): repo, venv, package layout, config from env, fake model, server skeleton.

Session 3 (Phase B): CLI and WebSocket client against the fake model. Plan, subtask, worker,
judge, answer shape fixed here.

Session 4 (Phase C): MCP-style skill loader. Skills discovered from workspace/mcp_skills/. Role
map introduced.

Session 5 (Phase D.1-D.2): real model wiring (core/llm.py), Ollama on Kaggle with T4 x2 GPU,
tunnel, KAGENT_LLM=ollama. First real plan produced.

Session 6 (Phase D.3 and partial D.4): scripts/check_ollama.py committed (15c877f). Kaggle cell 4
clean. Real run reached the worker and failed with budget exhausted. Read the code and found the
chain in section 3.1. No code changed.

Session 7 (D.4 continued): Kaggle cells 1-4 re-run from scratch. Handshake passed. Experiment A run:
the worker reported ok, the judge rejected, the file did not change, the answer cited WSL.
Read-only checks done (3.3b). Section 3.2 explains why the experiment did not settle the question.
No app code changed. Docs rewritten for session 8.

## 9. Working rules

1. Session starts by reading HANDOFF.md, NEXT_SESSION.md and PROJECT_SCOPE.md and reporting the line
   count of each. If a file arrives as a summary rather than raw text, say so and ask for the paste.
   The user's Get-Content output wins over anything recalled.
2. Start at NEXT_SESSION.md Part 3 (after the Part 2 checks) and nowhere else.
3. Explain each step in plain language. Full files, never snippets.
4. One PowerShell block per step. State the window, whether (.venv) must show, and the folder.
5. Kaggle output is reported as one line per cell.
6. Nothing is "verified" until the user pastes output. Say "untested" until then.
7. No push, delete, merge or amend without explicit confirmation.
8. Never ask for or repeat a token, password or tunnel URL.
9. One approach per decision, stated in one line. No menus.
10. Work stays on phase-b-cli.
11. Chat replies must end complete. Long outputs are split across replies, never cut mid-sentence.
