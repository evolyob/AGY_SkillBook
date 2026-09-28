#!/usr/bin/env python3
"""NoAI-Note Minimalist Detox Gate (Structure-First, Zero-Whack-a-Mole)."""
import argparse, re, sys
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

    raw = args.text or (Path(args.file).read_text(encoding="utf-8", errors="replace") if args.file else sys.stdin.read())
    if not raw.strip():
        sys.exit(0)

    # 1. Strip code blocks and inline code spans to test pure natural language prose
    prose = strip_code_blocks(raw)
    kb, res = max(len(prose) / 1000.0, 0.1), engine.run_detox(prose)

    # 2. Block hard non-local terminology, empty buzzwords, and simplified characters
    bad = [m for m in res.get("mainland_terms", []) if m.get("category") != "需看語境"]
    if res.get("simplified") or bad or res.get("buzzwords"):
        tgt = bad[0] if bad else ((res.get("buzzwords") or res.get("simplified") or [{}])[0])
        lbl = tgt.get("term") or tgt.get("char") or tgt.get("label", "Simplified character")
        ex = tgt.get("example") or (tgt.get("examples", [""])[0] if "examples" in tgt else "")
        sys.exit(f"[FAIL] Flagged term/buzzword: [{lbl}]\n> Context: {ex}\n[DIRECTIVE] Do not replace individual words. Rewrite the surrounding paragraph in standup voice.")

    # 3. Structural density budget inspection (nominalization, dashes, rhetorical cliches)
    rules = engine.load_rules(res.get("lang", "zhtw"))
    pat_key = "generic_patterns" if res.get("lang") == "en" else "patterns"
    flags = re.I if res.get("lang") == "en" else 0
    for p_rule in rules.get(pat_key, []):
        cnt = len(re.findall(p_rule["regex"], prose, flags))
        rate, budget = cnt / kb, p_rule.get("budget", 0.0)
        if cnt > 0 and rate > budget:
            ex = (engine.extract_context(prose, p_rule["regex"], limit=1) or [""])[0]
            sys.exit(f"[FAIL] AI Pattern: [{p_rule['label']}] (Rate: {rate:.1f}/k chars, Limit: {budget})\n> Context: {ex}\n[DIRECTIVE] {p_rule.get('advice', '')} Rewrite holistically using active verbs.")

    print("[PASS] Standup tone & detox gate passed.")


if __name__ == "__main__":
    main()
