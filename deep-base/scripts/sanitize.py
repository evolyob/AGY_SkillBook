#!/usr/bin/env python3
"""Gate-1 Markdown Syntax Sanitizer & Normalizer for deep-base.

Cleanses legacy HackMD pseudo-wikilinks, unclosed code fences,
platform-specific code fence decorators (e.g. js=, csharp=, js!),
collapsed blockquote tables, and byte-order marks (BOM).
"""

import argparse
import json
import re
import sys
from pathlib import Path


def load_patterns() -> dict:
    cfg_path = Path(__file__).resolve().parent / "config.json"
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8")).get("sanitize", {}).get("patterns", {})
    except Exception:
        return {}


PATS = load_patterns()
PSEUDO_WIKILINK_RX = re.compile(PATS.get("pseudo_wikilink", r"\[\[([^/\\]\n]+/[^/\\]\n]+)\]\]"))
HACKMD_FENCE_RX = re.compile(PATS.get("hackmd_fence", r"^(\s*```+)([a-zA-Z0-9_\-]+)[=!]+.*$"), re.M)
HACKMD_EMPTY_FENCE_RX = re.compile(PATS.get("hackmd_empty_fence", r"^(\s*```+)[=!]+.*$"), re.M)
COLLAPSED_TABLE_SEP_RX = re.compile(PATS.get("collapsed_table_sep", r"^>\s*(\|[\s\-:|]+\|)\s*$"), re.M)
FENCE_LINE_RX = re.compile(PATS.get("fence_line", r"^\s*(```+|~~~+)"))
OPEN_FENCE_LINE_RX = re.compile(PATS.get("open_fence_line", r"^\s*(```+|~~~+)[a-zA-Z0-9_\-]+"))
HR_LINE_RX = re.compile(PATS.get("hr_line", r"^---\s*$"))
SEC_HEADING_RX = re.compile(PATS.get("sec_heading", r"^##\s+\d+\.\s+.*\(來源:|^##\s+關聯實體與擴展防護"))


def sanitize_fences_boundary_aware(lines: list[str]) -> tuple[list[str], int]:
    """Closes unclosed code fences at AST boundaries (consecutive open fences, sections, EOF)."""
    out: list[str] = []
    in_code = False
    open_tag = "```"
    fixed_count = 0

    for i, line in enumerate(lines):
        m = FENCE_LINE_RX.match(line)
        if m:
            raw_fence = m.group(1)[:3]
            is_open_with_lang = bool(OPEN_FENCE_LINE_RX.match(line))

            if not in_code:
                in_code = True
                open_tag = raw_fence
                out.append(line)
            else:
                if is_open_with_lang:
                    # Consecutive open fence encountered without closing previous block
                    out.append(f"{open_tag}\n\n")
                    fixed_count += 1
                    open_tag = raw_fence
                    out.append(line)
                else:
                    # Closing fence
                    in_code = False
                    out.append(line)
        elif not in_code:
            out.append(line)
        else:
            is_h2_sec = bool(SEC_HEADING_RX.match(line))
            is_hr = bool(HR_LINE_RX.match(line.strip()))
            sub = [l for l in lines[i + 1 : i + 6] if l.strip()] if is_hr else []
            is_boundary = is_h2_sec or (is_hr and ((sub and SEC_HEADING_RX.match(sub[0])) or (not sub and i > 20)))

            if is_boundary:
                out.append(f"{open_tag}\n\n")
                fixed_count += 1
                in_code = False
                out.append(line)
            else:
                out.append(line)

    if in_code:
        suffix = "\n" if (out and not out[-1].endswith("\n")) else ""
        out.append(f"{suffix}{open_tag}\n")
        fixed_count += 1

    return out, fixed_count


def sanitize_markdown_text(text: str) -> tuple[str, dict]:
    """Sanitizes raw markdown string and returns (cleaned_text, stats)."""
    stats = {
        "bom_removed": False,
        "pseudo_wikilinks_fixed": 0,
        "fences_normalized": 0,
        "unclosed_fences_fixed": 0,
        "collapsed_tables_fixed": 0,
    }

    if text.startswith("\ufeff"):
        text = text[1:]
        stats["bom_removed"] = True

    def _replace_pseudo_wikilink(m):
        stats["pseudo_wikilinks_fixed"] += 1
        return f"`{m.group(1).strip()}`"

    text = PSEUDO_WIKILINK_RX.sub(_replace_pseudo_wikilink, text)

    def _normalize_fence_with_lang(m):
        stats["fences_normalized"] += 1
        return f"{m.group(1)}{m.group(2)}"

    def _normalize_fence_empty(m):
        stats["fences_normalized"] += 1
        return f"{m.group(1)}"

    text = HACKMD_FENCE_RX.sub(_normalize_fence_with_lang, text)
    text = HACKMD_EMPTY_FENCE_RX.sub(_normalize_fence_empty, text)

    def _fix_collapsed_table(m):
        stats["collapsed_tables_fixed"] += 1
        return m.group(1)

    text = COLLAPSED_TABLE_SEP_RX.sub(_fix_collapsed_table, text)

    lines = text.splitlines(keepends=True)
    fixed_lines, unclosed_fixed = sanitize_fences_boundary_aware(lines)
    if unclosed_fixed > 0:
        stats["unclosed_fences_fixed"] = unclosed_fixed
        text = "".join(fixed_lines)

    return text, stats


def sanitize_file(file_path: Path, fix: bool = False) -> dict:
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, Exception):
        return {"file": str(file_path), "status": "SKIPPED_BINARY"}

    cleaned, stats = sanitize_markdown_text(content)
    total_fixes = sum(stats[k] for k in stats if isinstance(stats[k], int)) + (1 if stats["bom_removed"] else 0)

    if fix and total_fixes > 0:
        file_path.write_text(cleaned, encoding="utf-8")
        stats["status"] = "FIXED"
    else:
        stats["status"] = "DIRTY" if total_fixes > 0 else "CLEAN"

    stats["file"] = str(file_path)
    stats["total_fixes"] = total_fixes
    return stats


def sanitize_path(target_path: Path, fix: bool = False) -> list[dict]:
    if target_path.is_file():
        return [sanitize_file(target_path, fix=fix)] if target_path.suffix.lower() == ".md" else []
    if not target_path.is_dir():
        return []
    md_files = sorted(target_path.rglob("*.md"))
    return [sanitize_file(p, fix=fix) for p in md_files]


def main():
    parser = argparse.ArgumentParser(description="Gate-1 Markdown Syntax Sanitizer.")
    parser.add_argument("target", help="File or directory path to sanitize")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in-place")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(f"Error: Target path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    results = sanitize_path(target, fix=args.fix)
    fixed_or_dirty = [r for r in results if r.get("total_fixes", 0) > 0]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        sys.exit(0 if len(fixed_or_dirty) == 0 or args.fix else 2)

    print(f"=== Sanitize Scan: {target} ===")
    print(f"Scanned files : {len(results)}")
    print(f"Affected files: {len(fixed_or_dirty)}")
    for r in fixed_or_dirty:
        print(f"  - [{r['status']}] {r['file']} (fixes: {r['total_fixes']}, wikilinks: {r['pseudo_wikilinks_fixed']}, fences: {r['fences_normalized']}, unclosed: {r['unclosed_fences_fixed']})")
    sys.exit(0 if len(fixed_or_dirty) == 0 or args.fix else 2)


if __name__ == "__main__":
    main()
