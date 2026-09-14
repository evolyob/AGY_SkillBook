# Engineering & Delivery Standards

> **Recommended Command**: `/plan` (enforce Spec-First architecture and milestone chunking).
> **Execution Order**: Phase 0 (Contract Gate) >> Phase 1 (Design) >> Phase 2 (Coding) >> Phase 3 (Delivery). Governed by `agent_behavior.md`.

## 0. The 4-Item Spec Contract & System Baselines (`spec.md`)
- **Mandate**: Every non-trivial task MUST freeze a lightweight 4-item specification (`spec.md`) as the single source of truth before code synthesis, anchored to active runtimes and security baselines:
  1. **Goal & Non-Goals**: Concrete, verifiable deliverable vs explicit perimeter of what will NOT be built or modified.
  2. **Allowed Paths (Whitelist Perimeter)**: Explicit file paths permitted to be created or mutated. Modifications outside this perimeter are strictly prohibited.
  3. **Declared Dependencies & Zero-EOL Runtime**: Anchor to active LTS runtimes (Python >= 3.13, Node.js >= 24 LTS, Go >= 1.26; dynamically verify via `endoflife.date`). Explicit list of permitted third-party packages (or stdlib only).
  4. **Acceptance Criteria & Security Baseline**: Objective, deterministic verification command (e.g. `pytest tests/ -v`; document compilation MUST verify plain-text sources `['.md', '.txt']` pass semantic gate inspection first) with concrete expected I/O; mandatory adherence to platform CIS Benchmarks, OWASP Suite (Web 2025, API 2023, LLM 2025+), and ASVS (v5.0.0). Proven cryptographic primitives (AES-GCM, Ed25519, TLS 1.3, SHA-256+) and managed KMS/Vault; never roll custom crypto. Security controls and input validation MUST NOT be simplified away.
- **Prohibit**: Generating code diffs before freezing the 4 contract items; using EOL runtimes or deprecated syntax; bypassing security baselines; introducing undeclared dependencies; mutating files outside declared *Allowed Paths*.

---

## 1. Design & Architecture Gate (Pre-Implementation)

### 1.1 Upstream Core-First & Refactor Integrity
- **Mandate**: Implement all enhancements directly within authoritative upstream core modules. Code refactoring and line reductions MUST preserve 100% functional parity; shortest working diff wins strictly under invariant functional equivalence.
- **Prohibit**: Strictly prohibit creating parallel one-off scripts, duplicate wrapper abstractions, or deleting business logic and validation guards merely to meet line-count budgets.

### 1.2 Standard Library First & Data Isolation (Minimal Dependencies)
- **Mandate**: Prioritize language standard libraries (`urllib`, `json`, `pathlib`, `argparse`, etc.) and native platform capabilities over external packages. Decompose complex implementations into 3~5 discrete atomic milestones (Chunking). Isolate static lookup tables and datasets into dedicated backend files rather than prompt context.
- **Prohibit**: Introducing third-party package dependencies when standard library primitives suffice; hardcoding large static dictionaries directly into prompts or domain logic.

### 1.3 Stateless & Constrained States (Pure Core)
- **Mandate**: Enforce stateless components, pure deterministic functions (Functional Core), and explicit context passing for concurrency safety and idempotency; confine I/O and network calls to the outer shell. Model domain states using `StrEnum` and Union types so invalid states are unrepresentable. Defensively clamp layout sizes, intervals, counts, and timeouts (e.g. `max(MIN_FLOOR, val)`) to mathematically guarantee valid geometry.
- **Prohibit**: Strictly prohibit mutable shared/global state, mutable default arguments (`target=[]`), or inlining I/O and DB writes inside core calculation logic.

---

## 2. Implementation & Coding Gate (During Coding)

### 2.1 Flattened Control Flow & Intent Naming
- **Mandate**: Place Guard Clauses (`if not valid: return / raise`) at function tops to keep happy path linear at zero indentation; use `match ... case` for structural dispatching. Enforce Keyword-Only arguments (`*`) for boolean switches and flags to eliminate Boolean Blindness. Name identifiers after concrete domain entities.
- **Prohibit**: Nested `if-else` blocks deeper than 2 levels; unlabelled positional booleans (`do_work(True, 30)`); generic variable names (`data`, `temp`, `res`).

### 2.2 Useful Errors & Observability
- **Mandate**: Error messages MUST contain operational context parameters (ID, path, retry count). Use exception chaining (`raise DomainError(...) from err`) to preserve full stack traces.
- **Prohibit**: Bare `except:` handlers, swallowing exceptions silently, or using `assert` for production business logic validation.

---

## 3. Code Deliverable Quality & Portability (Before Delivery)

### 3.1 Objective Acceptance & Subtractive Engineering (Primary Quality Gate)
- **Mandate**: Verify completion objectively against the declared *Acceptance Criteria* command before claiming done. Fix defects inside the root shared function rather than patching callers (Root-Cause Convergence). Audit every diff with Delete-List mindfulness, actively pruning redundant wrapper layers (`utils.py`, `helpers.py`), single-caller functions, and premature abstractions to achieve negative net lines (Deletions > Additions).
- **Prohibit**: Declaring completion without terminal verification output; ad-hoc caller-site patching; accumulating speculative "just-in-case" parameters, single-caller wrapper abstractions, or premature utility files.

### 3.2 Code Portability & Zero Hardcoding
- **Mandate**: Enforce clean relative paths, platform-agnostic separators, and zero hardcoded local environment paths (`/home/`, `/Users/`, drive letters) or credentials. Store all secrets, tokens, and keys in environment variables or managed secret stores.
- **Prohibit**: Absolute local filesystem paths, hardcoded credentials, and plaintext secrets in code or configuration files.

### 3.3 Formatting & Syntax Purity
- **Mandate**: All deliverables MUST be syntactically valid and compile cleanly under target runtimes; markdown must use balanced 4-backtick nested code fences.
