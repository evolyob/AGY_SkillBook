---
name: deep-base
description: Local-first compounding personal knowledge base engine. Enforces local Markdown persistence at ~/.gemini/wiki, local-first retrieval gates, SHA-256 deduplication, and wikilink integrity audits.
dependencies: []
---

# Deep Base: Personal Compounding Knowledge Base

## Objective
Operate a local-first personal knowledge base at `~/.gemini/wiki/`. User-provided materials serve as primary ground truth before any external search.

## 1. Directory Boundaries
All operations are strictly rooted at `~/.gemini/wiki/`:
- `~/.gemini/wiki/raw/`: Immutable flattened text/Markdown sources (`articles/<slug>/chapters/*.md`, `notes/`). Binary documents (PDF/DOCX/XLSX) are flattened into `<= 40 KB` chapter Markdown files upon ingestion to eliminate repeated binary parsing overhead.
- `~/.gemini/wiki/wiki/`: AI-synthesized compounding layer (`entities/`, `topics/`, `sources/`, `comparisons/`, `synthesis/`, `queries/`).
- `~/.gemini/wiki/data/`: Standardized knowledge schemas, taxonomies, and entity glossaries (`glossary.json`).
- `~/.gemini/wiki/index.md` & `~/.gemini/wiki/log.md`: Global index and append-only audit trail.
- `~/.gemini/wiki/.wiki-schema.md` & `~/.gemini/wiki/.wiki-cache.json`: Governance schema and SHA-256 cache registry.

## 2. Core Workflows

### Workflow 1: Initialization (`init`)
- Command: `python3 scripts/assemble.py --init --path ~/.gemini/wiki`

### Workflow 2: Ingestion Pipeline (`ingest`)
1. **Deduplication**: Run `python3 scripts/cache.py check <file>`. If exit code `0` (`HIT`), notify user and read existing summary.
2. **Reconnaissance & Flattening (`flatten.py`)**:
   - Run `python3 scripts/flatten.py <file> --list-only` to inspect page density, chapter structure, and `dispatch_mode` (`single_agent` vs `subagent_parallel`). If exit code `3` (`OCR_REQUIRED`), run OCR before ingestion.
   - Export clean UTF-8 chapters (`<= 40 KB` each) via `python3 scripts/flatten.py <file> --split-dir ~/.gemini/wiki/raw/articles/<slug>/chapters --json`.
   - Point `source_path` in `wiki/sources/<slug>.md` to `raw/articles/<slug>/chapters`.
3. **Zero-Lookback Synthesis & Write-Isolated Dispatch**:
   - **Dispatch Rule**: For `single_agent` (`<= 80 KB` and `<= 6` chapters), synthesize directly. For `subagent_parallel` (e.g., multi-hundred-page standards), dispatch subagents by `recommended_batches`; each subagent writes ONLY to its assigned `wiki/entities/<entity>.md` and returns JSON metadata to prevent race conditions on shared index files.
   - **Source Map**: Generate structural index and takeaways in `wiki/sources/<slug>.md` via `templates/source.template.md`.
   - **No-Elision Enumeration**: Extract entities to `wiki/entities/<entity>.md` via `templates/entity.template.md`. Preserve 100% of enumerated items (modules, APIs, CLI flags, algorithm steps, taxonomy codes, or clauses) in Markdown tables; never truncate lists with "etc." or high-level prose summaries.
   - **Quantitative & Operational Fidelity**: Retain all exact numbers, thresholds, bounds, formulas, defaults, and verification rules so `wiki/` serves as a standalone reference without requiring `raw/` lookback.
   - **Adaptive Atomic Sharding**: Shard complex sources by sub-system or sub-domain so each entity remains self-contained within the 45 KB budget, connected via `templates/topic.template.md`.
4. **Registration**: The main agent updates `index.md`, `log.md`, `data/glossary.json`, and runs `python3 scripts/cache.py update <file> <summary_page>`.

### Workflow 3: Query & Crystallization (`query`)
1. **Local-First Gate**: Query via `python3 scripts/query.py ~/.gemini/wiki --filter <keyword>` or `--entity <name>` (supports `--format markdown|json`). If sufficient, output answer with `[EXTRACTED]` and local wikilinks.
2. **External Delta Gate**: If facts are missing, perform targeted web search strictly for the missing delta.
3. **Crystallization**: On high-value conclusions or complex debates, persist to `wiki/synthesis/<topic>.md` via `templates/synthesis.template.md`, or cache frequent Q&As via `templates/query.template.md`.

### Workflow 4: Health Audit (`lint` & `stats`)
- Link & size audit: `python3 scripts/lint_links.py ~/.gemini/wiki --strict --verify-quotes` (enforces 45 KB max file budget and validates quotes against flattened chapter directories).
- Backlinks query: `python3 scripts/lint_links.py ~/.gemini/wiki --backlinks <entity>`
- Telemetry: `python3 scripts/stats.py ~/.gemini/wiki`
