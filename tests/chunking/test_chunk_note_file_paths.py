import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.chunk_and_index import chunk_note_file


def _sentinel_chunk(chunk_type: str):
    return [
        {
            "content": "sentinel",
            "metadata": {
                "filename": "x.md",
                "filepath": "D:/x.md",
                "chunk_id": 0,
                "chunk_type": chunk_type,
            },
        }
    ]


class TestChunkNoteFilePaths(unittest.TestCase):
    def test_chat_memo_filename_routes_to_chat_memo_splitter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chat-memo_1_20260101.md"
            path.write_text("plain text without memo markers", encoding="utf-8")

            expected = _sentinel_chunk("chat")
            with patch("scripts.chunk_and_index.chunk_chat_memo", return_value=expected) as chat_mock:
                chunks = chunk_note_file(str(path))

            self.assertEqual(chunks, expected)
            chat_mock.assert_called_once()

    def test_topic_notes_content_routes_to_topic_splitter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "topic.md"
            path.write_text("#topic\nsome text", encoding="utf-8")

            expected = _sentinel_chunk("topic")
            with patch("scripts.chunk_and_index.chunk_topic_notes", return_value=expected) as topic_mock:
                chunks = chunk_note_file(str(path))

            self.assertEqual(chunks, expected)
            topic_mock.assert_called_once()

    def test_markdown_default_route_is_used_when_no_special_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text("# Title\nnormal markdown content", encoding="utf-8")

            expected = _sentinel_chunk("markdown")
            with patch("scripts.chunk_and_index.chunk_markdown_document", return_value=expected) as md_mock:
                chunks = chunk_note_file(str(path))

            self.assertEqual(chunks, expected)
            md_mock.assert_called_once()

    def test_invalid_path_returns_empty_list(self):
        chunks = chunk_note_file("D:/ai_memory_chat/not-exists.md")
        self.assertEqual(chunks, [])


if __name__ == "__main__":
    unittest.main()
