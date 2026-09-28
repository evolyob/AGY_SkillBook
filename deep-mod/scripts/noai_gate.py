#!/usr/bin/env python3
"""Lightweight Anti-AI Verification Gate for deep-mod (Stdlib only)."""
import argparse, json, re, sys
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "rules_gate.json"
if not RULES_PATH.exists(): RULES_PATH = Path(__file__).resolve().parent / "rules_gate.json"


def scan_content(text: str, filename: str, rules: dict) -> list[str]:
    """Scan natural language prose and aggregate all violations."""
    tech_denies = [
        ((f"(?<!{re.escape(v[:v.index(k)])})" if v[:v.index(k)] else "") +
         re.escape(k) +
         (f"(?!{re.escape(v[v.index(k)+len(k):])})" if v[v.index(k)+len(k):] else ""))
        if k in v else re.escape(k)
        for k, v in rules.get("tech_terms_zh", {}).items()
    ]
    denies = [re.escape(w) for w in rules.get("hard_buzzwords_zh", [])] + tech_denies +              [p["regex"] for p in rules.get("formulaic_patterns_zh", []) + rules.get("patterns_en", [])]
    deny_re = re.compile(f"({'|'.join(denies)})", re.IGNORECASE)
    context_whitelists = rules.get("contextual_whitelists_zh", {})

    violations = []
    in_code, fence = False, ""
    for line_num, raw_line in enumerate(text.splitlines(), start=1):
        s = raw_line.strip()
        if not in_code and (s.startswith("````") or s.startswith("```")):
            in_code, fence = True, ("````" if s.startswith("````") else "```")
            continue
        if in_code and s.startswith(fence):
            in_code = False
            continue
        prose = re.sub(r"`[^`\n]+`", "", raw_line)
        match = deny_re.search(prose)
        if match:
            violations.append(f"  • {filename}:{line_num} 包含「{match.group(1)}」➔ 『{s[:50]}』")
            continue
        for term, white_pat in context_whitelists.items():
            if term in prose and not re.search(white_pat, prose, re.IGNORECASE):
                violations.append(f"  • {filename}:{line_num} 語境不合規「{term}」➔ 『{s[:50]}』")

    return violations


def main() -> None:
    p = argparse.ArgumentParser(description="deep-mod lightweight Anti-AI gate")
    p.add_argument("target", nargs="?", help="Target markdown file or directory to scan")
    p.add_argument("--text", help="Direct text input to scan")
    args = p.parse_args()

    if not RULES_PATH.exists():
        sys.exit(f"Error: Missing rules file at {RULES_PATH}")
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))

    if args.text:
        violations = scan_content(args.text, "direct_text", rules)
        if violations:
            msg = f"[FAIL] 發現 {len(violations)} 處套話或非慣用語，請一次性全部修正：\n" + "\n".join(violations)
            sys.exit(msg)
        print("[PASS] Anti-AI verification passed.")
        return

    if not args.target:
        p.print_usage()
        sys.exit(1)

    tgt = Path(args.target).resolve()
    files = [tgt] if tgt.is_file() else sorted(tgt.rglob("*.md")) if tgt.is_dir() else []
    if not files:
        sys.exit(f"No valid markdown files found in {tgt}")

    all_violations = []
    for f in files:
        errs = scan_content(f.read_text(encoding="utf-8-sig", errors="ignore"), f.name, rules)
        all_violations.extend(errs)

    if all_violations:
        msg = f"[FAIL] 在 {len(files)} 個檔案中發現 {len(all_violations)} 處套話，請一次性重寫：\n" + "\n".join(all_violations)
        sys.exit(msg)

    print(f"[PASS] Anti-AI verification passed ({len(files)} file(s) checked).")


if __name__ == "__main__":
    main()
