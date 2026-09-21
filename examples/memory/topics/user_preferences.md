# User Preferences & Task Architecture (`user_preferences.md`)

> **Role**: SSOT for agent-facing knowledge purity, compute-cognition division of labor, and output formatting.

---

## 1. Intuitive & Non-Abstract Specifications
- **Mandate**: All internal memory topics, specifications, and templates are consumed directly by the AI agent. They MUST be concrete, intuitive, and non-abstract (plain English, high-signal constraints, operational tables/lists).
- **Prohibit**: Lengthy essays, full-file dumps for localized fixes, dramatic metaphors, or vague philosophical concepts that bloat token context.

---

## 2. Clear Division of Responsibilities (分工明確)
- **Deterministic Computation**: Python scripts handle 100% of arithmetic, data filtering, keyword indexing, and schema validation. Never offload math or heavy lookup logic to LLM deduction.
- **Cognitive Orchestration**: The LLM focuses strictly on intent classification, candidate selection, user clarification, and compact formatting (surgical diffs, ASCII trees, and terminal box-drawing diagrams).
- **Contract Enforcement**: Specifications define hard boundaries (Non-Goals, Allowed Paths, Verification Commands) before any code execution begins.
