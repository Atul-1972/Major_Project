# Chat-history preservation report

Date: 2026-10-25 (Asia/Calcutta).

The user explicitly requested saving all project chat history. This is maintenance of development records, not the start of Phase 2.

## Delivered

- `scripts/export_chat.py` registers the current project thread and exports its available original user/assistant text to local Markdown and JSONL.
- `chat_history/README.md` indexes conversations; each conversation has a transcript, structured messages, and a manifest with counts and content hashes.
- The master prompt is saved alongside the transcript. Final answers, progress messages, user requirements, IDE context in requests, and asynchronous question/answer replies are preserved.
- `scripts/checkpoint.py` now refreshes registered chat archives after saving progress. Chat-source errors do not discard the saved development checkpoint.
- A two-second watcher was started for the current session. OS-backed locking serializes watcher/manual/checkpoint refreshes; files use atomic replacement. The process must be restarted after termination or reboot.
- Instructions are in `docs/CHAT_HISTORY.md`, with resume links in README, AGENTS, and the resume guide.
- Private exports and machine-specific source registration are excluded from Git.

## Verification

- Five standard-library unit tests passed: original text/Unicode preservation with internal-content filtering, incomplete-tail tolerance, malformed-completed-record rejection, session-identity validation, and UI-event filtering/question-reply preservation/deduplication.
- Initial export contained 21 messages: 6 user and 15 assistant, including all three earlier final answers. Subsequent refreshes include new messages and therefore increase the count.
- Verified presence of the initial project request, current archive request, and actual Colab reply.
- Verified message/Markdown SHA-256 hashes and the preserved master-prompt content/hash.
- Verified that chat exports/source registration are ignored by Git and checked the source diff for whitespace errors.

Test command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_export_chat.py -v
```

## Limits

The archive captures available public conversation text, not system/developer instructions, private reasoning, or internal tool payloads. Environment-only UI snapshots are omitted. Non-text blocks are marked; arbitrary images/attachments are not silently claimed as copied. Final replies are captured only once persisted by the local session writer. Missing original logs cannot be reconstructed, but prior exports remain on disk. Archives need a separate workspace backup because they are excluded from Git. New project threads must be registered explicitly.

The project remains at the Phase 1 completion boundary awaiting Phase 2 approval. No dataset, model, application, or mobile implementation changed.
