#!/usr/bin/env python3
"""
Anti-Blind Mutation PreToolUse Hook (Vibe-Friendly & Stateless)
Prevents blind code mutations when human explicitly calls for a brake or inquires about architecture,
while ensuring normal debugging/vibe coding requests (e.g. 跑版, 報錯, 有bug) proceed smoothly.
"""

import sys
import json
import re
from pathlib import Path

# -----------------------------------------------------------------------------
# Tier 1: Directory Hygiene (Deterministic Path Policy)
# -----------------------------------------------------------------------------
def check_directory_hygiene(target_file: str) -> dict | None:
    if not target_file:
        return None
    # Block writing executable scripts to final delivery directory
    if re.search(r"/agy/download/.*\.(py|sh)$", target_file):
        return {
            "decision": "deny",
            "reason": "【交付目錄防護】~/agy/download/ 為最終交付目錄，嚴禁寫入 .py 或 .sh 腳本！臨時腳本請存放於 scratch/，核心邏輯請整合至既有模組。"
        }
    return None

# -----------------------------------------------------------------------------
# Tier 2: Intent Critique & Brake Check
# -----------------------------------------------------------------------------
def get_last_user_prompt(transcript_path: Path) -> str:
    if not transcript_path.is_file():
        return ""
    try:
        lines = transcript_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "USER_INPUT":
                    content = data.get("content", "")
                    # Extract prompt inside <USER_REQUEST> if present
                    m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                    if m:
                        return m.group(1).strip()
                    return content.strip()
            except Exception:
                continue
    except Exception:
        pass
    return ""

def check_circuit_breaker(transcript_str: str) -> dict | None:
    if not transcript_str:
        return None

    transcript_path = Path(transcript_str)
    user_prompt = get_last_user_prompt(transcript_path)
    if not user_prompt:
        return None

    # Precise Brake & Inquiry patterns with word boundaries (avoids bare wait/stop false positives)
    REGEX_BRAKE_ZH = r"(先(不要動|別動|別改|停下?|確認|理一下|討論)|等一下|等等|停下來|先別改|不要(直接)?改|千萬?別動)"
    REGEX_INQUIRY_ZH = r"(為什麼(要|會)?(改|修壞|變成這樣)|怎麼會(修壞|改壞|變這樣)|你做了什麼|誰叫你改|解釋一下為什麼(要|會)?改)"

    REGEX_BRAKE_EN = r"\b(hold\s+on|wait\s+a\s+(sec|second|minute)|pause\s+for\s+a\s+moment|stop\s+(modifying|changing|editing)|don't\s+(modify|change|edit)|do\s+not\s+(modify|change|edit)|step\s+back|slow\s+down)\b"
    REGEX_INQUIRY_EN = r"\b(why\s+did\s+you\s+(change|modify|do)|why\s+would\s+you\s+(change|modify)|what\s+did\s+you\s+just\s+do|explain\s+why\s+you\s+(changed|modified))\b"

    critique_regex = re.compile(
        f"({REGEX_BRAKE_ZH}|{REGEX_INQUIRY_ZH}|{REGEX_BRAKE_EN}|{REGEX_INQUIRY_EN})",
        re.IGNORECASE
    )

    if critique_regex.search(user_prompt):
        return {
            "decision": "deny",
            "reason": "【防盲改熔斷】偵測到用戶發出暫停指令或質疑架構改動！嚴禁直接修改程式碼。請立即停止寫入檔案，在對話中直接向用戶詳細解釋原因與對齊方案。"
        }

    return None

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        tool_args = payload.get("toolCall", {}).get("args", {})
        target_file = tool_args.get("TargetFile") or tool_args.get("file_path") or ""

        # Check Tier 1
        tier1_result = check_directory_hygiene(target_file)
        if tier1_result:
            print(json.dumps(tier1_result))
            return

        # Check Tier 2
        transcript_path = payload.get("transcriptPath", "")
        tier2_result = check_circuit_breaker(transcript_path)
        if tier2_result:
            print(json.dumps(tier2_result))
            return

    except Exception:
        pass

    # Default: Allow tool execution
    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
