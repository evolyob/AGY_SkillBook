# Engineering & Delivery Standards

> **Recommended Command**: `/plan` (enforce Spec-First architecture and milestone chunking).
> **Execution Order**: Phase 0 (Contract Gate) >> Phase 1 (Design) >> Phase 2 (Coding) >> Phase 3 (Delivery). Governed by `agent_behavior.md`.

## 0. The 4-Item Spec Contract Gate (`spec.md`)
- **Mandate**: Every non-trivial task MUST freeze a lightweight 4-item specification (`spec.md`) as the single source of truth before code synthesis:
  1. **Goal & Non-Goals**: Concrete, verifiable deliverable vs explicit perimeter of what will NOT be built or modified.
  2. **Allowed Paths (Whitelist Perimeter)**: Explicit file paths permitted to be created or mutated. Modifications outside this perimeter are strictly prohibited.
  3. **Declared Dependencies**: Explicit list of permitted third-party packages (or standard library only). No undeclared packages may be imported.
  4. **Acceptance Criteria & Verification**: Objective, deterministic verification command (e.g. `pytest tests/ -v`; document compilation MUST verify plain-text sources `['.md', '.txt']` pass semantic gate inspection first) with concrete expected I/O.
- **Prohibit**: Generating code diffs before freezing the 4 contract items; introducing undeclared dependencies or mutating files outside declared *Allowed Paths*.

---

## 1. Design & Baseline Gate (Pre-Implementation)

### 1.1 Upstream Core-First & Refactor Integrity
- **Mandate**: Implement all enhancements directly within authoritative upstream core modules. Code refactoring and line reductions MUST preserve 100% functional parity; shortest working diff wins strictly under invariant functional equivalence.
- **Prohibit**: Strictly prohibit creating parallel one-off scripts, duplicate wrapper abstractions, or deleting business logic and validation guards merely to meet line-count budgets.

### 1.2 Active Lifecycle (Zero-EOL)
- **Mandate**: Anchor to Python >= 3.13, Node.js >= 24 LTS, Go >= 1.26, Java >= 21/25 LTS, .NET >= 10 LTS, PHP >= 8.4; dynamically verify with `endoflife.date`.
- **Prohibit**: Strictly prohibit deprecated syntax and EOL runtimes.

### 1.3 Lazy Senior (Stdlib First & Minimal Dependencies)
- **Mandate**: Prioritize language standard libraries (`urllib`, `json`, `pathlib`, `argparse`, etc.) and native platform capabilities over external packages. Anchor implementation to three Lazy Senior pillars:
  1. **Contract-Driven**: Implement the approved 4-item contract; isolate static lookup tables into backend files rather than prompt context.
  2. **Chunking**: Decompose complex features into 3~5 discrete atomic milestones, implementing and verifying one unit at a time.
  3. **Root-Cause Convergence**: Grep all invocation points and fix defects inside the shared root function; never patch individual callers.
- **Prohibit**: Avoid pip dependency bloat, premature abstractions, redundant wrapper layers (`utils.py`, `helpers.py`), and ad-hoc caller-site patches.

### 1.4 Stateless & Deterministic Execution
- **Mandate**: Enforce stateless components, pure functions, and explicit context passing for concurrency safety and idempotency.
- **Prohibit**: Strictly prohibit mutable shared/global state.

### 1.5 Security & Compliance Baselines
- **Mandate**: Strictly adhere to platform CIS Benchmarks, OWASP Suite (Web 2025, API 2023, LLM 2025+), and ASVS (v5.0.0).

---

## 2. Implementation & Cryptography Gate (During Coding)

### 2.1 Flattened Control Flow & Intent Naming
- **Mandate**: Place Guard Clauses (`if not valid: return / raise`) at function tops to keep happy path linear at zero indentation; use `match ... case` for structural dispatching. Enforce Keyword-Only arguments (`*`) for boolean switches and flags to eliminate Boolean Blindness.
- **Prohibit**: Nested `if-else` blocks deeper than 2 levels; unlabelled positional booleans (`do_work(True, 30)`); generic variable names (`data`, `temp`, `res`).

### 2.2 Useful Errors & Observability
- **Mandate**: Error messages MUST contain operational context parameters (ID, path, retry count). Use exception chaining (`raise DomainError(...) from err`) to preserve full stack traces.
- **Prohibit**: Bare `except:` handlers, swallowing exceptions silently, or using `assert` for production business logic validation.

### 2.3 Modern Cryptography & Auth
- **Mandate**: Use proven primitives (AES-GCM, Ed25519, TLS 1.3, SHA-256+) and standard RFC flows (OAuth2, OIDC, PKCE); leverage managed KMS/Vault over plaintext keys.
- **Prohibit**: Never roll custom crypto.

---

## 3. Code Deliverable Quality & Portability (Before Delivery)

### 3.1 Objective Acceptance & Subtractive Engineering
- **Mandate**: Verify completion objectively against the declared *Acceptance Criteria* command before claiming done. Audit every diff with Delete-List mindfulness, actively pruning redundant code to achieve negative net lines (Deletions > Additions).
- **Prohibit**: Declaring completion without terminal verification output; accumulating speculative "just-in-case" parameters, single-caller wrapper functions, or premature abstractions.

### 3.2 Code Portability & Zero Hardcoding
- **Mandate**: Enforce clean relative paths, platform-agnostic separators, and zero hardcoded local environment paths (`/home/`, `/Users/`, drive letters).
- **Prohibit**: Absolute local filesystem paths and hardcoded environment-specific assumptions.

### 3.3 Formatting & Syntax Purity
- **Mandate**: All deliverables MUST be syntactically valid and compile cleanly under target runtimes; markdown must use balanced 4-backtick nested code fences.
