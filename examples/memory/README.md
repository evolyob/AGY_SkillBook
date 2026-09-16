# Antigravity Production Templates & Memory Architecture

This directory provides production-grade templates and governance scaffolds for building deterministic, context-efficient skills and tools in Google Antigravity.

---

## 1. Core Architecture: System Governance & Concrete Templates

The memory architecture separates system security baselines from implementation scaffolds:

1. **System Governance Topic (`topics/system_governance.md`)**:
   - Single authoritative standard for security (OWASP, AES-GCM/Ed25519/TLS 1.3), Zero-EOL runtimes, credential protection, 0-retry auth protocol, 7-step anti-drift pause, and pre-delivery zero-leakage machine verification.
2. **Implementation Templates Suite (`templates/*.md`)**:
   - High-signal scaffolds for building code, schemas, and skills with clear division of labor (Python computes, LLM formats, Spec enforces boundaries).

---

## 2. Component Directory & Responsibilities

### Global System Governance (`topics/`)

| Topic | File | Core Responsibility & Boundary |
|---|---|---|
| **System Governance** | [`topics/system_governance.md`](topics/system_governance.md) | **Security & Runtime Guardrails**: OWASP/CIS standards, proven cryptography (AES-GCM, Ed25519, TLS 1.3), Zero-EOL runtimes (Python/Node/Go), credential file blacklist (`.ssh`, `.env`), 0-retry auth pause, 7-step debug pause, and pre-delivery machine verification. |

### Reference Templates (`templates/`)

| Template / Contract | File | Core Responsibility & Boundary |
|---|---|---|
| **Specification Contract** | [`spec_template.md`](templates/spec_template.md) | **No-Spec-No-Code Gate**: Freezes Goal, Non-Goals (what MUST NOT be done), Allowed Paths whitelist, dependencies, and deterministic verification command. |
| **Clean Code Radar** | [`senior_coding_laws.md`](templates/senior_coding_laws.md) | **5-Step Implementation Hygiene**: Boundary isolation, pure functional core, flattened flow (max `if` depth $\le 2$), useful error context, and subtractive delivery. |
| **Skill Data Standards** | [`SKILL_DATA_SPEC.md`](templates/SKILL_DATA_SPEC.md) | **Data & Indexing Rules**: Pattern A (flat list) universal default, thresholded in-memory inverted index ($N > 20$, $O(1)$ lookup), zero envelope tax. |
| **Skill Lifecycle Guide** | [`vibe_skill_lifecycle.md`](templates/vibe_skill_lifecycle.md) | **Evolution & Quality Guard**: 4-step build flow, 5 evolution traps rejection (no cognitive dumping, no ghost tools, no prompt-script contradictions), and 8-point pre-delivery cheatsheet. |

---

## 3. Directory Layout

```text
examples/memory/
├── README.md               # Architecture overview and usage guide
├── core.md                 # Lean index & user preferences sample (< 35 lines)
├── topics/                 # Authoritative system governance & security
│   └── system_governance.md # Security baselines, runtime EOL, & agent execution brakes
└── templates/              # Concrete implementation scaffolds & contracts
    ├── spec_template.md    # 4+1 item specification contract boilerplate
    ├── senior_coding_laws.md # Clean code 5-step engineering radar
    ├── SKILL_DATA_SPEC.md  # Pattern A flat list vs Pattern B grouped taxonomy
    └── vibe_skill_lifecycle.md # 4-step lifecycle, 5 traps, 8-point checklist
```

---

## 4. Deployment to Local Environment

### Step 1: Create Memory Directories
```bash
mkdir -p ~/../memory/topics ~/../memory/templates
```

### Step 2: Deploy Scaffolds
```bash
# Copy core index sample
cp examples/memory/core.md ~/../memory/core.md

# Copy system governance topic
cp examples/memory/topics/system_governance.md ~/../memory/topics/

# Copy production templates
cp examples/memory/templates/*.md ~/../memory/templates/
```

### Step 3: Link in System Instructions (`RULE[user_global]`)
```markdown
Persistent Memory Management:
  - Scope: Use `~/../memory/core.md` as index; workspace data MUST remain in `<workspace>/.memory/project.md`.
  - Load/Save: Read `core.md` at conversation start. Load governance topic and templates on-demand.
```
