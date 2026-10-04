# Tracer-Bullet Ticket Decomposition Protocol (`ticket_decomposition.md`)

> **Core Philosophy**: Break frozen specifications into vertical slices forming a Directed Acyclic Graph (DAG) with explicit blocking relationships.

---

## 1. Tracer-Bullet Vertical Slicing Rules
1. **Vertical, Not Horizontal**: Each ticket implements a minimal end-to-end slice (data model + core logic + CLI/interface + unit test). Horizontal slicing (e.g. creating all data models without executable logic) is prohibited.
2. **Context Window Fit**: Each slice must modify $\le$ 3 files and $\le$ 150 net lines so it fits comfortably within a single subagent context.
3. **Self-Verifiable**: Every ticket must have a deterministic test command proving its slice functions end-to-end.

---

## 2. Dependency Graph & Blocking Relationships (DAG)
Each ticket explicitly declares its `Blocked By` requirements:
```text
[Ticket 1: Tracer Bullet #1 - Happy Path E2E] (No Blockers - Ready Frontier)
       │ (Minimal parser + core transform + CLI flag + test)
       ├───> [Ticket 2: Edge Cases & Bounds Protection] (Blocked by #1) ──┐
       │                                                                  ├───> [Ticket 4: Multi-Module Integration] (Blocked by #2, #3)
       └───> [Ticket 3: Output Formatting & Structured JSON] (Blocked by #1) ┘
```
- **Ready Frontier**: Tickets with zero active blockers are ready for immediate subagent dispatch.

---

## 3. Wide Refactors: Expand–Contract Pattern
For cross-cutting changes with wide blast radius:
1. **Expand**: Introduce the new interface/function alongside the legacy one.
2. **Migrate**: Transition callers in isolated batches (one ticket per module/batch).
3. **Contract**: Verify `grep -rn "<legacy_symbol>"` returns 0 references, then delete the obsolete code.

