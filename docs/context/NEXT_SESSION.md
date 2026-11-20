# NEXT SESSION - KaggleAgent-Hybrid

## Part 1 - Summary of session 7

Goal of session 7: find out why the real-model coder worker fails (step D.4).

What happened:

1. Kaggle cells 1 to 4 ran from scratch. All passed. Cell 4 showed 8 API calls and 0 errors. The old
   count of 19 from session 6 was stale.
2. The handshake check (scripts/check_ollama.py, through the tunnel) printed OK: Ollama is reachable and
   has qwen2.5-coder:7b.
3. Experiment A ran: a file was made by hand (workspace/scratch_target.py, two small functions), and the
   CLI was asked to add a one-line docstring to each function. The request was sent twice by mistake.
   - The planner chose role executor (session 6 saw coder).
   - Worker r1-0 reported ok, but the judge rejected it. Worker r2-0 failed. Both judge rounds rejected.
   - The file did not change. The answer mentioned a WSL error.
4. Read-only checks: the file is still 6 lines with no docstrings. bash resolves to the Windows app
   alias WindowsApps\bash.exe. A search for role names in the code returned nothing, which conflicts
   with the session 6 reading and must be re-checked.

What this means:

- The worker says ok with no change. The success check is missing or wrong. That is a new bug. It
  is not yet tied to the new-file hypothesis from session 6.
- The planner's role choice is not fixed. Results from one role do not carry over to another.
- The server does not log tool calls, so the actual tool behaviour is invisible.

No application code was changed in session 7. The fix is not written. Session 8 starts with read-only
checks and raw code reads, then decides the cause.

## Part 2 - Start of session 8

### 2.1 Context files

Read these three files in this order and report the line count of each:

- docs\context\HANDOFF.md
- docs\context\NEXT_SESSION.md
- docs\context\PROJECT_SCOPE.md

If a file comes back as a summary, say so and ask for the Get-Content paste. The pasted text is the
source of truth.

### 2.2 Window map

| Window | Name | Folder | (.venv) must show | Purpose |
| --- | --- | --- | --- | --- |
| W3 | checks | repo root | yes | git, scripts, ruff, pytest, read-only checks |
| W1 | server | repo root | yes | uvicorn core.server:make_app --factory |
| W2 | cli | repo root | yes | python -m client.cli |
| Browser | Kaggle notebook kagent-ollama | - | - | cells 1 to 4 |

Use three separate PowerShell windows. Do not reuse one window for server and CLI. Open each window
with Terminal > New Terminal.

### 2.3 First checks (W3)

Copy the whole block. (.venv) must show in the prompt afterwards. If it does not, stop.

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
git --no-pager log --oneline -3
git status --short
python -c "import sys; print(sys.version.split()[0])"
```

Expected: top commit 15c877f, two modified docs (M), and untracked scripts/debug_worker.py and
workspace/example.py. Plus workspace/scratch_target.py from session 7. None of the untracked files
are committed in this session.

## Part 3 - Step D.4: why does the coder worker fail?

Do the steps in order. Do not skip to the fix.

### 3.1 Kaggle back up (browser)

Run cells 1, 2, 3, 4 in order. Report one line per cell, for example:

- cell 1: zstd OK, ollama OK, cloudflared OK
- cell 2: Ollama running True, model pull OK
- cell 3: tunnel URL found, notebook test OK
- cell 4: api calls N, error lines 0

Cell 3 must keep --http-host-header localhost:11434. Never paste the tunnel URL in chat. Logs if a
cell misbehaves: /kaggle/working/ollama.log and /kaggle/working/tunnel.log.

### 3.2 Handshake check (W3)

Copy the block. You will be asked for the tunnel URL. Paste it only at the prompt, then delete it
from the terminal output before pasting anything back to chat.

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
$env:KAGENT_LLM = "ollama"
$env:OLLAMA_HOST = Read-Host "Paste tunnel URL"
python scripts\check_ollama.py
```

Expected: OK: Ollama is reachable and has qwen2.5-coder:7b. Anything else: stop and paste the output.

### 3.3 Read-only checks (W3, no changes)

This step changes nothing. It answers two questions: does WSL exist, and where are the role
and skill definitions.

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
wsl --list --verbose
Get-ChildItem core -Name
Get-ChildItem workspace\mcp_skills -Name
Select-String -Path "core\workers.py" -Pattern "ROLE_SKILLS"
Select-String -Path "core\*.py" -Pattern "executor"
```

Expected: the WSL command lists distros or says no installed distributions. The two folder listings
show the file names. The two Select-String lines show the line numbers where the names appear.
Paste all output. Empty output for a Select-String is a result, not a mistake to hide.

### 3.4 Raw code reads (W3)

Paste the full output of each command. Do not summarize.

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
Get-Content -Encoding UTF8 core\workers.py
```

Then, in the same window, one at a time:

```powershell
Get-Content -Encoding UTF8 core\superagent.py
```

```powershell
Get-Content -Encoding UTF8 workspace\mcp_skills\bash_terminal.py
```

If one of the files does not exist, the command reports an error. Paste the error. That tells us
the file name is wrong, which is useful.

### 3.5 Experiment B: is the step budget part of it? (optional, after 3.3 and 3.4)

Only run this if the code read shows the budget matters. Restart the server with a bigger budget.
Stop W1 with Ctrl+C first.

W1 (.venv must show):

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
$env:KAGENT_LLM = "ollama"
$env:OLLAMA_HOST = Read-Host "Paste tunnel URL"
$env:KAGENT_TOKEN = "local-dev-test"
$env:KAGENT_MAX_ROUNDS = "2"
$env:KAGENT_MAX_SUBTASKS = "4"
$env:KAGENT_MAX_WORKER_STEPS = "12"
uvicorn core.server:make_app --factory --host 127.0.0.1 --port 8000
```

W2, one request only:

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
$env:KAGENT_LLM = "ollama"
$env:OLLAMA_HOST = Read-Host "Paste tunnel URL"
$env:KAGENT_TOKEN = "local-dev-test"
python -m client.cli
```

Type this request once, then press Enter:

```
Add a one-line docstring to each function in scratch_target.py. Change nothing else.
```

Report: worker line (ok or failed), judge line (accepted or rejected), and the output of
Get-Content workspace\scratch_target.py in W3.

### 3.6 The fix (on hold)

The fix is written only after 3.3 and 3.4 output is pasted and the cause is named. Two parts are
already decided:

- Judge parsing (gap 14): strict. True, "true", 1 accepted; "false", "no", 0, missing rejected.
  Full file plus tests.
- Worker success check: a worker reports ok only when the file it was asked to change actually
  changed. Its exact shape depends on the code read. Full file plus tests.

The new-file creation idea from session 6 stays as a candidate, not a decision. It is tested only
after the worker success check exists.

### 3.7 After the fix

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
ruff check .
pytest -v
```

Two skips on Windows are expected. Then restart W1, send ONE request in W2, and confirm the worker
returns a final answer. Only then start D.5.

## Part 4 - Kaggle notebook reference

| Cell | Does | Expected line |
| --- | --- | --- |
| 1 | installs zstd, Ollama, cloudflared | zstd OK, ollama OK, cloudflared OK |
| 2 | starts Ollama, pulls qwen2.5-coder:7b | Ollama running True, Model pull OK |
| 3 | opens the tunnel, tests it | Tunnel URL found, Notebook test OK |
| 4 | reads the Ollama log | api calls: N, error lines: 0 |

Notebook kagent-ollama: private, GPU T4 x2, Internet On.
Cell 3 needs --http-host-header localhost:11434. Each cell 3 run gives a new URL. The URL never goes
into chat, a doc, a commit or a snapshot.
Cell text lives only in the notebook. RUNBOOK.md capture is Phase E.3. Paste the four cells when
writing it.

## Part 5 - Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| 403 from the tunnel | host header missing | cell 3 must pass --http-host-header localhost:11434 |
| Tunnel URL: None | cloudflared not started or crashed | re-run cell 3, check /kaggle/working/tunnel.log |
| Pager stuck at (END) | git opened a pager | press q; use git --no-pager |
| ModuleNotFoundError: No module named 'core' | run from scripts\ | $env:PYTHONPATH = (Get-Location).Path before python |
| worker reports ok, file unchanged | success check missing (gap 17) | this is the D.4 bug; see Part 3 |
| worker failed, no other symptom | budget exhausted or tool error | run 3.3 and 3.4 first |
| Select-String returns nothing | pattern or path wrong, or code moved | re-check with a simpler command (gap 16) |
| WSL error text in the answer | shell tool on Windows | see 3.3 wsl --list |
| Two you> requests in CLI | pasted twice | one request per run |
| check_ollama.py times out | tunnel dead or model not pulled | re-run cells 2 and 3 |
| 2 skipped tests | Windows-only skips | expected, not a failure |

## Part 6 - Don'ts

- Do not commit scripts/debug_worker.py, workspace/example.py or workspace/scratch_target.py.
- Do not run git add -A.
- Do not paste the tunnel URL, KAGENT_TOKEN, or any password.
- Do not say "verified" before the output is pasted.
- Do not push, merge, delete or amend without explicit confirmation.
- Do not fix D.4 before 3.3 and 3.4 output is pasted.
- Do not add bash_terminal to the coder role. It is the lazy fix (see HANDOFF section 7).

## Part 7 - Commit and snapshot at end of session 8

Run only after the user confirms. The commit needs the two docs files only.

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
.\.venv\Scripts\Activate.ps1
git status --short
git add docs/context/HANDOFF.md docs/context/NEXT_SESSION.md
git --no-pager diff --cached --stat
git commit -m "Update context docs for session 7 (D.4 experiment A)"
git push origin phase-b-cli
git --no-pager log --oneline -3
git status -sb
```

Check before pressing Enter: the --cached --stat line must list only the two docs files.

Snapshot (after the push succeeds). It is written outside the repo folder so it cannot be committed:

```powershell
Set-Location "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Hybrid"
$snap = "D:\Projects\Kaggle Projects\Projects\KaggleAgent-Snapshots"
New-Item -ItemType Directory -Force -Path $snap | Out-Null
git archive --format=zip -o "$snap\kagent-snapshot.zip" HEAD
Get-Item "$snap\kagent-snapshot.zip" | Select-Object Name, Length
```

## Part 8 - Assistant working rules

1. Start by reading the three context docs and reporting each line count.
2. Start work at Part 2, then Part 3, nowhere else.
3. Explain each step in plain language. Full files, never snippets.
4. One PowerShell block per step. Say which window, whether (.venv) must show, and the folder.
5. Kaggle output: one line per cell.
6. Nothing is "verified" until the user pastes output.
7. No push, delete, merge or amend without explicit confirmation.
8. Never ask for or repeat a token, password or tunnel URL.
9. One approach per decision, one line. No menus.
10. Work stays on phase-b-cli.
11. Replies end complete. Long material is split across replies.

## Known doc gaps (fix in session 8 docs pass)

- PROJECT_SCOPE.md still lists Phase D as "Not started".
- RUNBOOK.md has no Kaggle cell text (Phase E.3).
- README.md (docs/context) lists Part 1 to Part 5 of NEXT_SESSION; Part numbers have changed.
