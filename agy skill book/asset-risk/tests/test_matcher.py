"""Zero-dependency unit tests for matcher.py inference engine."""

import unittest
from pathlib import Path
import sys

# Ensure scripts directory is in path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from matcher import load_parameters, select_pair


class TestMatcherInference(unittest.TestCase):
    """Tests 6 hotzones disambiguation and head-noun weighting."""

    @classmethod
    def setUpClass(cls):
        cls.param_db = load_parameters()
        cls.categories = cls.param_db["categories"]

    def test_hotzone_1_ai_collision(self):
        """Hotzone 1: Disambiguates AI software vs data vs personnel."""
        self.assertEqual(select_pair(self.param_db, "", "", "客服 AI Agent 系統")["category"], "軟體")
        self.assertEqual(select_pair(self.param_db, "", "", "輸入AI之個資")["category"], "資料")
        self.assertEqual(select_pair(self.param_db, "", "", "使用影子AI員工")["category"], "人員")
        self.assertEqual(select_pair(self.param_db, "", "", "企業內部 AI 知識庫")["category"], "資料")

    def test_hotzone_2_contract_paper_vs_digital(self):
        """Hotzone 2: Disambiguates physical paper contracts vs digital files."""
        self.assertEqual(select_pair(self.param_db, "", "", "紙本合約")["category"], "文件")
        self.assertEqual(select_pair(self.param_db, "", "", "電子合約")["category"], "資料")
        self.assertEqual(select_pair(self.param_db, "", "", "電子合約檔")["category"], "資料")
        self.assertEqual(select_pair(self.param_db, "", "", "主管機關紙本來函")["category"], "文件")

    def test_hotzone_3_log_and_backup(self):
        """Hotzone 3: Disambiguates backup host vs backup data."""
        self.assertEqual(select_pair(self.param_db, "", "", "備份伺服器")["category"], "硬體")
        self.assertEqual(select_pair(self.param_db, "", "", "備份主機")["category"], "硬體")
        self.assertEqual(select_pair(self.param_db, "", "", "稽核日誌檔")["category"], "資料")
        self.assertEqual(select_pair(self.param_db, "", "", "離線備份磁帶")["category"], "資料")

    def test_hotzone_4_crypto_hardware_vs_keys(self):
        """Hotzone 4: Disambiguates HSM device vs digital API keys."""
        self.assertEqual(select_pair(self.param_db, "", "", "硬體加密機HSM")["category"], "硬體")
        self.assertEqual(select_pair(self.param_db, "", "", "API金鑰設定檔")["category"], "資料")

    def test_hotzone_5_office_software_vs_data(self):
        """Hotzone 5: Disambiguates Office software vs business reports."""
        self.assertEqual(select_pair(self.param_db, "", "", "Excel應用程式")["category"], "軟體")
        self.assertEqual(select_pair(self.param_db, "", "", "財務Excel報表")["category"], "資料")

    def test_hotzone_6_roles_vs_systems(self):
        """Hotzone 6: Disambiguates personnel vs systems/hardware."""
        self.assertEqual(select_pair(self.param_db, "", "", "外包維運工程師")["category"], "人員")
        self.assertEqual(select_pair(self.param_db, "", "", "API 閘道系統")["category"], "軟體")
        self.assertEqual(select_pair(self.param_db, "", "", "核心網路交換機")["category"], "硬體")

    def test_pii_inventory_evaluation(self):
        """Tests Natural Join PII inventory evaluation and special PII detection."""
        from matcher import load_pii_parameters, evaluate_pii_inventory
        pii_db = load_pii_parameters()
        rec1 = evaluate_pii_inventory(pii_db, "軟體", "應用系統", "會員CRM系統")
        self.assertTrue(rec1["is_pii_applicable"])
        self.assertEqual(rec1["has_special_pii"], "否")
        self.assertEqual(rec1["col_h_format"], "資料庫")

        rec2 = evaluate_pii_inventory(pii_db, "文件", "作業紀錄", "員工健檢報告紙本")
        self.assertTrue(rec2["is_pii_applicable"])
        self.assertEqual(rec2["has_special_pii"], "是")
        self.assertEqual(rec2["col_h_format"], "紙本")

    def test_pii_non_applicable_guard(self):
        """Tests that hardware assets are blocked from PII inventory."""
        from matcher import load_pii_parameters, evaluate_pii_inventory
        pii_db = load_pii_parameters()
        rec = evaluate_pii_inventory(pii_db, "硬體", "網路設備", "核心網路交換機")
        self.assertFalse(rec["is_pii_applicable"])


if __name__ == "__main__":
    unittest.main()
