# Protocol Specification: Type B Agent Skill Directory Delivery

## Objective
Distill multi-source documents into structured, production-ready Agent Skill directories conforming to progressive disclosure, single-shot I/O budgets, and deterministic verification gates.

---

## 1. Chapter Directory Standards (chapters/)
- **Capacity Budget**: Target **30 ~ 38 KB (strictly <= 45 KB / 46,080 bytes)** per chapter file (`chapters/*.md`) to guarantee zero-pagination ingestion via `view_file`.
- **Zero Detail Loss Mandate**: Prohibit aggressive summarization. Retain 100% of statutory articles, technical parameters, detection logic, and control matrices.
- **Mandatory 3-Section Chapter Backbone**:
  1. **Statutory Baseline & Technical Control Matrix**: Core legal and technical obligations mapped to quantitative telemetry (KPI/KRI/KCI).
  2. **Production Incident & Remediation Architecture**: End-to-end failure walk-through (Context -> Root Cause -> Architecture Fix).
  3. **Exam Question Bank & Distractor Forensics**: 3 to 4 scenario questions (`FIRST`, `BEST/MOST`, `NEXT`, `PRIMARY/EXCEPT`) with complete 4-option distractor analysis for every choice.
- **Subagent Execution Contract**:
  - **Single Write Path**: Exactly 1 exclusive target file per worker (e.g. `chapters/chapter_XX_*.md`).
  - **Context Quota**: Exactly 2 read-only inputs (1 assigned raw chunk + `data/glossary.json` or `data/*.json`).
  - **Zero Micro-Trimming**: Prohibit multi-round line-by-line trimming loops. Synthesize to target budget in a single pass. If output exceeds 45 KB, execute 1 compact pass; if still > 44 KB, split into sub-shards (e.g. `chapter_XX-1a.md`, `chapter_XX-1b.md`).

---

## 2. Structured Data Layer Standards (data/)
- **`data/index.json`**: Chapter sequence, titles, relative file paths, and estimated token counts.
- **`data/glossary.json`**: Canonical technical terms, aliases (Chinese/English), 1-sentence definitions, and referencing chapter list.
- **Syntax & Encoding**: Strict UTF-8 with zero trailing commas and valid schema structure.

---

## 3. Deterministic Tooling Standards (scripts/)
- **Deterministic Offloading**: Offload querying, filtering, and table lookup to standalone Python scripts (e.g. `query.py`). Prohibit LLM runtime arithmetic.
- **Semantic CLI Flags**: Scripts MUST support `--format markdown|json`, `--batch <file.json>`, and `--filter <keyword>` flags.
- **AST Hygiene**: AST nesting depth <= 2, flat control flow with early returns, zero mutable defaults, and zero PEP 594 deprecated modules.

---

## 4. Top-Level Interface Specifications (SKILL.md & SECURITY.md)
- **`SKILL.md` Constraints** (<= 50 lines, <= 4,000 tokens):
  - Frontmatter fields: `name:` (kebab-case), `description:`, `dependencies: []`, `metadata: task_type:` (no `version:` field).
  - Required sections: `# <Title>`, `## Objective`, `## Execution Workflow`.
  - Path safety: Prohibit hardcoded local paths (`/home/...`, `/Users/...`; use `~/` or `$HOME`).
- **`SECURITY.md` Constraints** (<= 30 lines):
  - Required sections: `## Scope`, `## Dependencies`, `## Execution`.

---

## 5. Verification & Quality Gates
- **Gate 1 (Anti-AI Baseline)**: Run `python3 tests/noai_gate.py <generated_skill_dir>` to verify zero prohibited buzzwords, canned openings, or formulaic patterns.
- **Gate 2 (Structure & AST Audit)**: Run `python3 tests/audit.py <generated_skill_dir>` to verify frontmatter constraints, single-file sizes (<= 45 KB), valid JSON syntax, and script AST rules.
- **Gate 3 (Circuit Breaker)**: Maximum 2 automated fix retries upon gate failure. If blocking errors persist, generate `FAILED_REMEDIATION_REPORT.md` and pause for user direction.
