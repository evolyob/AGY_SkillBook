---
name: deep-base
description: Local-first compounding personal knowledge base engine. Enforces local Markdown persistence at ~/wiki, local-first retrieval gates, SHA-256 deduplication, and wikilink integrity audits.
dependencies: []
---

# Deep Base: Personal Compounding Knowledge Base

## Objective
Operate a local-first personal knowledge base at `~/wiki/`. User-provided materials serve as primary ground truth before any external search.

## 1. Directory Boundaries
All operations are strictly rooted at `~/wiki/`:
- `~/wiki/raw/`: Immutable source files (`articles/`, `pdfs/`, `notes/`, `assets/`).
- `~/wiki/wiki/`: AI-synthesized compounding layer (`entities/`, `topics/`, `sources/`, `comparisons/`, `synthesis/`, `queries/`).
- `~/wiki/data/`: Standardized knowledge schemas, taxonomies, and entity glossaries (`glossary.json`).
- `~/wiki/index.md` & `~/wiki/log.md`: Global index and append-only audit trail.
- `~/wiki/.wiki-schema.md` & `~/wiki/.wiki-cache.json`: Governance schema and SHA-256 cache registry.

## 2. Core Workflows

### Workflow 1: Initialization (`init`)
- Command: `python3 scripts/assemble.py --init --path ~/wiki`

### Workflow 2: Ingestion Pipeline (`ingest`)
1. **Deduplication**: Run `python3 scripts/cache.py check <file>`. If exit code `0` (`HIT`), notify user and read existing summary.
2. **Raw Archiving**: Save untouched source to `~/wiki/raw/<category>/<filename>`.
3. **Synthesis**:
   - Generate summary in `wiki/sources/<slug>.md` via `templates/source.template.md`.
   - Extract 1-3 entities to `wiki/entities/<entity>.md` via `templates/entity.template.md`.
   - Link topics via `templates/topic.template.md`.
4. **Registration**: Update `index.md`, `log.md`, and run `python3 scripts/cache.py update <file> <summary_page>`.

### Workflow 3: Query & Crystallization (`query`)
1. **Local-First Gate**: Query via `python3 scripts/query.py ~/wiki --filter <keyword>` or `--entity <name>` (supports `--format markdown|json`). If sufficient, output answer with `[EXTRACTED]` and local wikilinks.
2. **External Delta Gate**: If facts are missing, perform targeted web search strictly for the missing delta.
3. **Crystallization**: On high-value conclusions or complex debates, persist to `wiki/synthesis/<topic>.md` via `templates/synthesis.template.md`, or cache frequent Q&As via `templates/query.template.md`.

### Workflow 4: Health Audit (`lint` & `stats`)
- Link & size audit: `python3 scripts/lint_links.py ~/wiki --strict --verify-quotes` (enforces 45 KB max file budget).
- Backlinks query: `python3 scripts/lint_links.py ~/wiki --backlinks <entity>`
- Telemetry: `python3 scripts/stats.py ~/wiki`
