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
            (proj / "大纲").mkdir()
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

            ctx = proj / "追踪" / "上下文.md"
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
            (proj / "大纲").mkdir(parents=True)
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
            (proj / "大纲" / "细纲_第001章.md").write_text("# 细纲 第1章\n- 核心事件: 测试\n- 字数目标: 2000字\n", encoding="utf-8")
            (proj / "正文" / "第001章_测试.md").write_text("# 第一章 测试\n\n他推开值班室的门，桌上放着一张发黄的登记表。\n", encoding="utf-8")
            r_chk = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "storyctl.py"), "chapter", "check", "--project", str(proj), "--chapter", "1"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_chk.returncode, 0, r_chk.stderr)
            payload = json.loads(r_chk.stdout)
            self.assertEqual(payload["quality"]["status"], "pass", payload)
            self.assertEqual(payload["quality"]["tool_errors"], [], payload)


if __name__ == "__main__":
    unittest.main()
