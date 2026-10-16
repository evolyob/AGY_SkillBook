#!/usr/bin/env python3
"""Terminal FTS5 Knowledge Query & Entity Resolution Engine with RRF for deep-base."""

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
RRF_K = CFG.get("rrf_k", 60)
DEFAULT_LIMIT = CFG.get("default_limit", 5)
TITLE_SCORING = CFG.get("title_scoring", {"exact": 100, "prefix": 80, "contains": 60, "all_tokens": 40, "any_token": 20})
GLOSSARY_FIELDS = tuple(CFG.get("glossary_fields", ["entity", "abbr", "term_zh", "term_en"]))
ENTITY_LABELS = CFG.get("entity_labels", {"abbr": "Abbreviation", "aliases": "Aliases", "definition": "Definition"})
FILTER_TABLE_HEADERS = CFG.get("filter_table_headers", ["Rank", "File", "RRF Score", "BM25 Score", "Tracks", "Excerpt"])
WIKILINK_PATTERN = re.compile(r"\[\[(.*?)\]\]")


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


def extract_glossary_targets(term: dict | None, default_target: str) -> list[str]:
    """Extract search target aliases from a glossary term."""
    targets = [default_target]
    if term:
        targets.extend(str(term[k]) for k in GLOSSARY_FIELDS if term.get(k))
    return targets


def locate_entity_file(wiki_root: Path, term: dict | None, query: str) -> Path | None:
    """Locate markdown document associated with the entity."""
    q = query.strip()
    names = [term.get("entity") if term else None, term.get("abbr", "").lower() if term else None, term.get("term_zh") if term else None, q, q.lower()]
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
    heading, para = "", ""
    for line in (line.strip() for line in content.splitlines() if line.strip()):
        if line.startswith("#") and not heading:
            heading = line.lstrip("#").strip()
        elif not line.startswith("#") and not para:
            para = line
            if heading:
                break
    return heading, para


def score_title_match(q: str, q_tokens: list[str], stem: str, heading: str, aliases: set[str]) -> int:
    """Deterministic priority heuristic for title and entity matching."""
    s = TITLE_SCORING
    if stem in aliases or heading in aliases or stem == q or heading == q:
        return s.get("exact", 100)
    if stem.startswith(q) or heading.startswith(q):
        return s.get("prefix", 80)
    if q in stem or q in heading:
        return s.get("contains", 60)
    if q_tokens and all(t in stem or t in heading for t in q_tokens):
        return s.get("all_tokens", 40)
    if q_tokens and any(t in stem or t in heading for t in q_tokens):
        return s.get("any_token", 20)
    return 0


def find_title_matches(wiki_root: Path, keyword: str, limit: int = 50) -> list[dict]:
    """Identify documents matching keyword in filename stem or heading."""
    wiki_dir = wiki_root / "wiki"
    q = keyword.strip().lower()
    q_tokens = [t.lower() for t in re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9_\-]+", keyword.strip())]
    if not wiki_dir.exists() or not q:
        return []

    term = find_glossary_term(load_glossary(wiki_root).get("terms", []), keyword)
    aliases = {str(term[k]).strip().lower() for k in GLOSSARY_FIELDS if term and term.get(k)}
    if term:
        aliases.update(a.strip().lower() for a in term.get("aliases", []))

    matches = []
    for md in wiki_dir.glob("**/*.md"):
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        heading, first_para = extract_file_headings(content)
        priority = score_title_match(q, q_tokens, md.stem.lower(), heading.lower(), aliases)
        if priority > 0:
            snippet = heading or first_para or md.stem
            matches.append({"file": str(md.relative_to(wiki_root)), "paragraph": snippet, "_priority": priority})

    matches.sort(key=lambda x: (-x["_priority"], len(x["file"]), x["file"]))
    for m in matches:
        m.pop("_priority", None)
    return matches[:limit]


def inspect_file_backlinks(lines: list[str], targets: set[str]) -> tuple[int, str]:
    """Count wikilink references to target entities and return first excerpt line."""
    hit_count, first_hit = 0, ""
    for line in lines:
        trimmed = line.strip()
        for raw_link in WIKILINK_PATTERN.findall(trimmed):
            clean = raw_link.split("|")[0].split("#")[0].strip().lower()
            if clean in targets or Path(clean).stem.lower() in targets:
                hit_count += 1
                if not first_hit:
                    first_hit = trimmed
    return hit_count, first_hit


def find_backlinks_matches(wiki_root: Path, target_names: list[str], limit: int = 50) -> list[dict]:
    """Locate documents referencing target entities via wikilinks."""
    wiki_dir = wiki_root / "wiki"
    targets = {t.strip().lower() for t in target_names if t.strip()}
    if not wiki_dir.exists() or not targets:
        return []

    matches, seen_files = [], set()
    for md in sorted(wiki_dir.glob("**/*.md")):
        rel = str(md.relative_to(wiki_root))
        try:
            lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        hit_count, first_hit = inspect_file_backlinks(lines, targets)
        if hit_count > 0 and rel not in seen_files:
            seen_files.add(rel)
            matches.append({"file": rel, "paragraph": first_hit or f"[[{next(iter(targets))}]]", "_hits": hit_count})

    matches.sort(key=lambda x: (-x["_hits"], x["file"]))
    for m in matches:
        m.pop("_hits", None)
    return matches[:limit]


def reciprocal_rank_fusion(result_lists: list[tuple[str, list[dict]]], k: int = RRF_K) -> list[dict]:
    """Merge multiple ranked result lists using Reciprocal Rank Fusion (RRF)."""
    rrf_scores: dict[str, float] = {}
    source_ranks: dict[str, dict[str, int]] = {}
    all_retrievals: dict[str, dict] = {}

    for src, results in result_lists:
        seen: set[str] = set()
        for rank, item in enumerate(results, start=1):
            doc = item["file"]
            if doc in seen:
                continue
            seen.add(doc)
            existing = all_retrievals.setdefault(doc, dict(item))
            if not existing.get("paragraph") and item.get("paragraph"):
                existing["paragraph"] = item["paragraph"]
            if "bm25_score" in item:
                existing.setdefault("bm25_score", item["bm25_score"])
            if "score" in item:
                existing.setdefault("score", item["score"])
            rrf_scores[doc] = rrf_scores.get(doc, 0.0) + 1.0 / (k + rank)
            source_ranks.setdefault(doc, {})[f"{src}_rank"] = rank

    merged = []
    for rank, (doc, score) in enumerate(sorted(rrf_scores.items(), key=lambda x: (-x[1], x[0])), start=1):
        item = dict(all_retrievals[doc])
        item.update({"rrf_score": round(score, 6), "rrf_rank": rank, "source_ranks": source_ranks[doc]})
        item.setdefault("score", round(item.get("bm25_score", 0.0), 4))
        merged.append(item)
    return merged


def run_filter(conn: sqlite3.Connection, wiki_root: Path, keyword: str, limit: int = DEFAULT_LIMIT, enable_backlinks: bool = False) -> list[dict]:
    """Execute multi-track retrieval (FTS5 BM25 + Title Match + Backlinks) fused via RRF."""
    tokens = re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9_\-]+", keyword.strip())
    fts_rows = []
    if tokens:
        phrase = "\"" + " ".join(tokens) + "\""
        sql = "SELECT filepath, paragraph, bm25(fts) FROM fts WHERE content MATCH ? ORDER BY bm25(fts) LIMIT ?"
        try:
            fts_rows = list(conn.execute(sql, (phrase, limit * 2))) or list(conn.execute(sql, (" OR ".join(f"\"{t}\"" for t in tokens), limit * 2)))
        except sqlite3.OperationalError:
            fts_rows = []

    seen: set[str] = set()
    fts_candidates = []
    for r in fts_rows:
        if r[0] not in seen:
            seen.add(r[0])
            fts_candidates.append({"file": r[0], "paragraph": r[1], "score": round(r[2], 4), "bm25_score": round(r[2], 4)})

    title_candidates = find_title_matches(wiki_root, keyword, limit=limit * 2)
    backlink_candidates = []
    if enable_backlinks:
        term = find_glossary_term(load_glossary(wiki_root).get("terms", []), keyword)
        targets = extract_glossary_targets(term, keyword) + [Path(tc["file"]).stem for tc in title_candidates[:3]]
        backlink_candidates = find_backlinks_matches(wiki_root, targets, limit=limit * 2)

    arms = [(src, cands) for src, cands in [("fts5", fts_candidates), ("title", title_candidates), ("backlinks", backlink_candidates)] if cands]
    return reciprocal_rank_fusion(arms, k=RRF_K)[:limit] if arms else []


def render_filter_view(kw: str, results: list[dict], as_table: bool = False) -> str:
    """Render full-text or backlinks search results as Markdown or table."""
    if not results:
        return f"No matching full-text content found for '{kw}'."
    if as_table:
        hdr = " | ".join(FILTER_TABLE_HEADERS)
        lines = [
            f"### Search Results Table: `{kw}` ({len(results)} matches, RRF fused)\n",
            f"| {hdr} |",
            "|:---:|:---|:---:|:---:|:---|:---|",
        ]
        for r in results:
            rank, f_path = r.get("rrf_rank", "-"), f"`{r['file']}`"
            rrf = f"{r.get('rrf_score', 0):.6f}" if "rrf_score" in r else "-"
            bm25 = str(r.get("bm25_score", r.get("score", "-")))
            srcs = ", ".join(f"{k.replace('_rank', '')}#{v}" for k, v in sorted(r.get("source_ranks", {}).items())) or "-"
            snip = r.get("paragraph", "").replace("\n", " ").replace("|", "\\|")[:80]
            lines.append(f"| {rank} | {f_path} | {rrf} | {bm25} | {srcs} | {snip} |")
        return "\n".join(lines).strip()

    lines = [f"### Search Results: `{kw}` ({len(results)} matches, RRF fused)\n"]
    for r in results:
        snip = r.get("paragraph", "")
        snip_str = snip[:240] + "..." if len(snip) > 240 else snip
        info = [f"RRF: {r['rrf_score']:.6f}"] if "rrf_score" in r else []
        if "bm25_score" in r or "score" in r:
            info.append(f"BM25: {r.get('bm25_score', r.get('score'))}")
        srcs = [f"{k.replace('_rank', '')}#{v}" for k, v in sorted(r.get("source_ranks", {}).items())]
        if srcs:
            info.append(f"Tracks: {', '.join(srcs)}")
        annot = f" ({'; '.join(info)})" if info else ""
        lines.append(f"- **Source**: `{r['file']}`{annot}\n  > {snip_str}\n")
    return "\n".join(lines).strip()


def render_entity_view(res: dict, as_table: bool = False) -> str:
    """Render entity resolution output as Markdown or table."""
    if not res.get("matched"):
        return f"No entity or authoritative term matched '{res.get('entity', '')}'."
    t = res.get("term") or {}
    term_str = f"{t.get('term_zh', '')} ({t.get('term_en', '')})" if t.get("term_zh") or t.get("term_en") else ""
    fields = [(lbl, ", ".join(t[k]) if isinstance(t[k], list) else t[k]) for k, lbl in ENTITY_LABELS.items() if t.get(k)]
    if as_table:
        hdr = " | ".join(CFG.get("entity_table_headers", ["Attribute", "Value"]))
        lines = [f"### Entity Resolution Table: `{res['entity']}`\n", f"| {hdr} |", "|:---|:---|"]
        if term_str:
            lines.append(f"| Standard Term | {term_str} |")
        lines.extend(f"| {lbl} | {val} |" for lbl, val in fields)
        if res.get("file"):
            lines.append(f"| Entity File | `{res['file']}` |")
        if res.get("backlinks"):
            lines.append(f"| Backlinks | {len(res['backlinks'])} references |")
        return "\n".join(lines)

    lines = [f"### Entity Resolution: {res['entity']}\n"]
    if term_str:
        lines.append(f"- **Standard Term**: {term_str}")
    lines.extend(f"- **{lbl}**: {val}" for lbl, val in fields)
    if res.get("file"):
        lines.append(f"- **Entity File**: `{res['file']}`")
    if res.get("backlinks"):
        lines.append(f"- **Backlinks**: {len(res['backlinks'])} references")
        lines.extend(f"  - `{b['file']}`: > {b['paragraph']}" for b in res["backlinks"][:5])
    if res.get("content"):
        lines.append(f"\n#### Entity File Content\n\n```markdown\n{res['content'].strip()}\n```")
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

    as_table = (args.format == "table")
    parts = []
    if "entity" in payload:
        parts.append(render_entity_view(payload["entity"], as_table=as_table))
    if "filter" in payload:
        parts.append(render_filter_view(args.keyword, payload["filter"]["results"], as_table=as_table))
    if "backlinks" in payload:
        parts.append(render_filter_view(args.backlinks, payload["backlinks"]["results"], as_table=as_table))
    return "\n\n".join(parts)


def main():
    """CLI entrypoint for deep-base knowledge query engine."""
    p = argparse.ArgumentParser(description="Terminal FTS5 Knowledge Query & Entity Resolution Engine with RRF.")
    p.add_argument("wiki_root", nargs="?", default="~/.gemini/wiki", help="Wiki root directory (default: ~/.gemini/wiki)")
    p.add_argument("--filter", dest="keyword", help="Full-text keyword search across wiki markdown files")
    p.add_argument("--entity", dest="entity", help="Lookup entity using data/glossary.json alias resolution")
    p.add_argument("--backlinks", dest="backlinks", nargs="?", const=True, default=False, help="Enable backlinks graph traversal or specify entity target")
    p.add_argument("--format", choices=["markdown", "json", "table"], default="markdown", help="Output format (default: markdown)")
    p.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Maximum number of results (default: {DEFAULT_LIMIT})")
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
