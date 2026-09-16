#!/usr/bin/env python3
"""
Anti-AI PreToolUse Gate (Senior Coding Laws Edition)
- Step 1: Standard library only (sys, json, re, pathlib)
- Step 2: SSOT rules & code block stack stripper
- Step 3: Zero-nesting Guard Clauses & flattened flow
- Step 4: Line-level actionable diagnostics
- Step 5: Subtractive engineering (negative net lines)
"""
import sys, json, re
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent / "rules_gate.json"
TARGET_EXTS = (".md", ".typ", ".tex", ".txt")

def deny(fname: str, line_num: int, word: str, snippet: str) -> None:
    reason = (
        f"[Anti-AI Gate Denied] File {Path(fname).name} line {line_num} contains forbidden AI buzzword or tell '{word}': '{snippet[:60]}'.\n"
        "[DIRECTIVE] Rewrite the entire paragraph using active verbs and direct tone; never perform word-for-word substitution."
    )
    print(json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False))
    sys.exit(0)

def main() -> None:
    try:
        args = json.load(sys.stdin).get("toolCall", {}).get("args", {})
        target = Path(args.get("TargetFile") or args.get("file_path") or "")
        fname = str(target).lower()
    except Exception:
        print(json.dumps({"decision": "allow"})); return

    # Guard Clauses: Scope fence & asset validation
    if not fname.endswith(TARGET_EXTS) or re.search(r"(noai|detox|remediation|template|rule)", fname):
        print(json.dumps({"decision": "allow"})); return

    try:
        rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    except Exception:
        print(json.dumps({"decision": "allow"})); return

    # Context Reconstruction: 局部代換時重組完整文本，杜絕反引號上下文脫節
    text = args.get("CodeContent") or ""
    if not text and target.is_file() and "TargetContent" in args:
        text = target.read_text(encoding="utf-8", errors="ignore").replace(args["TargetContent"], args.get("ReplacementContent", ""), 1)
    text = text or args.get("ReplacementContent") or ""

    denies = [re.escape(w) for w in rules.get("hard_buzzwords_zh", [])] + \
             [re.escape(k) for k in rules.get("tech_terms_zh", {}).keys()] + \
             [p["regex"] for p in rules.get("formulaic_patterns_zh", []) + rules.get("patterns_en", [])]
    deny_re = re.compile(f"({'|'.join(denies)})", re.IGNORECASE)
    context_whitelists = rules.get("contextual_whitelists_zh", {})

    in_code, fence = False, ""
    for line_num, raw_line in enumerate(text.splitlines(), start=1):
        s = raw_line.strip()
        if not in_code:
            if s.startswith("````") or s.startswith("```"):
                in_code, fence = True, ("````" if s.startswith("````") else "```")
                continue
        elif s.startswith(fence):
            in_code = False
            continue

        if in_code or not s:
            continue

        prose = re.sub(r"`[^`\n]+`", "", raw_line)
        match = deny_re.search(prose)
        if match:
            deny(fname, line_num, match.group(1), s)

        for term, white_pat in context_whitelists.items():
            if term in prose and not re.search(white_pat, prose, re.IGNORECASE):
                deny(fname, line_num, term, s)

    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
