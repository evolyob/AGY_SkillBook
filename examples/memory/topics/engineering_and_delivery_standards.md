# Engineering & Delivery Standards

> **Recommended Command**: `/plan` (enforce Spec-First architecture and milestone chunking).

## 1. Design & Baseline Gate (Pre-Implementation)

### 1.1 Upstream Core-First & Refactor Integrity
- **Mandate**: Implement all enhancements directly within authoritative upstream core modules. Code refactoring and line reductions MUST preserve 100% functional parity; shortest working diff wins strictly under invariant functional equivalence.
- **Prohibit**: Strictly prohibit creating parallel one-off scripts, duplicate wrapper abstractions, or deleting business logic and validation guards merely to meet line-count budgets.

### 1.2 Active Lifecycle (Zero-EOL)
- **Mandate**: Anchor to Python >= 3.13, Node.js >= 24 LTS, Go >= 1.26, Java >= 21/25 LTS, .NET >= 10 LTS, PHP >= 8.4; dynamically verify with `endoflife.date`.
- **Prohibit**: Strictly prohibit deprecated syntax and EOL runtimes.

### 1.3 Lazy Senior (Stdlib First & Minimal Dependencies)
- **Mandate**: Prioritize language standard libraries (`urllib`, `json`, `pathlib`, `argparse`, etc.) and native platform capabilities over external packages. Anchor implementation to three Lazy Senior pillars:
  1. **Spec-First**: Define schemas, data models, and contracts before writing implementation code; isolate static lookup tables and datasets into backend files rather than prompt context.
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

### 2.1 Modern Cryptography & Auth
- **Mandate**: Use proven primitives (AES-GCM, Ed25519, TLS 1.3, SHA-256+) and standard RFC flows (OAuth2, OIDC, PKCE); leverage managed KMS/Vault over plaintext keys.
- **Prohibit**: Never roll custom crypto.

---

## 3. Code Deliverable Quality & Portability (Before Delivery)

### 3.1 Code Portability & Zero Hardcoding
- **Mandate**: Enforce clean relative paths, platform-agnostic separators, and zero hardcoded local environment paths (`/home/`, `/Users/`, drive letters).
- **Prohibit**: Absolute local filesystem paths and hardcoded environment-specific assumptions.

### 3.2 Formatting & Syntax Purity
- **Mandate**: All deliverables MUST be syntactically valid and compile cleanly under target runtimes; markdown must use balanced 4-backtick nested code fences.
