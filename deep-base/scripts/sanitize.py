#!/usr/bin/env python3
"""Gate-1 Markdown Syntax & Structural Normalizer for deep-base.

Performs boundary-aware code fence isolation, legacy syntax cleansing,
glued heading separation, heading elevation, and plain-text semantic floor auditing.
"""

import argparse
import json
from pathlib import Path
import re
import sys


def load_patterns() -> dict[str, re.Pattern]:
    cfg = Path(__file__).resolve().parent / "config.json"
    raw = json.loads(cfg.read_text(encoding="utf-8")).get("sanitize", {}).get("patterns", {})
    return {k: re.compile(v) for k, v in raw.items()}


RX = load_patterns()


def check_semantic_floor(text: str, stats: dict) -> None:
    b_len = len(text.encode("utf-8"))
    stats["file_bytes"] = b_len
    if stats["h1_count"] == 0 and stats["h2_count"] == 0:
        stats["warnings"].append("NO_HEADINGS: Plain text without any markdown structural headings (# or ##)")
    elif b_len > 2048 and stats["h2_count"] == 0:
        stats["warnings"].append("LOW_HEADING_DENSITY: Document exceeds 2KB without any H2 (##) structural headings")


def sanitize_markdown_text(text: str) -> tuple[str, dict]:
    """Sanitizes raw markdown string with single-pass boundary-aware AST processing."""
    stats = {
        "bom_removed": False, "warnings": [], "h1_count": 0, "h2_count": 0, "h3_count": 0,
        "pseudo_wikilinks_fixed": 0, "fences_normalized": 0, "unclosed_fences_fixed": 0,
        "collapsed_tables_fixed": 0, "pua_symbols_cleaned": 0, "headings_deglued": 0, "headings_elevated": 0,
        "list_items_bulleted": 0,
    }
    if text.startswith("\ufeff"):
        text, stats["bom_removed"] = text.lstrip("\ufeff"), True

    lines, out = text.splitlines(), []
    in_code, open_tag = False, "```"

    for i, raw_line in enumerate(lines):
        line = raw_line.rstrip("\r\n")

        # 1. Code Fence Detection & Normalization
        if m_fence := RX["fence_line"].match(line):
            raw_fence = m_fence.group(1)[:3]
            if m_hk := RX["hackmd_fence"].match(line):
                line, stats["fences_normalized"] = f"{m_hk.group(1)}{m_hk.group(2)}", stats["fences_normalized"] + 1
            elif m_hk_e := RX["hackmd_empty_fence"].match(line):
                line, stats["fences_normalized"] = f"{m_hk_e.group(1)}", stats["fences_normalized"] + 1

            if not in_code:
                in_code, open_tag = True, raw_fence
            elif bool(RX["open_fence_line"].match(line)):
                out.append(f"{open_tag}\n"); stats["unclosed_fences_fixed"] += 1; open_tag = raw_fence
            else:
                in_code = False
            out.append(line)
            continue

        # 2. Inside Code Fence: Guard Boundary Check
        if in_code:
            is_hr = bool(RX["hr_line"].match(line.strip()))
            sub = [l for l in lines[i + 1 : i + 6] if l.strip()] if is_hr else []
            if bool(RX["sec_heading"].match(line)) or (is_hr and ((sub and RX["sec_heading"].match(sub[0])) or (not sub and i > 20))):
                out.append(f"{open_tag}\n"); stats["unclosed_fences_fixed"] += 1; in_code = False
            else:
                out.append(raw_line)
                continue

        # 3. Outside Code Fence: Syntax & Heading Sanitization
        if "\uf097" in line or "\uf0a7" in line:
            line, stats["pua_symbols_cleaned"] = re.sub(r"[\uf097\uf0a7]\s*", "- ", line), stats["pua_symbols_cleaned"] + 1
        if RX["pseudo_wikilink"].search(line):
            line, count = RX["pseudo_wikilink"].subn(r"`\1`", line); stats["pseudo_wikilinks_fixed"] += count
        if m_tbl := RX["collapsed_table_sep"].match(line):
            line, stats["collapsed_tables_fixed"] = m_tbl.group(1), stats["collapsed_tables_fixed"] + 1

        s = line.strip()
        if not s or s.startswith(("#", ">", "|", "---", "***", "- ", "* ", "+ ")):
            stats["h1_count"] += int(s.startswith(("# ", "#\t")))
            stats["h2_count"] += int(s.startswith(("## ", "##\t")))
            stats["h3_count"] += int(s.startswith(("### ", "###\t")))
            out.append(line)
            continue

        # 3a. List Item Normalization: (1) -> - (1)
        if (m_list := RX["list_bracket_num"].match(s)) and not s.endswith(("》", "]", "】")) and not re.search(r"^[（(]\d+[）)][》\]】]", s):
            out.append(f"- ({m_list.group(1)}) {m_list.group(2)}")
            stats["list_items_bulleted"] += 1
            continue

        # 3b. Glued Heading De-gluing
        if m_glued := RX["glued_heading"].match(s):
            num, title, body = m_glued.groups()
            prefix = "###" if num.count(".") >= 2 else "##"
            stats["h2_count"] += int(prefix == "##"); stats["headings_deglued"] += 1
            out.append(f"{prefix} {num} {title}\n\n{body}")
            continue

        # 3c. Heading Elevation
        if not s.endswith(("。", "！", "？", ".", "!", "?", "；", "，", "、", "”", "’")):
            if m_st := RX["statute_section"].match(s):
                out.append(f"## {m_st.group(1)}"); stats["h2_count"] += 1; stats["headings_elevated"] += 1; continue
            if RX["standalone_h2_num"].match(s):
                out.append(f"## {s}"); stats["h2_count"] += 1; stats["headings_elevated"] += 1; continue
            if RX["standalone_h3_num"].match(s):
                out.append(f"### {s}"); stats["h3_count"] += 1; stats["headings_elevated"] += 1; continue
            if (m_cjk_h3 := RX["cjk_h3"].match(s)) and not re.search(r"[，,]", s):
                out.extend(["", f"### {m_cjk_h3.group(1)}"] if out and out[-1] != "" else [f"### {m_cjk_h3.group(1)}"])
                stats["h3_count"] += 1; stats["headings_elevated"] += 1; continue
            if (m_cjk_h4 := RX["cjk_h4"].match(s)) and not re.search(r"^[（(][一二三四五六七八九十]+[）)][》\]】]", s) and not any(k in s for k in ("以下简称", "中增加的", "增设的", "中规定", "即针对")):
                out.extend(["", f"#### {m_cjk_h4.group(1)}"] if out and out[-1] != "" else [f"#### {m_cjk_h4.group(1)}"])
                stats["headings_elevated"] += 1; continue

        out.append(line)

    if in_code:
        out.append(f"{open_tag}"); stats["unclosed_fences_fixed"] += 1

    cleaned_text = "\n".join(out)
    if text.endswith("\n") and not cleaned_text.endswith("\n"):
        cleaned_text += "\n"

    check_semantic_floor(cleaned_text, stats)
    return cleaned_text, stats


def sanitize_file(file_path: Path, fix: bool = False) -> dict:
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, Exception):
        return {"file": str(file_path), "status": "SKIPPED_BINARY", "total_fixes": 0, "warnings": []}

    cleaned, stats = sanitize_markdown_text(content)
    fix_keys = ("pseudo_wikilinks_fixed", "fences_normalized", "unclosed_fences_fixed",
                "collapsed_tables_fixed", "pua_symbols_cleaned", "headings_deglued", "headings_elevated",
                "list_items_bulleted")
    total_fixes = sum(stats[k] for k in fix_keys) + int(stats["bom_removed"])

    if fix and total_fixes > 0:
        file_path.write_text(cleaned, encoding="utf-8"); stats["status"] = "FIXED"
    elif total_fixes > 0:
        stats["status"] = "DIRTY"
    elif stats["warnings"]:
        stats["status"] = "WARN"
    else:
        stats["status"] = "CLEAN"
    stats["file"], stats["total_fixes"] = str(file_path), total_fixes
    return stats


def sanitize_path(target_path: Path, fix: bool = False) -> list[dict]:
    if target_path.is_file():
        return [sanitize_file(target_path, fix=fix)] if target_path.suffix.lower() == ".md" else []
    return [sanitize_file(p, fix=fix) for p in sorted(target_path.rglob("*.md"))] if target_path.is_dir() else []


def main():
    parser = argparse.ArgumentParser(description="Gate-1 Markdown Syntax & Structural Normalizer.")
    parser.add_argument("target", help="File or directory path to sanitize")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in-place")
    parser.add_argument("--strict", action="store_true", help="Exit code 2 on warnings as well as dirty files")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        sys.exit(f"Error: Target path does not exist: {target}")

    results = sanitize_path(target, fix=args.fix)
    dirty = any(r["status"] == "DIRTY" for r in results)
    warns = any(r["status"] == "WARN" for r in results)
    exit_code = 2 if ((not args.fix and dirty) or (args.strict and (dirty or warns))) else 0

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2)); sys.exit(exit_code)

    affected = [r for r in results if r.get("total_fixes", 0) > 0 or r.get("warnings")]
    print(f"=== Sanitize Scan: {target} ===\nScanned files : {len(results)}\nAffected files: {len(affected)}")
    for r in affected:
        fixes = f"fixes: {r['total_fixes']} (elevated: {r.get('headings_elevated', 0)}, bullets: {r.get('list_items_bulleted', 0)})"
        w_str = f" | warnings: {'; '.join(r.get('warnings', []))}" if r.get("warnings") else ""
        print(f"  - [{r['status']}] {r['file']} ({fixes}{w_str})")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
