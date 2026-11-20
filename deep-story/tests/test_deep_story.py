"""End-to-end integration tests for deep-story scripts and JSON configs."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
DATA_DIR = SKILL_ROOT / "data"


class DeepStoryTests(unittest.TestCase):
    """Verify data-driven JSON configs, tracking ledger, and prose checkers."""

    def test_json_configs_valid(self) -> None:
        contracts = json.loads((DATA_DIR / "contracts.json").read_text(encoding="utf-8"))
        deslop = json.loads((DATA_DIR / "deslop_rules.json").read_text(encoding="utf-8"))
        self.assertEqual(contracts["tracking_limits"]["active_character_max"], 20)
        self.assertIn("zhtw_narrative_supplement", deslop)

    def test_tracking_init_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "book"
            proj.mkdir()
            (proj / "大綱").mkdir()
            (proj / "正文").mkdir()
            init_json = Path(tmp) / "init.json"
            init_json.write_text(
                json.dumps({
                    "schema_version": 1,
                    "book_title": "Cyber Law Test",
                    "last_chapter": 0,
                    "context": {
                        "position": {"scene": "Init", "volume": "Vol 1", "story_time": "Day 1", "volume_start_chapter": 1}
                    },
                }),
                encoding="utf-8",
            )
            r_init = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "tracking_commit.py"), "init", "--project", str(proj), "--input", str(init_json)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_init.returncode, 0, r_init.stderr)

            r_check = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "tracking_commit.py"), "check", "--project", str(proj)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_check.returncode, 0, r_check.stderr)

            ctx = proj / "追蹤" / "上下文.md"
            ctx.write_text(ctx.read_text(encoding="utf-8") + "\nManual tamper\n", encoding="utf-8")
            r_tamper = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "tracking_commit.py"), "check", "--project", str(proj)],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(r_tamper.returncode, 0)

    def test_ai_patterns_zhtw_and_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean.md"
            clean.write_text("# 第一章\n\n他推開值班室的門，桌上放著一張發黃的登記表。\n", encoding="utf-8")
            r_clean = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_ai_patterns.py"), "--check", "--json", "--fail-on=blocking", str(clean)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_clean.returncode, 0, r_clean.stdout)

            dirty_zhtw = Path(tmp) / "dirty_zhtw.md"
            dirty_zhtw.write_text("# 第二章\n\n沒人知道，這一切才剛剛開始。\n\n他眼中閃過一絲冷意。\n", encoding="utf-8")
            r_dirty = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_ai_patterns.py"), "--check", "--json", "--fail-on=blocking", str(dirty_zhtw)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_dirty.returncode, 1)
            findings = json.loads(r_dirty.stdout)["findings"]
            self.assertTrue(any(f["type"].startswith("zhtw-") for f in findings), findings)

    def test_degeneration_and_wordcount(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            degen = Path(tmp) / "degen.md"
            degen.write_text("# 第三章\n\n作為一個AI語言模型，我無法繼續創作。\n", encoding="utf-8")
            r_degen = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_degeneration.py"), "--check", "--json", str(degen)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_degen.returncode, 1)

            r_wc = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "storyctl.py"), "wordcount", "measure", "--file", str(degen)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_wc.returncode, 0, r_wc.stdout)

    def test_storyctl_chapter_check_e2e(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "book"
            (proj / "大綱").mkdir(parents=True)
            (proj / "正文").mkdir(parents=True)
            init_json = Path(tmp) / "init.json"
            init_json.write_text(
                json.dumps({
                    "schema_version": 1,
                    "book_title": "E2E Check",
                    "last_chapter": 0,
                    "context": {
                        "position": {"scene": "Init", "volume": "Vol 1", "story_time": "Day 1", "volume_start_chapter": 1}
                    },
                }),
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "tracking_commit.py"), "init", "--project", str(proj), "--input", str(init_json)],
                check=True,
            )
            (proj / "大綱" / "細綱_第001章.md").write_text("# 細綱 第1章\n- 核心事件: 測試\n- 字數目標: 2000字\n", encoding="utf-8")
            (proj / "正文" / "第001章_測試.md").write_text("# 第一章 測試\n\n他推開值班室的門，桌上放着一張發黃的登記表。\n", encoding="utf-8")
            r_chk = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "storyctl.py"), "chapter", "check", "--project", str(proj), "--chapter", "1"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_chk.returncode, 0, r_chk.stderr)
            payload = json.loads(r_chk.stdout)
            self.assertEqual(payload["quality"]["status"], "pass", payload)
            self.assertEqual(payload["quality"]["tool_errors"], [], payload)

    def test_outline_contract_zhtw_and_en_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outline = Path(tmp) / "細綱_第001章.md"
            outline.write_text(
                "# 第1章 細綱\n\n"
                "- Core Event: 測試系統登錄與取證\n"
                "- Word Count Target: 2000\n"
                "- Unit Position: L1-01\n"
                "- Target Emotion: 緊張 -> 警覺\n"
                "- Protagonist Goal / Key Choice: 保留原始日誌 / 是否通報資安長\n"
                "- Opening Hook: 凌晨兩點異常登入告警\n"
                "- Payoff: 鎖定內部帳號異常\n"
                "- Forbidden Reveals: 無\n\n"
                "### Chapter Flow\n"
                "- Cause: 發現異地登入\n"
                "- Escalation: 備份被試圖刪除\n"
                "- Turn: 啟動 WORM 唯讀鎖定\n"
                "- Climax: 抓出跳板 IP\n"
                "- Ending: 螢幕彈出第二封勒索信\n\n"
                "### Plot Arrangement\n主線推進。\n\n"
                "### Character Relationships & Presence Order\n資安長與工程師。\n\n"
                "### Plot Beats\n"
                "| Beat | Action | Function | Bounds |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| 1 | 檢視登入紀錄 | 鋪墊 | 禁：不揭內鬼姓名 |\n"
                "| 2 | 鎖定 WORM 日誌 | 推進 | 放：可寫機房冷氣聲 |\n",
                encoding="utf-8",
            )
            r = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_outline_contract.py"), "--json", str(outline)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
