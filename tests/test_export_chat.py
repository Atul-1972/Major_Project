"""Verify archive fidelity, privacy boundaries, and interrupted source writes."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.export_chat import read_messages, render_markdown


class ChatExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = Path(self.temporary.name) / "session.jsonl"

    def write_records(self, records, tail=b""):
        content = b"".join((json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8") for record in records)
        self.source.write_bytes(content + tail)

    def metadata(self):
        return {"type": "session_meta", "payload": {"id": "test-thread"}}

    def message(self, identifier, role, text, phase=None):
        return {
            "timestamp": "2026-10-25T01:00:00Z", "type": "response_item",
            "payload": {"type": "message", "id": identifier, "role": role, "phase": phase,
                        "content": [{"type": "input_text" if role == "user" else "output_text", "text": text}]},
        }

    def test_preserves_unicode_and_messages_but_excludes_internal_content(self):
        self.write_records([
            self.metadata(), self.message("u", "user", "Save café and CNN–Transformer exactly."),
            self.message("d", "developer", "PRIVATE INSTRUCTION"),
            self.message("s", "system", "PRIVATE SYSTEM"),
            self.message("a", "assistant", "PRIVATE REASONING", "analysis"),
            {"type": "response_item", "payload": {"type": "reasoning", "text": "PRIVATE REASONING"}},
            {"type": "response_item", "payload": {"type": "function_call_output", "output": "PRIVATE TOOL"}},
            self.message("p", "assistant", "Saving now.", "commentary"),
            self.message("f", "assistant", "Saved.", "final_answer"),
        ])
        messages = read_messages(self.source, "test-thread")
        self.assertEqual([message["id"] for message in messages], ["u", "p", "f"])
        self.assertEqual(messages[0]["text"], "Save café and CNN–Transformer exactly.")
        markdown = render_markdown("test-thread", messages, [])
        self.assertIn("2026-10-25 06:30:00 IST", markdown)
        self.assertNotIn("PRIVATE", markdown)

    def test_unfinished_tail_waits_for_next_refresh(self):
        records = [self.metadata(), self.message("u", "user", "Hello")]
        self.write_records(records, tail=b'{"type":"response_item"')
        self.assertEqual(len(read_messages(self.source, "test-thread")), 1)

    def test_malformed_completed_line_fails(self):
        self.write_records([self.metadata()], tail=b"not json\n")
        with self.assertRaisesRegex(ValueError, "Invalid completed record"):
            read_messages(self.source, "test-thread")

    def test_wrong_thread_is_rejected(self):
        self.write_records([self.metadata()])
        with self.assertRaisesRegex(ValueError, "identity"):
            read_messages(self.source, "another-thread")

    def test_ui_only_events_excluded_question_reply_preserved_and_ids_deduplicated(self):
        reply = '<send_user_message_question_reply>[{"question":"GPU?","answer":"Colab"}]</send_user_message_question_reply>'
        self.write_records([
            self.metadata(), self.message("e", "user", "<environment_context>metadata</environment_context>"),
            self.message("page", "user", '<external_codex_apps_open_page>{"page_id":null}</external_codex_apps_open_page>'),
            self.message("q", "user", reply), self.message("q", "user", reply),
        ])
        messages = read_messages(self.source, "test-thread")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["text"], reply)


if __name__ == "__main__":
    unittest.main()
