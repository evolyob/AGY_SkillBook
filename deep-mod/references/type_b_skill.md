# Protocol Specification: Type B Agent Skill Directory Delivery

## Objective
Distill multi-source documents into structured, production-ready Agent Skill directories conforming to 23-Gate audit standards and three-tier progressive disclosure.

---

## 1. Pure Rule Extraction Discipline (chapters/)
- **Zero Detail Loss Mandate**: Strictly prohibit aggressive over-summarization, dropping sub-clauses, or omitting technical parameters/matrices to artificially fit line budgets. All statutory articles, engineering controls, and technical specifications MUST be preserved in full technical depth.
- **Semantic-Boundary Modular Partitioning**: When source chapters or topic domains exceed the single-shot I/O budget (> 40 KB / > 10,000 tokens), hierarchically segment them into standalone semantic sub-modules (e.g. `chapter_XX-1_*.md`, `chapter_XX-2_*.md`) based on functional themes rather than rigid mechanical line splits.
- **Single-Shot Tool I/O Budget**: Target **25 KB ~ 45 KB (approx. 250 ~ 600 lines)** per synthesized chapter file (`chapters/*.md`), strictly fitting within the agent `view_file` single-read limit (46,080 bytes) to enable zero-pagination, surgical O(1) ingestion.
- **Mandatory 3-Section Chapter Backbone**:
  1. **Statutory Baseline & Technical Control Matrix**: Core legal/technical obligations mapped to architectural standards and quantitative telemetry (KPI/KRI/KCI).
  2. **Production Incident & Remediation Architecture**: End-to-end operational failure walk-through (Context -> Root-Cause Defect -> Architecture Fix).
  3. **Exam Question Bank & Distractor Forensics**: 3 to 4 complete practice questions (`FIRST`, `BEST/MOST`, `NEXT`, `PRIMARY/EXCEPT`) with complete 4-option distractor analysis for every single choice.
- **Single Source of Truth Rule**: Directly embed all domain-specific scenarios, advanced methods, and question banks inside the canonical chapter files. Prohibit scattering orphan fragments across `references/`.
- **Socratic Ambiguity Gate**: If undefined terms or conflicting rules arise, pause and issue ONE targeted question before generating the file.

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
- **AST Hygiene & Guardrails**:
  - Flat control flow: Enforce guard clauses with early returns (maximum `if` nesting depth $\le$ 2).
  - No mutable default arguments (`def f(x=[])`).
  - No bare `except:` handlers (specify explicit exception types).
  - Explicit file encoding: Enforce `open(..., encoding="utf-8")`.
  - Zero dangerous calls: Strictly prohibit `eval()`, `exec()`, and `os.system()`.
  - Zero deprecated modules: Prohibit PEP 594 removed standard library modules.

---

## 4. Top-Level Interface Specifications (SKILL.md & SECURITY.md)
- **`SKILL.md` Constraints** ($\le$ 50 lines, $\le$ 4,000 tokens):
  - Frontmatter fields: `name:` (kebab-case), `description:` (trigger conditions & intent), `dependencies: []` (no wildcard `*`), `metadata: task_type:` (no `version:` field).
  - Required sections: `# <Title>`, `## Objective`, `## Execution Workflow`.
  - Path safety: Prohibit hardcoded absolute paths (`/Users/...`, `/home/...`; use `~/` or `$HOME`).
  - Zero plaintext secrets, privilege escalations (`sudo`, `chmod +x`), or insecure telemetry endpoints.
- **`SECURITY.md` Constraints** ($\le$ 30 lines):
  - Required sections: `## Scope`, `## Dependencies`, `## Execution`.

---

## 5. Protocol Overflow Standards (references/)
- **Overflow Threshold**: Any detailed protocol, complex diagram, or deep specification causing `SKILL.md` to exceed 50 lines MUST overflow to `references/`.
- **Per-File Budget**: Maximum 200 lines per reference file.
- **Mandatory Linkage**: Every file in `references/` MUST be explicitly referenced in `SKILL.md`. Zero orphan files permitted.
- **Code Fence Hygiene**: Strictly maintain balanced code fences and 4-backtick nesting rules.

---

## 6. Verification & Quality Gates
- **Gate 1 (Anti-AI Baseline)**: Run self-contained scanner `python3 scripts/noai_gate.py <generated_skill_dir>` to guarantee zero AI buzzwords or formulaic patterns.
- **Gate 2 (Script AST & Safety Audit)**: Run self-contained script auditor `python3 tests/audit.py <generated_skill_dir>/scripts` to verify 13 AST hygiene, safety, and dynamic line budget rules.
- **Gate 3 (Circuit Breaker)**: If any blocking issue or prohibited pattern is detected, output the failure report and halt for user confirmation.
