# Core Memory & Template Index

> **Directive**: Keep core memory under 35 lines. Load templates on-demand when creating or modifying skills/code. Never dump unprompted.

---

## 1. Reference Templates (`templates/` - Scaffolds & Implementation Laws)

### 1. Specification Contract (No-Spec-No-Code)
- **Path**: `templates/spec_template.md`
- **Role**: Phase 0 boundary freezing (Goal/Non-Goals firewalls, Whitelist paths, Zero-EOL deps, Verification command).

### 2. Senior Clean Code Radar (Architecture & Craft)
- **Path**: `templates/senior_coding_laws.md`
- **Role**: 5-step implementation hygiene (Boundary isolation, Pure functional core, Flattened flow <= 2, Useful errors, Subtractive delivery).

### 3. Skill Data & Indexing Laws
- **Path**: `templates/SKILL_DATA_SPEC.md`
- **Role**: Pattern A flat catalog default vs Pattern B grouped exception, in-memory inverted index mandate (N > 20, O(1) lookup), zero envelope tax.

### 4. Vibe Skill Lifecycle & Evolution Guide
- **Path**: `templates/vibe_skill_lifecycle.md`
- **Role**: Standard 4-step build flow, 5 evolution traps rejection, and 8-point pre-delivery cheatsheet.

---

## 2. Operational Safety Brakes
- **High-Risk Confirmation**: Must obtain explicit confirmation before executing destructive commands or unreviewed `git push`.
- **7-Step Debug Pause**: Halt execution after 7 consecutive tool errors to summarize eliminated hypotheses and refocus on root cause.

---

## 3. Minimal User Preference Boilerplate (Example)
- **Export Path**: `~/Downloads` for all deliverables (.docx, .xlsx, .pptx, .pdf).
- **Encoding**: `utf-8-sig` (UTF-8 with BOM) for cross-platform compatibility.
- **Guardrail**: Write to persistent memory only upon explicit user command.
