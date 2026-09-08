#!/usr/bin/env python3
"""
NoAI-Note First-Mile Detox & Standup Test Tool.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import engine


def load_input(file_path: str = None, direct_text: str = None) -> str:
    if direct_text:
        return direct_text
    if file_path:
        p = Path(file_path)
        if not p.exists():
            sys.exit(f"Error: File not found: {file_path}")
        return p.read_text(encoding="utf-8", errors="replace")
    return sys.stdin.read()


def main():
    p = argparse.ArgumentParser(description="NoAI-Note First-Mile Detox & Standup Test Tool")
    p.add_argument("file", nargs="?", help="Input text or markdown file")
    p.add_argument("--text", help="Direct string input")
    p.add_argument("--mode", choices=["detox", "gate1", "auto"], default="auto")
    p.add_argument("--json", action="store_true", help="Output JSON")

    args = p.parse_args()
    raw = load_input(args.file, args.text)
    if not raw.strip():
        sys.exit("Error: No input text provided.")

    mode = args.mode
    if mode == "auto":
        mode = "gate1" if len(raw.strip().splitlines()) <= 2 and len(raw.strip()) < 120 else "detox"

    if mode == "gate1":
        res = engine.run_gate1(raw)
        print(json.dumps(res, indent=2, ensure_ascii=False) if args.json else engine.report_gate1(res))
        if not res["passed"]: sys.exit(1)
    else:
        res = engine.run_detox(raw)
        print(json.dumps(res, indent=2, ensure_ascii=False) if args.json else engine.report_detox(res))


if __name__ == "__main__":
    main()
