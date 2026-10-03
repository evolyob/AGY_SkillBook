# Specification Contract Protocol (`spec_contract.md`)

> **Core Philosophy**: **No-Spec-No-Code**. Never generate functional code or modify existing scripts before the specification contract is frozen.

---

## 1. Goal & Non-Goals Firewall (Integrated MISSION Rules)

### Goal (Concrete Deliverable)
- **Concrete Outcome (Why)**: Single-sentence observable outcome solving an exact technical or architectural problem.
- **Anti-Abstract Mandate**: Strictly prohibit vague verbs like "understand", "support", or "improve". Mandate concrete deliverables (e.g. standalone CLI script, pure parser).
- **Observable Success**: Explicit state or metric that proves completion (e.g. 100% tests pass, latency $\le$ 20ms).

### Non-Goals (Scope Firewall & Out-of-Scope Isolation)
- **Adjacent Isolation**: Explicitly list high-temptation adjacent modules or files that MUST NOT be touched.
- **Dependency Quarantine**: Strictly prohibit unapproved third-party packages or speculative wrapper layers.
- **Perimeter Lockdown**: Strictly block modifications to any file outside the declared *Allowed Paths*.

---

## 2. Allowed Paths Perimeter (Strict Whitelist)
Modifications outside this declared perimeter are strictly blocked:
- `scripts/<module_name>.py`
- `SKILL.md`
- `tests/test_<module_name>.py`

---

## 3. Seam-Driven Verification Contract
- **Seam**: Declare the highest single entry point where the entire feature can be tested end-to-end.
- **Deterministic Verification Command**:
  ```bash
  python3 -m unittest discover -s tests
  ```
- **Quantitative Quality Gates**:
  - [ ] 100% unit tests pass (`OK`).
  - [ ] Maximum function nesting depth $\le 2$.
  - [ ] Zero bare `except:` clauses; explicit exception chaining.
  - [ ] Negative or zero net line diffs achieved on refactors (Deletions $\ge$ Additions).
