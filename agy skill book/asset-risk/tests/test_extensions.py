"""Unit tests for drill_generator.py extension."""

import unittest
from pathlib import Path
import sys

# Ensure scripts directory is in path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from drill_generator import generate_drill_plan, format_as_markdown, resolve_asset_keywords, load_parameters


class TestDrillGenerator(unittest.TestCase):
    """Validates standardized disaster recovery drill plan and execution steps generation."""

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

    def test_pii_drill_plan_override(self):
        """Verifies PII breach drill overrides steps 4-7 with statutory requirements."""
        plan = generate_drill_plan(
            asset_name="核心帳務系統",
            category="軟體",
            asset_type="應用系統",
            threat="網站遭SQL/指令注入攻擊",
            vulnerability="軟體開發未實作輸入參數過濾與參數化查詢",
            is_pii=True
        )
        self.assertIn("個人資料外洩重大事件", plan["planning_fields"]["drill_theme"])
        steps = plan["execution_steps"]
        # Step 4: Special PII check
        self.assertIn("特種個資", steps[3]["procedure"])
        # Step 5: Art. 6 check
        self.assertIn("個資法", steps[4]["procedure"])
        # Step 6: 72-hour and Art. 12 notification
        self.assertIn("72小時", steps[5]["procedure"])
        self.assertIn("第12條", steps[5]["procedure"])
        # Step 7: Controls A~J
        self.assertIn("Controls A~J", steps[6]["procedure"])


if __name__ == "__main__":
    unittest.main()
