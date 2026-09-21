# Visual Architecture & Review Archetypes (`visual_archetypes.md`)

> **Protocol Rule**: Render output in Traditional Chinese with active verbs. Adhere to `capacity_budget` constraints defined in `primitives_map.json`.

---

## 1. Sub-track B1: Explore (Architecture & System Overview)

Triggered when the user wants to understand system structure, topology, interaction flow, or directory hierarchy.

### Formats & Capacity Rules
1. **Service Topology / Architecture**:
   - Format: Mermaid `flowchart LR` or `flowchart TD`
   - Capacity: Max 6 nodes, node label <= 15 chars.
2. **API Interaction / Handshake**:
   - Format: Mermaid `sequenceDiagram`
   - Capacity: Max 4 participants, max 6 message steps, step label <= 20 chars.
3. **Directory Structure**:
   - Format: ASCII directory tree block.
   - Capacity: Only show impacted directories and core modified files.
4. **Logic Skeleton**:
   - Format: Pseudocode block (4~6 lines).
   - Capacity: Expose critical control flow and guards only.

---

## 2. Sub-track B2: Diff (Surgical Minimal-Diff Review)

Triggered when the user wants to inspect changes, refactor code, or review patches.

### Template
```markdown
### [Module / File Name] — Surgical Minimal-Diff

• Diagnosis: [1-sentence statement explaining the core defect, bottleneck, or revision mandate]

• Comparison:
  - Before: [Line reference, e.g. Line xx or Lxx-Lyy]
  - After:
    ```[language]
    [Insert surgical replacement lines only; keep context minimal]
    ```

• Drop-in Replacement:
```[language]
[Insert complete drop-in replacement snippet ready for deployment]
```
```

---

## 3. Sub-track B3: Explain (Plain-Language Logic Walkthrough)

Triggered when the user wants to understand an algorithm, state transition, or business rule.

### Format
1. Render 1 focused visual aid (State Diagram or 4~6 line Pseudocode).
2. Provide 3~5 concise, active-verb sentences explaining the mechanism without jargon.
