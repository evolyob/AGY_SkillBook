# Protocol Specification: Common Clarification Gate

## Objective
Execute universal neutral clarification immediately following `scripts/ingest.py` to freeze domain, workflow, and delivery route before generating final deliverables.

---

## 1. Intake & Probe Protocol (Step 2.6 Discipline)
- **Pre-flight Scan**: Always invoke `python3 scripts/ingest.py <input> --list-only` first. Operates with zero disk I/O, outputting total tokens, chapter metadata, taxonomy aliases, and `key_elements`.
- **REPL Probing Discipline**: For large documents (`est_tokens > 10,000`), strictly prohibit unconstrained full-text reads. Inspect only the specific target chapter file in the auto-exported temp directory (`/tmp/deep_mod_work/` or system tempdir) or use targeted line slices.
- **Fact-Checking Probes**: Verify named frameworks and critical terms against extracted chapter files before introducing them into downstream questions.

---

## 2. Neutral Clarification Protocol
- Anti-Sycophancy: Challenge implicit or unverified assumptions before generating deliverables.
- Scope Freeze: Do not route to downstream branches until domain and workflow are aligned.

---

## 3. Three-Tier Sequential Gate Questions
Present questions with dynamic recommendations derived from ingested document features:

1. **Question 1: Domain Alignment**
   - Identify the specific engineering or business domain governed by the input documents.
   - Dynamic recommendations: Extract 2~3 candidate domains directly from the `taxonomy` aliases and `key_elements` returned by `--list-only`.

2. **Question 2: Workflow Clarification**
   - Clarify the runtime lifecycle, operational procedure, or analysis sequence.
   - Dynamic recommendations: (A) Audit & Linter, (B) Reference & Query, (C) Runbook & SOP, (D) Trade-off Decision.

3. **Question 3: Delivery Routing**
   - Route to **Branch 1** (`references/type_a_research.md`): Research & Architecture Review.
   - Route to **Branch 2** (`references/type_b_skill.md`): Agent Skill Directory (`data/`, `scripts/`, `chapters/`).
