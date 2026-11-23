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
        blocks = json.loads((DATA_DIR / "story_blocks.json").read_text(encoding="utf-8"))
        self.assertEqual(contracts["tracking_limits"]["active_character_max"], 20)
        self.assertIn("zhtw_narrative_supplement", deslop)
        valid_ids = set()
        for key in ("role_definitions", "motivation_engines", "flaw_patterns", "relationship_arcs"):
            valid_ids.update(blocks[key].keys())
        for g in blocks["genres"].values():
            for cid in g.get("recommended_character_mix", []):
                self.assertIn(cid, valid_ids)

    def test_tracking_init_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "book"
            proj.mkdir()
            (proj / "outlines").mkdir()
            (proj / "chapters").mkdir()
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

            ctx = proj / "tracking" / "context.md"
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
            (proj / "outlines").mkdir(parents=True)
            (proj / "chapters").mkdir(parents=True)
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
            (proj / "outlines" / "ch_001.md").write_text("# 細綱 第1章\n- 核心事件: 測試\n- 字數目標: 2000字\n", encoding="utf-8")
            (proj / "chapters" / "ch_001.md").write_text("# 第一章 測試\n\n他推開值班室的門，桌上放著一張發黃的登記表。\n", encoding="utf-8")
            (proj / "chapters" / "ch_001_bak_20261121.md").write_text("# 第一章 舊稿\n\n備份檔不應干擾正文定位。\n", encoding="utf-8")
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
            outline = Path(tmp) / "ch_001.md"
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

    def test_book_local_deslop_whitelist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / "book"
            prose_dir = book / "chapters"
            prose_dir.mkdir(parents=True)
            (book / ".deslop-whitelist").write_text("# Domain anchors\n合理隱私期待——界線\n", encoding="utf-8")
            chap = prose_dir / "ch_001.md"
            chap.write_text("# 第一章\n\n律師指著卷宗說出合理隱私期待——界線這六個字。\n", encoding="utf-8")

            r_norm = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "normalize_punctuation.py"), "--check", str(chap)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_norm.returncode, 0, r_norm.stdout + r_norm.stderr)

            r_ai = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_ai_patterns.py"), "--json", str(chap)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_ai.returncode, 0, r_ai.stdout + r_ai.stderr)

    def test_templates_match_script_contracts(self) -> None:
        templates_dir = SKILL_ROOT / "templates"
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "book"
            (proj / "outlines").mkdir(parents=True)
            (proj / "chapters").mkdir(parents=True)
            r_init = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "tracking_commit.py"), "init", "--project", str(proj), "--input", str(templates_dir / "init.json")],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_init.returncode, 0, r_init.stderr)

        r_vol = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "outline_view.py"), "--check", str(templates_dir / "book_outline.md")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(r_vol.returncode, 0, r_vol.stdout + r_vol.stderr)

        r_chap = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check_outline_contract.py"), "--json", str(templates_dir / "chapter_outline.md")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(r_chap.returncode, 0, r_chap.stdout + r_chap.stderr)

    def test_english_path_autodiscovery_and_setting_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "book"
            (proj / "outlines").mkdir(parents=True)
            (proj / "chapters").mkdir(parents=True)
            (proj / "settings" / "world").mkdir(parents=True)
            (proj / "stories" / "ep01").mkdir(parents=True)

            init_json = Path(tmp) / "init.json"
            init_json.write_text(
                json.dumps({
                    "schema_version": 1,
                    "book_title": "PathTest",
                    "last_chapter": 0,
                    "context": {
                        "position": {"scene": "Lab", "volume": "Vol 1", "story_time": "Day 1", "volume_start_chapter": 1},
                        "long_term_constraints": ["Hard limit"],
                    },
                }),
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "tracking_commit.py"), "init", "--project", str(proj), "--input", str(init_json)],
                check=True,
            )

            # 1. check_outline_copy auto-discovers outlines/ch_001.md and stories/ep01/short_outline.md
            outline_1 = proj / "outlines" / "ch_001.md"
            outline_1.write_text(
                "# Chapter 1 Outline: Cold Boot\n\n"
                "- Core Event: Audit `settings/world/missing_rule.md`\n"
                "- Word Count Target: 2000\n"
                "- Unit Position: L1-01\n"
                "- Target Emotion: A -> B\n"
                "- Protagonist Goal / Key Choice: X / Y\n"
                "- Opening Hook: Hook\n"
                "- Payoff: Payoff\n"
                "- Forbidden Reveals: 無\n\n"
                "### Chapter Flow\n- Cause: c\n- Escalation: e\n- Turn: t\n- Climax: cl\n- Ending: en\n\n"
                "### Plot Arrangement\nMain plot.\n\n"
                "### Character Relationships & Presence Order\nHero.\n\n"
                "### Plot Beats\n| # | Plot Beat | Function | Bounds |\n|---|---|---|---|\n"
                "| 1 | Check server room | Setup | 禁：Nothing |\n"
                "| 2 | Find log tamper | Advance | 放：Badge |\n",
                encoding="utf-8",
            )
            chap_1 = proj / "chapters" / "ch_001.md"
            chap_1.write_text("# 第一章\n\n他走進機房檢查日誌。\n", encoding="utf-8")

            r_copy_long = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_outline_copy.py"), str(chap_1)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_copy_long.returncode, 0, r_copy_long.stdout + r_copy_long.stderr)

            short_out = proj / "stories" / "ep01" / "short_outline.md"
            short_out.write_text("# Short Outline\n\n### Plot Beats\n| # | Plot Beat | Function | Bounds |\n|---|---|---|---|\n| 1 | A | Hook | 禁：X |\n", encoding="utf-8")
            short_story = proj / "stories" / "ep01" / "story.md"
            short_story.write_text("# 單元一\n\n完全不同的正文字句。\n", encoding="utf-8")
            r_copy_short = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_outline_copy.py"), str(short_story)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_copy_short.returncode, 0, r_copy_short.stdout + r_copy_short.stderr)

            # 2. check_outline_contract detects missing `settings/world/missing_rule.md` and passes once created
            r_ref_fail = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_outline_contract.py"), "--json", "--project", str(proj), "--chapter", "1"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_ref_fail.returncode, 1)
            (proj / "settings" / "world" / "missing_rule.md").write_text("# Rule\n", encoding="utf-8")
            r_ref_ok = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_outline_contract.py"), "--json", "--project", str(proj), "--chapter", "1"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_ref_ok.returncode, 0, r_ref_ok.stdout + r_ref_ok.stderr)

            # 3. tracking_commit draft extracts chapter_title from outlines/ch_001.md
            r_draft = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "tracking_commit.py"), "draft", "--project", str(proj), "--chapter", "1"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(r_draft.returncode, 0, r_draft.stderr)
            draft_doc = json.loads((proj / ".story" / "work" / "ch_001" / "tracking.json").read_text(encoding="utf-8"))
            self.assertEqual(draft_doc["chapter_title"], "Cold Boot")


if __name__ == "__main__":
    unittest.main()
