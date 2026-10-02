import unittest
from pathlib import Path
import sys

# Add scripts directory to path for unit testing
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
from ingest import clean_text, chunk_chapters, read_raw


class TestDeepModRouting(unittest.TestCase):
    """Unit tests validating deep-mod intent routing, security boundaries, and defensive sanitization."""

    def setUp(self):
        self.base_dir = BASE_DIR
        self.skill_md = self.base_dir / "SKILL.md"
        self.security_md = self.base_dir / "SECURITY.md"
        self.type_a_md = self.base_dir / "references" / "type_a_research.md"
        self.type_b_md = self.base_dir / "references" / "type_b_skill.md"
        self.common_gate_md = self.base_dir / "references" / "common_gate.md"
        self.ingest_py = self.base_dir / "scripts" / "ingest.py"

    def test_required_files_exist(self):
        self.assertTrue(self.skill_md.exists(), "SKILL.md must exist")
        self.assertTrue(self.security_md.exists(), "SECURITY.md must exist")
        self.assertTrue(self.common_gate_md.exists(), "common_gate.md must exist")
        self.assertTrue(self.type_a_md.exists(), "type_a_research.md must exist")
        self.assertTrue(self.type_b_md.exists(), "type_b_skill.md must exist")
        self.assertTrue(self.ingest_py.exists(), "scripts/ingest.py must exist")
        self.assertTrue((self.base_dir / "tests" / "noai_gate.py").exists(), "tests/noai_gate.py must exist")
        self.assertTrue((self.base_dir / "data" / "rules_gate.json").exists(), "data/rules_gate.json must exist")
        self.assertTrue((self.base_dir / "data" / "chapter_rules.json").exists(), "data/chapter_rules.json must exist")
        self.assertTrue((self.base_dir / "tests" / "audit.py").exists(), "tests/audit.py must exist")

    def test_skill_purity_and_length(self):
        content = self.skill_md.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        self.assertLessEqual(len(lines), 50, "SKILL.md must be 50 lines or fewer")
        self.assertIn("## Objective", content)
        self.assertIn("## Execution Workflow", content)
        self.assertIn("dependencies: []", content)
        self.assertNotIn("version:", content, "version should not be in metadata")

    def test_security_boundary_file(self):
        content = self.security_md.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        self.assertLessEqual(len(lines), 30, "SECURITY.md must be 30 lines or fewer")
        self.assertIn("## Scope", content)
        self.assertIn("## Dependencies", content)
        self.assertIn("## Execution", content)

    def test_routing_keywords(self):
        content = self.skill_md.read_text(encoding="utf-8")
        for kw in ["diff", "review", "架構圖", "重構", "轉技能", "提取技能"]:
            self.assertIn(kw, content, f"Routing keyword '{kw}' must be present in SKILL.md")
        self.assertNotIn("book-to-skill", content)
        self.assertNotIn("書籍提煉", content)

    def test_sanitizer_preserves_cjk_and_strips_noise(self):
        # Item 1: Test zero-width, bidi, cid stripped, and CJK preserved
        noise = "前置\u200b測試\ufeff文字\u202a方向\u202c(cid:123)結尾"
        cleaned = clean_text(noise)
        self.assertNotIn("\u200b", cleaned)
        self.assertNotIn("\ufeff", cleaned)
        self.assertNotIn("\u202a", cleaned)
        self.assertNotIn("(cid:123)", cleaned)
        # CJK preserved byte-for-byte
        cjk_sample = "微服務分散式系統架構設計與驗證"
        self.assertEqual(clean_text(cjk_sample), cjk_sample)

    def test_epub_explicit_rejection(self):
        # Format boundary: EPUB must raise ValueError
        fake_epub = Path("/tmp/test_book.epub")
        with self.assertRaises(ValueError):
            read_raw(fake_epub)

    def test_chapter_detection_circuit_breaker(self):
        # Chapter detection: unmatched text returns matched=False
        plain_text = "這是一段沒有任何章節標題的普通段落文字。"
        chunks, matched = chunk_chapters(plain_text, "plain.txt")
        self.assertFalse(matched, "Text without chapters should flag matched=False")
        self.assertEqual(chunks[0]["chapter"], "Full Document")

        # Matched text returns matched=True
        chapter_text = "# 第一章 核心架構\n\n本章節詳細說明系統之核心模組架構設計原則與相關安全防禦技術措施，涵蓋通訊協定、日誌審計與資料流程規範，確保整體架構具備高度防禦彈性與合規要求。本章節進一步提供各模組間介面規格說明。\n\n# 第二章 實作細節\n\n本章節進一步探討具體程式碼之實作方式與測試驗證流程，確保系統符合各項安全與品質指標，並完整涵蓋單元測試與整合測試各項情境。\n"
        chunks, matched = chunk_chapters(chapter_text, "book.md")
        self.assertTrue(matched, "Markdown headings should flag matched=True")
        self.assertEqual(len(chunks), 2)

    def test_html_and_insecure_http_boundary(self):
        import subprocess
        # 1. Insecure http:// must be rejected
        res = subprocess.run(["python3", str(self.ingest_py), "http://insecure.test"], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Insecure HTTP is prohibited", res.stderr)

    def test_indexing_summary_and_key_elements(self):
        sample = "# 第一講 系統架構\n\n本講定義系統的基礎運作機制。\n包含了 **RPC Gateway** 與 `TokenBucket`。\n架構: 熔斷隔離\n"
        chunks, matched = chunk_chapters(sample, "sample.md")
        self.assertTrue(matched)
        c0 = chunks[0]
        self.assertIn("本講定義系統的基礎運作機制", c0["summary"])
        self.assertIn("RPC Gateway", c0["key_elements"])
        self.assertIn("TokenBucket", c0["key_elements"])
        self.assertIn("熔斷隔離", c0["key_elements"])
    def test_large_document_circuit_breaker(self):
        import subprocess, json, tempfile
        tmp_txt = Path(tempfile.gettempdir()) / "test_big_plain.txt"
        tmp_txt.write_text("無章節標題普通段落\n" * 3500, encoding="utf-8")
        try:
            res = subprocess.run(["python3", str(self.ingest_py), str(tmp_txt)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Outputting chapter list", res.stderr)
            data = json.loads(res.stdout)
            self.assertGreater(data["total_est_tokens"], 10000)
            self.assertIn("chapters", data)
            self.assertEqual(data["chapters"][0]["lines"], 802)
            self.assertIn("source_start_line", data["chapters"][0])
        finally:
            if tmp_txt.exists(): tmp_txt.unlink()


    def test_defang_and_reference_stripping(self):
        sample = (
            "Incident Response | Chapter 1 | 123\n"
            "Source: PDF Pages 45-48\n"
            "Here is an IoC: https://attacker.example.com/c2/payload.ps1\n"
            "Here is http://test.org:8080/api\n"
            "## References\n"
            "[1] Author, A. (2025). Paper Title. https://doi.org/10.1234/5678\n"
            "[2] Standards Org. (2024). Guideline. https://example.org/guideline.pdf\n"
        )
        cleaned = clean_text(sample)
        self.assertNotIn("Incident Response | Chapter 1 | 123", cleaned)
        self.assertNotIn("Source: PDF Pages", cleaned)
        self.assertNotIn("## References", cleaned)
        self.assertNotIn("[1] Author", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("http://", cleaned)
        self.assertIn("hxxps://attacker[.]example[.]com/c2/payload.ps1", cleaned)
        self.assertIn("hxxp://test[.]org:8080/api", cleaned)


if __name__ == "__main__":
    unittest.main()
