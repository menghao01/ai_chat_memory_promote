import unittest


from scripts.chunking.markdown_blocks import parse_blocks


class TestMarkdownBlocks(unittest.TestCase):
    def test_detect_heading_without_space(self):
        blocks = parse_blocks("##关于孤独\n内容")
        self.assertTrue(blocks)
        self.assertEqual("heading", blocks[0]["type"])
        self.assertEqual("关于孤独", blocks[0]["text"])

    def test_detect_heading_with_space(self):
        blocks = parse_blocks("## 关于关系\n一些内容")
        self.assertEqual("heading", blocks[0]["type"])
        self.assertEqual("关于关系", blocks[0]["text"])


if __name__ == "__main__":
    unittest.main()
