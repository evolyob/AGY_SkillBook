#!/usr/bin/env python3
"""
Universal PDF Quality Verifier (verifier.py)
- Standalone 6-Gate Binary, Typography & Detox Quality Inspector
- Gate 1: File Existence & Size Threshold Check
- Gate 2: PDF Binary Stream & Reader Structure Integrity
- Gate 3: Positive Page Count & Boundary Validation
- Gate 4: Non-Empty Text Layer & Typography Scale Inspection
- Gate 5: Unicode Tofu & Replacement Character Detection (\ufffd Check)
- Gate 6: AI Buzzwords & Mainland Chinese Terms Detox Gate
"""

import os
import sys
import argparse
from pathlib import Path
import json
import re
from pypdf import PdfReader


def load_gate_rules():
    for p in [Path(__file__).parent / "rules_gate.json", Path.home() / ".gemini/hooks/rules_gate.json"]:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f: return json.load(f)
            except Exception: pass
    return None


def check_gate6_detox(text: str, page_num: int, rules: dict):
    """Gate 6: Strict AI Buzzwords & Mainland Chinese Terms Detox Guard."""
    denies = [re.escape(w) for w in rules.get("hard_buzzwords_zh", [])] + \
             [re.escape(k) for k in rules.get("tech_terms_zh", {}).keys()] + \
             [p["regex"] for p in rules.get("formulaic_patterns_zh", []) + rules.get("patterns_en", [])]
    deny_re = re.compile(f"({'|'.join(denies)})", re.IGNORECASE)
    context_whitelists = rules.get("contextual_whitelists_zh", {})
    violations = []

    for raw_line in text.splitlines():
        s = raw_line.strip()
        if not s: continue
        match = deny_re.search(s)
        if match: violations.append(match.group(1))
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
        raise ValueError(f"[Gate 1 Failed] File size {size} bytes is below threshold ({min_size} bytes): {filepath}")
    
    try:
        reader = PdfReader(filepath)
    except Exception as e:
        raise RuntimeError(f"[Gate 2 Failed] PDF binary stream corrupt or unreadable: {e}")
    
    pages = len(reader.pages)
    if pages <= 0:
        raise ValueError(f"[Gate 3 Failed] PDF contains 0 pages: {filepath}")
    if expected_pages is not None and pages != expected_pages:
        raise ValueError(f"[Gate 3 Failed] Page count mismatch: expected {expected_pages} page(s), got {pages}: {filepath}")
    
    rules = load_gate_rules()
    page_reports = []
    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        
        # Gate 4: Typography scale & Non-Empty Text Layer Inspection
        def visitor_body(t, cm, tm, font_dict, font_size):
            if t and t.strip() and font_size and min_font_pt and font_size < (min_font_pt - 0.05):
                raise ValueError(f"[Gate 4 Failed] Typography size {font_size}pt on page {page_num} is below minimum {min_font_pt}pt rule: '{t.strip()[:30]}'")

        try:
            text = page.extract_text(visitor_text=visitor_body) or ""
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"[Gate 4 Failed] Error extracting text layer on page {page_num}: {e}")
        
        text_len = len(text.strip())
        if text_len == 0:
            raise ValueError(f"[Gate 4 Failed] Page {page_num} has 0 text characters (Blank Page)!")
        
        # Gate 5: Unicode tofu detection (\ufffd)
        if "\ufffd" in text:
            raise ValueError(f"[Gate 5 Failed] Font glyph tofu / replacement character detected on page {page_num}!")
        
        # Gate 6: AI Buzzwords & Mainland Chinese Terms Detection
        if rules:
            check_gate6_detox(text, page_num, rules)
        
        page_reports.append({"page": page_num, "text_chars": text_len})
    
    report = {
        "status": "PASS", "file": filepath, "size_bytes": size,
        "size_kb": round(size / 1024, 2), "pages": pages, "page_details": page_reports
    }
    if verbose:
        print(f"[Verification PASSED] 6/6 Gates OK | {pages} Page(s) | {report['size_kb']} KB | {filepath}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Universal PDF Quality Verifier CLI")
    parser.add_argument("pdf_files", nargs="+", help="One or more PDF file paths to verify")
    parser.add_argument("--min-size", type=int, default=512, help="Minimum file size in bytes (default: 512)")
    parser.add_argument("--pages", type=int, default=None, help="Expected exact page count (e.g. 1 for 1-pager)")
    parser.add_argument("--min-font", type=float, default=10.5, help="Minimum allowed font size in pt (default 10.5pt)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output on success")
    
    args = parser.parse_args()
    all_passed = True
    
    for pdf_path in args.pdf_files:
        try:
            verify_pdf(pdf_path, min_size=args.min_size, expected_pages=args.pages, min_font_pt=args.min_font, verbose=not args.quiet)
        except Exception as e:
            all_passed = False
            print(f"[Verification FAILED] {pdf_path} -> {e}", file=sys.stderr)
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
