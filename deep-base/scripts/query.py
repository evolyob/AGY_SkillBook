#!/usr/bin/env python3
"""Terminal FTS5 Knowledge Query & Entity Resolution Engine for deep-base."""

import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys

def load_glossary(wiki_root: Path) -> dict:
    p = wiki_root / "data" / "glossary.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def find_glossary_term(terms: list[dict], query: str) -> dict | None:
    q = query.strip().lower()
    for t in terms:
        names = {t.get("term_zh", "").lower(), t.get("term_en", "").lower(), t.get("abbr", "").lower(), t.get("entity", "").lower()}
        names.update(a.lower() for a in t.get("aliases", []))
        if q in names:
            return t
    return None

def locate_entity_file(wiki_root: Path, term: dict | None, query: str) -> Path | None:
    cands = []
    if term:
        ent = term.get("entity") or term.get("abbr", "").lower()
        if ent:
            cands.append(wiki_root / "wiki" / "entities" / f"{ent}.md")
        if term.get("term_zh"):
            cands.append(wiki_root / "wiki" / "entities" / f"{term["term_zh"]}.md")
    cands.extend([wiki_root / "wiki" / "entities" / f"{query.strip()}.md", wiki_root / "wiki" / "entities" / f"{query.strip().lower()}.md"])
    return next((c for c in cands if c.is_file()), None)

def query_entity(wiki_root: Path, name: str) -> dict:
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
    return re.sub(r"([\u4e00-\u9fa5])", r" \1 ", text)

def index_file(conn: sqlite3.Connection, wiki_root: Path, md_path: Path):
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return
    rel = str(md_path.relative_to(wiki_root))
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    rows = [(rel, p, tokenize_cjk(p)) for p in paras]
    if rows:
        conn.executemany("INSERT INTO fts VALUES (?, ?, ?)", rows)

def build_index(wiki_root: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE VIRTUAL TABLE fts USING fts5(filepath UNINDEXED, paragraph UNINDEXED, content);")
    wiki_dir = wiki_root / "wiki"
    if wiki_dir.exists():
        for md in wiki_dir.glob("**/*.md"):
            index_file(conn, wiki_root, md)
    return conn

def run_filter(conn: sqlite3.Connection, keyword: str, limit: int) -> list[dict]:
    tokens = re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9_\-]+", keyword.strip())
    if not tokens:
        return []
    phrase = "\"" + " ".join(tokens) + "\""
    sql = "SELECT filepath, paragraph, bm25(fts) FROM fts WHERE content MATCH ? ORDER BY bm25(fts) LIMIT ?"
    try:
        rows = list(conn.execute(sql, (phrase, limit)))
        if not rows:
            alt = " OR ".join(f"\"{t}\"" for t in tokens)
            rows = list(conn.execute(sql, (alt, limit)))
    except sqlite3.OperationalError:
        return []
    return [{"file": r[0], "paragraph": r[1], "score": round(r[2], 4)} for r in rows]

def format_filter_markdown(kw: str, results: list[dict]) -> str:
    if not results:
        return f"未找到與「{kw}」相符之全文內容。"
    lines = [f"### 全文檢索結果：`{kw}` (共 {len(results)} 筆)\n"]
    for r in results:
        snip = r["paragraph"] if len(r["paragraph"]) <= 240 else r["paragraph"][:240] + "..."
        lines.append(f"- **來源**：`{r["file"]}` (BM25: {r["score"]})\n  > {snip}\n")
    return "\n".join(lines).strip()

def format_entity_markdown(res: dict) -> str:
    if not res["matched"]:
        return f"未找到與「{res["entity"]}」相符之實體或權威詞彙。"
    t = res.get("term") or {}
    lines = [f"### 實體查詢：{res["entity"]}\n"]
    if t.get("term_zh") or t.get("term_en"):
        lines.append(f"- **標準術語**：{t.get("term_zh", "")} ({t.get("term_en", "")})")
    for k, label in [("abbr", "英文縮寫"), ("aliases", "別名列表"), ("definition", "詞彙定義")]:
        if t.get(k):
            val = ", ".join(t[k]) if isinstance(t[k], list) else t[k]
            lines.append(f"- **{label}**：{val}")
    if res.get("file"):
        lines.append(f"- **實體檔案**：`{res["file"]}`")
    if res.get("content"):
        lines.append(f"\n#### 實體檔案內容\n\n```markdown\n{res["content"].strip()}\n```")
    return "\n".join(lines)

def handle_query(root: Path, args) -> str:
    payload = {}
    if args.entity:
        payload["entity"] = query_entity(root, args.entity)
    if args.keyword:
        conn = build_index(root)
        payload["filter"] = {"query": args.keyword, "results": run_filter(conn, args.keyword, args.limit)}
        conn.close()
    if args.format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    parts = []
    if "entity" in payload:
        parts.append(format_entity_markdown(payload["entity"]))
    if "filter" in payload:
        parts.append(format_filter_markdown(args.keyword, payload["filter"]["results"]))
    return "\n\n".join(parts)

def main():
    p = argparse.ArgumentParser(description="Terminal FTS5 Knowledge Query & Entity Resolution Engine.")
    p.add_argument("wiki_root", nargs="?", default="~/wiki", help="Wiki root directory (default: ~/wiki)")
    p.add_argument("--filter", dest="keyword", help="Full-text keyword search across wiki markdown files")
    p.add_argument("--entity", dest="entity", help="Lookup entity using data/glossary.json alias resolution")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format (default: markdown)")
    p.add_argument("--limit", type=int, default=5, help="Maximum number of results (default: 5)")
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
