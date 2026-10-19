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
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


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

    def test_09_title_weighted_ranking_and_structural_lint(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)

        target_ent = self.test_dir / "wiki" / "entities" / "vector_db.md"
        target_ent.write_text("# Vector DB\n\nVector database for semantic similarity and retrieval.\n", encoding="utf-8")

        spam_doc = self.test_dir / "wiki" / "sources" / "noisy_notes.md"
        spam_doc.write_text("# Notes\n\nVector database vector database vector database keyword repetition.\n", encoding="utf-8")

        # 1. Native FTS5 title weighting ensures entity page outranks keyword-stuffed note
        cmd_json = [sys.executable, str(SCRIPTS_DIR / "query.py"), str(self.test_dir), "--filter", "vector_db", "--format", "json"]
        res_json = subprocess.run(cmd_json, capture_output=True, text=True)
        self.assertEqual(res_json.returncode, 0, f"Query failed: {res_json.stderr}")
        results = json.loads(res_json.stdout)["filter"]["results"]
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["file"], "wiki/entities/vector_db.md")
        self.assertIn("score", results[0])

        # 2. Hindsight structural integrity check catches collapsed tables and unbalanced fences
        broken_md = self.test_dir / "wiki" / "sources" / "malformed.md"
        broken_md.write_text("# Malformed\n| A | B | |---|---|\n```python\nprint(1)\n", encoding="utf-8")
        res_lint = subprocess.run([sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--strict", "--json"], capture_output=True, text=True)
        self.assertEqual(res_lint.returncode, 2)
        issues = json.loads(res_lint.stdout).get("structural_issues", [])
        issue_types = {i["type"] for i in issues}
        self.assertIn("collapsed_table", issue_types)
        self.assertIn("unbalanced_fences", issue_types)

    def test_10_flatten_and_directory_quote_verification(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        src_doc = self.test_dir / "sample_standard.md"
        src_doc.write_text(
            "# 1. 適用範圍\n" + ("本標準規定工業自動化及控制系統之安全要求事項。\n" * 6) +
            "\n# 2. 安全控制要求\n" + ("所有特權帳戶必須啟用多因素鑑別與通行碼強度檢查。\n" * 6),
            encoding="utf-8",
        )

        res_list = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "flatten.py"), str(src_doc), "--list-only"],
            capture_output=True, text=True,
        )
        self.assertEqual(res_list.returncode, 0, f"flatten.py --list-only failed: {res_list.stderr}")
        meta = json.loads(res_list.stdout)
        self.assertEqual(meta["total_chapters"], 2)
        self.assertEqual(meta["dispatch_mode"], "single_agent")

        out_chapters = self.test_dir / "raw" / "articles" / "sample_std" / "chapters"
        res_split = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "flatten.py"), str(src_doc), "--split-dir", str(out_chapters), "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(res_split.returncode, 0, f"flatten.py --split-dir failed: {res_split.stderr}")
        self.assertTrue((out_chapters / "index.json").exists())

        summary_md = self.test_dir / "wiki" / "sources" / "sample_std.md"
        summary_md.write_text(
            "---\ntags: [source-summary]\nsource_path: raw/articles/sample_std/chapters\nconfidence: EXTRACTED\n---\n\n"
            "# Sample Standard\n## Notable Quotes\n> \"所有特權帳戶必須啟用多因素鑑別與通行碼強度檢查。\"\n",
            encoding="utf-8",
        )
        res_verify = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "lint_links.py"), str(self.test_dir), "--strict", "--verify-quotes"],
            capture_output=True, text=True,
        )
        self.assertEqual(res_verify.returncode, 0, f"Directory quote verification failed: {res_verify.stdout}")

    def test_11_sanitize_markdown(self):
        dirty_file = self.test_dir / "dirty.md"
        dirty_file.write_text("# Test\nReference: [[compliance/CWE Top 25]]\n```js=\ncode\n```\n> | H1 | H2 |\n> |---|---|\n```bash\nunclosed\n", encoding="utf-8")
        res_dry = subprocess.run([sys.executable, str(SCRIPTS_DIR / "sanitize.py"), str(dirty_file)], capture_output=True, text=True)
        self.assertEqual(res_dry.returncode, 2)
        res_fix = subprocess.run([sys.executable, str(SCRIPTS_DIR / "sanitize.py"), str(dirty_file), "--fix"], capture_output=True, text=True)
        self.assertEqual(res_fix.returncode, 0)
        fixed_text = dirty_file.read_text(encoding="utf-8")
        self.assertNotIn("[[compliance/CWE Top 25]]", fixed_text)
        self.assertIn("`compliance/CWE Top 25`", fixed_text)
        self.assertNotIn("```js=", fixed_text)
        self.assertIn("```js", fixed_text)
        self.assertIn("|---|---|", fixed_text)
        import re
        self.assertEqual(len(re.findall(r"^\s*```", fixed_text, re.M)) % 2, 0)

    def test_12_assemble_update_index(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        (self.test_dir / "wiki" / "entities" / "demo_tool.md").write_text("---\ntags: [entity, appsec]\ncontext: \"Automated AppSec test tool\"\n---\n\n# Demo Tool\n> Tool description.\n", encoding="utf-8")
        res_up = subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--update-index", "--path", str(self.test_dir), "--json"], capture_output=True, text=True)
        self.assertEqual(res_up.returncode, 0, f"update-index failed: {res_up.stderr}")
        meta = json.loads(res_up.stdout)
        self.assertEqual(meta["total_entities"], 1)
        self.assertIn("demo_tool", meta["newly_added_to_index"])
        index_text = (self.test_dir / "index.md").read_text(encoding="utf-8")
        self.assertIn("[[demo_tool]]", index_text)
    def test_13_boundary_aware_fences(self):
        mid_file = self.test_dir / "mid_break.md"
        mid_file.write_text(
            "# Title\n\n```http\nscript-src 'nonce-123';\n\n---\n\n## 2. Next Section (來源: `test.md`)\n\nCode demo:\n```csharp\nint x = 1;\n```\n",
            encoding="utf-8"
        )
        res_fix = subprocess.run([sys.executable, str(SCRIPTS_DIR / "sanitize.py"), str(mid_file), "--fix"], capture_output=True, text=True)
        self.assertEqual(res_fix.returncode, 0)
        fixed_text = mid_file.read_text(encoding="utf-8")
        # Ensure that ``` was inserted BEFORE the section delimiter
        sec_idx = fixed_text.find("## 2. Next Section")
        fence_before_sec = fixed_text[:sec_idx].rstrip()
        self.assertTrue(fence_before_sec.endswith("```\n\n---") or "```\n\n---" in fixed_text[:sec_idx])
        # Ensure csharp block starts cleanly
        self.assertIn("```csharp\nint x = 1;\n```", fixed_text)

    def test_14_real_index_omission_simulation(self):
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--init", "--path", str(self.test_dir)], check=True)
        index_file = self.test_dir / "index.md"
        # Seed index.md with sections
        index_file.write_text(
            "# Index\n\n> Local-first knowledge base (`0` Entities | `0` Topics | `0` Source Summaries).\n\n"
            "## 2. Entity Quick-Lookup Tables\n\n"
            "### 2.5 應用程式與 Web 站點安全\n| 實體卡片 | 標籤 | 說明 |\n| :--- | :--- | :--- |\n\n"
            "### 2.4 端點系統、網路協定與暴險防禦\n| 實體卡片 | 標籤 | 說明 |\n| :--- | :--- | :--- |\n",
            encoding="utf-8"
        )
        (self.test_dir / "wiki" / "entities" / "web_card.md").write_text("---\ntags: [entity, csp]\ncontext: \"CSP Web Security\"\n---\n# CSP\n", encoding="utf-8")
        (self.test_dir / "wiki" / "entities" / "linux_card.md").write_text("---\ntags: [entity, linux]\ncontext: \"Linux Kernel\"\n---\n# Linux\n", encoding="utf-8")

        res_up = subprocess.run([sys.executable, str(SCRIPTS_DIR / "assemble.py"), "--update-index", "--path", str(self.test_dir), "--json"], capture_output=True, text=True)
        self.assertEqual(res_up.returncode, 0)
        idx_content = index_file.read_text(encoding="utf-8")
        
        pos_25 = idx_content.find("### 2.5")
        pos_24 = idx_content.find("### 2.4")
        pos_web = idx_content.find("[[web_card]]")
        pos_linux = idx_content.find("[[linux_card]]")
        
        self.assertTrue(pos_25 < pos_web < pos_24)
        self.assertTrue(pos_24 < pos_linux)

    def test_15_extract_meta_anchors(self):
        from query import extract_meta_anchors

        text1 = "---\ntags: [entity]\nalias: [ZH_Term, EN_Term, Abbr]\n---\n# Title\n"
        self.assertEqual(extract_meta_anchors(text1), "ZH_Term  EN_Term  Abbr")

        text2 = "---\ntags: [entity]\naliases: [foo, bar]\n---\n# Title\n"
        self.assertEqual(extract_meta_anchors(text2), "foo  bar")

        text3 = "# Just Title\nNo frontmatter here."
        self.assertEqual(extract_meta_anchors(text3), "")

        text4 = "---\ntags: [entity]\n---\n# Title\n"
        self.assertEqual(extract_meta_anchors(text4), "")


if __name__ == "__main__":
    unittest.main()


