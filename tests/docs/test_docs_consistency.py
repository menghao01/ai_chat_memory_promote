import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestDocsConsistency(unittest.TestCase):
    def test_root_readme_exists(self):
        self.assertTrue((ROOT / "README.md").exists(), "README.md should exist at repo root")

    def test_check_model_references_existing_scripts(self):
        check_model = ROOT / "scripts" / "check_model.py"
        content = check_model.read_text(encoding="utf-8")
        referenced = re.findall(r"scripts/([A-Za-z0-9_.-]+\.py)", content)
        missing = [name for name in referenced if not (ROOT / "scripts" / Path(name).name).exists()]
        self.assertEqual(
            missing,
            [],
            f"check_model.py references missing scripts: {missing}",
        )


if __name__ == "__main__":
    unittest.main()
