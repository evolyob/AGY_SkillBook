#!/usr/bin/env python3
"""Knowledge Base Scaffolding & Assembly Engine for deep-base.

Supports scaffolding initialization and lightweight index synchronization.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import re


def default_wiki_path() -> str:
    gemini_wiki = Path.home() / ".gemini" / "wiki"
    return "~/.gemini/wiki" if gemini_wiki.exists() else "~/wiki"


def load_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "config.json"
    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        return raw.get("scaffold", {})
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

    schema_path = target / ".wiki-schema.md"
    if not schema_path.exists():
        schema_path.write_text(f"# Wiki Schema & Governance\n- Language: en (English-first synthesis; zh-TW glossary & query bridging) | Version: 1.0.0 | Methodology: Andrej Karpathy LLM Wiki Architecture\n- Boundary: Local-first Markdown (Layer 1: raw/ Immutable Sources, Layer 2: wiki/ Synthesized Knowledge)\n\n## Confidence Labels & Gate-1 Hygiene\n- Labels: [EXTRACTED] Source extraction, [INFERRED] LLM deduction, [AMBIGUOUS] Conflicting, [UNVERIFIED] External.\n- Hygiene: Scrub PII mobile numbers, live credentials (sk-, ghp-, AKIA-), and normalize user paths to ~/ at Gate 1.\n", encoding="utf-8")

    index_path = target / "index.md"
    if not index_path.exists():
        index_path.write_text(f"# Personal Knowledge Base Index\n\n> Local-first personal compounding knowledge base initialized on {today}.\n\n## Navigation\n- [[wiki/entities/]], [[wiki/topics/]], [[wiki/sources/]], [[wiki/comparisons/]], [[wiki/synthesis/]], [[wiki/queries/]]\n\n## Recent Entries\n", encoding="utf-8")

    home_str = str(Path.home())
    display_target = str(target).replace(home_str, "~", 1) if str(target).startswith(home_str) else str(target)
    log_path = target / "log.md"
    if not log_path.exists():
        log_path.write_text(f"# Wiki Operation Log\n- {today}: Initialized personal knowledge base structure at {display_target}.\n", encoding="utf-8")

    glossary_path = target / "data" / "glossary.json"
    if not glossary_path.exists():
        initial_glossary = {"version": "1.0.0", "last_updated": today, "terms": CFG.get("initial_terms", [])}
        glossary_path.write_text(json.dumps(initial_glossary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Knowledge base successfully initialized at {target}")


def parse_entity_metadata(e_path: Path, meta_cache: dict) -> tuple[list[str], str]:
    meta = meta_cache.get(e_path.stem, {})
    tags = meta.get("tags", [])
    context = meta.get("context", "")
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

    metadata_map = {}
    glossary_file = target / "data" / "glossary.json"
    if glossary_file.exists():
        try:
            g_data = json.loads(glossary_file.read_text(encoding="utf-8"))
            for term in g_data.get("terms", []):
                ent = term.get("entity")
                if ent and ent not in metadata_map:
                    metadata_map[ent] = {
                        "tags": term.get("tags", []),
                        "context": term.get("definition", "")
                    }
        except Exception:
            pass

    if metadata_json and metadata_json.exists():
        try:
            m_data = json.loads(metadata_json.read_text(encoding="utf-8"))
            custom_map = {Path(item.get("path", item.get("file_path", ""))).stem: item for item in m_data} if isinstance(m_data, list) else m_data
            metadata_map.update(custom_map)
        except Exception:
            pass

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
        if recent_idx != -1:
            next_h2 = content.find("\n## ", recent_idx + 17)
            insert_pt = next_h2 if next_h2 != -1 else len(content)
            content = content[:insert_pt].rstrip() + "\n" + "\n".join(new_rows) + "\n\n" + content[insert_pt:].lstrip()
        else:
            content = content.rstrip() + "\n\n## Recent Entries\n" + "\n".join(new_rows) + "\n"

    index_file.write_text(content.strip() + "\n", encoding="utf-8")
    return {
        "status": "SUCCESS",
        "index_file": str(index_file),
        "total_entities": len(entities),
        "total_topics": len(topics),
        "total_sources": len(sources),
        "newly_added_to_index": newly_added
    }


def main():
    parser = argparse.ArgumentParser(description="Assemble & Scaffold Knowledge Base.")
    parser.add_argument("--init", action="store_true", help="Initialize a fresh knowledge base")
    parser.add_argument("--path", default=default_wiki_path(), help="Target path for knowledge base")
    parser.add_argument("--update-index", action="store_true", help="Synchronize index.md metrics and append new entities")
    parser.add_argument("--metadata-json", help="Optional path to metadata JSON from subagent batch execution")
    parser.add_argument("--json", action="store_true", help="Output JSON result summary")
    args = parser.parse_args()

    wiki_path = Path(args.path)
    if args.init:
        init_knowledge_base(wiki_path)
        return
    if args.update_index:
        meta_p = Path(args.metadata_json) if args.metadata_json else None
        res = update_index(wiki_path, metadata_json=meta_p)
        print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else f"Updated index.md: {res['total_entities']} Entities, {res['total_topics']} Topics, {res['total_sources']} Sources (Newly added: {len(res['newly_added_to_index'])})")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
