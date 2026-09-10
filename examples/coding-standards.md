# Senior Developer 7 Coding Laws & Static Code Audit Guide

This guide integrates the **Senior Developer 7 Coding Laws (Architectural Governance Standards)** with automated **AST Static Code Analysis**. It provides modern engineering specifications spanning architectural mindsets, standard SOP operating directives, and automated machine verification.

---

## 1. Three-Tier Governance Architecture

In enterprise-grade software and AI-assisted pair programming ("Vibe Coding"), code quality is guarded through a closed-loop Three-Tier Architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Pre-Implementation Architectural Mindset & Radar                     │
│  • Role: Design radar & mindfulness checklist (Senior Heuristics)       │
│  • Core: Spec-First, Chunking (3~5 Milestones), Root-Cause Convergence │
├────────────────────────────────────────────────────────────────────────┤
│ 2. In-Flight Objective Stethoscope: Static Code AST Engine             │
│  • Role: Unbiased, sub-20ms automated machine security & AST linter   │
│  • Action: [BLOCKER] stops fatal flaws; [ADVISORY] architecture tips   │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Post-Failure Remediation Ladder: Automated Triage Runbook           │
│  • Role: Algorithmic triage runbook (Delete -> Root -> Sec)            │
│  • Output: 1-to-1 code diff templates, preventing blind AI guessing    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Senior Developer 7 Coding Laws Specifications (SOP Manual)

### Quick Reference & Pragmatic Boundaries

| Law & Name | Mindfulness Focus | Senior Heuristic | Pragmatic Boundary |
| :--- | :--- | :--- | :--- |
| **Law 1: Return Early** | Eliminate nested pyramid conditionals | Use top Guard Clauses; use `match...case` for branching | 1~2 levels of shallow `if` are valid; avoid fragmenting micro-functions |
| **Law 2: Name the Meaning** | Avoid generic names (`data`) & boolean blindness | Domain entity naming; enforce keyword-only (`*`) for flags | 1~2 arg pure math or helper functions (`add(a, b)`) exempt |
| **Law 3: Own the Boundary** | Isolate external dependencies & token limits | **Spec-First**: define schema before coding; keep bulk data on disk | Standard library calls (`pathlib.Path`) require no anti-corruption layer |
| **Law 4: Model the State** | Eliminate invalid states & clamp lower bounds | Use `StrEnum` / Unions; defensively clamp geometry with `max(MIN, ...)` | Temporary internal script dicts do not need full class modeling |
| **Law 5: Split the Decision** | Decouple pure computation from side effects | Functional core with zero I/O; shell orchestrates I/O and network | Simple sequential conversion scripts (read -> transform -> save) exempt |
| **Law 6: Useful Errors** | Actionable context for machines & humans | Domain exceptions; preserve stack trace with `raise ... from err` | Small scripts can use stdlib exceptions (`ValueError`) without over-engineering |
| **Law 7: Ship Small Diffs** | Atomic PRs & laser-focused changes | **Chunking**: 3~5 milestones; **Root Cause**: grep all callers | Single-file modular scripts under 300~400 lines remain healthy |

---

### Gate 1: Control Flow & Structure Gate

#### 1.1 Law 1: Return Early (Keep Happy Paths Flat)
* **Explanation**: Code should read like a straightforward checklist. Use Guard Clauses at the top of functions to eliminate edge cases and error states immediately, keeping the primary happy path at zero indentation.
* **Mandate**:
  * Use Guard Clauses (`if not valid: return / raise`) at function entry to handle anomalies early.
  * Multi-branch dispatch must prioritize structured pattern matching (Python 3.10+ `match ... case`).
  * Manage resource lifecycles (files, sockets, locks) with context managers (`with` statements).
* **Prohibit**: Deep conditional nesting exceeding 2 indentation levels; over-compressed nested list comprehensions.
* **SOP Code Comparison**:
```python
# ❌ Anti-pattern: Conditional pyramid nesting (depth 3 > 2)
if user:
    if user.is_active:
        if user.has_permission("admin"):
            return process_admin_action(user)
```
```python
# ✅ SOP Standard: Guard Clauses with early return; zero-indent happy path
if not user or not user.is_active or not user.has_permission("admin"):
    return None
return process_admin_action(user)
```
* **Pragmatic Boundary**: 1~2 levels of shallow `if` conditions are completely legitimate. Never over-fragment simple logic into micro-functions solely to eliminate all `if` statements.

---

### Gate 2: Semantics & Interface Gate

#### 2.1 Law 2: Name the Meaning (Intent-Revealing Names)
* **Explanation**: Names must communicate domain intent and business purpose (e.g. `pending_orders`), rather than technical implementation artifacts (e.g. `data`, `res`).
* **Mandate**:
  * Variables and functions must describe domain entities and business intent.
  * All boolean flags and thresholds must be declared as **Keyword-only arguments (`*`)**, eliminating call-site "Boolean Blindness".
  * Strict PEP 8 adherence (`snake_case` for variables/functions, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants).
* **Prohibit**: Ambiguous placeholder names (`data`, `temp`, `res`, `info`); passing bare boolean literals as positional arguments at call sites.
* **SOP Code Comparison**:
```python
# ❌ Anti-pattern: Ambiguous naming & boolean blindness
def export(d, flag=True): ...
export(res, True)  # Call site has no domain context for what True means
```
```python
# ✅ SOP Standard: Domain naming & mandatory keyword-only flag
def export_orders(orders: list[dict], *, include_cancelled: bool = True): ...
export_orders(pending_orders, include_cancelled=True)
```
* **Pragmatic Boundary**: Pure math operations or utility functions with 1~2 arguments (e.g. `add(a, b)`) do not require keyword-only enforcement.

#### 2.2 Law 3: Own the Boundary (Isolate External I/O & Prompt Context)
* **Explanation**: External schemas and APIs evolve unpredictably; build anti-corruption layers at boundaries. In AI engineering, prompt context is also a critical boundary—leaking large static datasets inflates token costs and triggers context eviction.
* **Mandate**:
  * **Spec-First Workflow**: Define domain models (`@dataclass(frozen=True)` / Pydantic) or interface contracts (`Protocol`) before writing implementation logic.
  * **Boundary Anti-Corruption & Context Decoupling**: Parse external raw data into immutable models immediately at ingress; load large static datasets via backend disk reads (0 Prompt Tokens).
* **Prohibit**: Passing untyped raw dictionaries (`dict[str, Any]`) through core business logic; leaking 3rd-party vendor SDK objects into internal domain models.
* **SOP Code Comparison**:
```python
# ❌ Anti-pattern: Core business logic coupled to raw untyped dictionary
def process_order(payload: dict):
    return payload["order"]["items"][0]["price"]
```
```python
# ✅ SOP Standard: Spec-First strongly-typed immutable models
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderItem:
    sku: str
    price: float
```
* **Pragmatic Boundary**: Standard library invocations (`pathlib.Path`, `json.loads`) do not require extra abstraction layers.

---

### Gate 3: State & Architecture Gate

#### 3.1 Law 4: Model the State (Illegal States Unrepresentable)
* **Explanation**: Use type systems and data structures to ensure invalid states cannot exist at runtime. Defensively clamp numeric computations to prevent impossible negative values or underflows.
* **Mandate**:
  * Constrain state sets using string enums (`enum.StrEnum`) or union types.
  * Default domain models to immutable data structures (`@dataclass(frozen=True)`).
  * **Defensive Bounds Clamping**: For geometric dimensions (width, margins), time spans, or quota deductions, defensively clamp values at the computation site: `max(MIN_FLOOR, val - delta)`.
* **Prohibit**: Magic strings or magic numbers in business decisions; mutable default arguments in function signatures (`def f(x=[])`); unbounded subtraction without `max()` floor clamping.
* **SOP Code Comparison**:
```python
# ❌ Anti-pattern: Mutable default argument & negative geometric corruption
def create_card(w, h, tags=[]):
    width = w - 10  # If w < 10, yields negative dimension, breaking renderers
```
```python
# ✅ SOP Standard: None fallback & defensive max() lower bound clamping
def create_card(w: float, h: float, *, tags: list[str] | None = None) -> float:
    active_tags = tags if tags is not None else []
    return max(0.0, w - 10.0)
```
* **Pragmatic Boundary**: Small, short-lived dictionaries inside lightweight scripts do not need full class abstraction.

#### 3.2 Law 5: Split the Decision (Decouple Pure Logic from Side Effects)
* **Explanation**: Separate pure decision logic from side effects (database writes, API requests, filesystem I/O). Pure computational logic can achieve 100% unit test coverage with zero mocking.
* **Mandate**: Core business calculations must be pure functions with zero I/O, network, or DB calls; side effects must be orchestrated exclusively in the outer service shell.
* **Prohibit**: Smuggling I/O operations into calculation or validation functions; initializing network connections or DB queries inside constructors (`__init__`) or property getters; relying on mutable global state.
* **SOP Code Comparison**:
```python
# ❌ Anti-pattern: Pure calculation coupled with network side effect
def calculate_tax(amount):
    requests.post("https://api.log/audit", json={"amt": amount})
    return amount * 0.05
```
```python
# ✅ SOP Standard: Pure calculation isolated in Functional Core (zero mocks needed)
def calculate_tax(amount: float, rate: float = 0.05) -> float:
    return amount * rate
```
* **Pragmatic Boundary**: Straightforward linear conversion scripts (read -> transform -> save) do not need multi-layer architecture.

---

### Gate 4: Reliability & Governance Gate

#### 4.1 Law 6: Useful Errors (Machine-Actionable & Human-Readable)
* **Explanation**: Errors must provide actionable diagnostics for automated agents and human engineers alike, supplying structured context while preserving root-cause traces.
* **Mandate**: Define project-specific domain exception hierarchies; always use exception chaining (`raise DomainError(...) from err`) when rewrapping lower-level errors.
* **Prohibit**: Bare `except:` or catch-all `except Exception: pass`; using `assert` for production business validation (stripped under `python -O`).
* **SOP Code Comparison**:
```python
# ❌ Anti-pattern: Swallowing interrupts or using production assert
try:
    process_payment()
except: pass  # Swallows SIGINT and masks critical bugs
assert order.amount > 0, "Bad amount"  # Stripped in optimized Python
```
```python
# ✅ SOP Standard: Domain exception chaining preserving root cause
try:
    process_payment()
except Exception as err:
    raise PaymentGatewayError(order_id, f"Gateway network fault: {err}") from err
```
* **Pragmatic Boundary**: Lightweight utility scripts may use standard exceptions (`ValueError`, `RuntimeError`) rather than creating custom classes.

#### 4.2 Law 7: Ship Small Diffs (Keep Changes Focused & Atomic)
* **Explanation**: Changes must be small enough to fit effortlessly into reviewer cognitive working memory. Smaller diffs guarantee higher review quality and fewer regressions.
* **Mandate**:
  * **Chunking SOP**: Decompose complex features into 3~5 atomic milestones, implementing and verifying one component or function at a time.
  * **Root Cause over Caller Patching**: When resolving defects, grep all invocation sites and fix the issue inside the shared root function once, minimizing net diff size.
* **Prohibit**: Dumping catch-all junk modules (`utils.py`, `helpers.py`); scattering ad-hoc `if-else` or `try-catch` workarounds across multiple caller sites.
* **SOP Code Comparison**:
```python
# ❌ Anti-pattern: Patching individual callers across multiple files
# 5 callers each implement defensive checks independently:
res = get_data()
if res is not None and "items" in res: ...
```
```python
# ✅ SOP Standard: Root-cause defense consolidated in shared core function
def get_data() -> dict:
    raw = fetch()
    return raw.get("items", {}) if isinstance(raw, dict) else {}
```
* **Pragmatic Boundary**: Modular single-file scripts under 300~400 lines maintain high portability; avoid excessive fragmentation into dozens of 5-line files.

---

## 3. AST Static Code Audit Specifications

AST static code audit provides lightweight, deterministic security and architecture linting that executes in sub-20ms using Abstract Syntax Tree parsing and regular expressions.

### Audit Rules & Severity Classification

| Category | Inspection Target | AST / Detection Mechanism | Severity | Remediation Directive |
| :--- | :--- | :--- | :---: | :--- |
| **Shadowing** | Overwritten functions/classes | Scans for duplicate `FunctionDef` / `ClassDef` in same scope | `[BLOCKER]` | Remove shadowed definition or rename |
| **Dict Collision** | Duplicate dictionary keys | Checks `ast.Dict` literal keys for duplicates | `[BLOCKER]` | Remove duplicate key, keep correct config |
| **State Trap** | Mutable default arguments | Inspects `args.defaults` for `List`, `Dict`, `Set` | `[BLOCKER]` | Default to `None` and initialize in body |
| **Silent Swallowing** | Bare `except:` | Checks `ast.ExceptHandler.type is None` | `[BLOCKER]` | Specify caught exception type explicitly |
| **Security Leak** | Absolute host paths / Secrets | Regex match for local paths (`/home/`, `/Users/`), `sk-...`, `AKIA...` | `[BLOCKER]` | Use relative paths, env vars, or config files |
| **Dangerous Exec** | Arbitrary execution | Checks for `eval()`, `exec()`, `os.system()` | `[BLOCKER]` | Use `subprocess.run([...])` or safe parsers |
| **Control Flow** | Nested `if` depth $> 2$ | Traverses `ast.If` measuring indentation depth (flat `elif` allowed) | `[ADVISORY]` | Flatten using Guard Clauses with early return |
| **Reliability** | Production `assert` | Checks for `ast.Assert` in non-test code | `[ADVISORY]` | Replace with `if not cond: raise DomainError(...)` |
| **Code Scale** | File length $> 200$ lines | Measures total line count | `[ADVISORY]` | Modularize unless file is a core engine |
| **Dependency** | Heavy external libraries | Checks imports for `requests`, `pandas`, `numpy`, etc. | `[ADVISORY]` | Prioritize standard library (`urllib`, `json`) |

---

## 4. Production Code Comparison (Checkout Service)

### ❌ Anti-Pattern (Junior Code / 7 Violations / Audit FAIL)

```python
import os

def calculate_tax(amount): return amount * 0.05
def calculate_tax(amount): return amount * 0.10  # ❌ Violation 1: Overwriting definition
PAYMENT_CONFIG = {"timeout": 30, "timeout": 60}   # ❌ Violation 2: Duplicate key

def checkout(order, coupons=[], is_vip=False):     # ❌ Violation 3: Mutable default; Violation 4: Boolean blindness
    assert order is not None                       # ❌ Violation 5: Production assert
    if order.get("status") == "pending":           # ❌ Violation 6: Nesting depth > 2 + I/O smuggled in logic
        if order.get("amount") > 0 and not order.get("is_frozen"):
            os.system(f"curl -X POST https://api.bank.com/pay -d id={order.get('id')}")
            try: return {"id": order.get("id"), "paid": True}
            except: pass                           # ❌ Violation 7: Bare except swallowing signals
    return None
```

### ✅ Senior Code (100% Compliant with 7 Laws / Audit PASS)

```python
#!/usr/bin/env python3
from enum import StrEnum
from dataclasses import dataclass
from typing import Protocol
from decimal import Decimal

class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FROZEN = "frozen"

@dataclass(frozen=True)
class Order:
    order_id: str
    amount: Decimal
    status: OrderStatus
    is_frozen: bool = False

@dataclass(frozen=True)
class CheckoutDecision:
    order_id: str
    final_amount: Decimal

class CheckoutError(Exception):
    def __init__(self, order_id: str, msg: str):
        super().__init__(f"Order '{order_id}' failed: {msg}")

class PaymentGateway(Protocol):
    def charge(self, order_id: str, amount: Decimal) -> str: ...

# Pure Decision Core (Guard Clauses + Lower-Bound Clamping + Zero Side Effects)
def calculate_checkout_decision(order: Order, *, discount: Decimal = Decimal("0")) -> CheckoutDecision:
    if order.status != OrderStatus.PENDING or order.is_frozen:
        raise CheckoutError(order.order_id, "Order not ready for checkout")
    if order.amount <= Decimal("0"):
        raise CheckoutError(order.order_id, "Order amount must be positive")
    
    final = max(Decimal("0"), order.amount - discount)  # Physical lower bound clamping
    return CheckoutDecision(order_id=order.order_id, final_amount=final)

# Side-Effect Shell (Keyword-Only + Exception Chaining)
def process_checkout(order: Order, gateway: PaymentGateway, *, discount: Decimal = Decimal("0")) -> CheckoutDecision:
    decision = calculate_checkout_decision(order, discount=discount)
    try:
        gateway.charge(decision.order_id, decision.final_amount)
    except Exception as err:
        raise CheckoutError(decision.order_id, f"Gateway fault: {err}") from err
    return decision
```

---

## 5. Collaborative Workflow (4-Step SOP)

In human-AI pair programming, adhere to this closed-loop prompt workflow:

### Step 1: Baseline Setup
* **Action**: Set upfront constraints in the project prompt or rule files (standard library first, explicit dependencies only, preserve existing tests).
* **Prompt Template**:
  > "This project strictly enforces the Senior 7 Coding Laws and minimal dependency principles. Prioritize standard library capabilities; undeclared third-party packages are prohibited."

### Step 2: Spec-First Design (Law 3)
* **Action**: Before implementing business logic, lock down data schemas and API contracts to calibrate domain boundaries.
* **Prompt Template**:
  > "Do not write concrete business logic yet. First outline the data models (Dataclass/Schema) and API interface contracts (Protocol). Once the structural foundation is approved, we will proceed to implementation."

### Step 3: Milestone Chunking (Law 7)
* **Action**: Once the specification is finalized, instruct the agent to decompose the work into 3~5 atomic milestones.
* **Prompt Template**:
  > "Decompose this feature into 3 independent atomic milestones. Execute only Milestone 1 now: create the pure decision function and unit tests. Do not generate all code at once."

### Step 4: Automated Machine Verification
* **Action**: Immediately run automated static checks upon code generation. If an alert triggers, resolve it using root-cause remediation at the source.
* **Verification Directives**:
  1. Validate syntax and compilation cleanly under target runtime.
  2. Perform static pattern scan ensuring zero hardcoded local environment paths (`/home/`, `/Users/`) or plaintext credentials.
  3. Ensure AST checks pass with zero blocker alerts before claiming completion.

---

## 6. Architectural Summary & Mindset

1. **Mindfulness First**: Consider cognitive load, Spec-First design, Chunking, and Pragmatic Boundaries from line one, preventing prompt context bloat and over-engineering.
2. **Deterministic Machine Gates**: In the final delivery phase, intercept syntax anti-patterns, shadowing, and hardcoded secrets using sub-20ms AST static analysis.
3. **Root-Cause Convergence**: When an audit rule triggers, resolve the defect at the shared root function rather than scattering workarounds across caller sites.
4. **Three-Tier Synergy**: Maintain the agility of rapid prototyping while safeguarding enterprise-grade resilience, portability, and security guardrails.
