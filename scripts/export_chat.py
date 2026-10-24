"""Archive registered project conversations without internal instructions or tool logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".project" / "chat_sources.local.json"
ARCHIVES = ROOT / "chat_history"
INDIA = timezone(timedelta(hours=5, minutes=30))


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            handle.close()
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def archive_lock():
    """Serialize manual, watcher, and checkpoint refreshes; OS releases on exit."""
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    with (ARCHIVES / ".export.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_messages(source: Path, thread_id: str) -> list[dict]:
    """Read only public message records; tolerate an unfinished final log write."""
    raw = source.read_bytes()
    lines = raw.splitlines(keepends=True)
    messages = []
    seen = set()
    verified_session = False
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            if number == len(lines) and not line.endswith(b"\n"):
                break
            raise ValueError(f"Invalid completed record at line {number} in {source.name}")
        payload = entry.get("payload", {})
        if entry.get("type") == "session_meta":
            if payload.get("id") != thread_id:
                raise ValueError("Session identity does not match the registered thread")
            verified_session = True
            continue
        if entry.get("type") != "response_item" or payload.get("type") != "message":
            continue
        role = payload.get("role")
        phase = payload.get("phase") or payload.get("channel")
        if role != "user" and not (role == "assistant" and phase in ("commentary", "final", "final_answer")):
            continue
        blocks = payload.get("content", [])
        text_blocks = [block["text"] for block in blocks if block.get("type") in ("input_text", "output_text") and isinstance(block.get("text"), str)]
        text = "\n".join(text_blocks)
        # These are UI/environment snapshots, not messages typed by the user.
        stripped = text.strip()
        if role == "user" and any(
            stripped.startswith(f"<{tag}>") and stripped.endswith(f"</{tag}>")
            for tag in ("environment_context", "external_codex_apps_open_page")
        ):
            continue
        non_text = [block.get("type", "unknown") for block in blocks if block.get("type") not in ("input_text", "output_text")]
        if not text and not non_text:
            continue
        identifier = payload.get("id") or f"line-{number}"
        if identifier in seen:
            continue
        seen.add(identifier)
        messages.append({
            "id": identifier, "timestamp": entry.get("timestamp"),
            "role": role, "phase": phase if role == "assistant" else None,
            "text": text, "non_text_content_types": non_text,
        })
    if not verified_session:
        raise ValueError("No matching session metadata found; archive was not updated")
    return messages


def local_time(value: str | None) -> str:
    if not value:
        return "timestamp unavailable"
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(INDIA).strftime("%Y-%m-%d %H:%M:%S IST")


def render_markdown(thread_id: str, messages: list[dict], attachments: list[dict]) -> str:
    lines = [
        "# SkinDiseaseAI chat history", "",
        f"Conversation: `{thread_id}`", "",
        "Exported from local session records. User and assistant text is preserved, including assistant progress updates and question/answer replies. Times below use Asia/Calcutta (IST).",
        "", "System/developer instructions, private reasoning, tool payloads, and environment-only UI events are excluded. This is a snapshot through the last listed message; refresh captures later replies. Non-text blocks are marked, not silently represented as saved images.", "",
    ]
    if attachments:
        lines.extend(["## Saved attachments", ""])
        for attachment in attachments:
            lines.append(f"- [{attachment['name']}](attachments/{attachment['name']})")
        lines.append("")
    for index, message in enumerate(messages, start=1):
        label = "User" if message["role"] == "user" else "Assistant"
        phase = f" ({message['phase']})" if message.get("phase") else ""
        lines.extend([f"## {index}. {label}{phase} — {local_time(message['timestamp'])}", "", message["text"], ""])
        if message["non_text_content_types"]:
            lines.extend(["Non-text blocks present in source: " + ", ".join(message["non_text_content_types"]) + ".", ""])
    return "\n".join(lines)


def register_current() -> None:
    thread_id = os.environ.get("CODEX_THREAD_ID")
    if not thread_id:
        raise ValueError("CODEX_THREAD_ID is unavailable. Run registration from the intended project conversation.")
    candidates = list((Path.home() / ".codex" / "sessions").rglob(f"*{thread_id}*.jsonl"))
    if len(candidates) != 1:
        raise ValueError(f"Expected one local record for the current thread; found {len(candidates)}")
    source = candidates[0]
    with source.open(encoding="utf-8") as handle:
        metadata = json.loads(next(handle))["payload"]
    if metadata.get("id") != thread_id or Path(metadata.get("cwd", "")).resolve() not in (ROOT, ROOT.parent):
        raise ValueError("The current thread is not associated with this project workspace")
    read_messages(source, thread_id)
    config = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {"schema_version": 1, "sessions": []}
    if not any(session["thread_id"] == thread_id for session in config["sessions"]):
        config["sessions"].append({"thread_id": thread_id, "source": str(source)})
    write_atomic(CONFIG, json.dumps(config, indent=2) + "\n")


def refresh_archives() -> int:
    with archive_lock():
        return _refresh_archives()


def _refresh_archives() -> int:
    if not CONFIG.exists():
        return 0
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    index = ["# SkinDiseaseAI conversation archive", "", "Private local exports. See [archive instructions](../docs/CHAT_HISTORY.md) for scope and refresh commands.", ""]
    for session in config["sessions"]:
        thread_id = session["thread_id"]
        if not thread_id or Path(thread_id).name != thread_id or any(char not in "0123456789abcdef-" for char in thread_id):
            raise ValueError("Invalid thread identifier")
        messages = read_messages(Path(session["source"]), thread_id)
        destination = ARCHIVES / thread_id
        attachments = []
        prompt = ROOT / "docs" / "MASTER_PROJECT_PROMPT.md"
        if prompt.exists() and any("# Files pasted by the user:" in message["text"] for message in messages if message["role"] == "user"):
            content = prompt.read_text(encoding="utf-8")
            name = "master-project-prompt.md"
            write_atomic(destination / "attachments" / name, content)
            attachments.append({"name": name, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()})
        structured = "".join(json.dumps(message, ensure_ascii=False) + "\n" for message in messages)
        markdown = render_markdown(thread_id, messages, attachments)
        manifest_path = destination / "manifest.json"
        old = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        digest = hashlib.sha256(structured.encode("utf-8")).hexdigest()
        markdown_digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
        if old.get("messages_sha256") != digest or old.get("markdown_sha256") != markdown_digest or old.get("attachments") != attachments or not all((destination / filename).exists() for filename in ("messages.jsonl", "conversation.md")):
            write_atomic(destination / "messages.jsonl", structured)
            write_atomic(destination / "conversation.md", markdown)
            manifest = {
                "schema_version": 1, "thread_id": thread_id,
                "exported_at_utc": datetime.now(timezone.utc).isoformat(),
                "message_count": len(messages), "roles": dict(Counter(message["role"] for message in messages)),
                "last_message_at": messages[-1]["timestamp"] if messages else None,
                "messages_sha256": digest, "markdown_sha256": markdown_digest,
                "attachments": attachments,
                "scope": "Available user/assistant text only; no system/developer instructions, private reasoning, or tool payloads.",
            }
            write_atomic(manifest_path, json.dumps(manifest, indent=2) + "\n")
        index.append(f"- [Conversation {thread_id}]({thread_id}/conversation.md) — {len(messages)} messages")
    write_atomic(ARCHIVES / "README.md", "\n".join(index) + "\n")
    return len(config["sessions"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register-current", action="store_true", help="Register only this project's current conversation")
    parser.add_argument("--watch", action="store_true", help="Refresh while this process is running; Ctrl+C to stop")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()
    if args.poll_seconds < 0.5:
        parser.error("Polling interval must be at least 0.5 seconds")
    try:
        if args.register_current:
            register_current()
        count = refresh_archives()
        if count == 0:
            raise ValueError("No registered conversations. Run with --register-current from the project conversation.")
        print(f"Saved {count} conversation archive(s) in {ARCHIVES}", flush=True)
        if args.watch:
            print(f"Watching for new messages every {args.poll_seconds:g} seconds; Ctrl+C to stop.", flush=True)
            while True:
                time.sleep(args.poll_seconds)
                try:
                    refresh_archives()
                except (OSError, ValueError, StopIteration) as error:
                    print(f"Archive refresh failed; previous exports retained: {error}", file=sys.stderr, flush=True)
    except KeyboardInterrupt:
        print("Chat archiving watcher stopped.")
    except (OSError, ValueError, StopIteration) as error:
        print(f"Chat export failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
