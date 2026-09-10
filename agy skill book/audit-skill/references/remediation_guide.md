# Universal Skill & Code Remediation Runbook

> **Policy**: This runbook provides universal remediation procedures for alerts triggered by `audit.py` (Python / spec audit) and `audit_frontend.py` (frontend / asset audit). Centered on "minimal dependencies, native-first, and uncompromising security guardrails," it governs full-stack applications and tooling scripts.

---

## Universal Remediation Ladder

When an audit alert fires, evaluate solutions top-to-bottom and stop at the first matching tier:
1. **Delete (YAGNI)**: Eliminate dead code, unused flags, and single-caller wrapper functions directly.
2. **Root-Cause Governance**: Defend inside the root shared function. Never copy-paste ad-hoc patches across call sites.
3. **Platform / Stdlib First**: Prefer Python standard library modules and native Web / browser APIs over third-party packages.
4. **Guard Clause**: Invert conditions to return early, flatten indentation levels, and avoid unnecessary helper abstractions.
5. **Preserve Security Controls**: Never simplify away input validation, error handling that prevents data loss, or XSS/injection sanitization.

---

## 1. Universal Security & Path Guardrails

### 1. Hardcoded Absolute Paths (`Hardcoded absolute user path`)
* **Remediation**: Remove hardcoded user paths (`/Users/...` or `/home/...`). Resolve paths dynamically or relatively.
  * **Python**: `Path.home() / "project"` or `Path(__file__).resolve().parent`
  * **JS/TS**: `path.resolve(__dirname, ...)` or environment variables `process.env.DATA_DIR`

### 2. Dangerous Dynamic Execution (`eval` / `exec` / `os.system` / `new Function`)
* **Remediation**: Never execute unvalidated dynamic strings.
  * **Python**: Replace `os.system` with `subprocess.run([...])`; replace `eval` with `ast.literal_eval`.
  * **JS/TS**: Prohibit `eval()` / `new Function()`. Parse structured strings with `JSON.parse()`.

### 3. Plaintext Secrets & Private IPs (`Plaintext secret` / `Internal private IP`)
* **Remediation**: Extract secrets into environment variables. Inject internal IPs via configuration files or parameters.

---

## 2. Modernization & Anti-Legacy Standards

### 1. Python Removed Standard Libraries (`Zero-EOL: removed stdlib module`)
* **Remediation**: Align with PEP 594 using modern standard library alternatives (Python 3.13+):
  * `cgi` -> `urllib.parse`
  * `pipes` -> `shlex`
  * `distutils` -> `setuptools` or `sys`

### 2. Frontend Deprecated Syntax & DOM Operations (`Legacy syntax`)
* **Remediation**: Upgrade to modern Web standards:
  * `var` -> Use block-scoped `const` or `let`
  * `XMLHttpRequest` -> Use native `fetch()`
  * `document.write()` -> Use modern DOM manipulation APIs (e.g., `element.append()`)

---

## 3. Dependency & Asset Budgets

### 1. Undeclared Dependencies & Package Bloat (`undeclared dependency`)
* **Remediation**: Prioritize built-in platform capabilities to eliminate unnecessary dependencies:
  * **Python**: `requests` -> `urllib.request`; `pyyaml` -> `json`; `bs4` -> `html.parser`
  * **Frontend**: Date picker / color picker -> Native `<input type="date">`; simple animations -> Native CSS

### 2. Line Limits & Asset Budgets (`Lines > limit` / `Asset budget > 100KB`)
* **Remediation**:
  * **Backend line overflow**: Prune single-caller wrappers; consolidate repetitive branches into "1 spec dictionary + 1 loop".
  * **Frontend asset overflow (>100KB)**: Enable code splitting; remove heavy third-party libraries (e.g., replace lodash with native Array methods).

### 3. Excessive Nesting Depth (`nested if-block depth > 2`)
* **Remediation**: Invert conditions and return early (Guard Clause) at the start of functions to flatten indentation.

```text
[Anti-Pattern]: Depth > 2
if (data && data.isValid()) {
    if (data.hasPermission()) {
        return data.execute();
    }
}
```
```python
# [Remediation]: Guard Clause
if not data or not data.is_valid() or not data.has_permission():
    return None
return data.execute()
```

---

## 4. Stack-Specific Hardening

### 1. Python AST Hardening (`audit.py`)
* **Mutable Default Arguments**: Replace `def f(x=[])` with `def f(x=None): x = [] if x is None else x`.
* **Bare Except Handlers**: Prohibit `except: pass`. Use pre-condition checks (`if path.exists():`) or catch explicit exception classes.
* **Text Encoding**: Always specify explicit encoding for `open()` (e.g., `encoding="utf-8"`, or `"utf-8-sig"` if BOM is present).

### 2. Frontend Rich-Text XSS Defense (`audit_frontend.py`)
* **Remediation**: When assigning to `innerHTML`, `v-html`, or `dangerouslySetInnerHTML`, always sanitize through DOMPurify:
```javascript
// [Anti-Pattern]: Direct unsanitized HTML injection
el.innerHTML = userContent;

// [Remediation]: Sanitized via DOMPurify
el.innerHTML = DOMPurify.sanitize(userContent);
```

### 3. Prompt Data Bloat & Decoupling (`Heavy static asset`)
* **Remediation**: Never inline large lookup tables into prompt or markdown files. Keep data on disk and implement backend fallback resolution so callers only pass intent:
  * **Backend Code**: Read via `Path(__file__).parent / "data.json"`; gracefully fallback to a safe default if unmatched.
  * **Prompt Boundary**: Keep documentation declarative; callers pass high-level values without reciting the entire catalog.