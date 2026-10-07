# Specification Contract: [Skill / Feature Name]

> **Status**: `DRAFT` | `APPROVED` | `FROZEN`  
> **Laws**: 
> 1. **No-Spec-No-Code**: Never generate code or modify files before this contract is frozen.
> 2. **Measure-Not-Assert**: No claimed quality, token, or latency improvement without reproducible before/after benchmark data.

---

## 1. Goal & Non-Goals (Firewall Against Scope Creep)
- **Goal**: [Concrete, measurable deliverable; the exact pain point being solved]
- **Non-Goals (CRITICAL - What MUST NOT be done)**:
  - PROHIBITED: [Speculative hypotheses or academic concepts without passing empirical benchmark gates]
  - PROHIBITED: [Any unapproved architectural refactoring or unmeasured wrapper layers]
  - PROHIBITED: [Modifying files outside the declared allowed paths]

---

## 2. Allowed Paths (Strict Whitelist Perimeter)
Modifications outside this perimeter are strictly prohibited:
- `scripts/<module_name>.py`
- `SKILL.md`
- `tests/test_<module_name>.py`

---

## 3. Declared Dependencies & Zero-EOL Runtime
- **Target Runtime**: Python >= 3.13 (LTS) / Node.js >= 24 (LTS)
- **Permitted Packages**: Standard Library Only (`pathlib`, `json`, `re`, `argparse`, `sys`, `unicodedata`)
- **Prohibition**: Zero unapproved third-party packages; zero EOL libraries.

---

## 4. Acceptance Criteria & Empirical Verification
- **Deterministic Verification Command**:
  ```bash
  python3 -m unittest discover -s tests
  ```
- **Quantitative & Quality Gates**:
  - [ ] All unit tests pass (`OK`).
  - [ ] `/audit-skill` passes with 0 FAIL, 0 WARN.
  - [ ] **Empirical Delta**: Measured improvements with concrete before/after benchmark numbers (e.g., token savings >= X%, latency <= Y ms).
  - [ ] **Data Quarantine**: 100% synthetic/public fixtures; never commit raw copyrighted text or live telemetry corpora.

---

## 5. SKILL.md Interface Contract (Purity Check)
- [ ] **Minimal Routing Table**: Only declare Mission and input ➔ CLI command ➔ output table.
- [ ] **Zero Abstract Jargon**: No buzzwords without backing scripts.
- [ ] **100% Executable**: Every script and argument in `SKILL.md` must physically exist and run locally.
