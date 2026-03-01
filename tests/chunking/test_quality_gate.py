import unittest


class TestQualityGateAndIncrementalId(unittest.TestCase):
    def test_chunk_id_changes_when_late_content_changes(self):
        from scripts.incremental_update import get_chunk_id

        c1 = {
            "content": ("A" * 150) + "x",
            "metadata": {"filename": "a.md", "chunk_id": 1},
        }
        c2 = {
            "content": ("A" * 150) + "y",
            "metadata": {"filename": "a.md", "chunk_id": 1},
        }
        self.assertNotEqual(get_chunk_id(c1), get_chunk_id(c2))

    def test_quality_gate_reports_failed_rules(self):
        from scripts.chunking.quality_gate import evaluate

        stats = {
            "total_chunks": 10,
            "small_chunks": 4,
            "large_chunks": 0,
            "avg_chars": 200.0,
            "dup_ratio_proxy": 0.5,
        }
        gate = evaluate(
            stats,
            thresholds={
                "small_ratio_max": 0.2,
                "large_ratio_max": 0.2,
                "dup_ratio_proxy_max": 0.3,
                "min_total_chunks": 1,
            },
        )
        self.assertFalse(gate["passed"])
        self.assertIn("small_ratio_max", gate["failed_rules"])
        self.assertIn("dup_ratio_proxy_max", gate["failed_rules"])

    def test_chunking_module_can_run_without_vector_dependencies(self):
        from scripts.chunk_and_index import chunk_markdown_document

        chunks = chunk_markdown_document(
            filepath="notes/a.md",
            content="## Title\ncontent line",
            filename="a.md",
            filepath_str="D:/ai_memory_chat/notes/a.md",
        )
        self.assertGreaterEqual(len(chunks), 1)


if __name__ == "__main__":
    unittest.main()
