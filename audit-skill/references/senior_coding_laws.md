# Senior Clean Code & Vibe Craft Guide

Practical engineering awareness standards for clean code architecture and resilient system implementation.
**Core Philosophy**: Implements the approved spec contract through a sequential 5-step engineering radar. Balance architectural hygiene with pragmatism.

---

## 1. Step 1: Own the Boundary & Dict Lookups
- **Mandates (MUST)**:
  - MUST prioritize Python 3.13+ standard library (`pathlib`, `urllib`, `json`) over third-party dependencies declared in `spec.md`.
  - MUST isolate volatile third-party SDKs behind structural protocols (`typing.Protocol`) or adapters.
  - MUST treat static JSON assets as SSOT lookup dictionaries; consume them via targeted key-indexing, structured mapping, or generator queries in Python 3, never by brute-force loops or whole-file prompt dumps.
- **Prohibitions (MUST NOT)**:
  - MUST NOT leak raw SDK objects or unvalidated dictionaries into the domain core.
  - MUST NOT permit semantic tag contamination (e.g. assigning contradictory or nonsensical tags) or silent unpopulated arrays in data assets.
  - MUST NOT patch around malformed JSON with ad-hoc `if-else` ladders (Anti-Whack-A-Mole); enforce the dictionary contract at the root.
- **Pragmatic Boundary**: Built-in standard library utilities and stable internal helpers do not require protocol abstraction layers.

---

## 2. Step 2: Pure Core & Constrained States
- **Mandates (MUST)**:
  - MUST structure decision-making as pure, deterministic functions (Functional Core) without side effects; confine file I/O, DB writes, and network calls to the outer service shell.
  - MUST use `enum.StrEnum` and Union types so invalid business states are unrepresentable.
  - MUST defensively clamp layout sizes, intervals, counts, and timeouts (e.g. `max(MIN_FLOOR, val - delta)`) to mathematically guarantee non-negative geometry.
- **Prohibitions (MUST NOT)**:
  - MUST NOT inline I/O, DB writes, or system commands inside calculation loops; require complex mock fixtures to verify business rules.
  - MUST NOT use mutable default arguments (`target=[]`) which leak state across invocations.
- **Pragmatic Boundary**: Linear, straightforward scripts (read -> transform -> write) do not need elaborate multi-tier architectural separation.

---

## 3. Step 3: Flattened Flow & Intent Naming
- **Mandates (MUST)**:
  - MUST place Guard Clauses (`if not valid: return / raise`) at function tops to keep happy path linear at zero indentation; use `match ... case` for structural dispatching.
  - MUST name identifiers after concrete business domain entities (`pending_orders`, `sanitized_payload`).
  - MUST use Keyword-Only arguments (`*`) for boolean switches and optional configs to eliminate Boolean Blindness (e.g. `export_report(users, include_pii=True)`).
- **Prohibitions (MUST NOT)**:
  - MUST NOT write nested `if-else` blocks deeper than 2 levels; fragment linear logic into single-line micro-functions merely to dodge an `if`.
  - MUST NOT use generic variable names (`data`, `temp`, `res`); pass unlabelled positional booleans (`do_work(True, 30)`).
- **Pragmatic Boundary**: 1~2 levels of shallow `if` are fine for local algorithms; obvious utility/math functions with 1~2 args do not need keyword-only restriction.

---

## 4. Step 4: Useful Errors & Observability
- **Mandates (MUST)**:
  - MUST provide actionable error messages containing operational context parameters (`order_id`, `file_path`, `retry_count`).
  - MUST use exception chaining (`raise DomainError(...) from err`) when re-raising lower-level exceptions to retain the full stack trace.
- **Prohibitions (MUST NOT)**:
  - MUST NOT use bare `except:` handlers or swallow exceptions silently.
  - MUST NOT rely on `assert` statements for production business logic validation (which can be optimized away via `-O`).
- **Pragmatic Boundary**: Standard built-in exceptions (`ValueError`, `RuntimeError`) with clear messages are preferred over deep custom exception hierarchies for internal tools.

---

## 5. Step 5: Contract Closure & Delete-List
- **Mandates (MUST)**:
  - MUST confine all file diffs strictly within the *Allowed Paths* approved in `spec.md`.
  - MUST verify task completion objectively against the declared *Acceptance Criteria* command before declaring done.
  - MUST fix defects inside the root shared function (SSOT) rather than patching callers ad-hoc (Strict Anti-Whack-A-Mole).
  - MUST audit every diff with Delete-List mindfulness, actively challenging unnecessary abstractions to achieve negative net lines (Deletions > Additions).
- **Prohibitions (MUST NOT)**:
  - MUST NOT mutate files outside declared *Allowed Paths*; accumulate sprawling changesets mixing feature additions, mass formatting, and structural refactorings.
  - MUST NOT introduce speculative "just-in-case" parameters, single-caller wrapper functions, or premature abstractions.
  - **Pragmatic Boundary**: Modular, self-contained single-file engines around 300~400 lines are healthy and straightforward to maintain in solo projects; do not over-fragment files prematurely.
