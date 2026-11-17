# Context docs

Start with HANDOFF.md, then NEXT_SESSION.md, then PROJECT_SCOPE.md.

| File | What it is | Read when |
|---|---|---|
| HANDOFF.md | Current state, verified checks, gaps, next steps, session log | Always, first |
| NEXT_SESSION.md | Part 1: end of a session. Part 2: start of a session. Part 3: the plan. Part 4: how the assistant works. Part 5: common problems. | Start and end of every session |
| PROJECT_SCOPE.md | Goal, architecture, settings, phases and plans | Planning or starting a phase |
| ARCHITECTURE.md | Components, WebSocket protocol, Kaggle path | Changing server, client, UI or graph code |
| DECISIONS.md | Numbered decisions with reasons and status | "Why was this done?" |
| RUNBOOK.md | Commands for tests, server, CLI, UI, Kaggle cells and git | Running things |

Rules:
- The source of truth is the committed snapshot plus the raw Get-Content text pasted into the new chat. A summary is not a source.
- Never write a real token, password or tunnel URL in these files.
