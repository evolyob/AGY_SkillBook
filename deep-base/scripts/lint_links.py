#!/usr/bin/env python3
"""Deterministic Wikilink & Health Scanner for deep-base."""

import argparse
import json
import re
import sys
from pathlib import Path

def load_linter_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "config.json"
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8")).get("linter", {})
    except Exception:
        return {}


CFG = load_linter_config()
MAX_FILE_SIZE = CFG.get("max_file_size_bytes", 46080)
PATTERNS = CFG.get("patterns", {})
WIKILINK_PATTERN = re.compile(PATTERNS.get("wikilink", r"\[\[(.*?)\]\]"))
SEP_CELL_RX = re.compile(PATTERNS.get("sep_cell", r"\|\s*:?-{2,}:?\s*\|"))
PURE_SEP_RX = re.compile(PATTERNS.get("pure_sep", r"^\s*\|?[\s:|-]+\|?\s*$"))
FENCE_RX = re.compile(PATTERNS.get("fence", r"^\s*(```|~~~)"))
EXEMPT_FILES = tuple(CFG.get("exempt_files", ["index.md", "log.md"]))
EXEMPT_PREFIXES = tuple(CFG.get("exempt_prefixes", [".", "raw/"]))
CATEGORIES = CFG.get("categories", [])



def strip_markdown_code(content: str) -> str:
    """Filter out fenced code blocks and inline code spans."""
    content = re.sub(r'(?:```[\s\S]*?```|~~~[\s\S]*?~~~)', '', content)
    return re.sub(r'`[^`\n]*?`', '', content)


def resolve_target(wiki_root: Path, link_text: str) -> Path | None:
    raw_target = link_text.split('|')[0].split('#')[0].strip()
    if not raw_target:
        return None
    subdirs = ["entities", "topics", "sources", "comparisons", "synthesis", "queries"]
    candidates = [wiki_root / raw_target, wiki_root / f"{raw_target}.md"] + [
        wiki_root / "wiki" / d / f"{raw_target}.md" for d in subdirs
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def extract_raw_source_path(content: str) -> str | None:
    fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        m = re.search(r'^(?:source_path|raw_path|raw_file|Raw File):\s*["\']?([^"\'\n\r]+)[\'"]?', fm_match.group(1), re.M | re.I)
        if m:
            return m.group(1).strip()
    m = re.search(r'[-*]\s*\*{0,2}(?:Raw File|source_path|Raw Path)\*{0,2}:\s*[`"\']?([^`"\'\n\r]+)[`"\']?', content, re.I)
    return m.group(1).strip() if m else None


def resolve_raw_file(wiki_root: Path, source_md: Path, raw_path_str: str) -> Path | None:
    raw_path = Path(raw_path_str.strip())
    candidates = [raw_path, wiki_root / raw_path, source_md.parent / raw_path, wiki_root / "raw" / raw_path, wiki_root / "raw" / raw_path.name]
    return next((c for c in candidates if c.is_file()), None)


def extract_quotes(content: str) -> list[str]:
    cleaned = strip_markdown_code(content)
    has_sec = bool(re.search(r'^#{1,6}\s+.*(?:quote|引文|citation|notable).*$', cleaned, re.M | re.I))
    quotes, in_sec = [], False
    for line in cleaned.splitlines():
        trimmed = line.strip()
        if trimmed.startswith('#'):
            in_sec = bool(re.search(r'^#{1,6}\s+.*(?:quote|引文|citation|notable).*$', trimmed, re.I))
            continue
        if not trimmed.startswith('>') or trimmed.startswith('>[!'):
            continue
        raw_quote = trimmed.lstrip('>').strip()
        is_quoted = bool(re.match(r'^["\'“”].+?["\'“”]$', raw_quote))
        if has_sec and not (in_sec or is_quoted):
            continue
        cleaned_quote = raw_quote.strip('"\'“”').strip()
        if cleaned_quote:
            quotes.append(cleaned_quote)
    return quotes


def verify_quotes_in_sources(wiki_root: Path) -> list[dict]:
    sources_dir = wiki_root / "wiki" / "sources"
    if not sources_dir.exists():
        return []
    unverified, seen = [], set()
    for sf in sorted(sources_dir.rglob("*.md")):
        if sf.resolve() in seen:
            continue
        seen.add(sf.resolve())
        try:
            content = sf.read_text(encoding="utf-8")
        except Exception:
            continue
        quotes = extract_quotes(content)
        if not quotes:
            continue
        raw_path_str = extract_raw_source_path(content)
        resolved_raw = resolve_raw_file(wiki_root, sf, raw_path_str) if raw_path_str else None
        rel_sf = str(sf.relative_to(wiki_root))
        if not raw_path_str or not resolved_raw:
            raw_label = raw_path_str or "MISSING_METADATA"
            for q in quotes:
                unverified.append({"source": rel_sf, "raw_file": raw_label, "quote": q})
            continue
        try:
            raw_text = resolved_raw.read_text(encoding="utf-8", errors="replace")
        except Exception:
            raw_text = ""
        rel_raw = str(resolved_raw.relative_to(wiki_root))
        for q in quotes:
            if q not in raw_text:
                unverified.append({"source": rel_sf, "raw_file": rel_raw, "quote": q})
    return unverified


def verify_markdown_structure(content: str) -> dict:
    """Verifies markdown structural integrity (collapsed tables and unbalanced code fences)."""
    lines = content.splitlines()
    fence_matches = 0
    collapsed_tables = []
    in_fence = False

    for idx, line in enumerate(lines, 1):
        if FENCE_RX.match(line):
            fence_matches += 1
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if SEP_CELL_RX.search(line) and not PURE_SEP_RX.match(line):
            collapsed_tables.append({"line": idx, "content": line.strip()})

    unbalanced_fences = (fence_matches % 2 != 0)
    return {
        "valid": len(collapsed_tables) == 0 and not unbalanced_fences,
        "collapsed_tables": collapsed_tables,
        "unbalanced_fences": unbalanced_fences,
        "fence_count": fence_matches,
    }


def collect_structural_issues(rel_file: str, struct: dict) -> list[dict]:
    """Format structural failures into diagnostic issue records."""
    if struct.get("valid", True):
        return []
    issues = []
    if struct.get("unbalanced_fences"):
        issues.append({
            "file": rel_file,
            "type": "unbalanced_fences",
            "detail": f"Unbalanced code fences (total fence marks: {struct.get('fence_count', 0)})",
        })
    for ct in struct.get("collapsed_tables", []):
        issues.append({
            "file": rel_file,
            "type": "collapsed_table",
            "line": ct["line"],
            "detail": f"Collapsed table separator at line {ct['line']}: {ct['content']}",
        })
    return issues


def scan_wiki(wiki_root: Path, verify_quotes: bool = False, verify_structure: bool = True) -> dict:
    if wiki_root.is_file():
        all_md_files = [wiki_root]
        base_dir = wiki_root.parent
    else:
        all_md_files = sorted(wiki_root.rglob("*.md"))
        base_dir = wiki_root

    broken_links, oversized_files, structural_issues = [], [], []
    incoming_counts = {f.resolve(): 0 for f in all_md_files}
    total_links = 0

    for md_file in all_md_files:
        try:
            rel_file = str(md_file.relative_to(base_dir))
        except ValueError:
            rel_file = md_file.name

        try:
            st_size = md_file.stat().st_size
            if st_size > MAX_FILE_SIZE:
                oversized_files.append({"file": rel_file, "size": st_size})
        except Exception:
            pass

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        if verify_structure:
            struct = verify_markdown_structure(content)
            structural_issues.extend(collect_structural_issues(rel_file, struct))

        filtered = strip_markdown_code(content)
        for match in WIKILINK_PATTERN.finditer(filtered):
            total_links += 1
            target_str = match.group(1)
            resolved = resolve_target(wiki_root if wiki_root.is_dir() else base_dir, target_str)
            if resolved:
                incoming_counts[resolved.resolve()] = incoming_counts.get(resolved.resolve(), 0) + 1
            else:
                broken_links.append({"source": rel_file, "target": target_str})

    orphan_pages = []
    if wiki_root.is_dir():
        for f, count in incoming_counts.items():
            rel = str(f.relative_to(wiki_root))
            is_exempt = rel.endswith(EXEMPT_FILES) or rel.startswith(EXEMPT_PREFIXES)
            if count == 0 and not is_exempt:
                orphan_pages.append(rel)

    results = {
        "total_files": len(all_md_files),
        "total_links": total_links,
        "broken_links": broken_links,
        "orphan_pages": orphan_pages,
        "oversized_files": oversized_files,
        "structural_issues": structural_issues,
    }
    if verify_quotes and wiki_root.is_dir():
        results["unverified_quotes"] = verify_quotes_in_sources(wiki_root)
    return results


def find_backlinks(wiki_root: Path, entity_name: str) -> list[dict]:
    clean_target = entity_name.split('|')[0].split('#')[0].strip()
    target_stem = Path(clean_target).stem.lower()
    resolved_target = resolve_target(wiki_root, clean_target)
    target_path = resolved_target.resolve() if resolved_target else None

    backlinks = []
    for md_file in sorted(wiki_root.rglob("*.md")):
        if target_path and md_file.resolve() == target_path:
            continue
        try:
            lines = md_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        for idx, line in enumerate(lines, 1):
            cleaned_line = strip_markdown_code(line)
            matches = WIKILINK_PATTERN.findall(cleaned_line)
            matched = False
            for m in matches:
                link_clean = m.split('|')[0].split('#')[0].strip()
                res = resolve_target(wiki_root, link_clean)
                if (target_path and res and res.resolve() == target_path) or Path(link_clean).stem.lower() == target_stem:
                    matched = True
                    break
            if matched:
                backlinks.append({"source": str(md_file.relative_to(wiki_root)), "line": idx, "context": line.strip()})
    return backlinks


def main():
    parser = argparse.ArgumentParser(description="Deterministic Wikilink & Health Scanner for deep-base.")
    parser.add_argument("wiki_root", nargs="?", default="~/.gemini/wiki", help="Root path of wiki or markdown file")
    parser.add_argument("--strict", action="store_true", help="Exit code 2 on broken links, oversized files, structural issues, or unverified quotes")
    parser.add_argument("--verify-quotes", action="store_true", help="Verify quotes in wiki/sources/*.md against raw files")
    parser.add_argument("--verify-structure", dest="verify_structure", action="store_true", default=True, help="Verify markdown structural integrity (collapsed tables, unbalanced code fences; default: True)")
    parser.add_argument("--no-verify-structure", dest="verify_structure", action="store_false", help="Disable markdown structural integrity checks")
    parser.add_argument("--backlinks", metavar="ENTITY", help="List all markdown files referencing the entity with context excerpts")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    wiki_root = Path(args.wiki_root).expanduser().resolve()
    if not wiki_root.exists():
        sys.exit(f"Error: Target path does not exist: {wiki_root}")

    if args.backlinks:
        bl = find_backlinks(wiki_root, args.backlinks)
        if args.json:
            print(json.dumps({"entity": args.backlinks, "backlinks": bl}, ensure_ascii=False, indent=2))
        else:
            print(f"=== Backlinks for '{args.backlinks}': {wiki_root} ===")
            print(f"Total References Found: {len(bl)}")
            for b in bl:
                print(f"  - {b['source']}:{b['line']}: {b['context']}")
        sys.exit(0)

    results = scan_wiki(wiki_root, verify_quotes=args.verify_quotes, verify_structure=args.verify_structure)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"=== Wiki Health Scan: {wiki_root} ===")
        print(f"Total Markdown Files : {results['total_files']}")
        print(f"Total Wikilinks       : {results['total_links']}")
        print(f"Broken Links Found   : {len(results['broken_links'])}")
        print(f"Orphan Pages Found   : {len(results['orphan_pages'])}")
        print(f"Oversized Files (>45K): {len(results['oversized_files'])}")
        if args.verify_structure:
            print(f"Structural Issues    : {len(results['structural_issues'])}")
        if args.verify_quotes:
            print(f"Unverified Quotes    : {len(results.get('unverified_quotes', []))}")

        categories = [
            ("Structural Issues", results.get("structural_issues", []), lambda i: f"{i['file']}:{i.get('line', '')} [{i['type']}]: {i['detail']}"),
            ("Broken Links", results["broken_links"], lambda b: f"{b['source']} -> [[{b['target']}]]"),
            ("Oversized Files (>45KB)", results["oversized_files"], lambda o: f"{o['file']} ({o['size']} bytes)"),
            ("Orphan Pages", results["orphan_pages"], lambda op: str(op)),
            ("Unverified Quotes", results.get("unverified_quotes", []), lambda u: f"{u['source']} (Raw: {u['raw_file']}) -> \"{u['quote']}\""),
        ]
        for header, items, fmt in categories:
            if items:
                print(f"\n[!] {header}:")
                for it in items[:10]:
                    print(f"  - {fmt(it)}")

    if args.strict:
        has_errors = (
            bool(results["broken_links"])
            or bool(results["oversized_files"])
            or bool(results.get("structural_issues"))
            or (args.verify_quotes and bool(results.get("unverified_quotes")))
        )
        if has_errors:
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

