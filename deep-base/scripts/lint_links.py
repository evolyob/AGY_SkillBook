#!/usr/bin/env python3
"""Deterministic Wikilink & Broken Link Scanner for llm-wiki."""

import argparse
import json
import re
import sys
from pathlib import Path

WIKILINK_PATTERN = re.compile(r'\[\[(.*?)\]\]')


def resolve_target(wiki_root: Path, link_text: str) -> Path | None:
    raw_target = link_text.split('|')[0].strip()
    if not raw_target:
        return None

    # Handle explicit extensions or directory references
    candidates = [
        wiki_root / raw_target,
        wiki_root / f"{raw_target}.md",
        wiki_root / "wiki" / "entities" / f"{raw_target}.md",
        wiki_root / "wiki" / "topics" / f"{raw_target}.md",
        wiki_root / "wiki" / "sources" / f"{raw_target}.md",
        wiki_root / "wiki" / "comparisons" / f"{raw_target}.md",
        wiki_root / "wiki" / "synthesis" / f"{raw_target}.md",
        wiki_root / "wiki" / "queries" / f"{raw_target}.md",
    ]

    for cand in candidates:
        if cand.exists():
            return cand
    return None


def scan_wiki(wiki_root: Path) -> dict:
    all_md_files = list(wiki_root.glob("**/*.md"))
    broken_links = []
    incoming_counts = {f.resolve(): 0 for f in all_md_files}
    total_links = 0

    for md_file in all_md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for match in WIKILINK_PATTERN.finditer(content):
            total_links += 1
            target_str = match.group(1)
            resolved = resolve_target(wiki_root, target_str)
            if resolved:
                incoming_counts[resolved.resolve()] = incoming_counts.get(resolved.resolve(), 0) + 1
            else:
                broken_links.append({
                    "source": str(md_file.relative_to(wiki_root)),
                    "target": target_str
                })

    # Find orphan pages (pages with 0 incoming links, excluding index.md, log.md, dotfiles, and raw/ folder)
    orphan_pages = []
    for f, count in incoming_counts.items():
        rel = str(f.relative_to(wiki_root))
        if count == 0 and not (rel.endswith("index.md") or rel.endswith("log.md") or rel.startswith(".") or rel.startswith("raw/")):
            orphan_pages.append(rel)

    return {
        "total_files": len(all_md_files),
        "total_links": total_links,
        "broken_links": broken_links,
        "orphan_pages": orphan_pages
    }


def main():
    parser = argparse.ArgumentParser(description="Scan wiki for broken links and orphan pages.")
    parser.add_argument("wiki_root", nargs="?", default="~/wiki", help="Root path of wiki")
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero if broken links exist")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    wiki_root = Path(args.wiki_root).expanduser().resolve()
    if not wiki_root.exists():
        print(f"Error: Wiki root does not exist: {wiki_root}", file=sys.stderr)
        sys.exit(1)

    results = scan_wiki(wiki_root)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"=== Wiki Health Scan: {wiki_root} ===")
        print(f"Total Markdown Files : {results['total_files']}")
        print(f"Total Wikilinks       : {results['total_links']}")
        print(f"Broken Links Found   : {len(results['broken_links'])}")
        print(f"Orphan Pages Found   : {len(results['orphan_pages'])}")

        if results["broken_links"]:
            print("\n[!] Broken Links:")
            for b in results["broken_links"][:10]:
                print(f"  - {b['source']} -> [[{b['target']}]]")

        if results["orphan_pages"]:
            print("\n[*] Orphan Pages:")
            for o in results["orphan_pages"][:10]:
                print(f"  - {o}")

    if args.strict and results["broken_links"]:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
