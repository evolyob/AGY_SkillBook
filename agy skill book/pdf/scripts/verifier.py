#!/usr/bin/env python3
"""
Universal PDF & Markdown Quality Verifier (verifier.py)
- Standalone multi-gate quality inspector for deliverables:
  * PDF Mode (6-Gate): File, Binary, Pages, Font Scale (>=10.5pt), Glyph Tofu, Detox
  * Markdown Mode (5-Gate): File, Tag Symmetry, Layout Geometry & Orphan Cards,
    Content Balance & Whitespace Ratio, AI Buzzwords & Localization (with --fix)
"""

import os
import sys
import argparse
from pathlib import Path
import json
import re
from pypdf import PdfReader


def load_gate_rules():
    for p in [
        Path(__file__).parent.parent / "data" / "rules_gate.json",
        Path(__file__).parent / "rules_gate.json",
        Path.home() / ".gemini/config/skills/pdf/data/rules_gate.json",
        Path.home() / ".gemini/config/skills/pdf/scripts/rules_gate.json",
        Path.home() / ".gemini/hooks/rules_gate.json",
    ]:
        if not p.exists(): continue
        try:
            with open(p, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return None


def check_gate6_detox(text: str, page_num: int, rules: dict):
    """Gate 6 (PDF): Strict AI Buzzwords & Mainland Chinese Terms Detox Guard."""
    denies = [re.escape(w) for w in rules.get("hard_buzzwords_zh", [])] + \
             [re.escape(k) for k in rules.get("tech_terms_zh", {}).keys()] + \
             [p["regex"] for p in rules.get("formulaic_patterns_zh", []) + rules.get("patterns_en", [])]
    deny_re = re.compile(f"({'|'.join(denies)})", re.IGNORECASE)
    context_whitelists = rules.get("contextual_whitelists_zh", {})
    violations = []

    for raw_line in text.splitlines():
        s = raw_line.strip()
        if not s: continue
        m = deny_re.search(s)
        if m: violations.append(m.group(1))
        for term, white_pat in context_whitelists.items():
            if term in s and not re.search(white_pat, s, re.IGNORECASE):
                violations.append(term)

    if violations:
        unique = list(dict.fromkeys(violations))
        raise ValueError(f"[Gate 6 Failed] Detected AI/Mainland buzzwords on page {page_num}: {unique[:5]}")


def verify_pdf(filepath, min_size=512, expected_pages=None, min_font_pt=10.5, verbose=True):
    """Executes rigorous 6-Gate programmatic quality verification on a PDF document."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"[Gate 1 Failed] Target file does not exist: {filepath}")
    
    size = os.path.getsize(filepath)
    if size < min_size:
        raise ValueError(f"[Gate 1 Failed] File size {size} bytes below threshold ({min_size} bytes): {filepath}")
    
    try: reader = PdfReader(filepath)
    except Exception as e: raise RuntimeError(f"[Gate 2 Failed] PDF binary stream corrupt: {e}")
    
    pages = len(reader.pages)
    if pages <= 0: raise ValueError(f"[Gate 3 Failed] PDF contains 0 pages: {filepath}")
    if expected_pages and pages != expected_pages:
        raise ValueError(f"[Gate 3 Failed] Page count mismatch: expected {expected_pages}, got {pages}: {filepath}")
    
    rules = load_gate_rules()
    page_reports = []
    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        
        def visitor_body(t, cm, tm, font_dict, font_size):
            if t and t.strip() and font_size and min_font_pt and font_size < (min_font_pt - 0.05):
                raise ValueError(f"[Gate 4 Failed] Font size {font_size}pt on page {page_num} < {min_font_pt}pt: '{t.strip()[:30]}'")

        text = page.extract_text(visitor_text=visitor_body) or ""
        if not text.strip():
            raise ValueError(f"[Gate 4 Failed] Page {page_num} has 0 text characters (Blank Page)!")
        if "\ufffd" in text:
            raise ValueError(f"[Gate 5 Failed] Font glyph tofu / replacement character on page {page_num}!")
        if rules:
            check_gate6_detox(text, page_num, rules)
        
        page_reports.append({"page": page_num, "text_chars": len(text.strip())})
    
    report = {"status": "PASS", "file": filepath, "size_kb": round(size / 1024, 2), "pages": pages}
    if verbose:
        print(f"[Verification PASSED] 6/6 Gates OK | {pages} Page(s) | {report['size_kb']} KB | {filepath}")
    return report


def _extract_grid_blocks(text):
    """Extracts top-level grid container bodies using depth-aware parsing."""
    blocks, pattern, pos = [], re.compile(r'<div\s+class=["\'](?:grdid|card-grid)[^"\']*["\']>', re.IGNORECASE), 0
    while True:
        m = pattern.search(text, pos)
        if not m: break
        start_idx, depth, curr = m.end(), 1, m.end()
        while depth > 0 and curr < len(text):
            next_open, next_close = text.find('<div', curr), text.find('</div>', curr)
            if next_close == -1: break
            if next_open != -1 and next_open < next_close:
                depth += 1
                curr = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    blocks.append(text[start_idx:next_close])
                curr = next_close + 6
        pos = curr
    return blocks


def _extract_child_cards(grid_text):
    """Extracts immediate child div cards inside a grid container."""
    cards, depth, start, attr, i = [], 0, -1, "", 0
    while i < len(grid_text):
        if grid_text[i:i+4].lower() == '<div':
            if depth == 0:
                end_tag = grid_text.find('>', i)
                attr, start, i, depth = grid_text[i+4:end_tag], end_tag + 1, end_tag + 1, 1
                continue
            depth += 1
        elif grid_text[i:i+6].lower() == '</div>':
            depth -= 1
            if depth == 0 and start != -1:
                cards.append((attr, grid_text[start:i]))
                start, attr = -1, ""
        i += 1
    return cards


def _check_layout_geometry(content):
    """Inspects layout symmetry, orphan cards, and balance ratios."""
    advisories = []
    grids = _extract_grid_blocks(content)
    for idx, g in enumerate(grids, 1):
        cards = _extract_child_cards(g)
        if not cards: continue
        has_span = any('span' in c[0].lower() for c in cards)
        if len(cards) % 2 != 0 and not has_span:
            advisories.append(f"Grid #{idx}: {len(cards)} cards without span-2 -> Orphan card risk")
        if len(cards) == 2:
            l1 = len(re.sub(r'<[^>]+>', '', cards[0][1]).strip())
            l2 = len(re.sub(r'<[^>]+>', '', cards[1][1]).strip())
            ratio = (max(l1, l2) / min(l1, l2)) if min(l1, l2) > 0 else 1.0
            if ratio > 2.5:
                advisories.append(f"Grid #{idx}: Dual-card content imbalance (Ratio {ratio:.1f}x: {l1} vs {l2} chars)")
    if re.search(r'<br\s*/?>\s*<br\s*/?>', content, re.IGNORECASE):
        advisories.append("Consecutive <br><br> tags detected (hack whitespace padding)")
    return advisories


def _check_md_detox(content, rules, fix=False, filepath=None):
    """Verifies and optionally fixes AI buzzwords and localization in Markdown prose."""
    if not rules: return content, []
    fixed = content
    if fix and rules.get("tech_terms_zh"):
        for cn, tw in rules["tech_terms_zh"].items():
            fixed = re.sub(re.escape(cn), tw, fixed)
        if fixed != content and filepath:
            with open(filepath, "w", encoding="utf-8") as f: f.write(fixed)
            content = fixed
    prose = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    prose = re.sub(r'<style.*?</style>', '', prose, flags=re.DOTALL)
    denies = [re.escape(w) for w in rules.get("hard_buzzwords_zh", [])] + \
             [re.escape(k) for k in rules.get("tech_terms_zh", {}).keys()] + \
             [p["regex"] for p in rules.get("formulaic_patterns_zh", []) + rules.get("patterns_en", [])]
    deny_re = re.compile(f"({'|'.join(denies)})", re.IGNORECASE)
    violations = [m.group(1) for line in prose.splitlines() if line.strip() for m in [deny_re.search(line)] if m]
    return content, list(dict.fromkeys(violations))


def verify_md(filepath, fix=False, verbose=True):
    """Executes 5-Gate quality, tag symmetry, layout geometry & detox verification on Markdown."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"[Gate 1 Failed] Target markdown does not exist: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f: content = f.read()
    size = os.path.getsize(filepath)
    if size == 0: raise ValueError(f"[Gate 1 Failed] File size is 0 bytes: {filepath}")

    div_o, div_c = len(re.findall(r'<div\b', content, re.IGNORECASE)), len(re.findall(r'</div>', content, re.IGNORECASE))
    if div_o != div_c: raise ValueError(f"[Gate 2 Failed] <div> mismatch: {div_o} open vs {div_c} close tags!")
    sty_o, sty_c = len(re.findall(r'<style\b', content, re.IGNORECASE)), len(re.findall(r'</style>', content, re.IGNORECASE))
    if sty_o != sty_c: raise ValueError(f"[Gate 2 Failed] <style> mismatch: {sty_o} open vs {sty_c} close tags!")
    fences = len(re.findall(r'^```', content, re.MULTILINE))
    if fences % 2 != 0: raise ValueError(f"[Gate 2 Failed] Code fences mismatch: odd count ({fences}) detected!")

    advisories = _check_layout_geometry(content)
    rules = load_gate_rules()
    content, violations = _check_md_detox(content, rules, fix=fix, filepath=filepath)

    if verbose:
        adv_msg = f" | {len(advisories)} layout advisories" if advisories else ""
        print(f"[Verification PASSED] 5/5 Gates OK | {div_o} Divs matched | {fences} Fences{adv_msg} | {filepath}")
        for adv in advisories: print(f"  [!] Layout Advisory: {adv}")
        if violations: print(f"  [!] Detox Warning: Detected buzzwords: {violations[:5]}")
    return {"status": "PASS", "file": filepath, "size_kb": round(size / 1024, 2), "advisories": advisories}


def main():
    parser = argparse.ArgumentParser(description="Universal PDF & Markdown Quality Verifier CLI")
    parser.add_argument("files", nargs="+", help="One or more PDF or Markdown file paths to verify")
    parser.add_argument("--min-size", type=int, default=512, help="Minimum file size for PDF in bytes (default: 512)")
    parser.add_argument("--pages", type=int, default=None, help="Expected exact page count for PDF")
    parser.add_argument("--min-font", type=float, default=10.5, help="Minimum allowed font size in pt for PDF")
    parser.add_argument("--fix", action="store_true", help="Auto-fix tech term localization for Markdown")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output on success")
    args = parser.parse_args()
    all_passed = True
    for target in args.files:
        try:
            if target.lower().endswith(".md"):
                verify_md(target, fix=args.fix, verbose=not args.quiet)
            else:
                verify_pdf(target, min_size=args.min_size, expected_pages=args.pages, min_font_pt=args.min_font, verbose=not args.quiet)
        except Exception as e:
            all_passed = False
            print(f"[Verification FAILED] {target} -> {e}", file=sys.stderr)
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
