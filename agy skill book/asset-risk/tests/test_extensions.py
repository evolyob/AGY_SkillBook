"""Unit tests for drill_generator.py and news_analyzer.py extensions."""

import unittest
from pathlib import Path
import sys

# Ensure scripts directory is in path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from drill_generator import generate_drill_plan, format_as_markdown, resolve_asset_keywords
from news_analyzer import load_parameters, build_tag_index, analyze_news


class TestDrillGenerator(unittest.TestCase):
    """Validates standardized IT4-21 disaster recovery drill plan and execution steps generation."""

    def test_planning_fields_structure(self):
        """Verifies that only 3 core planning fields are generated and administrative fields are removed."""
        plan = generate_drill_plan(
            asset_name="核心郵件伺服器",
            category="軟體",
            asset_type="系統",
            threat="憑證遭竊取",
            vulnerability="多因子認證機制未健全"
        )
        self.assertIn("planning_fields", plan)
        fields = plan["planning_fields"]
        # Core scenario fields
        self.assertIn("drill_theme", fields)
        self.assertIn("target_and_scope", fields)
        self.assertIn("scenario_description", fields)
        self.assertIn("playbook_flow", fields)
        # Verify administrative fields are removed
        self.assertNotIn("participants", fields)
        self.assertNotIn("timeline_and_deadlines", fields)
        self.assertNotIn("testing_methods_and_resources", fields)
        self.assertNotIn("review_schedule", fields)
        self.assertIn("核心郵件伺服器", fields["drill_theme"])
        self.assertIn("憑證遭竊取", fields["drill_theme"])

    def test_execution_steps_compliance(self):
        """Verifies 8 standardized execution steps and blank unit_role / duration for user fill-in."""
        plan = generate_drill_plan(
            asset_name="客戶資料庫",
            category="資料",
            asset_type="業務交易資料",
            threat="核心資料庫遭竊取或大量匯出",
            vulnerability="資料庫連線採用弱密碼且未限制存取來源"
        )
        steps = plan.get("execution_steps", [])
        self.assertEqual(len(steps), 8, "Must contain exactly 8 standardized execution steps")
        expected_phases = ["收到通報", "緊急阻斷", "隔離保全", "受害清查", "事故判定", "通報主管機關", "修補還原", "驗證重啟"]
        for idx, step in enumerate(steps, start=1):
            self.assertEqual(step["step_no"], idx)
            self.assertEqual(step["phase_code"], expected_phases[idx - 1])
            self.assertEqual(step["unit_role"], "", f"Step {idx} unit_role must be empty string")
            self.assertEqual(step["duration"], "", f"Step {idx} duration must be empty string")
        # Step 6: Regulatory reporting
        self.assertIn("主管機關", steps[5]["procedure"])
        # Step 7: Vulnerability remediation
        self.assertIn("資料庫連線採用弱密碼且未限制存取來源", steps[6]["procedure"])
        # Step 8: Verification & resumption
        self.assertIn("客戶資料庫", steps[7]["procedure"])

    def test_markdown_formatting(self):
        """Verifies that markdown table outputs both Block A and Block B."""
        plan = generate_drill_plan(
            asset_name="主機伺服器01",
            category="硬體",
            asset_type="主機伺服器",
            threat="實體伺服器/儲存設備故障毀損",
            vulnerability="核心設備缺乏冗餘備援與高可用機制"
        )
        md = format_as_markdown(plan)
        self.assertIn("區塊 A：演練規劃表", md)
        self.assertIn("情境說明", md)
        self.assertIn("區塊 B：演練暨處理執行表", md)

    def test_pair_id_resolution_and_keyword_binding(self):
        """Verifies extracting keywords from parameters.json by pair_id and binding to fields."""
        param_db = load_parameters()
        name, c, t, th, v = resolve_asset_keywords(param_db, pair_id="軟體_01", name="AD主機")
        self.assertEqual(c, "軟體")
        self.assertEqual(t, "作業系統")
        self.assertEqual(th, "遭勒索軟體或木馬惡意程式利用")
        self.assertEqual(v, "未定期安裝作業系統安全性修補程式")

        plan = generate_drill_plan(name, c, t, th, v)
        self.assertIn("AD主機", plan["planning_fields"]["drill_theme"])
        self.assertIn("遭勒索軟體或木馬惡意程式利用", plan["planning_fields"]["drill_theme"])
        self.assertIn("未定期安裝作業系統安全性修補程式", plan["planning_fields"]["target_and_scope"])


class TestNewsAnalyzer(unittest.TestCase):
    """Validates in-memory inverted index and news-to-canonical threat/vuln matching."""

    @classmethod
    def setUpClass(cls):
        cls.param_db = load_parameters()

    def test_inverted_index_spec_contract(self):
        """Validates SKILL_DATA_SPEC.md compliance: index built on tags for N > 20 records."""
        records, tag_index = build_tag_index(self.param_db)
        self.assertEqual(len(records), 60)
        self.assertGreater(len(tag_index), 200, "Tag index must cover > 200 tags")
        self.assertIn("作業系統", tag_index)
        self.assertIn("主機伺服器", tag_index)

    def test_ransomware_news_matching(self):
        """Tests ransomware attack news mapping to OS unpatched pair (軟體_01)."""
        news = "某醫院多台主機遭勒索軟體攻擊加密，調查發現駭客利用微軟作業系統未修補漏洞植入惡意程式。"
        result = analyze_news(news, self.param_db, top_k=3)
        self.assertGreater(len(result["matches"]), 0)
        top = result["matches"][0]
        self.assertEqual(top["pair_id"], "軟體_01")
        self.assertEqual(top["category"], "軟體")
        self.assertEqual(top["threat"], "遭勒索軟體或木馬惡意程式利用")

    def test_phishing_mfa_news_matching(self):
        """Tests phishing email leading to MFA bypass mapping to 軟體_04 or 人員_01."""
        news = "員工點擊假冒內部公告的釣魚郵件導致密碼洩漏，由於雲端管理後台未開啟多因子認證(MFA)，攻擊者成功登入。"
        result = analyze_news(news, self.param_db, top_k=3)
        match_ids = [m["pair_id"] for m in result["matches"]]
        self.assertTrue("軟體_04" in match_ids or "人員_01" in match_ids)

    def test_cloud_bucket_leak_matching(self):
        """Tests cloud storage bucket misconfiguration news mapping to 軟體_05."""
        news = "知名企業因雲端儲存貯體 (Bucket) 權限設定不當，造成超過百萬筆用戶資料公開外洩。"
        result = analyze_news(news, self.param_db, top_k=3)
        top = result["matches"][0]
        self.assertEqual(top["pair_id"], "軟體_05")
        self.assertEqual(top["threat"], "雲端儲存物件遭公開外洩")

    def test_empty_input_graceful_handling(self):
        """Tests that empty input returns empty matches gracefully without exception."""
        result = analyze_news("   ", self.param_db, top_k=3)
        self.assertEqual(len(result["matches"]), 0)


if __name__ == "__main__":
    unittest.main()
