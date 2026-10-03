# Specification Contract Protocol (`spec_contract.md`)

> **Core Philosophy**: **No-Spec-No-Code**. Never generate functional code or modify existing scripts before the specification contract is frozen.

---

## 1. Goal & Non-Goals Firewall
- **Goal**: Concrete, single-sentence deliverable solving an exact technical or architectural problem.
- **Non-Goals (CRITICAL Scope Firewall)**:
  - PROHIBITED: Unapproved third-party dependencies or external connections.
  - PROHIBITED: Speculative abstractions or wrapper layers without empirical benchmark backing.
  - PROHIBITED: Modifying any file outside the declared *Allowed Paths*.

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
