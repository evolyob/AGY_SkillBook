# Engineering & System Governance (`system_governance.md`)

> **Role**: Single authoritative baseline for system security, agent execution boundaries, and deliverable verification.

---

## 1. Security & Cryptography Baselines
- **Modern Cryptography**: Use ONLY proven primitives (`AES-GCM`, `Ed25519`, `TLS 1.3`, `SHA-256+`) via platform KMS/libraries. NEVER roll custom crypto.
- **Security Standards**: Mandatory adherence to platform CIS Benchmarks, OWASP Suite (Web 2025, API 2023, LLM 2025+), and ASVS (v5.0.0). Never simplify away input validation or security controls.
- **Zero-EOL Runtimes**: Anchor strictly to active LTS runtimes (Python >= 3.13, Node.js >= 24, Go >= 1.26; verify via `endoflife.date`). Zero EOL packages.
- **Credential Guard**: PROHIBITED from reading, inspecting, or outputting sensitive credential files (`.ssh`, `.aws`, `.env`, `.kube`).

---

## 2. Code Portability & Environment Hygiene
- **Zero Local Hardcoding**: PROHIBITED from hardcoding host paths (`/home/`, `/Users/`, drive letters). Use relative paths via `pathlib`.
- **Secret Isolation**: Inject credentials, tokens, and keys strictly via environment variables, never into source code or test fixtures.
- **Document Syntax Purity**: Plain-text sources (`.md`, `.txt`) must pass syntax inspection; markdown code fences must use balanced 4-backtick nesting when wrapping code blocks.

---

## 3. Agent Execution Guardrails & Brakes
- **Phase 0 & Pragmatic Scope**: Read-only during architecture discussions. Localized refactorings or small bug fixes execute directly; formal spec contracts (`spec_template.md`) are required for multi-module shifts or ambiguous goals.
- **High-Risk Confirmation**: Require explicit user confirmation before executing destructive commands, mass deletions, or `git push`.
- **0-Retry Auth Protocol**: Abort immediately on `Permission Denied` or `Auth Error` (0 retries); cap operational error retries at 3 before pausing.
- Anti-Drift Circuit Breaker: Halt execution and pause if: (1) 4 consecutive tool errors or unconfirmed mutation calls occur, or (2) 3 consecutive turns accumulate > 6,000 output tokens without interaction. Record eliminated hypotheses and refocus on root cause.

---

## 4. Pre-Delivery Machine Verification (Zero Self-Assertion)
Never claim task completion without active terminal tool execution output:
1. **Compilation & Linting**: Run native compiler/linter (`python3 -m py_compile`, `tsc`, `go vet`).
2. **Zero-Leakage Scan**: Static regex scan for local paths and plaintext secrets; match count MUST be 0.
3. **Automated Test Run**: Unit test suite must pass with 100% OK.
