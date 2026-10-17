---
name: deep-base
description: Local-first compounding personal knowledge base engine. Enforces local Markdown persistence at ~/wiki, local-first retrieval gates, SHA-256 deduplication, and wikilink integrity audits.
dependencies: []
---

# Deep Base: Personal Compounding Knowledge Base

## Objective
Operate a local-first personal knowledge base at `~/wiki/` (pure filesystem backed up externally; no Git). User-provided materials serve as primary ground truth before any external search.

## 1. Directory Boundaries
- `~/wiki/raw/`: Immutable flattened sources (`articles/<slug>/chapters/*.md`, `assets/`) and monthly note buffers (`notes/YYYY-MM.md`, `notes/archive/YYYY-MM.md`).
- `~/wiki/wiki/`: Synthesized compounding cards (`<= 45 KB` per file: `entities/`, `topics/`, `sources/`, `comparisons/`, `synthesis/`, `queries/`).
- `~/wiki/data/glossary.json`: Pattern A flat terminology and alias array with domain `tags` (`tech`, `academic`, `compliance`).
- `~/wiki/index.md`, `~/wiki/log.md`, `~/wiki/.wiki-cache.json`: Global index, append-only audit trail, and SHA-256 cache registry.

## 2. Core Workflows & CLI Routing

| Workflow | Trigger Intent | Deterministic CLI Command |
| :--- | :--- | :--- |
| **1. Init (`init`)** | Initialize scaffold | `python3 ~/.gemini/skills/deep-base/scripts/assemble.py --init --path ~/wiki` |
| **2. Ingest (`ingest`)** | Check duplicate hash | `python3 ~/.gemini/skills/deep-base/scripts/cache.py check <file>` |
| | Inspect density / OCR | `python3 ~/.gemini/skills/deep-base/scripts/flatten.py <file> --list-only` |
| | Flatten `<= 40 KB` chapters | `python3 ~/.gemini/skills/deep-base/scripts/flatten.py <file> --split-dir ~/wiki/raw/articles/<slug>/chapters --json` |
| | Register summary hash | `python3 ~/.gemini/skills/deep-base/scripts/cache.py update <file> <summary_page>` |
| **3. Query (`query`)** | FTS5 & alias lookup | `python3 ~/.gemini/skills/deep-base/scripts/query.py ~/wiki --filter <kw>` or `--entity <name>` (`--format markdown\|json`) |
| **4. Audit (`lint`)** | Link, size & quote check | `python3 ~/.gemini/skills/deep-base/scripts/lint_links.py ~/wiki --strict --verify-quotes` |
| | Dynamic backlinks | `python3 ~/.gemini/skills/deep-base/scripts/lint_links.py ~/wiki --backlinks <entity>` |
| | Layer telemetry | `python3 ~/.gemini/skills/deep-base/scripts/stats.py ~/wiki` |

## 3. Operational & Synthesis Specifications
Load [workflows_spec.md](references/workflows_spec.md) for daily note buffering, batch distillation, zero-lookback synthesis, and local-first grounding rules.
