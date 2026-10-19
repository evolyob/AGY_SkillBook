#!/usr/bin/env python3
"""Regression test suite for deep-base engine scripts."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class TestWikiEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="wiki_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_cmd(self, script_name: str, *args, check: bool = False) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(SCRIPTS_DIR / script_name), *args]
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    def init_wiki(self) -> Path:
        self.run_cmd("assemble.py", "--init", "--path", str(self.test_dir), check=True)
        return self.test_dir

    def test_01_assemble_init(self):
        res = self.run_cmd("assemble.py", "--init", "--path", str(self.test_dir))
        self.assertEqual(res.returncode, 0, f"assemble.py failed: {res.stderr}")
        self.assertTrue((self.test_dir / ".wiki-schema.md").exists())
        self.assertTrue((self.test_dir / "index.md").exists())
        self.assertTrue((self.test_dir / "raw" / "articles").is_dir())
        self.assertTrue((self.test_dir / "wiki" / "entities").is_dir())
        self.assertTrue((self.test_dir / "wiki" / "comparisons").is_dir())
        self.assertTrue((self.test_dir / "data" / "glossary.json").exists())

    def test_02_cache_check_and_update(self):
        self.init_wiki()
        sample_file = self.test_dir / "raw" / "articles" / "test.txt"
        sample_file.write_text("Unique content 12345", encoding="utf-8")

        res_check1 = self.run_cmd("cache.py", "check", str(sample_file))
        self.assertEqual(res_check1.returncode, 2)
        self.assertIn("MISS", res_check1.stdout)

        res_up = self.run_cmd("cache.py", "update", str(sample_file), "wiki/sources/test_summary.md")
        self.assertEqual(res_up.returncode, 0)

        res_check2 = self.run_cmd("cache.py", "check", str(sample_file))
        self.assertEqual(res_check2.returncode, 0)
        self.assertIn("HIT", res_check2.stdout)

    def test_03_cache_corruption_defense(self):
        self.init_wiki()
        sample_file = self.test_dir / "raw" / "articles" / "test.txt"
        sample_file.write_text("Unique sample content for test_03", encoding="utf-8")

        cache_file = self.test_dir / ".wiki-cache.json"
        corrupted_payload = "CORRUPTED_JSON_DATA__{{INVALID}}"
        cache_file.write_text(corrupted_payload, encoding="utf-8")

        res_check = self.run_cmd("cache.py", "check", str(sample_file))
        self.assertNotEqual(res_check.returncode, 0)
        self.assertEqual(cache_file.read_text(encoding="utf-8"), corrupted_payload)

        res_update = self.run_cmd("cache.py", "update", str(sample_file), "wiki/sources/test_summary.md")
        self.assertNotEqual(res_update.returncode, 0)
        self.assertEqual(cache_file.read_text(encoding="utf-8"), corrupted_payload)

    def test_04_lint_links_detection(self):
        self.init_wiki()
        entity_file = self.test_dir / "wiki" / "entities" / "known_tool.md"
        entity_file.write_text("# Known Tool\nReferencing [[wiki/entities/missing_tool]]\n", encoding="utf-8")

        res_lint = self.run_cmd("lint_links.py", str(self.test_dir), "--strict")
        self.assertEqual(res_lint.returncode, 2)
        self.assertIn("Broken Links Found   : 1", res_lint.stdout)

    def test_05_lint_anchor_and_code_blocks(self):
        self.init_wiki()
        target_b = self.test_dir / "wiki" / "entities" / "B.md"
        target_b.write_text("# Target Entity B\n\n## sec\nSection details.\n", encoding="utf-8")

        source_a = self.test_dir / "wiki" / "entities" / "A.md"
        source_a.write_text("# Source A\nLink [[B#sec]] and [[B#sec|Sec]].\n```python\n# [[dummy]]\n```\n`[[dummy]]`\n", encoding="utf-8")

        res_lint = self.run_cmd("lint_links.py", str(self.test_dir), "--strict")
        self.assertEqual(res_lint.returncode, 0, f"Lint failed: {res_lint.stderr}")
        self.assertIn("Broken Links Found   : 0", res_lint.stdout)

    def test_06_verify_quotes(self):
        self.init_wiki()
        raw_article = self.test_dir / "raw" / "articles" / "deep_dive.txt"
        real_quote = "Deterministic execution eliminates hallucination risks entirely."
        raw_article.write_text(f"Introduction\n{real_quote}\nConclusion\n", encoding="utf-8")

        summary_file = self.test_dir / "wiki" / "sources" / "deep_dive_summary.md"
        summary_file.write_text(f"---\ntags: [source-summary]\nsource_path: raw/articles/deep_dive.txt\nconfidence: EXTRACTED\n---\n\n# Summary\n## Quotes\n> \"{real_quote}\"\n", encoding="utf-8")

        res_pass = self.run_cmd("lint_links.py", str(self.test_dir), "--strict", "--verify-quotes")
        self.assertEqual(res_pass.returncode, 0)
        self.assertIn("Unverified Quotes    : 0", res_pass.stdout)

        fake_quote = "This fabricated quote definitely does not exist in the raw source text."
        summary_file.write_text(f"---\ntags: [source-summary]\nsource_path: raw/articles/deep_dive.txt\nconfidence: EXTRACTED\n---\n\n# Summary\n## Quotes\n> \"{real_quote}\"\n> \"{fake_quote}\"\n", encoding="utf-8")

        res_fail = self.run_cmd("lint_links.py", str(self.test_dir), "--strict", "--verify-quotes")
        self.assertEqual(res_fail.returncode, 2)
        self.assertIn("Unverified Quotes    : 1", res_fail.stdout)

    def test_07_file_size_budget_and_backlinks(self):
        self.init_wiki()
        oversized = self.test_dir / "wiki" / "entities" / "oversized_spec.md"
        oversized.write_text("# Oversized Spec\n" + ("x" * 48000) + "\n", encoding="utf-8")

        res_strict = self.run_cmd("lint_links.py", str(self.test_dir), "--strict")
        self.assertEqual(res_strict.returncode, 2)
        self.assertIn("oversized_spec.md", res_strict.stdout)
        oversized.unlink()

        target_ent = self.test_dir / "wiki" / "entities" / "vector_db.md"
        target_ent.write_text("# Vector DB\nVector database for retrieval.\n", encoding="utf-8")
        ref_doc = self.test_dir / "wiki" / "sources" / "architecture.md"
        ref_doc.write_text("# Architecture\nIndex into [[vector_db]] for search.\n", encoding="utf-8")

        res_bl = self.run_cmd("query.py", str(self.test_dir), "--backlinks", "vector_db")
        self.assertEqual(res_bl.returncode, 0)
        self.assertIn("architecture.md", res_bl.stdout)
        self.assertIn("[[vector_db]]", res_bl.stdout)

    def test_08_structural_lint(self):
        self.init_wiki()
        broken_md = self.test_dir / "wiki" / "sources" / "malformed.md"
        broken_md.write_text("# Malformed\n| A | B | |---|---|\n```python\nprint(1)\n", encoding="utf-8")
        res_lint = self.run_cmd("lint_links.py", str(self.test_dir), "--strict", "--json")
        self.assertEqual(res_lint.returncode, 2)
        issues = json.loads(res_lint.stdout).get("structural_issues", [])
        issue_types = {i["type"] for i in issues}
        self.assertIn("collapsed_table", issue_types)
        self.assertIn("unbalanced_fences", issue_types)

    def test_09_flatten_and_directory_quote_verification(self):
        self.init_wiki()
        src_doc = self.test_dir / "sample_standard.md"
        src_doc.write_text(
            "# 1. 適用範圍\n" + ("本標準規定工業自動化及控制系統之安全要求事項。\n" * 6) +
            "\n# 2. 安全控制要求\n" + ("所有特權帳戶必須啟用多因素鑑別與通行碼強度檢查。\n" * 6),
            encoding="utf-8",
        )

        res_list = self.run_cmd("flatten.py", str(src_doc), "--list-only")
        self.assertEqual(res_list.returncode, 0, f"flatten.py --list-only failed: {res_list.stderr}")
        meta = json.loads(res_list.stdout)
        self.assertEqual(meta["total_chapters"], 2)

        out_chapters = self.test_dir / "raw" / "articles" / "sample_std" / "chapters"
        res_split = self.run_cmd("flatten.py", str(src_doc), "--split-dir", str(out_chapters), "--json")
        self.assertEqual(res_split.returncode, 0, f"flatten.py --split-dir failed: {res_split.stderr}")
        self.assertTrue((out_chapters / "index.json").exists())

        summary_md = self.test_dir / "wiki" / "sources" / "sample_std.md"
        summary_md.write_text(
            "---\ntags: [source-summary]\nsource_path: raw/articles/sample_std/chapters\nconfidence: EXTRACTED\n---\n\n"
            "# Sample Standard\n## Notable Quotes\n> \"所有特權帳戶必須啟用多因素鑑別與通行碼強度檢查。\"\n",
            encoding="utf-8",
        )
        res_verify = self.run_cmd("lint_links.py", str(self.test_dir), "--strict", "--verify-quotes")
        self.assertEqual(res_verify.returncode, 0, f"Directory quote verification failed: {res_verify.stdout}")

    def test_10_assemble_update_index(self):
        self.init_wiki()
        (self.test_dir / "wiki" / "entities" / "demo_tool.md").write_text(
            "---\ntags: [entity, appsec]\ncontext: \"Automated AppSec test tool\"\n---\n\n# Demo Tool\n> Tool description.\n",
            encoding="utf-8"
        )
        res_up = self.run_cmd("assemble.py", "--update-index", "--path", str(self.test_dir), "--json")
        self.assertEqual(res_up.returncode, 0, f"update-index failed: {res_up.stderr}")
        meta = json.loads(res_up.stdout)
        self.assertEqual(meta["total_entities"], 1)
        self.assertIn("demo_tool", meta["newly_added_to_index"])

        index_text = (self.test_dir / "index.md").read_text(encoding="utf-8")
        self.assertIn("[[demo_tool]]", index_text)
        self.assertIn("`1` Entities", index_text)

    def test_11_lint_stats_telemetry(self):
        self.init_wiki()
        (self.test_dir / "raw" / "articles" / "doc1.txt").write_text("Source document", encoding="utf-8")
        (self.test_dir / "wiki" / "entities" / "ent1.md").write_text("# Entity 1", encoding="utf-8")

        res_stats = self.run_cmd("lint_links.py", str(self.test_dir), "--stats", "--json")
        self.assertEqual(res_stats.returncode, 0)
        data = json.loads(res_stats.stdout)
        self.assertEqual(data["raw_sources"], 1)
        self.assertEqual(data["total_synthesized"], 1)
        self.assertEqual(data["layers"]["entities"], 1)


if __name__ == "__main__":
    unittest.main()
