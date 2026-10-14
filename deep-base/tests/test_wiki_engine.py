#!/usr/bin/env python3
"""Regression test suite for deep-base engine scripts."""

import json
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
        self.assertTrue((self.test_dir / "wiki" / "comparisons").is_dir())
        self.assertTrue((self.test_dir / "data" / "glossary.json").exists())

    def test_02_cache_check_and_update(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        sample_file = self.test_dir / "raw" / "articles" / "test.txt"
        sample_file.write_text("Unique content 12345", encoding="utf-8")

        res_check1 = subprocess.run([sys.executable, str(SCRIPTS_DIR / "cache.py"), "check", str(sample_file)], capture_output=True, text=True)
        self.assertEqual(res_check1.returncode, 2)
        self.assertIn("MISS", res_check1.stdout)

        res_up = subprocess.run([sys.executable, str(SCRIPTS_DIR / "cache.py"), "update", str(sample_file), "wiki/sources/test_summary.md"], capture_output=True, text=True)
        self.assertEqual(res_up.returncode, 0)

        res_check2 = subprocess.run([sys.executable, str(SCRIPTS_DIR / "cache.py"), "check", str(sample_file)], capture_output=True, text=True)
        self.assertEqual(res_check2.returncode, 0)
        self.assertIn("HIT", res_check2.stdout)

    def test_03_lint_links_detection(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        entity_file = self.test_dir / "wiki" / "entities" / "known_tool.md"
        entity_file.write_text("# Known Tool\nReferencing [[wiki/entities/missing_tool]]\n", encoding="utf-8")

        res_lint = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--strict"], capture_output=True, text=True)
        self.assertEqual(res_lint.returncode, 2)
        self.assertIn("Broken Links Found   : 1", res_lint.stdout)

    def test_04_cache_corruption_defense(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        sample_file = self.test_dir / "raw" / "articles" / "test.txt"
        sample_file.write_text("Unique sample content for test_04", encoding="utf-8")

        cache_file = self.test_dir / ".wiki-cache.json"
        corrupted_payload = "CORRUPTED_JSON_DATA__{{INVALID}}"
        cache_file.write_text(corrupted_payload, encoding="utf-8")

        res_check = subprocess.run([sys.executable, str(SCRIPTS_DIR / "cache.py"), "check", str(sample_file)], capture_output=True, text=True)
        self.assertNotEqual(res_check.returncode, 0)
        self.assertEqual(cache_file.read_text(encoding="utf-8"), corrupted_payload)

        res_update = subprocess.run([sys.executable, str(SCRIPTS_DIR / "cache.py"), "update", str(sample_file), "wiki/sources/test_summary.md"], capture_output=True, text=True)
        self.assertNotEqual(res_update.returncode, 0)
        self.assertEqual(cache_file.read_text(encoding="utf-8"), corrupted_payload)

    def test_05_lint_anchor_and_code_blocks(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        target_b = self.test_dir / "wiki" / "entities" / "B.md"
        target_b.write_text("# Target Entity B\n\n## sec\nSection details.\n", encoding="utf-8")

        source_a = self.test_dir / "wiki" / "entities" / "A.md"
        source_a.write_text("# Source A\nLink [[B#sec]] and [[B#sec|Sec]].\n```python\n# [[dummy]]\n```\n`[[dummy]]`\n", encoding="utf-8")

        res_lint = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--strict"], capture_output=True, text=True)
        self.assertEqual(res_lint.returncode, 0, f"Lint failed: {res_lint.stderr}")
        self.assertIn("Broken Links Found   : 0", res_lint.stdout)

    def test_06_verify_quotes(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        raw_article = self.test_dir / "raw" / "articles" / "deep_dive.txt"
        real_quote = "Deterministic execution eliminates hallucination risks entirely."
        raw_article.write_text(f"Introduction\n{real_quote}\nConclusion\n", encoding="utf-8")

        summary_file = self.test_dir / "wiki" / "sources" / "deep_dive_summary.md"
        summary_file.write_text(f"---\ntags: [source-summary]\nsource_path: raw/articles/deep_dive.txt\nconfidence: EXTRACTED\n---\n\n# Summary\n## Quotes\n> \"{real_quote}\"\n", encoding="utf-8")

        res_pass = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--strict", "--verify-quotes"], capture_output=True, text=True)
        self.assertEqual(res_pass.returncode, 0)
        self.assertIn("Unverified Quotes    : 0", res_pass.stdout)

        fake_quote = "This fabricated quote definitely does not exist in the raw source text."
        summary_file.write_text(f"---\ntags: [source-summary]\nsource_path: raw/articles/deep_dive.txt\nconfidence: EXTRACTED\n---\n\n# Summary\n## Quotes\n> \"{real_quote}\"\n> \"{fake_quote}\"\n", encoding="utf-8")

        res_fail = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--strict", "--verify-quotes"], capture_output=True, text=True)
        self.assertEqual(res_fail.returncode, 2)
        self.assertIn("Unverified Quotes    : 1", res_fail.stdout)

    def test_07_query_engine(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        sample_doc = self.test_dir / "wiki" / "sources" / "rag_pipeline.md"
        sample_doc.write_text("# RAG Pipeline\nRetrieval-Augmented Generation eliminates hallucination by grounding responses.\n", encoding="utf-8")

        res_filter_md = subprocess.run([sys.executable, str(SCRIPTS_DIR / "query.py"), str(self.test_dir), "--filter", "RAG"], capture_output=True, text=True)
        self.assertEqual(res_filter_md.returncode, 0)
        self.assertIn("rag_pipeline.md", res_filter_md.stdout)

        res_filter_json = subprocess.run([sys.executable, str(SCRIPTS_DIR / "query.py"), str(self.test_dir), "--filter", "RAG", "--format", "json"], capture_output=True, text=True)
        self.assertEqual(res_filter_json.returncode, 0)
        data_filter = json.loads(res_filter_json.stdout)
        self.assertEqual(data_filter["filter"]["results"][0]["file"], "wiki/sources/rag_pipeline.md")

        res_ent_md = subprocess.run([sys.executable, str(SCRIPTS_DIR / "query.py"), str(self.test_dir), "--entity", "RAG"], capture_output=True, text=True)
        self.assertEqual(res_ent_md.returncode, 0)
        self.assertIn("檢索增強生成", res_ent_md.stdout)

        res_ent_json = subprocess.run([sys.executable, str(SCRIPTS_DIR / "query.py"), str(self.test_dir), "--entity", "RAG", "--format", "json"], capture_output=True, text=True)
        self.assertEqual(res_ent_json.returncode, 0)
        data_ent = json.loads(res_ent_json.stdout)
        self.assertTrue(data_ent["entity"]["matched"])
        self.assertEqual(data_ent["entity"]["term"]["abbr"], "RAG")

    def test_08_file_size_budget_and_backlinks(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        oversized = self.test_dir / "wiki" / "entities" / "oversized_spec.md"
        oversized.write_text("# Oversized Spec\n" + ("x" * 48000) + "\n", encoding="utf-8")

        res_strict = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--strict"], capture_output=True, text=True)
        self.assertEqual(res_strict.returncode, 2)
        self.assertIn("oversized_spec.md", res_strict.stdout)

        res_json = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--json"], capture_output=True, text=True)
        self.assertEqual(res_json.returncode, 0)
        self.assertTrue(any(f["file"].endswith("oversized_spec.md") for f in json.loads(res_json.stdout).get("oversized_files", [])))
        oversized.unlink()

        target_ent = self.test_dir / "wiki" / "entities" / "vector_db.md"
        target_ent.write_text("# Vector DB\nVector database for retrieval.\n", encoding="utf-8")
        ref_doc = self.test_dir / "wiki" / "sources" / "architecture.md"
        ref_doc.write_text("# Architecture\nIndex into [[vector_db]] for search.\n", encoding="utf-8")

        res_bl = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--backlinks", "vector_db"], capture_output=True, text=True)
        self.assertEqual(res_bl.returncode, 0)
        self.assertIn("architecture.md", res_bl.stdout)
        self.assertIn("[[vector_db]]", res_bl.stdout)

        res_bl_json = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--backlinks", "vector_db", "--json"], capture_output=True, text=True)
        self.assertEqual(res_bl_json.returncode, 0)
        bl_items = json.loads(res_bl_json.stdout).get("backlinks", [])
        self.assertGreaterEqual(len(bl_items), 1)
        self.assertIn("architecture.md", bl_items[0]["source"])


if __name__ == "__main__":
    unittest.main()
