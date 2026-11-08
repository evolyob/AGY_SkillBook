---
name: deep-base
description: Local-first compounding personal knowledge base engine. Enforces local Markdown persistence at ~/wiki, local-first retrieval gates, SHA-256 deduplication, and wikilink integrity audits.
dependencies: []
---

# Deep Base: Personal Compounding Knowledge Base

## Objective
Operate a local-first personal knowledge base at `~/wiki/` (or `~/wiki/`). User-provided materials serve as primary ground truth before any external search. Synthesize technical knowledge cards with Source-Language Fidelity (native English for English sources, native Traditional Chinese for Chinese sources; frontmatter Traditional Chinese aliases enable instant CJK retrieval).

## 1. Directory Boundaries
- `~/wiki/raw/`: Immutable flattened sources (`articles/<slug>/chapters/*.md`, `assets/`) and monthly note buffers (`notes/YYYY-MM.md`, `notes/archive/YYYY-MM.md`).
- `~/wiki/wiki/`: Synthesized compounding cards (`<= 45 KB` per file: `entities/`, `topics/`, `sources/`, `comparisons/`, `synthesis/`, `queries/`).
- `~/wiki/data/glossary/`: Pattern A flat terminology and alias shards (`tech.json`, `compliance.json`) with domain `tags` (`ai`, `tech`, `rmf`, `compliance`, `work`).
- `~/wiki/index.md`, `~/wiki/log.md`, `~/wiki/.wiki-cache.json`: Global index, append-only audit trail, and SHA-256 cache registry.

## 2. Core Workflows & CLI Routing

| Workflow | Trigger Intent | Deterministic CLI Command |
| :--- | :--- | :--- |
| **1. Init (`init`)** | Initialize scaffold | `python3 scripts/assemble.py --init --path ~/wiki` |
| **2. Ingest (`ingest`)** | Check duplicate hash | `python3 scripts/cache.py check <file>` |
| | Inspect density / OCR | `python3 scripts/flatten.py <file> --list-only` |
| | Flatten `<= 40 KB` chapters | `python3 scripts/flatten.py <file> --split-dir ~/wiki/raw/articles/<slug>/chapters --json` |
| | Register summary hash | `python3 scripts/cache.py update <file> <summary_page>` |
| | Gate-1 Syntax Sanitizer | `python3 scripts/sanitize.py <file_or_dir> --fix` |
| | Semantic Chunking Pipeline | `python3 scripts/assemble.py --semantic-chunk <file_or_dir> --write` |
| **3. Query (`query`)** | FTS5 & alias lookup | `python3 scripts/query.py ~/wiki --filter <kw>` or `--entity <name>` (`--format markdown\|json`) |
| | Dynamic backlinks | `python3 scripts/query.py ~/wiki --backlinks <entity>` |
| **4. Audit (`lint`)** | Link, size & quote check | `python3 scripts/lint_links.py ~/wiki --strict --verify-tags --verify-quotes` |
| | Layer telemetry | `python3 scripts/lint_links.py ~/wiki --stats` |
| | Automated Index Compiler | `python3 scripts/assemble.py --update-index --path ~/wiki` |

## 3. Operational & Synthesis Specifications
Load [workflows_spec.md](references/workflows_spec.md) for daily note buffering, batch distillation, zero-lookback synthesis, and local-first grounding rules.
