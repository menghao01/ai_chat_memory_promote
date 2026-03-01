import unittest

from scripts.chunking.semantic_refine import apply_semantic_refine


class TestSemanticRefine(unittest.TestCase):
    def test_disabled_keeps_original_chunks(self):
        original = ["short chunk", "another chunk"]
        refined = apply_semantic_refine(original, enabled=False)
        self.assertEqual(original, refined)

    def test_only_oversized_chunks_are_refined(self):
        refined = apply_semantic_refine(
            ["x" * 200, "y" * 1700],
            enabled=True,
            only_if_over_max=True,
            max_chars=1400,
            target_chars=500,
            min_chars=120,
        )
        self.assertEqual("x" * 200, refined[0])
        self.assertGreaterEqual(len(refined), 2)
        self.assertTrue(all(len(c) <= 1400 for c in refined))

    def test_refine_splits_on_topic_shift(self):
        topic_a = "database index query latency " * 45
        topic_b = "painting color brush canvas style " * 45
        combined = f"{topic_a}\n\n{topic_b}"

        refined = apply_semantic_refine(
            [combined],
            enabled=True,
            only_if_over_max=True,
            max_chars=900,
            target_chars=500,
            min_chars=120,
            similarity_threshold=0.5,
        )

        self.assertGreaterEqual(len(refined), 2)
        self.assertIn("database", refined[0])
        self.assertIn("painting", refined[-1])


if __name__ == "__main__":
    unittest.main()
