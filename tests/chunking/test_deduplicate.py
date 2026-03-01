import unittest


class TestDeduplicateChunks(unittest.TestCase):
    def test_exact_duplicates_are_collapsed_and_sources_are_aggregated(self):
        from scripts.chunking.deduplicate import deduplicate_exact_chunks

        chunks = [
            {
                "content": "Hello   world",
                "metadata": {
                    "filename": "a.md",
                    "filepath": "/tmp/a.md",
                    "chunk_id": 0,
                    "chunk_type": "paragraph",
                },
            },
            {
                "content": "hello world",
                "metadata": {
                    "filename": "b.md",
                    "filepath": "/tmp/b.md",
                    "chunk_id": 7,
                    "chunk_type": "paragraph",
                },
            },
            {
                "content": "Another chunk",
                "metadata": {
                    "filename": "c.md",
                    "filepath": "/tmp/c.md",
                    "chunk_id": 2,
                    "chunk_type": "paragraph",
                },
            },
        ]

        deduped, stats = deduplicate_exact_chunks(chunks)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(stats["before"], 3)
        self.assertEqual(stats["after"], 2)
        self.assertEqual(stats["removed"], 1)

        merged = deduped[0]
        self.assertEqual(merged["metadata"]["source_count"], 2)
        self.assertEqual(len(merged["metadata"]["sources"]), 2)

    def test_different_content_is_kept(self):
        from scripts.chunking.deduplicate import deduplicate_exact_chunks

        chunks = [
            {
                "content": "alpha",
                "metadata": {
                    "filename": "a.md",
                    "filepath": "/tmp/a.md",
                    "chunk_id": 0,
                    "chunk_type": "paragraph",
                },
            },
            {
                "content": "beta",
                "metadata": {
                    "filename": "b.md",
                    "filepath": "/tmp/b.md",
                    "chunk_id": 0,
                    "chunk_type": "paragraph",
                },
            },
        ]

        deduped, stats = deduplicate_exact_chunks(chunks)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(stats["removed"], 0)


if __name__ == "__main__":
    unittest.main()
