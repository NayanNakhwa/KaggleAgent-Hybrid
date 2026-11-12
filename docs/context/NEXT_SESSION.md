# Next session guide

Read this first when starting a new chat.

## What to give the new chat
1. Download the latest project as a zip. In PowerShell, from the repo root, run the two commands in the section "Download the latest project" below.
2. Upload kagent-snapshot.zip to the new chat.
3. Paste this text as your first message:

   I am continuing the KaggleAgent-Hybrid project. The zip contains the latest code and docs.
   Read docs/context/HANDOFF.md first, then docs/context/NEXT_SESSION.md.
   Follow the working rules in HANDOFF.md. I am still learning to code, so explain each step
   and give full files. Do not ask for real tokens or passwords.
   Current state: branch phase-b-cli, commit 7e64ce8 (pushed).
   Next: manual Ctrl+C and auth-message check, then Phase C (Streamlit UI).

4. Paste the output of the last PowerShell step you ran.

## Download the latest project
Use the same PowerShell window. Its prompt shows the repo path. Make sure `(.venv)` is shown, though these commands do not need it. Run from the repo root:

    git pull
    git archive --format=zip --output="$env:USERPROFILE\Desktop\kagent-snapshot.zip" HEAD

`git pull` gets the newest commit from GitHub. `git archive` packs the current branch into a zip on your Desktop.

## Next steps for the user
1. Run the fake-mode server and the CLI as described in RUNBOOK.md.
2. Check: a wrong token shows "auth failed" once, with no doubled text.
3. Check: press Ctrl+C during a chat answer. The CLI prints "interrupted" and exits.
4. Paste the full output of each step into the next chat.
