# Protocol Specification: Type B Agent Skill Directory Delivery

## Objective
Distill multi-source documents into structured, production-ready Agent Skill directories conforming to progressive disclosure, single-shot I/O budgets, and deterministic verification gates.

---

## 1. Pure Rule Extraction Discipline (chapters/)
- **Zero Detail Loss Mandate**: Strictly prohibit aggressive over-summarization, dropping sub-clauses, or omitting technical parameters/matrices to fit arbitrary constraints. All statutory articles, engineering controls, and technical specifications MUST be preserved in full technical depth.
- **Single-Shot Tool I/O Budget**: Target **<= 45 KB (strictly <= 46,080 bytes)** per synthesized chapter file (`chapters/*.md`), fitting within the agent `view_file` single-read limit to enable zero-pagination, surgical O(1) ingestion.
- **Paragraph Continuity Standard**: Enforce continuous paragraph unwrapping (zero spurious hard line-wraps or mid-sentence breaks). Paragraphs must flow as coherent logical blocks to ensure high semantic density and clean parsing.
- **Semantic-Boundary Modular Partitioning**: When source chapters or topic domains exceed the single-shot I/O budget (> 45 KB / > 6,500 tokens), hierarchically segment them into standalone semantic sub-modules (e.g. `chapter_XX-1_*.md`, `chapter_XX-2_*.md`) based on functional themes rather than mechanical line splits.
- **Mandatory 3-Section Chapter Backbone**:
  1. **Statutory Baseline & Technical Control Matrix**: Core legal/technical obligations mapped to architectural standards and quantitative telemetry (KPI/KRI/KCI).
  2. **Production Incident & Remediation Architecture**: End-to-end operational failure walk-through (Context -> Root-Cause Defect -> Architecture Fix).
  3. **Exam Question Bank & Distractor Forensics**: 3 to 4 complete practice questions (`FIRST`, `BEST/MOST`, `NEXT`, `PRIMARY/EXCEPT`) with complete 4-option distractor analysis for every single choice.
- **Single Source of Truth Rule**: Directly embed all domain-specific scenarios, advanced methods, and question banks inside the canonical chapter files. Prohibit scattering orphan fragments across `references/`.
- **Subagent Shard Execution Protocol**:
  - **Threshold**: When total chapters <= 3, synthesize sequentially in a single agent. Enable Subagent sharding only when chapters > 3.
  - **Read-Only Context Quota**: Maximum **2 reference files** per worker (1 raw chapter chunk + `data/glossary.json`).
  - **Allowed Write Paths**: Strictly exclusive single target file per worker (e.g. `chapters/chapter_XX_*.md`).
- **Batch Ambiguity Staging Protocol**: If undefined terms or conflicting rules arise during synthesis, do NOT halt mid-process. Record items into `<target_dir>/AMBIGUITY_LOG.md` and proceed with the best context default. Present the batch log to the user upon pipeline completion, patch resolutions back to chapters, and purge `AMBIGUITY_LOG.md`.

---

## 2. Structured Data Layer Standards (data/)
- **Mandatory JSON Standards**:
  - `data/index.json`: Chapter sequence, title, file path, and estimated token counts.
  - `data/glossary.json`: Technical terms, aliases (Chinese/English), exact 1-sentence definitions, and chapter references.
- **Syntax & Encoding**: Strict UTF-8 with zero JSON syntax errors (no trailing commas, valid key-value structures).

---

## 3. Deterministic Tooling Standards (scripts/)
- **Deterministic Offloading**: Offload searching, filtering, and row calculation to a local Python script (e.g. `query.py`) with zero LLM math.
- **Semantic CLI Flags**: Expose `--format markdown|json`, `--batch <file.json>`, and `--filter` flags.
- **AST Hygiene & Safety**: All scripts MUST satisfy nesting depth <= 2, flat control flow, no mutable defaults, no PEP 594 removed modules, and zero unsafe calls (verified automatically via `audit.py`).

---

## 4. Top-Level Interface Specifications (SKILL.md & SECURITY.md)
- **`SKILL.md` Constraints** (<= 50 lines, <= 4,000 tokens):
  - Frontmatter fields: `name:` (kebab-case), `description:` (trigger conditions & intent), `dependencies: []` (no wildcard `*`), `metadata: task_type:` (no `version:` field).
  - Required sections: `# <Title>`, `## Objective`, `## Execution Workflow`.
  - Path safety: Prohibit hardcoded absolute paths (`/Users/...`, `/home/...`; use `~/` or `$HOME`).
  - Zero plaintext secrets, privilege escalations (`sudo`, `chmod +x`), or insecure telemetry endpoints.
- **`SECURITY.md` Constraints** (<= 30 lines):
  - Required sections: `## Scope`, `## Dependencies`, `## Execution`.

---

## 5. Protocol Overflow Standards (references/)
- **Overflow Threshold**: Any detailed protocol, complex diagram, or deep specification causing `SKILL.md` to exceed 50 lines MUST overflow to `references/`.
- **Per-File Budget**: Maximum 200 lines per reference file.
- **Mandatory Linkage**: Every file in `references/` MUST be explicitly referenced in `SKILL.md`. Zero orphan files permitted.
- **Code Fence Hygiene**: Strictly maintain balanced code fences and 4-backtick nesting rules.

---

## 6. Verification & Quality Gates
- **Shift-Left Subagent Exit Gate**: Before handoff, every worker must verify:
  1. Paragraph continuity (zero mid-sentence broken wraps).
  2. Single-file physical size <= 45 KB.
  3. Anti-AI validation passing `python3 tests/noai_gate.py <target_file>`.
- **Gate 1 (Anti-AI Baseline)**: Run `python3 tests/noai_gate.py <generated_skill_dir>` to guarantee zero AI buzzwords or formulaic patterns across all files.
- **Gate 2 (Structure & AST Audit)**: Run `python3 tests/audit.py <generated_skill_dir>` to verify `SKILL.md` frontmatter/budgets, orphan `references/`, chapter <= 45 KB, `data/` JSON syntax, and script AST hygiene in one shot.
- **Gate 3 (Circuit Breaker & Batch Remediation)**: Maximum 2 retries on verification failure. If blocking issues persist, generate `FAILED_REMEDIATION_REPORT.md` and halt for batch user confirmation.
