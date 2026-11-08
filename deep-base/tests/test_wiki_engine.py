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

    def test_12_sanitize_structural_normalizer(self):
        self.init_wiki()
        # 1. Glued heading and code fence protection
        sample_md = self.test_dir / "raw" / "notes" / "sample_note.md"
        sample_md.parent.mkdir(parents=True, exist_ok=True)
        raw_content = (
            "2.1 系統架構 本系統採用微服務架構設計與容器化部署。\n\n"
            "```markdown\n"
            "## 範例標題保留\n"
            "[[legacy/pseudo_link]]\n"
            "```\n\n"
            "[[docs/legacy_note]]\n"
        )
        sample_md.write_text(raw_content, encoding="utf-8")

        res_fix = self.run_cmd("sanitize.py", str(sample_md), "--fix", "--json")
        self.assertEqual(res_fix.returncode, 0)
        fixed_text = sample_md.read_text(encoding="utf-8")

        # Heading was de-glued to H2
        self.assertIn("## 2.1 系統架構\n\n本系統採用微服務架構設計與容器化部署。", fixed_text)
        # Outside fence pseudo-wikilink was fixed
        self.assertIn("`docs/legacy_note`", fixed_text)
        # Inside fence content was strictly preserved (fence masking)
        self.assertIn("## 範例標題保留", fixed_text)
        self.assertIn("[[legacy/pseudo_link]]", fixed_text)

        # 2. CJK Heading Elevation and Bracket List Normalization
        cjk_md = self.test_dir / "raw" / "notes" / "cjk_note.md"
        cjk_raw = (
            "# 總則\n\n"
            "三、行為主體：網絡服務提供者\n"
            "(一) 保證人地位之確立\n"
            "(1) 服務提供者不知悉內容具有違法性\n"
            "(2) 經通知後及時採取必要處置\n\n"
            "被告具備兩項特徵：一、未成年；二、初犯，深具悔意。\n"
            "(九)》最高人民法院關於司法解釋之規定。\n"
        )
        cjk_md.write_text(cjk_raw, encoding="utf-8")
        res_cjk = self.run_cmd("sanitize.py", str(cjk_md), "--fix", "--json")
        self.assertEqual(res_cjk.returncode, 0)
        cjk_fixed = cjk_md.read_text(encoding="utf-8")

        # CJK H3 / H4 elevated
        self.assertIn("### 三、行為主體：網絡服務提供者", cjk_fixed)
        self.assertIn("#### (一) 保證人地位之確立", cjk_fixed)
        # List items bulleted
        self.assertIn("- (1) 服務提供者不知悉內容具有違法性", cjk_fixed)
        self.assertIn("- (2) 經通知後及時採取必要處置", cjk_fixed)
        # Sentence with 一、 ending with punctuation is NOT elevated
        self.assertIn("被告具備兩項特徵：一、未成年；二、初犯，深具悔意。", cjk_fixed)
        # Citation with (九)》 is NOT elevated
        self.assertIn("(九)》最高人民法院關於司法解釋之規定。", cjk_fixed)

        # 3. Plain text without headings warning
        plain_md = self.test_dir / "raw" / "notes" / "plain.md"
        plain_md.write_text("This is pure plain text without any markdown headings.\n", encoding="utf-8")
        res_warn = self.run_cmd("sanitize.py", str(plain_md), "--json")
        self.assertEqual(res_warn.returncode, 0)
        warn_data = json.loads(res_warn.stdout)[0]
        self.assertEqual(warn_data["status"], "WARN")
        self.assertTrue(any("NO_HEADINGS" in w for w in warn_data["warnings"]))

    def test_13_assemble_semantic_chunker(self):
        self.init_wiki()
        # 1. Glossary test
        raw_glossary = self.test_dir / "raw" / "articles" / "sample_glossary.md"
        raw_glossary.parent.mkdir(parents=True, exist_ok=True)
        raw_glossary.write_text("词汇表\nA\nASCII：字符编码标准\nB\n白箱测试：基于代码逻辑的测试\n", encoding="utf-8")

        res_chunk = self.run_cmd("assemble.py", "--semantic-chunk", str(raw_glossary), "--write", "--json")
        self.assertEqual(res_chunk.returncode, 0)
        chunked_text = raw_glossary.read_text(encoding="utf-8")
        self.assertIn("# 词汇表", chunked_text)
        self.assertIn("## A", chunked_text)
        self.assertIn("## B", chunked_text)

        # Sanitize should report CLEAN
        res_san = self.run_cmd("sanitize.py", str(raw_glossary), "--json")
        self.assertEqual(res_san.returncode, 0)
        san_data = json.loads(res_san.stdout)[0]
        self.assertEqual(san_data["status"], "CLEAN")

        # 2. QA Context & Negative False-Positive Prevention Test
        qa_doc = self.test_dir / "raw" / "articles" / "qa_doc.md"
        raw_qa = (
            "Overview\nThis is an overview section.\n\n"
            "Questions\n"
            "1-1 What is the primary benefit of microservices?\n"
            "3.5 meters is the length of the pipe\n"
            "A\n"
        )
        qa_doc.write_text(raw_qa, encoding="utf-8")
        res_qa = self.run_cmd("assemble.py", "--semantic-chunk", str(qa_doc), "--write", "--json")
        self.assertEqual(res_qa.returncode, 0)
        qa_text = qa_doc.read_text(encoding="utf-8")

        self.assertIn("# Overview", qa_text)
        self.assertIn("## Questions", qa_text)
        self.assertIn("### 1-1 What is the primary benefit of microservices?", qa_text)
        # Negative tests: decimals and isolated prose letters must NOT become headings
        self.assertIn("\n3.5 meters is the length of the pipe\n", qa_text)
        self.assertNotIn("### 3.5 meters", qa_text)
        self.assertIn("\nA\n", qa_text)
        self.assertNotIn("## A", qa_text)

        # 3. Idempotence: Second run produces 0 changes
        res_idempotent = self.run_cmd("assemble.py", "--semantic-chunk", str(qa_doc), "--write", "--json")
        self.assertEqual(res_idempotent.returncode, 0)
        data_idem = json.loads(res_idempotent.stdout)[0]
        self.assertFalse(data_idem["changed"])

        # 4. Structured Document Protection: Existing H1+H2 must NOT be mutated
        structured_doc = self.test_dir / "raw" / "articles" / "structured.md"
        structured_doc.write_text("# Original Title\n\n## Section 1\nContent.\n", encoding="utf-8")
        res_struct = self.run_cmd("assemble.py", "--semantic-chunk", str(structured_doc), "--write", "--json")
        self.assertEqual(res_struct.returncode, 0)
        data_struct = json.loads(res_struct.stdout)[0]
        self.assertFalse(data_struct["changed"])
        self.assertEqual(structured_doc.read_text(encoding="utf-8"), "# Original Title\n\n## Section 1\nContent.\n")


if __name__ == "__main__":
    unittest.main()
