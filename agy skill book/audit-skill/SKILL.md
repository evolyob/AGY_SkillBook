---
name: audit-skill
description: Audits skills and Python scripts against quantitative context-efficiency, Lazy Senior standards, security boundaries, and predictability metrics.
---

# Senior Skill & Python Code Auditor

## Objective
Provide automated 12-Gate quality, defensive bounds, and security guardrail auditing for skills, Markdown specifications, and Python scripts.

---

## Routing & Architecture

| Component | Type | Responsibility |
|---|---|---|
| `scripts/audit.py` | Executable Engine | One-shot automated 12-Gate inspection (<20ms) for Skills, Markdown, Python, and Security |
| `scripts/audit_frontend.py` | Executable Engine | Specialized security, syntax, and dependency discovery auditor for JS/TS/Vue scripts |
| `references/remediation_guide.md` | Reference Guide | Standard refactoring templates and patterns for non-compliant skills |

---

## Execution Workflow

### Step 1: Execute Automated One-Shot Auditor
- **Action**: Run the universal auditor in a single tool call:
  ```bash
  python3 <skill_dir>/scripts/audit.py <target_path>
  ```
- **12 Automated Gates**:
  - **Quality & Bounds**: Zero-EOL (Python >= 3.13, Node >= 24 LTS), explicit dependency declarations (Frontmatter & Pre-flight check), stdlib priority, clean imports, encoding safety, line budget.
  - **Markdown & Layout**: 4-backtick nesting, code fence balance, path purity, embedded snippet validation.
  - **Security Guardrails**: Zero plaintext secrets, zero privilege escalation, zero dynamic execution, zero prompt injections.

### Step 2: Fact-Based Findings Report
- **Action**: Summarize audit output using the **1-2-3 Fact-Based format**:
  1. `Finding`: The factual condition observed (`PASS`, `WARN`, or `FAIL`).
  2. `Objective Evidence`: Exact line numbers, files, and metrics from `audit.py`.
  3. `Requirement`: The explicit rule or threshold.

### Step 3: User Gate & Remediation
- **Action**: If blockers/advisories exist and user requests fixes, consult `references/remediation_guide.md` to propose concrete diffs.
- **Criteria**: Obtain explicit approval before modifying any files.
