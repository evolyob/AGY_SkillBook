#!/usr/bin/env python3
"""
NoAI-Note Minimalist Detox Gate (Structure-First, Zero-Whack-a-Mole).
Compliant with Senior Clean Code & Vibe Craft Guide.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine


def strip_code_blocks(text: str) -> str:
    lines, out, in_code, fence = text.splitlines(), [], False, ""
    for line in lines:
        s = line.strip()
        if not in_code:
            if s.startswith("````") or s.startswith("```"):
                in_code, fence = True, ("````" if s.startswith("````") else "```")
            else:
                out.append(line)
        elif s.startswith(fence):
            in_code = False
    return re.sub(r"(`+).*?\1", "", "\n".join(out))


def main():
    p = argparse.ArgumentParser(description="NoAI-Note Minimalist Gate")
    p.add_argument("file", nargs="?", help="Markdown file")
    p.add_argument("--text", help="Direct text")
    p.add_argument("--mode", default="auto", help=argparse.SUPPRESS)
    args = p.parse_args()

    if args.text:
        raw_input = args.text
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            sys.exit(f"Error: File not found: {args.file}")
        raw_input = file_path.read_text(encoding="utf-8", errors="replace")
    elif not sys.stdin.isatty():
        raw_input = sys.stdin.read()
    else:
        p.print_help()
        sys.exit(1)

    if not raw_input.strip():
        sys.exit(0)

    # 1. Strip code blocks and inline code spans to test pure natural language prose
    prose = strip_code_blocks(raw_input)
    detox_result = engine.run_detox(prose)

    # 2. Block hard non-local terminology and simplified characters
    if detox_result.get("simplified"):
        first_sim = detox_result["simplified"][0]
        char = first_sim.get("char", "")
        sys.exit(f"[FAIL] Flagged simplified character: [{char}]\n> Context: 發現簡體字殘留: {char}\n[DIRECTIVE] Rewrite using Traditional Chinese (Taiwan standard).")

    if detox_result.get("forbidden"):
        first_bad = detox_result["forbidden"][0]
        term = first_bad.get("term", "")
        example = first_bad.get("example", "")
        suggest = first_bad.get("suggest", "")
        sys.exit(f"[FAIL] Flagged forbidden term: [{term}] (Suggested: {suggest})\n> Context: {example}\n[DIRECTIVE] Do not replace individual words. Rewrite the surrounding paragraph in standup voice.")

    # 3. Structural density budget inspection (nominalization, dashes, rhetorical cliches)
    if detox_result.get("patterns"):
        first_pattern = detox_result["patterns"][0]
        label = first_pattern.get("label", "")
        rate = first_pattern.get("rate", 0.0)
        budget = first_pattern.get("budget", 0.0)
        advice = first_pattern.get("advice", "")
        example = (first_pattern.get("examples", [""]) or [""])[0]
        sys.exit(f"[FAIL] AI Pattern: [{label}] (Rate: {rate:.1f}/k chars, Limit: {budget})\n> Context: {example}\n[DIRECTIVE] {advice} Rewrite holistically using active verbs.")

    print("[PASS] Standup tone & detox gate passed.")


if __name__ == "__main__":
    main()
