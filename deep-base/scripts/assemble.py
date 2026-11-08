#!/usr/bin/env python3
"""Knowledge Base Scaffolding & Assembly Engine for deep-base.

Supports scaffolding initialization, index synchronization, and semantic chunking.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import unicodedata


def default_wiki_path() -> str:
    return "~/wiki"


def load_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "config.json"
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8")).get("scaffold", {})
    except Exception:
        return {}


CFG = load_config()


def init_knowledge_base(target_path: Path):
    target = target_path.expanduser().resolve()
    print(f"Initializing Knowledge Base at: {target}")

    dirs = [target / d for d in CFG.get("directories", [
        "raw/articles", "raw/notes", "raw/notes/archive", "raw/pdfs", "raw/assets",
        "wiki/entities", "wiki/topics", "wiki/sources", "wiki/comparisons",
        "wiki/synthesis", "wiki/queries", "wiki/archive", "templates", "data"
    ])]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    home_str = str(Path.home())
    display_target = str(target).replace(home_str, "~", 1) if str(target).startswith(home_str) else str(target)

    init_files = {
        target / ".wiki-schema.md": (
            "# Wiki Schema & Governance\n- Language: en (English-first synthesis; zh-TW glossary & query bridging) | Version: 1.0.0 | Methodology: Andrej Karpathy LLM Wiki Architecture\n"
            "- Boundary: Local-first Markdown (Layer 1: raw/ Immutable Sources, Layer 2: wiki/ Synthesized Knowledge)\n\n"
            "## Confidence Labels & Gate-1 Hygiene\n- Labels: [EXTRACTED] Source extraction, [INFERRED] LLM deduction, [AMBIGUOUS] Conflicting, [UNVERIFIED] External.\n"
            "- Hygiene: Scrub PII mobile numbers, live credentials (sk-, ghp-, AKIA-), and normalize user paths to ~/ at Gate 1.\n"
        ),
        target / "index.md": f"# Personal Knowledge Base Index\n\n> Local-first personal compounding knowledge base initialized on {today}.\n\n## Navigation\n- [[wiki/entities/]], [[wiki/topics/]], [[wiki/sources/]], [[wiki/comparisons/]], [[wiki/synthesis/]], [[wiki/queries/]]\n\n## Recent Entries\n",
        target / "log.md": f"# Wiki Operation Log\n- {today}: Initialized personal knowledge base structure at {display_target}.\n",
        target / "data" / "glossary.json": json.dumps({"version": "1.0.0", "last_updated": today, "terms": CFG.get("initial_terms", [])}, ensure_ascii=False, indent=2) + "\n",
    }
    for p, text in init_files.items():
        if not p.exists():
            p.write_text(text, encoding="utf-8")
    print(f"Knowledge base successfully initialized at {target}")


def parse_entity_metadata(e_path: Path, meta_cache: dict) -> tuple[list[str], str]:
    meta = meta_cache.get(e_path.stem, {})
    tags, context = meta.get("tags", []), meta.get("context", "")
    if context and tags:
        return tags, context
    if not e_path.exists():
        return tags or ["tech"], context or e_path.stem
    e_text = e_path.read_text(encoding="utf-8")
    ctx_m = re.search(r'context:\s*"([^"]+)"', e_text)
    context = ctx_m.group(1) if ctx_m else (re.search(r"^>\s*([^\n]+)", e_text, re.M).group(1) if re.search(r"^>\s*([^\n]+)", e_text, re.M) else e_path.stem)
    if not tags:
        tag_m = re.search(r"tags:\s*\[([^\]]+)\]", e_text)
        tags = [t.strip().strip("'\"") for t in tag_m.group(1).split(",")] if tag_m else ["tech"]
    return tags, context


def load_glossary_metadata(target: Path, metadata_json: Path | None = None) -> dict:
    metadata_map = {}
    g_sources = list((target / "data" / "glossary").glob("*.json")) if (target / "data" / "glossary").is_dir() else []
    if not g_sources and (target / "data" / "glossary.json").exists():
        g_sources.append(target / "data" / "glossary.json")

    for f in sorted(g_sources):
        try:
            g_data = json.loads(f.read_text(encoding="utf-8"))
            terms = g_data if isinstance(g_data, list) else g_data.get("terms", [])
            for term in terms:
                ent = term.get("entity")
                if ent and ent not in metadata_map:
                    metadata_map[ent] = {"tags": term.get("tags", []), "context": term.get("definition", "")}
        except Exception:
            pass

    if metadata_json and metadata_json.exists():
        try:
            m_data = json.loads(metadata_json.read_text(encoding="utf-8"))
            custom_map = {Path(item.get("path", item.get("file_path", ""))).stem: item for item in m_data} if isinstance(m_data, list) else m_data
            metadata_map.update(custom_map)
        except Exception:
            pass
    return metadata_map


def update_index(wiki_path: Path, metadata_json: Path | None = None) -> dict:
    """Deterministic index update to refresh header metrics and register untabled entities."""
    target = wiki_path.expanduser().resolve()
    index_file = target / "index.md"
    if not index_file.exists():
        raise FileNotFoundError(f"index.md not found at {index_file}")

    entities_dir = target / "wiki" / "entities"
    topics_dir = target / "wiki" / "topics"
    sources_dir = target / "wiki" / "sources"

    entities = sorted([f.stem for f in entities_dir.glob("*.md")]) if entities_dir.exists() else []
    topics = sorted([f.stem for f in topics_dir.glob("*.md")]) if topics_dir.exists() else []
    sources = sorted([f.stem for f in sources_dir.glob("*.md")]) if sources_dir.exists() else []

    content = index_file.read_text(encoding="utf-8")
    header_rx = re.compile(r"^>\s*Local-first personal compounding knowledge base.*$", re.M)
    new_header = f"> Local-first personal compounding knowledge base (`{len(entities)}` Entities | `{len(topics)}` Topics | `{len(sources)}` Source Summaries)."
    content = header_rx.sub(new_header, content) if header_rx.search(content) else content

    metadata_map = load_glossary_metadata(target, metadata_json)
    newly_added = []
    untabled = [e for e in entities if f"[[{e}]]" not in content]
    if untabled:
        new_rows = []
        for e in untabled:
            tags, context = parse_entity_metadata(entities_dir / f"{e}.md", metadata_map)
            primary_tag = tags[1] if len(tags) > 1 and tags[0] == "entity" else (tags[0] if tags else "tech")
            new_rows.append(f"- [[{e}]]: `#{primary_tag}` - {context}")
            newly_added.append(e)

        recent_idx = content.find("## Recent Entries")
        if recent_idx == -1:
            content = content.rstrip() + "\n\n## Recent Entries\n" + "\n".join(new_rows) + "\n"
        else:
            next_h2 = content.find("\n## ", recent_idx + 17)
            pt = next_h2 if next_h2 != -1 else len(content)
            content = content[:pt].rstrip() + "\n" + "\n".join(new_rows) + "\n\n" + content[pt:].lstrip()

    index_file.write_text(content.strip() + "\n", encoding="utf-8")
    return {
        "status": "SUCCESS", "index_file": str(index_file),
        "total_entities": len(entities), "total_topics": len(topics),
        "total_sources": len(sources), "newly_added_to_index": newly_added
    }


def load_chunker_config() -> tuple[dict[str, re.Pattern], set[str]]:
    cfg = Path(__file__).resolve().parent / "config.json"
    raw = json.loads(cfg.read_text(encoding="utf-8")).get("chunker", {})
    pats = {k: re.compile(v) for k, v in raw.get("patterns", {}).items()}
    keywords = set(unicodedata.normalize("NFKC", k).lower() for k in raw.get("keywords", []))
    return pats, keywords


CPATS, CKEYWORDS = load_chunker_config()


def semantic_chunk_markdown(text: str, filename: str = "") -> tuple[str, dict]:
    """Universal semantic chunker for raw unstructured question banks, glossaries, and plain texts."""
    lines = text.splitlines()
    stats = {"headings_added": 0, "h1": 0, "h2": 0, "h3": 0}

    # 1. Structural Gate: If already possesses adequate hierarchy, skip
    if any(l.strip().startswith(("# ", "#\t", "## ", "##\t")) for l in lines):
        return text, stats

    first_idx = next((i for i, l in enumerate(lines) if l.strip() and not l.strip().startswith("<!--")), -1)

    # 2. Synthesize H1 if missing
    if first_idx != -1:
        first_line = lines[first_idx].strip()
        first_norm = unicodedata.normalize("NFKC", first_line)
        is_toc = bool(CPATS["toc_leader"].search(first_norm))
        if not is_toc and first_idx + 1 < len(lines) and CPATS["toc_leader"].search(lines[first_idx + 1].strip()):
            is_toc = True

        invalid_ends = ("。", "！", "？", ".", "!", "?", "：", ":", "、", "，", ",")
        is_cand = (CPATS["section_part"].match(first_norm) or first_norm.lower() in CKEYWORDS or len(first_line) < 60)
        if is_cand and not is_toc and not first_line.endswith(invalid_ends):
            lines[first_idx] = f"# {first_line}"
            stats["h1"] += 1; stats["headings_added"] += 1
        elif filename:
            clean_title = re.sub(r"^\d+[-_]", "", Path(filename).stem).replace("_", " ").strip().title()
            lines.insert(first_idx, f"# {clean_title}\n")
            stats["h1"] += 1; stats["headings_added"] += 1

    # 3. Universal sectioning and sub-item hierarchy
    out = []
    in_qa = False
    in_glossary = any(k in filename.lower() for k in ("glossary", "詞彙", "词汇"))

    for i, l in enumerate(lines):
        s = l.strip()
        if not s or s.startswith("#"):
            out.append(l)
            continue
        s_norm = unicodedata.normalize("NFKC", s)

        # Lookahead TOC protection
        is_toc = bool(CPATS["toc_leader"].search(s_norm)) or any(
            bool(CPATS["toc_leader"].search(lines[j].strip()))
            for j in range(i + 1, min(i + 4, len(lines))) if lines[j].strip()
        )
        if is_toc:
            out.append(l)
            continue

        # Check section keywords
        if (s_norm.lower() in CKEYWORDS or any(s_norm.startswith(kw) for kw in CKEYWORDS)) and len(s) < 40 and not s.endswith(("。", "！", "？", ".", "!", "?")):
            out.append(f"## {s}")
            stats["h2"] += 1; stats["headings_added"] += 1
            in_qa = any(k in s_norm.lower() for k in ("question", "answer", "問題", "解答", "题", "答"))
            in_glossary = any(k in s_norm.lower() for k in ("glossary", "詞彙", "词汇"))
            continue

        # Alpha heading in glossary context
        if CPATS["alphabet_heading"].match(s):
            has_def_next = any(bool(CPATS["definition_term"].match(lines[j].strip())) for j in range(i + 1, min(i + 4, len(lines))) if lines[j].strip())
            if in_glossary or has_def_next:
                out.append(f"## {s}")
                stats["h2"] += 1; stats["headings_added"] += 1
                continue

        # Part heading
        if CPATS["section_part"].match(s) and len(s) < 60 and not s.endswith(("。", "！", "？", ".", "!", "?")):
            out.append(f"### {s}")
            stats["h3"] += 1; stats["headings_added"] += 1
            continue

        # QA item (only in QA context)
        if in_qa and (m_qa := CPATS["qa_numbered"].match(s)):
            out.append(f"### {m_qa.group(1)} {m_qa.group(2)}")
            stats["h3"] += 1; stats["headings_added"] += 1
            continue

        out.append(l)

    cleaned = "\n".join(out)
    if text.endswith("\n") and not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned, stats


def semantic_chunk_path(target_path: Path, write: bool = False) -> list[dict]:
    target = target_path.expanduser().resolve()
    files = [target] if target.is_file() else sorted(target.rglob("*.md"))
    results = []
    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        chunked, stats = semantic_chunk_markdown(content, filename=fp.name)
        changed = chunked != content
        if write and changed:
            fp.write_text(chunked, encoding="utf-8")
        results.append({
            "file": str(fp), "changed": changed, "written": write and changed,
            "headings_added": stats["headings_added"], "h1": stats["h1"], "h2": stats["h2"], "h3": stats["h3"]
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Assemble & Scaffold Knowledge Base.")
    parser.add_argument("--init", action="store_true", help="Initialize a fresh knowledge base")
    parser.add_argument("--path", default=default_wiki_path(), help="Target path for knowledge base")
    parser.add_argument("--update-index", action="store_true", help="Synchronize index.md metrics and append new entities")
    parser.add_argument("--metadata-json", help="Optional path to metadata JSON from subagent batch execution")
    parser.add_argument("--semantic-chunk", help="Path to file or directory to process via semantic chunking pipeline")
    parser.add_argument("--write", action="store_true", help="Write semantic chunking changes in-place")
    parser.add_argument("--json", action="store_true", help="Output JSON result summary")
    args = parser.parse_args()

    wiki_path = Path(args.path)
    if args.init:
        init_knowledge_base(wiki_path)
    elif args.update_index:
        meta_p = Path(args.metadata_json) if args.metadata_json else None
        res = update_index(wiki_path, metadata_json=meta_p)
        print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else f"Updated index.md: {res['total_entities']} Entities, {res['total_topics']} Topics, {res['total_sources']} Sources (Newly added: {len(res['newly_added_to_index'])})")
    elif args.semantic_chunk:
        target = Path(args.semantic_chunk)
        results = semantic_chunk_path(target, write=args.write)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return
        changed_count = sum(1 for r in results if r["changed"])
        print(f"=== Semantic Chunking Pipeline: {target} ===\nProcessed files: {len(results)} | Modified: {changed_count} (written: {args.write})")
        for r in results:
            if r["changed"]:
                print(f"  - {r['file']}: +{r['headings_added']} headings (H1: {r['h1']}, H2: {r['h2']}, H3: {r['h3']})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
