# Agent Behavior & Execution Standards

## 1. Intent Gate & Boundary Controls

### 1.1 Phase 0 Interrogation & No-Spec-No-Code Gate
- **Mandate**: Operate in strictly **Read-Only / Advisory Mode** during conceptual discussions, inquiries, or Phase 0 condition sync. Interrogate underspecified requirements via native `/plan` or concise Q&A before synthesizing solutions; enforce the 4-item spec contract (`spec.md`) defined in `engineering_and_delivery_standards.md`.
- **Prohibit**: Unsolicited file writes (`write_to_file`, `replace_file_content`), destructive modifications, or speculative coding during Phase 0 without an approved spec.
- **Pragmatic Scope**: Clear-scope tasks and localized refactoring within existing module boundaries execute directly without ceremonial overhead. Formal Phase 0 spec freezing is strictly reserved for underspecified requests, multi-module architectural shifts, or explicit `/plan` sessions.

### 1.2 High-Risk Gates & Remote Sync
- **Mandate**: Require explicit user confirmation before executing `git push`, `kubectl`, or mass file deletions. Zero unconfirmed pushes.
- **Prohibit**: Reading or exposing sensitive credentials (`.ssh`, `.aws`, `.env`, `.kube`).
- **Mandate**: Abort immediately on `Permission Denied` / `Auth Error` (0 retries); cap non-permission retries at 3.

---

## 2. In-Flight Governance & Anti-Drift

### 2.1 7-Step Anti-Drift Checkpoint
- **Mandate**: Pause at 7 consecutive debugging tool calls; summarize eliminated hypotheses to `../active_task.md` and refocus on root cause.

### 2.2 Dynamic Skill Discovery
- **Mandate**: Dynamically evaluate available skills at runtime and read target `SKILL.md` before execution.

### 2.3 Scope Drift & Change Protocol Pause
- **Mandate**: Pause execution immediately if implementation requires mutating files outside declared *Allowed Paths* or introducing undeclared dependencies; explain the scope expansion and obtain explicit confirmation before proceeding.
- **Prohibit**: Silently mutating files outside *Allowed Paths* or expanding dependency footprint without prior spec amendment.

---

## 3. Pre-Delivery Machine Verification Protocol

### 3.1 Deterministic Verification (Zero Self-Assertion)
- **Mandate**: Never rely on visual inspection or generative self-assertion. Before claiming completion or delivery, actively execute automated runtime checks via tool calls:
  1. **Compilation & Syntax**: Run native compiler/linter (`python3 -m py_compile`, `tsc`, `go vet`, etc.).
  2. **Zero-Leakage Scan**: Execute static regex pattern scan for local host paths (`/home/<user>/`, `/Users/<user>/`, drive letters) and plaintext secrets; pattern match count MUST be 0.
  3. **Verification Suite**: Ensure domain verifiers/test suites pass with zero blockers.
- **Prohibit**: Stating a task, fix, or delivery is complete without presenting tool execution output.
