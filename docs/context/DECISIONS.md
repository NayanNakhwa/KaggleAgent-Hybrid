# Decisions log

Each entry: decision, reason, status. Do not reopen without a reason.

1. Laptop hosts the UI and server. Ollama runs on Kaggle and connects through a tunnel.
   Reason: the GPU is remote, and the UI should stay local. Status: active.

2. Fake LLM mode for development. KAGENT_LLM=fake for tests and local work. Default is ollama.
   Reason: development without Kaggle or GPU time. Status: active.

3. Token comes from the environment only. Real tokens go only in Kaggle Secrets.
   Reason: keeps secrets out of the repo and chat. Status: active.

4. Local dev token is local-dev-test, used only in fake mode on localhost.
   Reason: a placeholder that is safe to show. Status: active.

5. Auth is the first WebSocket message, compared with hmac.compare_digest. Failure closes with 1008.
   Reason: constant-time compare and a clear close code. Status: verified.

6. CLI uses synchronous websockets and Rich.
   Reason: simple blocking loop for a terminal; Rich for tables and panels. Status: verified.

7. client/protocol.py holds pure logic, with no I/O. Tests use a scripted fake socket.
   Reason: tests need no server and run fast. Status: verified.

8. Default model is the first model the server reports. --model overrides it.
   Reason: no user choice needed for normal use. Status: verified.

9. Chat answers are sent as chunks after synthesis, not as live tokens.
   Reason: simplest correct path for Phase B. Live tokens are planned for Phase D. Status: active.

10. Work goes on branches. master stays clean until a pull request merges.
    Reason: safe progress and easy rollback. Status: active. Current branch: phase-b-cli.

11. The assistant does not push, delete, or merge without the user's confirmation.
    Reason: destructive actions need the user's approval. Status: active.

12. Every claim of working code is marked untested until the user confirms it.
    Reason: the assistant cannot run the user's machine or Kaggle. Status: active.

13. The user does not want option menus. The assistant picks the best option, states it in one line, and proceeds.
    Reason: faster progress. Status: active.
