# Core Memory & Topic Index

> **Primary Directive**: Read `core.md` at conversation start. Load topic files ONLY when triggered by relevant domains. Never dump full topics unprompted.

---

## 1. Active Memory Topics (`topics/` - Rules & Behavioral Gates)

### 1. Engineering & Delivery Standards
- **Domain**: Spec Contract, Architecture Design, Clean Code Craft, Security Baselines, Subtractive Delivery
- **Topic Path**: `topics/engineering_and_delivery_standards.md`
- **Keywords / Triggers**: Spec Contract, spec.md, Zero-EOL, CIS Hardening, OWASP Suite, Cryptography, Upstream Core-First, Stdlib First, Data Isolation, Pure Core, StrEnum, Clamp, Guard Clauses, Useful Errors, Subtractive Engineering, Root-Cause Convergence, Code Portability, Zero Leakage
- **Associated Templates**: `templates/spec_template.md`, `templates/senior_coding_laws.md`
- **Associated Command**: `/plan` (Spec Contract & Milestone Chunking)

### 2. Agent Behavior & Execution Protocol
- **Domain**: Phase 0 Gating, No-Spec-No-Code, Scope Drift Pause, Anti-Drift Governance, Machine Verification
- **Topic Path**: `topics/agent_behavior.md`
- **Keywords / Triggers**: Phase 0 Interrogation, No-Spec-No-Code Gate, Read-Only Mode, Human Approval, High-Risk Gates, Scope Drift Pause, 7-Step Anti-Drift, Dynamic Skill Discovery, Deterministic Verification, Zero Self-Assertion, Zero-Leakage Scan, Credential Guard
- **Associated Templates**: `templates/vibe_skill_lifecycle.md`

---

## 2. Reference Templates (`templates/` - Scaffolds & Implementation Laws)

### 1. 4+1 Item Specification Contract Template
- **Path**: `templates/spec_template.md`
- **Role**: Concrete boilerplate for Phase 0 gating (Goal/Non-Goals firewalls, Whitelist paths, Zero-EOL deps, Deterministic verification, and SKILL.md interface purity).

### 2. Vibe Coding Skill Lifecycle & Evolution Guide
- **Path**: `templates/vibe_skill_lifecycle.md`
- **Role**: Standard 4-step build flow, 5 evolution traps avoidance, surgical combo refactoring laws, and 8-point pre-delivery cheatsheet.

### 3. Senior Clean Code & Architecture Radar
- **Path**: `templates/senior_coding_laws.md`
- **Role**: 5-step implementation hygiene (Boundary isolation, Functional core, Flattened flow <= 2, Useful errors, Strict anti-whack-a-mole).

### 4. Skill Data & Indexing Laws
- **Path**: `templates/SKILL_DATA_SPEC.md`
- **Role**: Pattern A flat catalog default vs Pattern B grouped exception, in-memory inverted index mandate (N > 20, O(1) lookup), zero envelope tax.
