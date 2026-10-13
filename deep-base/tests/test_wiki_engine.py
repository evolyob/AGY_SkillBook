#!/usr/bin/env python3
"""Regression test suite for llm-wiki engine scripts."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"


class TestWikiEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="wiki_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_assemble_init(self):
        cmd = [sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"assemble.py failed: {res.stderr}")
        self.assertTrue((self.test_dir / ".wiki-schema.md").exists())
        self.assertTrue((self.test_dir / "index.md").exists())
        self.assertTrue((self.test_dir / "raw" / "articles").is_dir())
        self.assertTrue((self.test_dir / "wiki" / "entities").is_dir())

    def test_02_cache_check_and_update(self):
        # Init first
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)

        sample_file = self.test_dir / "raw" / "articles" / "test.txt"
        sample_file.write_text("Unique content 12345", encoding="utf-8")

        # First check -> MISS (return code 2)
        res_check1 = subprocess.run([sys.executable, str(SCRIPTS_DIR / "cache.py"), "check", str(sample_file)], capture_output=True, text=True)
        self.assertEqual(res_check1.returncode, 2)
        self.assertIn("MISS", res_check1.stdout)

        # Update cache
        res_up = subprocess.run([sys.executable, str(SCRIPTS_DIR / "cache.py"), "update", str(sample_file), "wiki/sources/test_summary.md"], capture_output=True, text=True)
        self.assertEqual(res_up.returncode, 0)

        # Second check -> HIT (return code 0)
        res_check2 = subprocess.run([sys.executable, str(SCRIPTS_DIR / "cache.py"), "check", str(sample_file)], capture_output=True, text=True)
        self.assertEqual(res_check2.returncode, 0)
        self.assertIn("HIT", res_check2.stdout)

    def test_03_lint_links_detection(self):
        # Init first
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)

        # Create a valid entity and a broken reference
        entity_file = self.test_dir / "wiki" / "entities" / "known_tool.md"
        entity_file.write_text("# Known Tool\nReferencing [[wiki/entities/missing_tool]]", encoding="utf-8")

        res_lint = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--strict"], capture_output=True, text=True)
        # Should fail with exit code 2 due to broken link
        self.assertEqual(res_lint.returncode, 2)
        self.assertIn("Broken Links Found   : 1", res_lint.stdout)


if __name__ == "__main__":
    unittest.main()
