# Core Memory & Template Index

> **Directive**: Keep core memory under 35 lines. Load governance topic and templates on-demand. Never dump unprompted.

---

## 1. System Governance Topics (`topics/` - Security & Architecture Baselines)

### 1. Engineering & System Governance
- **Domain**: Cryptography Baselines (AES-GCM/Ed25519/TLS 1.3), OWASP/CIS, Zero-EOL (Python/Node/Go), Credential Guard, 0-Retry Auth, 7-Step Pause, Pre-Delivery Verification
- **Path**: `topics/system_governance.md`
- **Keywords / Triggers**: OWASP, CIS, Cryptography, AES-GCM, TLS 1.3, Zero-EOL, Credential Guard, Anti-Drift, Zero-Leakage, Pre-Delivery Verification

### 2. User Preferences & Task Architecture
- **Domain**: Knowledge Purity, Compute vs Cognitive Division of Labor, Compact Formatting (Surgical Diffs, ASCII Trees)
- **Path**: `topics/user_preferences.md`
- **Keywords / Triggers**: Preferences, Division of Labor, Non-Abstract, Formatting, Diff, ASCII Tree

---

## 2. Reference Templates (`templates/` - Implementation Contracts & Scaffolds)

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

## 3. Minimal User Preference Boilerplate (Example)
- **Export Path**: `~/Downloads` for all deliverables (.docx, .xlsx, .pptx, .pdf).
- **Encoding**: `utf-8-sig` (UTF-8 with BOM) for cross-platform compatibility.
- **Guardrail**: Write to persistent memory only upon explicit user command.
