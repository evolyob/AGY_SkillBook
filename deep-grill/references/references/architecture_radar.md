# Architecture & Clean Code Radar (`architecture_radar.md`)

> **Core Philosophy**: Practical 5-step engineering radar for resilient, minimal, and secure code architecture.

---

## 1. The 5-Step Engineering Radar

### Step 1: Own the Boundary & Hash Lookups
- Isolate volatile third-party SDKs behind structural protocols (`typing.Protocol`).
- Use standard library `pathlib`: enforce `Path.resolve()` and `Path.is_relative_to()` against path traversal.
- Index lookup data via hash dictionaries $O(1)$; prohibit nested looping $O(N^2)$.

### Step 2: Pure Core & Constrained States
- Confine decision logic to pure, deterministic functions without side effects.
- Use `enum.StrEnum` and Union types so invalid business states are unrepresentable.
- Defensively clamp numeric layouts and time intervals to prevent negative geometry.

### Step 3: Flattened Flow & Intent Naming
- Place Guard Clauses (`if not valid: return`) at function tops; maximum nesting depth $\le 2$.
- Use Keyword-Only arguments (`*`) for boolean flags to prevent boolean blindness.

### Step 4: Useful Errors & Observability
- Include operational context parameters in exceptions (`order_id`, `path`, `limit`).
- Always use exception chaining (`raise DomainError(...) from err`); never swallow exceptions.

### Step 5: Subtractive Deletion & Delete-List
- Target negative net line diffs: eliminate dead code, single-caller wrappers, and unused parameters.
