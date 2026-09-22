# Specification Contract: [Skill / Feature Name]

> **Status**: `DRAFT` | `APPROVED` | `FROZEN`  
> **Law**: No-Spec-No-Code. Never generate code or modify files before this contract is frozen.

---

## 1. Goal & Non-Goals (Firewall Against Scope Creep)
- **Goal**: [Concrete, measurable deliverable; the exact pain point being solved]
- **Non-Goals (CRITICAL - What MUST NOT be done)**:
  - PROHIBITED: [Explicitly excluded scope, e.g., do not calculate speculative formulas, do not reformat existing layouts, do not modify unrelated files]
  - PROHIBITED: [Any unapproved architectural refactoring or speculative features]

---

## 2. Allowed Paths (Strict Whitelist Perimeter)
Modifications outside this perimeter are strictly prohibited:
- `scripts/<module_name>.py`
- `SKILL.md`
- `tests/test_<module_name>.py`

---

## 3. Declared Dependencies & Zero-EOL Runtime
- **Target Runtime**: Python >= 3.13 (LTS) / Node.js >= 24 (LTS)
- **Permitted Packages**: Standard Library Only (`pathlib`, `json`, `re`, `argparse`, `sys`)
- **Prohibition**: Zero unapproved third-party packages; zero EOL libraries.

---

## 4. Acceptance Criteria & Verification Command
- **Deterministic Verification Command**:
  ```bash
  python3 -m unittest discover -s tests
  ```
- **Expected Outcome**:
  - [x] All unit tests pass (`OK`).
  - [x] `/audit-skill` passes with 0 FAIL, 0 WARN.
  - [x] Execution completes within expected performance threshold.

---

## 5. SKILL.md Interface Contract (Purity Check)
- [ ] **Minimal Routing Table**: Only declare Mission and input ➔ CLI command ➔ output table.
- [ ] **Zero Abstract Jargon**: No buzzwords without backing scripts.
- [ ] **100% Executable**: Every script and argument in `SKILL.md` must physically exist and run locally.
