#!/usr/bin/env python3
"""Terminal FTS5 Knowledge Query & Entity Resolution Engine with RRF for deep-base."""

import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys

WIKILINK_PATTERN = re.compile(r"\[\[(.*?)\]\]")


def load_glossary(wiki_root: Path) -> dict:
    """Load terminology glossary from data/glossary.json."""
    p = wiki_root / "data" / "glossary.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def find_glossary_term(terms: list[dict], query: str) -> dict | None:
    """Resolve an entity by query matching primary names or aliases."""
    q = query.strip().lower()
    for t in terms:
        names = {
            t.get("term_zh", "").lower(),
            t.get("term_en", "").lower(),
            t.get("abbr", "").lower(),
            t.get("entity", "").lower(),
        }
        names.update(a.lower() for a in t.get("aliases", []))
        if q in names:
            return t
    return None


def extract_glossary_targets(term: dict | None, default_target: str) -> list[str]:
    """Extract search target aliases from a glossary term."""
    targets = [default_target]
    if not term:
        return targets
    for k in ["entity", "abbr", "term_zh", "term_en"]:
        val = term.get(k)
        if val:
            targets.append(str(val))
    return targets


def locate_entity_file(wiki_root: Path, term: dict | None, query: str) -> Path | None:
    """Locate markdown document associated with the entity."""
    cands = []
    if term:
        ent = term.get("entity") or term.get("abbr", "").lower()
        if ent:
            cands.append(wiki_root / "wiki" / "entities" / f"{ent}.md")
        if term.get("term_zh"):
            cands.append(wiki_root / "wiki" / "entities" / f"{term['term_zh']}.md")
    cands.extend([
        wiki_root / "wiki" / "entities" / f"{query.strip()}.md",
        wiki_root / "wiki" / "entities" / f"{query.strip().lower()}.md",
    ])
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


def index_file(conn: sqlite3.Connection, wiki_root: Path, md_path: Path):
    """Index markdown file paragraphs into in-memory SQLite FTS5 table."""
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
    """Build in-memory FTS5 virtual table across all wiki markdown files."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE VIRTUAL TABLE fts USING fts5(filepath UNINDEXED, paragraph UNINDEXED, content);")
    wiki_dir = wiki_root / "wiki"
    if wiki_dir.exists():
        for md in wiki_dir.glob("**/*.md"):
            index_file(conn, wiki_root, md)
    return conn


def extract_file_headings(content: str) -> tuple[str, str]:
    """Extract primary heading and first body snippet from markdown text."""
    first_heading = ""
    first_para = ""
    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        if trimmed.startswith("#") and not first_heading:
            first_heading = trimmed.lstrip("#").strip()
            continue
        if not trimmed.startswith("#") and not first_para:
            first_para = trimmed
            if first_heading:
                break
    return first_heading, first_para


def score_title_match(q: str, q_tokens: list[str], stem: str, heading: str, aliases: set[str]) -> int:
    """Deterministic priority heuristic for title and entity matching."""
    if stem in aliases or heading in aliases or stem == q or heading == q:
        return 100
    if stem.startswith(q) or heading.startswith(q):
        return 80
    if q in stem or q in heading:
        return 60
    if q_tokens and all(t in stem or t in heading for t in q_tokens):
        return 40
    if q_tokens and any(t in stem or t in heading for t in q_tokens):
        return 20
    return 0


def find_title_matches(wiki_root: Path, keyword: str, limit: int = 50) -> list[dict]:
    """Identify documents matching keyword in filename stem or heading."""
    wiki_dir = wiki_root / "wiki"
    if not wiki_dir.exists():
        return []

    q = keyword.strip().lower()
    q_tokens = [t.lower() for t in re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9_\-]+", keyword.strip())]
    if not q:
        return []

    glossary = load_glossary(wiki_root)
    term = find_glossary_term(glossary.get("terms", []), keyword)
    aliases: set[str] = set()
    if term:
        for k in ["entity", "abbr", "term_zh", "term_en"]:
            if term.get(k):
                aliases.add(str(term[k]).strip().lower())
        for a in term.get("aliases", []):
            aliases.add(str(a).strip().lower())

    matches = []
    for md in wiki_dir.glob("**/*.md"):
        rel = str(md.relative_to(wiki_root))
        stem = md.stem.lower()
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        heading, first_para = extract_file_headings(content)
        priority = score_title_match(q, q_tokens, stem, heading.lower(), aliases)
        if priority <= 0:
            continue

        snippet = heading if heading else (first_para if first_para else stem)
        matches.append({"file": rel, "paragraph": snippet, "_priority": priority})

    matches.sort(key=lambda x: (-x["_priority"], len(x["file"]), x["file"]))
    for m in matches:
        m.pop("_priority", None)
    return matches[:limit]


def inspect_file_backlinks(lines: list[str], targets: set[str]) -> tuple[int, str]:
    """Count wikilink references to target entities and return first excerpt line."""
    hit_count = 0
    first_hit = ""
    for line in lines:
        trimmed = line.strip()
        links = WIKILINK_PATTERN.findall(trimmed)
        for raw_link in links:
            clean_link = raw_link.split("|")[0].split("#")[0].strip().lower()
            clean_stem = Path(clean_link).stem.lower()
            if clean_link in targets or clean_stem in targets:
                hit_count += 1
                if not first_hit:
                    first_hit = trimmed
    return hit_count, first_hit


def find_backlinks_matches(wiki_root: Path, target_names: list[str], limit: int = 50) -> list[dict]:
    """Locate documents referencing target entities via wikilinks."""
    wiki_dir = wiki_root / "wiki"
    if not wiki_dir.exists() or not target_names:
        return []

    targets = {t.strip().lower() for t in target_names if t.strip()}
    if not targets:
        return []

    matches = []
    seen_files = set()
    for md in sorted(wiki_dir.glob("**/*.md")):
        rel = str(md.relative_to(wiki_root))
        try:
            lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        hit_count, first_hit = inspect_file_backlinks(lines, targets)
        if hit_count <= 0 or rel in seen_files:
            continue

        seen_files.add(rel)
        matches.append({
            "file": rel,
            "paragraph": first_hit or f"[[{next(iter(targets))}]]",
            "_hits": hit_count,
        })

    matches.sort(key=lambda x: (-x["_hits"], x["file"]))
    for m in matches:
        m.pop("_hits", None)
    return matches[:limit]


def reciprocal_rank_fusion(
    result_lists: list[tuple[str, list[dict]]],
    k: int = 60
) -> list[dict]:
    """Merge multiple ranked result lists using Reciprocal Rank Fusion (RRF).

    Formula: score(d) = sum(1.0 / (k + rank(d)))
    """
    rrf_scores: dict[str, float] = {}
    source_ranks: dict[str, dict[str, int]] = {}
    all_retrievals: dict[str, dict] = {}

    for source_name, results in result_lists:
        seen_in_source: set[str] = set()
        for rank, item in enumerate(results, start=1):
            doc_id = item["file"]
            if doc_id in seen_in_source:
                continue
            seen_in_source.add(doc_id)

            if doc_id not in all_retrievals:
                all_retrievals[doc_id] = dict(item)
            else:
                existing = all_retrievals[doc_id]
                if not existing.get("paragraph") and item.get("paragraph"):
                    existing["paragraph"] = item["paragraph"]
                if "bm25_score" in item and "bm25_score" not in existing:
                    existing["bm25_score"] = item["bm25_score"]
                if "score" in item and "score" not in existing:
                    existing["score"] = item["score"]

            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
                source_ranks[doc_id] = {}

            rrf_scores[doc_id] += 1.0 / (k + rank)
            source_ranks[doc_id][f"{source_name}_rank"] = rank

    merged_results = []
    sorted_items = sorted(rrf_scores.items(), key=lambda x: (-x[1], x[0]))
    for rrf_rank, (doc_id, rrf_score) in enumerate(sorted_items, start=1):
        merged_item = dict(all_retrievals[doc_id])
        merged_item["rrf_score"] = round(rrf_score, 6)
        merged_item["rrf_rank"] = rrf_rank
        merged_item["source_ranks"] = source_ranks[doc_id]
        if "score" not in merged_item:
            merged_item["score"] = round(merged_item.get("bm25_score", 0.0), 4)
        merged_results.append(merged_item)

    return merged_results


def run_filter(
    conn: sqlite3.Connection,
    wiki_root: Path,
    keyword: str,
    limit: int = 5,
    enable_backlinks: bool = False,
) -> list[dict]:
    """Execute multi-track retrieval (FTS5 BM25 + Title Match + Backlinks) fused via RRF."""
    tokens = re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9_\-]+", keyword.strip())
    fts_rows = []
    if tokens:
        phrase = "\"" + " ".join(tokens) + "\""
        sql = "SELECT filepath, paragraph, bm25(fts) FROM fts WHERE content MATCH ? ORDER BY bm25(fts) LIMIT ?"
        try:
            fts_rows = list(conn.execute(sql, (phrase, limit * 2)))
            if not fts_rows:
                alt = " OR ".join(f"\"{t}\"" for t in tokens)
                fts_rows = list(conn.execute(sql, (alt, limit * 2)))
        except sqlite3.OperationalError:
            fts_rows = []

    seen_fts_files: set[str] = set()
    fts_candidates = []
    for r in fts_rows:
        if r[0] not in seen_fts_files:
            seen_fts_files.add(r[0])
            fts_candidates.append({
                "file": r[0],
                "paragraph": r[1],
                "score": round(r[2], 4),
                "bm25_score": round(r[2], 4),
            })

    title_candidates = find_title_matches(wiki_root, keyword, limit=limit * 2)

    backlink_candidates = []
    if enable_backlinks:
        glossary = load_glossary(wiki_root)
        term = find_glossary_term(glossary.get("terms", []), keyword)
        targets = extract_glossary_targets(term, keyword)
        for tc in title_candidates[:3]:
            targets.append(Path(tc["file"]).stem)
        backlink_candidates = find_backlinks_matches(wiki_root, targets, limit=limit * 2)

    arms: list[tuple[str, list[dict]]] = []
    if fts_candidates:
        arms.append(("fts5", fts_candidates))
    if title_candidates:
        arms.append(("title", title_candidates))
    if backlink_candidates:
        arms.append(("backlinks", backlink_candidates))

    if not arms:
        return []

    merged = reciprocal_rank_fusion(arms, k=60)
    return merged[:limit]


def format_filter_markdown(kw: str, results: list[dict]) -> str:
    """Format search results into Markdown output with RRF score and sources."""
    if not results:
        return f"未找到與「{kw}」相符之全文內容。"
    lines = [f"### 全文檢索結果：`{kw}` (共 {len(results)} 筆，RRF 融合排序)\n"]
    for r in results:
        snip = r.get("paragraph", "")
        if len(snip) > 240:
            snip = snip[:240] + "..."
        score_info = []
        if "rrf_score" in r:
            score_info.append(f"RRF: {r['rrf_score']:.6f}")
        if "bm25_score" in r:
            score_info.append(f"BM25: {r['bm25_score']}")
        elif "score" in r and r.get("score") != 0.0:
            score_info.append(f"BM25: {r['score']}")
        srcs = [f"{k.replace('_rank', '')}#{v}" for k, v in sorted(r.get("source_ranks", {}).items())]
        if srcs:
            score_info.append(f"來源軌道: {', '.join(srcs)}")
        annot = f" ({'; '.join(score_info)})" if score_info else ""
        lines.append(f"- **來源**：`{r['file']}`{annot}\n  > {snip}\n")
    return "\n".join(lines).strip()


def format_filter_table(kw: str, results: list[dict]) -> str:
    """Format search results into structured Markdown table."""
    if not results:
        return f"未找到與「{kw}」相符之全文內容。"
    lines = [
        f"### 全文檢索結果表格：`{kw}` (共 {len(results)} 筆，RRF 融合排序)\n",
        "| 名次 | 檔案來源 | RRF 分數 | BM25 分數 | 命中軌道 | 內文摘錄 |",
        "|:---:|:---|:---:|:---:|:---|:---|",
    ]
    for r in results:
        rank = r.get("rrf_rank", "-")
        file_path = f"`{r['file']}`"
        rrf = f"{r.get('rrf_score', 0):.6f}" if "rrf_score" in r else "-"
        bm25 = str(r.get("bm25_score", r.get("score", "-")))
        srcs = [f"{k.replace('_rank', '')}#{v}" for k, v in sorted(r.get("source_ranks", {}).items())]
        src_str = ", ".join(srcs) if srcs else "-"
        snip = r.get("paragraph", "").replace("\n", " ").replace("|", "\\|")
        if len(snip) > 80:
            snip = snip[:80] + "..."
        lines.append(f"| {rank} | {file_path} | {rrf} | {bm25} | {src_str} | {snip} |")
    return "\n".join(lines).strip()


def format_entity_markdown(res: dict) -> str:
    """Format entity resolution details into Markdown."""
    if not res["matched"]:
        return f"未找到與「{res['entity']}」相符之實體或權威詞彙。"
    t = res.get("term") or {}
    lines = [f"### 實體查詢：{res['entity']}\n"]
    if t.get("term_zh") or t.get("term_en"):
        lines.append(f"- **標準術語**：{t.get('term_zh', '')} ({t.get('term_en', '')})")
    for k, label in [("abbr", "英文縮寫"), ("aliases", "別名列表"), ("definition", "詞彙定義")]:
        if t.get(k):
            val = ", ".join(t[k]) if isinstance(t[k], list) else t[k]
            lines.append(f"- **{label}**：{val}")
    if res.get("file"):
        lines.append(f"- **實體檔案**：`{res['file']}`")
    if res.get("backlinks"):
        lines.append(f"- **反向連結 (Backlinks)**：{len(res['backlinks'])} 處引用")
        for b in res["backlinks"][:5]:
            lines.append(f"  - `{b['file']}`: > {b['paragraph']}")
    if res.get("content"):
        lines.append(f"\n#### 實體檔案內容\n\n```markdown\n{res['content'].strip()}\n```")
    return "\n".join(lines)


def format_entity_table(res: dict) -> str:
    """Format entity metadata into structured Markdown table."""
    if not res["matched"]:
        return f"未找到與「{res['entity']}」相符之實體或權威詞彙。"
    t = res.get("term") or {}
    lines = [
        f"### 實體查詢表格：`{res['entity']}`\n",
        "| 屬性 | 內容 |",
        "|:---|:---|",
    ]
    if t.get("term_zh") or t.get("term_en"):
        lines.append(f"| 標準術語 | {t.get('term_zh', '')} ({t.get('term_en', '')}) |")
    for k, label in [("abbr", "英文縮寫"), ("aliases", "別名列表"), ("definition", "詞彙定義")]:
        if t.get(k):
            val = ", ".join(t[k]) if isinstance(t[k], list) else t[k]
            lines.append(f"| {label} | {val} |")
    if res.get("file"):
        lines.append(f"| 實體檔案 | `{res['file']}` |")
    if res.get("backlinks"):
        lines.append(f"| 反向連結 | {len(res['backlinks'])} 處引用 |")
    return "\n".join(lines)


def handle_query(root: Path, args) -> str:
    """Dispatch query handlers based on CLI options and output format."""
    payload = {}
    enable_bl = bool(args.backlinks)

    if args.entity:
        ent_res = query_entity(root, args.entity)
        if enable_bl:
            bl_targets = extract_glossary_targets(ent_res.get("term"), args.entity)
            ent_res["backlinks"] = find_backlinks_matches(root, bl_targets, limit=args.limit)
        payload["entity"] = ent_res

    if args.keyword:
        conn = build_index(root)
        filtered = run_filter(conn, root, args.keyword, limit=args.limit, enable_backlinks=enable_bl)
        payload["filter"] = {"query": args.keyword, "results": filtered}
        conn.close()

    if isinstance(args.backlinks, str) and not args.keyword and not args.entity:
        bl_matches = find_backlinks_matches(root, [args.backlinks], limit=args.limit)
        payload["backlinks"] = {"target": args.backlinks, "results": bl_matches}

    if args.format == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)

    if args.format == "table":
        parts = []
        if "entity" in payload:
            parts.append(format_entity_table(payload["entity"]))
        if "filter" in payload:
            parts.append(format_filter_table(args.keyword, payload["filter"]["results"]))
        if "backlinks" in payload:
            parts.append(format_filter_table(args.backlinks, payload["backlinks"]["results"]))
        return "\n\n".join(parts)

    parts = []
    if "entity" in payload:
        parts.append(format_entity_markdown(payload["entity"]))
    if "filter" in payload:
        parts.append(format_filter_markdown(args.keyword, payload["filter"]["results"]))
    if "backlinks" in payload:
        parts.append(format_filter_markdown(args.backlinks, payload["backlinks"]["results"]))
    return "\n\n".join(parts)


def main():
    """CLI entrypoint for deep-base knowledge query engine."""
    p = argparse.ArgumentParser(description="Terminal FTS5 Knowledge Query & Entity Resolution Engine with RRF.")
    p.add_argument("wiki_root", nargs="?", default="~/.gemini/wiki", help="Wiki root directory (default: ~/.gemini/wiki)")
    p.add_argument("--filter", dest="keyword", help="Full-text keyword search across wiki markdown files")
    p.add_argument("--entity", dest="entity", help="Lookup entity using data/glossary.json alias resolution")
    p.add_argument("--backlinks", dest="backlinks", nargs="?", const=True, default=False, help="Enable backlinks graph traversal or specify entity target")
    p.add_argument("--format", choices=["markdown", "json", "table"], default="markdown", help="Output format (default: markdown)")
    p.add_argument("--limit", type=int, default=5, help="Maximum number of results (default: 5)")
    args = p.parse_args()

    if not args.keyword and not args.entity and not args.backlinks:
        p.print_help()
        sys.exit(0)

    root = Path(args.wiki_root).expanduser().resolve()
    if not root.exists():
        print(f"Error: Wiki root does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    print(handle_query(root, args))


if __name__ == "__main__":
    main()
