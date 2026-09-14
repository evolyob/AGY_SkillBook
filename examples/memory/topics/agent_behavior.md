# Agent Behavior & Execution Standards

> **Core Role**: Runtime Execution Controller & Safety Brakes. Governs agent actions, permissions, and operational pauses.

## 1. Pre-Work Gating 

### 1.1 Phase 0 Interrogation & No-Spec-No-Code Gate
- **Mandate**: Operate in strictly **Read-Only / Advisory Mode** during conceptual discussions or Phase 0 condition sync. Interrogate underspecified requirements via `/plan` or concise Q&A before synthesizing code; enforce the spec contract defined in `engineering_and_delivery_standards.md`.
- **Prohibit**: Unsolicited file writes (`write_to_file`, `replace_file_content`) or speculative coding without an approved spec.
- **Pragmatic Scope**: Clear-scope tasks and localized refactoring within existing module boundaries execute directly without ceremonial overhead. Formal spec freezing is strictly reserved for underspecified requests, multi-module architectural shifts, or explicit `/plan` sessions.

### 1.2 Credential Guard & High-Risk Boundaries
- **Mandate**: Require explicit user confirmation before executing high-risk commands (`git push`, `kubectl`, mass deletions). Zero unconfirmed pushes.
- **Prohibit**: Reading, outputting, or inspecting sensitive credentials (`.ssh`, `.aws`, `.env`, `.kube`).
- **Failure Protocol**: Abort immediately on `Permission Denied` / `Auth Error` (0 retries); cap non-permission retries at 3 before pausing for guidance.

---

## 2. In-Flight Governance & Anti-Drift 

### 2.1 Scope Drift & Change Protocol Pause
- **Mandate**: Pause execution immediately if implementation requires mutating files outside declared *Allowed Paths* or introducing undeclared dependencies; explain the scope expansion and obtain explicit confirmation before proceeding.
- **Prohibit**: Silently mutating files outside *Allowed Paths* or expanding dependency footprint without prior spec amendment.

### 2.2 7-Step Anti-Drift Checkpoint
- **Mandate**: Pause at 7 consecutive debugging tool calls; summarize eliminated hypotheses to `../active_task.md` and refocus on root cause.

### 2.3 Dynamic Skill Discovery
- **Mandate**: Dynamically evaluate available skills at runtime and read target `SKILL.md` before execution.

---

## 3. Pre-Delivery Machine Verification Protocol 

### 3.1 Deterministic Verification (Zero Self-Assertion)
- **Mandate**: Never rely on visual inspection or generative self-assertion. Before claiming completion or delivery, actively execute automated runtime checks via tool calls:
  1. **Compilation & Syntax**: Run native compiler/linter (`python3 -m py_compile`, `tsc`, `go vet`, etc.).
  2. **Zero-Leakage Scan**: Execute static regex pattern scan for local host paths (`/home/<user>/`, `/Users/<user>/`, drive letters) and plaintext secrets; pattern match count MUST be 0.
  3. **Verification Suite**: Ensure domain verifiers and declared test suites pass with zero blockers.
- **Prohibit**: Stating a task, fix, or delivery is complete without presenting tool execution output.
