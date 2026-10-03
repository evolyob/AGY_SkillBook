# Tracer-Bullet Ticket Decomposition Protocol (`ticket_decomposition.md`)

> **Core Philosophy**: Break frozen specifications into vertical slices forming a Directed Acyclic Graph (DAG) with explicit blocking relationships.

---

## 1. Tracer-Bullet Vertical Slicing Rules
1. **Vertical, Not Horizontal**: Each ticket cuts through all necessary layers (data model, core logic, interface, unit test). Horizontal slicing (e.g. creating all models without logic) is prohibited.
2. **Context Window Fit**: Each slice must comfortably fit within a single fresh subagent context window.
3. **Self-Verifiable**: Every completed ticket must have a dedicated test verifying its slice end-to-end.

---

## 2. Dependency Graph & Blocking Relationships (DAG)
Each ticket explicitly declares its `Blocked By` requirements:
```text
[Ticket 1: Core Pure Engine] (No Blockers - Ready Frontier)
       │
       ├───> [Ticket 2: Parser & Boundary] (Blocked by #1) ──┐
       │                                                     ├───> [Ticket 4: Seam Integration] (Blocked by #2, #3)
       └───> [Ticket 3: CLI & Output Format] (Blocked by #1) ┘
```
- **Ready Frontier**: Tickets with zero active blockers are ready for immediate subagent dispatch.

---

## 3. Wide Refactors: Expand–Contract Pattern
For cross-cutting changes with wide blast radius:
1. **Expand**: Introduce the new form alongside the existing one without breaking callers.
2. **Migrate**: Transition call sites in discrete, isolated batches (one ticket per module/batch).
3. **Contract**: Delete the obsolete form once zero references remain.
