#!/usr/bin/env python3
"""SHA-256 Deduplication & Content Cache Manager for llm-wiki."""

import hashlib
import json
import os
import sys
from pathlib import Path


def get_wiki_root(start_path: Path) -> Path:
    current = start_path.resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".wiki-schema.md").exists() or (parent / ".wiki-cache.json").exists():
            return parent
    return Path.home() / "wiki"


def compute_file_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_cache(cache_file: Path) -> dict:
    if not cache_file.exists():
        return {}
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache_file: Path, data: dict) -> None:
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cache.py <check|update|invalidate> <file_path> [summary_page]", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    file_path = Path(sys.argv[2]).expanduser()

    if not file_path.exists():
        print(f"Error: Target file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    wiki_root = get_wiki_root(file_path)
    cache_file = wiki_root / ".wiki-cache.json"
    cache = load_cache(cache_file)
    file_hash = compute_file_hash(file_path)
    rel_path = str(file_path)

    if action == "check":
        if file_hash in cache:
            entry = cache[file_hash]
            print(f"HIT: File already ingested. Summary: {entry.get('summary_page', 'N/A')}")
            sys.exit(0)
        else:
            print("MISS: New file.")
            sys.exit(2)

    elif action == "update":
        summary_page = sys.argv[3] if len(sys.argv) > 3 else ""
        cache[file_hash] = {
            "path": rel_path,
            "summary_page": summary_page,
            "updated_at": os.path.getmtime(file_path)
        }
        save_cache(cache_file, cache)
        print(f"UPDATED: Cached hash {file_hash[:8]} for {file_path.name}")
        sys.exit(0)

    elif action == "invalidate":
        if file_hash in cache:
            del cache[file_hash]
            save_cache(cache_file, cache)
            print(f"INVALIDATED: Removed cache for {file_path.name}")
        else:
            print(f"NOT_FOUND: Hash not in cache.")
        sys.exit(0)

    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
