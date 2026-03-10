import importlib
import unittest


class TestRuntimeImports(unittest.TestCase):
    def test_chunking_import_without_external_skill_path(self):
        module = importlib.import_module("scripts.chunk_and_index")
        chunks = module.chunk_markdown_document(
            filepath="notes/a.md",
            content="## Title\ncontent line",
            filename="a.md",
            filepath_str="D:/ai_memory_chat/notes/a.md",
            semantic_refine_enabled=False,
        )
        self.assertGreaterEqual(len(chunks), 1)

    def test_incremental_update_import_without_external_skill_path(self):
        module = importlib.import_module("scripts.incremental_update")
        chunk_id = module.get_chunk_id(
            {
                "content": "example content",
                "metadata": {"filename": "a.md", "chunk_id": 1},
            }
        )
        self.assertIsInstance(chunk_id, str)
        self.assertTrue(chunk_id)


if __name__ == "__main__":
    unittest.main()
