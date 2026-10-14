#!/usr/bin/env python3
"""Knowledge Base Scaffolding & Assembly Engine for deep-base."""

import argparse
from datetime import datetime
import json
from pathlib import Path


def init_knowledge_base(target_path: Path):
    target = target_path.expanduser().resolve()
    print(f"Initializing Knowledge Base at: {target}")

    dirs = [
        target / "raw" / "articles",
        target / "raw" / "notes",
        target / "raw" / "pdfs",
        target / "raw" / "assets",
        target / "wiki" / "entities",
        target / "wiki" / "topics",
        target / "wiki" / "sources",
        target / "wiki" / "comparisons",
        target / "wiki" / "synthesis",
        target / "wiki" / "queries",
        target / "templates",
        target / "data",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

    # .wiki-schema.md
    schema_path = target / ".wiki-schema.md"
    if not schema_path.exists():
        schema_path.write_text(f"""# Wiki Schema & Governance
- Language: zh-TW
- Version: 1.0.0
- Methodology: Andrej Karpathy LLM Wiki Architecture
- Storage Boundary: Local-first Markdown
- Layer 1: raw/ (Immutable Source Files)
- Layer 2: wiki/ (Synthesized & Compounding Knowledge)

## Confidence Labels
- [EXTRACTED]: Direct factual quote/source extraction.
- [INFERRED]: LLM synthesis or cross-domain deduction.
- [AMBIGUOUS]: Conflicting sources requiring verification.
- [UNVERIFIED]: External claim pending empirical test.
""", encoding="utf-8")

    # index.md
    index_path = target / "index.md"
    if not index_path.exists():
        index_path.write_text(f"""# Personal Knowledge Base Index

> Local-first personal compounding knowledge base initialized on {today}.

## Navigation
- [[wiki/entities/]]: People, organizations, models, and tools.
- [[wiki/topics/]]: Structured conceptual frameworks.
- [[wiki/sources/]]: Raw source summaries.
- [[wiki/comparisons/]]: Multi-subject comparative analyses.
- [[wiki/synthesis/]]: Long-term conversation crystallizations.
- [[wiki/queries/]]: High-value answers retained for quick lookup.

## Recent Entries
""", encoding="utf-8")

    # log.md
    log_path = target / "log.md"
    if not log_path.exists():
        log_path.write_text(f"""# Wiki Operation Log
- {today}: Initialized personal knowledge base structure at {target}.
""", encoding="utf-8")

    # data/glossary.json
    glossary_path = target / "data" / "glossary.json"
    if not glossary_path.exists():
        initial_glossary = {
            "version": "1.0.0",
            "last_updated": today,
            "terms": [
                {
                    "term_zh": "檢索增強生成",
                    "term_en": "Retrieval-Augmented Generation",
                    "abbr": "RAG",
                    "entity": "rag",
                    "aliases": ["檢索增強生成", "Retrieval-Augmented Generation", "RAG"],
                    "definition": "結合外部檢索機制與大型語言模型生成能力之架構。"
                },
                {
                    "term_zh": "大型語言模型",
                    "term_en": "Large Language Model",
                    "abbr": "LLM",
                    "entity": "llm",
                    "aliases": ["大型語言模型", "Large Language Model", "LLM"],
                    "definition": "基於海量文字預訓練並具備語言理解與生成能力之深度學習模型。"
                }
            ]
        }
        glossary_path.write_text(json.dumps(initial_glossary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Knowledge base successfully initialized at {target}")


def main():
    parser = argparse.ArgumentParser(description="Assemble & Scaffold Knowledge Base.")
    parser.add_argument("--init", action="store_true", help="Initialize a fresh knowledge base")
    parser.add_argument("--path", default="~/wiki", help="Target path for knowledge base")
    args = parser.parse_args()

    if args.init:
        init_knowledge_base(Path(args.path))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
