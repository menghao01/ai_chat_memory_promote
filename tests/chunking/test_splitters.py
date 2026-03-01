import unittest

from scripts.chunking.markdown_blocks import parse_blocks
from scripts.chunking.splitters import normalize_size, structural_split


class TestSplitters(unittest.TestCase):
    def test_structural_split_respects_heading_boundaries(self):
        text = "## A\n第一段。\n\n## B\n第二段。"
        blocks = parse_blocks(text)
        chunks = structural_split(blocks)
        self.assertEqual(2, len(chunks))
        self.assertIn("## A", chunks[0])
        self.assertIn("## B", chunks[1])

    def test_size_window_enforced(self):
        chunks = normalize_size(
            ["x" * 20, "y" * 2500],
            min_chars=120,
            target_chars=500,
            max_chars=1400,
        )
        self.assertTrue(all(80 <= len(c) <= 1500 for c in chunks))
        self.assertTrue(len(chunks) >= 2)


if __name__ == "__main__":
    unittest.main()
