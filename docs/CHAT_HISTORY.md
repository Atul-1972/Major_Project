# Save the project's chat history

The user requested saving all project conversation history on 2026-10-25. Development checkpoints remain separate from the conversation transcript.

## Saved files

Private local exports are under `chat_history/` in the repository:

```text
chat_history/
  README.md                       Index of registered project conversations
  <thread-id>/
    conversation.md               Readable transcript with IST timestamps
    messages.jsonl                Structured user/assistant message records
    manifest.json                 Counts, export time, and content hashes
    attachments/
      master-project-prompt.md    Preserved master prompt, when referenced
```

The archive includes the available original user/assistant text, final answers, assistant progress updates, IDE context carried with requests, and question/answer replies. System/developer instructions, private reasoning, internal tool payloads, and environment-only UI snapshots are excluded. Non-text blocks are marked; image bytes and arbitrary attachments are not automatically copied. The known master prompt is copied from its preserved project document.

The export uses local session records, not a reconstruction from memory. `manifest.json` identifies the last included message and source text hashes. A current final reply can only be exported after it is written to the local session record.

## Refresh

Run from the repository:

```powershell
.\.venv\Scripts\python.exe scripts\export_chat.py
```

The source registration is stored in `.project/chat_sources.local.json`. For a new project conversation, the agent should register it from that conversation's environment:

```powershell
.\.venv\Scripts\python.exe scripts\export_chat.py --register-current
```

Registration requires the current thread ID and checks its original workspace. It never scans the contents of unrelated conversations. If the original session record is missing or malformed, existing exports are retained and an error is reported. A partially written final source record is left for the next refresh.

Every normal `scripts/checkpoint.py` invocation also refreshes registered archives. A chat-source failure does not prevent saving the development checkpoint.

## Capture new messages as they arrive

```powershell
.\.venv\Scripts\python.exe scripts\export_chat.py --watch
```

This refreshes every two seconds while the process runs. Ctrl+C stops a foreground watcher. A watcher is started for the current working session; it is not a Windows startup service and does not automatically return after shutdown or app/process termination. Restart it or run a manual refresh after reopening the project. Do not launch duplicate watchers against the same archive.

The archive and local registration are ignored by Git, so a Git clone alone does not restore them. Back up `chat_history/` with the workspace. Refreshing writes generated files; keep personal edits in a separate file. Saved messages cannot resume an agent automatically when credits return.
