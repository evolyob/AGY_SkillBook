# Subagent Dispatch & Isolation Protocol (`subagent_dispatch.md`)

> **Core Philosophy**: Dispatch isolated subagents across the ready frontier with mutually exclusive allowed paths and deterministic verification gates.

---

## 1. Dispatch Rules of Engagement
1. **Zero Overlapping Allowed Paths**: Subagents executing in parallel must NEVER modify the same file path.
2. **Minimal Self-Contained Prompt**: Provide only the exact Goal, Non-Goals, Allowed Paths, and Verification Command.
3. **Deterministic Exit Gate**: A subagent must achieve 100% test pass (`OK`) before its dependent tickets can be dispatched.

---

## 2. Dispatch Proposal Format (Presented to User)
At the conclusion of a grilling and spec freeze session, dynamically evaluate the DAG and present a concrete, non-abstract dispatch proposal:

```markdown
### 🚀 Subagents Dispatch Proposal

The task has been decomposed into **N independent subtasks** for parallel execution:

1. **Subagent 1 ([Concrete Role Name])**
   * **Allowed Paths**: `scripts/target_module.py`, `tests/test_target_module.py`
   * **Responsibility**: [Exact function/class to implement or refactor, avoiding vague summaries]
   * **Verification**: `python3 -m unittest tests/test_target_module.py`

2. **Subagent 2 ([Concrete Role Name])**
   * **Allowed Paths**: `scripts/cli_interface.py`, `tests/test_cli_interface.py`
   * **Responsibility**: [Exact CLI flags and output formatting to add]
   * **Verification**: `python3 -m unittest tests/test_cli_interface.py`

---
> 💡 Proceed with parallel subagent dispatch based on this proposal?
```
