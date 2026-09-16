# Antigravity Production Templates & Memory Architecture

This directory provides production-grade templates and scaffolds for building deterministic, context-efficient skills and tools in Google Antigravity.

---

## 1. Core Philosophy: Intuitive, Non-Abstract & Clear Division of Labor

Internal specifications and templates are written directly for the AI agent to execute. They prioritize high-signal constraints over abstract dogma:

1. **Clear Division of Responsibilities**:
   - **Deterministic Computation (Python stdlib)**: Handles 100% of arithmetic, data filtering, keyword indexing, and schema validation. Never offload computation or heavy lookup to LLM deduction.
   - **Cognitive Orchestration (LLM)**: Focuses strictly on intent routing, candidate selection, user clarification, and presentation formatting.
   - **Boundary Enforcement (Spec Contract)**: Freezes Non-Goals, Allowed Paths, and Verification Commands before touching code.
2. **Zero Overhead & Zero Hallucination**:
   - Templates provide concrete copy-paste skeletons, eliminating vague philosophical essays and token-wasting meta-theories.

---

## 2. Template Suite Overview (`templates/`)

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
├── core.md                 # Lean template index & user preferences sample (< 30 lines)
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
mkdir -p ~/../memory/templates
```

### Step 2: Deploy Scaffolds
```bash
# Copy core index sample
cp examples/memory/core.md ~/../memory/core.md

# Copy production templates
cp examples/memory/templates/*.md ~/../memory/templates/
```

### Step 3: Link in System Instructions (`RULE[user_global]`)
```markdown
Persistent Memory Management:
  - Scope: Use `~/../memory/core.md` as index; workspace data MUST remain in `<workspace>/.memory/project.md`.
  - Load/Save: Read `core.md` at conversation start. Load templates ONLY when building or refactoring skills.
```
