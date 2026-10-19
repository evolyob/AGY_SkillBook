#!/usr/bin/env python3
"""Terminal FTS5 Knowledge Query & Entity Resolution Engine for deep-base."""

import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys


def load_query_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "config.json"
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8")).get("query", {})
    except Exception:
        return {}


CFG = load_query_config()
DEFAULT_LIMIT = CFG.get("default_limit", 5)
TITLE_WEIGHT = float(CFG.get("title_weight", 10.0))
GLOSSARY_FIELDS = tuple(CFG.get("glossary_fields", ["entity", "abbr", "term_zh", "term_en"]))
ENTITY_LABELS = CFG.get("entity_labels", {"abbr": "Abbreviation", "aliases": "Aliases", "definition": "Definition"})


def load_glossary(wiki_root: Path) -> dict:
    """Load terminology glossary from data/glossary.json."""
    p = wiki_root / "data" / "glossary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def find_glossary_term(terms: list[dict], query: str) -> dict | None:
    """Resolve an entity by query matching primary names or aliases."""
    q = query.strip().lower()
    for t in terms:
        names = {str(t.get(k, "")).lower() for k in GLOSSARY_FIELDS} | {a.lower() for a in t.get("aliases", [])}
        if q in names:
            return t
    return None


def locate_entity_file(wiki_root: Path, term: dict | None, query: str) -> Path | None:
    """Locate markdown document associated with the entity."""
    q = query.strip()
    names = [
        term.get("entity") if term else None,
        term.get("abbr", "").lower() if term else None,
        term.get("term_zh") if term else None,
        q,
        q.lower(),
    ]
    cands = [wiki_root / "wiki" / "entities" / f"{n}.md" for n in names if n]
    return next((c for c in cands if c.is_file()), None)


def query_entity(wiki_root: Path, name: str) -> dict:
    """Lookup entity metadata and corresponding markdown file."""
    glossary = load_glossary(wiki_root)
    term = find_glossary_term(glossary.get("terms", []), name)
    file_path = locate_entity_file(wiki_root, term, name)
    rel_file = str(file_path.relative_to(wiki_root)) if file_path else None
    content = file_path.read_text(encoding="utf-8", errors="replace") if file_path else ""
    return {
        "entity": name,
        "matched": term is not None or file_path is not None,
        "term": term,
        "file": rel_file,
        "content": content,
    }


def tokenize_cjk(text: str) -> str:
    """Insert whitespace between CJK characters for token boundary support in FTS5."""
    return re.sub(r"([\u4e00-\u9fa5])", r" \1 ", text)


def extract_heading(text: str) -> str:
    """Extract first markdown heading from document text."""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
    return ""


def extract_meta_anchors(text: str) -> str:
    m = re.search(r"^alias(?:es)?:\s*\[(.*?)\]", text, re.M)
    return m.group(1).replace(",", " ") if m else ""


def index_file(conn: sqlite3.Connection, wiki_root: Path, md_path: Path):
    """Index markdown file paragraphs and title metadata into SQLite FTS5 table."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return
    rel = str(md_path.relative_to(wiki_root))
    stem = md_path.stem
    anchors = extract_meta_anchors(text)
    title_str = tokenize_cjk(f"{stem} {stem.replace('_', ' ').replace('-', ' ')} {extract_heading(text)} {anchors}")
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    rows = [(rel, p, title_str, tokenize_cjk(p)) for p in paras]
    if rows:
        conn.executemany("INSERT INTO fts VALUES (?, ?, ?, ?)", rows)


def build_index(wiki_root: Path) -> sqlite3.Connection:
    """Build in-memory FTS5 virtual table across all wiki markdown files."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE VIRTUAL TABLE fts USING fts5(filepath UNINDEXED, paragraph UNINDEXED, title, content);")
    wiki_dir = wiki_root / "wiki"
    if wiki_dir.exists():
        for md in wiki_dir.glob("**/*.md"):
            index_file(conn, wiki_root, md)
    return conn


def run_filter(conn: sqlite3.Connection, keyword: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """Execute single-track FTS5 search with native title column BM25 weighting."""
    raw_tokens = re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9_\-]+", keyword.strip())
    if not raw_tokens:
        return []
    sub_tokens = re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9]+", keyword.strip())
    all_tokens = list(dict.fromkeys(raw_tokens + sub_tokens))
    phrase_q = "\"" + " ".join(raw_tokens) + "\""
    or_q = " OR ".join(f"\"{t}\"" for t in all_tokens)
    sql = "SELECT filepath, paragraph, bm25(fts, ?, 1.0) AS score FROM fts WHERE fts MATCH ? ORDER BY score LIMIT ?"
    try:
        rows = list(conn.execute(sql, (TITLE_WEIGHT, phrase_q, limit * 3)))
        if len(rows) < limit:
            rows.extend(conn.execute(sql, (TITLE_WEIGHT, or_q, limit * 3)))
    except sqlite3.OperationalError:
        return []

    seen, results = set(), []
    for filepath, para, score in rows:
        if filepath not in seen:
            seen.add(filepath)
            results.append({"file": filepath, "paragraph": para, "score": round(score, 4)})
            if len(results) >= limit:
                break
    return results


def render_filter_view(kw: str, results: list[dict]) -> str:
    """Render full-text search results as Markdown."""
    if not results:
        return f"No matching full-text content found for '{kw}'."
    lines = [f"### Search Results: `{kw}` ({len(results)} matches)\n"]
    for r in results:
        snip = r.get("paragraph", "")
        snip_str = snip[:240] + "..." if len(snip) > 240 else snip
        lines.append(f"- **Source**: `{r['file']}` (BM25: {r['score']})\n  > {snip_str}\n")
    return "\n".join(lines).strip()


def render_entity_view(res: dict) -> str:
    """Render entity resolution output as Markdown."""
    if not res.get("matched"):
        return f"No entity or authoritative term matched '{res.get('entity', '')}'."
    t = res.get("term") or {}
    lines = [f"### Entity Resolution: {res['entity']}\n"]
    if t.get("term_zh") or t.get("term_en"):
        lines.append(f"- **Standard Term**: {t.get('term_zh', '')} ({t.get('term_en', '')})")
    for k, lbl in ENTITY_LABELS.items():
        if t.get(k):
            val = ", ".join(t[k]) if isinstance(t[k], list) else t[k]
            lines.append(f"- **{lbl}**: {val}")
    if res.get("file"):
        lines.append(f"- **Entity File**: `{res['file']}`")
    if res.get("content"):
        lines.append(f"\n#### Entity File Content\n\n```markdown\n{res['content'].strip()}\n```")
    return "\n".join(lines)


def handle_query(root: Path, args) -> str:
    """Dispatch query handlers based on CLI options and output format."""
    payload = {}
    if args.entity:
        payload["entity"] = query_entity(root, args.entity)
    if args.keyword:
        conn = build_index(root)
        payload["filter"] = {"query": args.keyword, "results": run_filter(conn, args.keyword, limit=args.limit)}
        conn.close()
    if args.format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)

    parts = []
    if "entity" in payload:
        parts.append(render_entity_view(payload["entity"]))
    if "filter" in payload:
        parts.append(render_filter_view(args.keyword, payload["filter"]["results"]))
    return "\n\n".join(parts)


def main():
    """CLI entrypoint for deep-base knowledge query engine."""
    p = argparse.ArgumentParser(description="Terminal FTS5 Knowledge Query & Entity Resolution Engine.")
    p.add_argument("wiki_root", nargs="?", default="~/.gemini/wiki", help="Wiki root directory (default: ~/.gemini/wiki)")
    p.add_argument("--filter", dest="keyword", help="Full-text keyword search across wiki markdown files")
    p.add_argument("--entity", dest="entity", help="Lookup entity using data/glossary.json alias resolution")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format (default: markdown)")
    p.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Maximum number of results (default: {DEFAULT_LIMIT})")
    args = p.parse_args()

    if not args.keyword and not args.entity:
        p.print_help()
        sys.exit(0)

    root = Path(args.wiki_root).expanduser().resolve()
    if not root.exists():
        print(f"Error: Wiki root does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    print(handle_query(root, args))


if __name__ == "__main__":
    main()
