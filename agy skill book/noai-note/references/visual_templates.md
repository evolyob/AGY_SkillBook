# Visual Blueprint Execution Specifications (`visual_templates.md`)

> **Agent Execution Rule**: Match input against `trigger_signals` in `data/primitives_map.json` to pick the primitive. Enforce element counts and label lengths from `capacity_budget`. On ambiguous input, default to `flowchart`. Deliver user-facing output in Traditional Chinese.

---

## 1. Universal Primitive Selection Matrix & Output Syntax

- `kpi_row` [100% Full Width | Light 4 lines | SLA, %, ms, revenue] ──> `• [Metric]: [Value+Unit] ([Trend ▲/▼ Delta%])`
- `action_board` [50/50 Split | Medium 6 lines | As-Is, To-Be, pain points] ──> `• ✖ As-Is: [...] vs ✔ To-Be: [...]`
- `pipeline_flow` [100% Full Width | Light 4 lines | SOP, Phase, Steps, Lifecycle] ──> `• Progression: Phase 01 [...] -> Phase 02 [...] -> Phase 03 [...] -> Phase 04 [...]`
- `flowchart` [100% Full Width | Heavy 10 lines | Topology, Routing, File Tree] ──> 4-6 line Mermaid `flowchart LR` block
- `mermaid_sequence` [50% or 100% | Heavy 10 lines | API, JWT, Handshake, Auth] ──> 4-6 line Mermaid `sequenceDiagram` block
- `mermaid_er` [100% Full Width | Heavy 10 lines | DB schema, PK/FK, Entity Relationship] ──> 4-6 line Mermaid `erDiagram` block
- `matrix` [100% Full Width | Heavy 10 lines | P0-P3, Quadrant, Quick Wins] ──> `• [Q1 Quick Wins]: [...] | [Q2 Strategic Bets]: [...]`
- `zebra_table` [100% Full Width | Medium 6-8 lines | Registry, Specs, Compliance] ──> 3-column Markdown table (`| Domain | Requirement | Status | Due Date |`)
- `stateDiagram` / `classDiagram` [on-demand only] ──> Only render when input explicitly mentions state/lifecycle or class/interface. No primitives_map key; never auto-select.

---

## 2. Branch B: 16:9 Presentation Slide Deck Outline
*(Output Spec: Multi-slide deck driven by conclusion-led assertion narrative chain. Each slide snaps 1-2 layers; pure Markdown.)*

```text
# [Topic Name] — Presentation Slide Deck

【Storyboard Narrative】
• [Consecutive reading conveys executive context]
  - Slide 1: [Conclusion-Led Assertion Title 1]
  - Slide 2: [Conclusion-Led Assertion Title 2]

【Executive Summary】
• Alignment: [Strategic goals] | Baseline: [Core metrics] | Decision: [Decisions required]

---

### Slide [Page]: [Conclusion-Led Assertion Title (Never use neutral labels)]
【Canvas Composition】(Snap 1~2 layers from matrix above)
• Layer 1 [Pillar :: Primitive] — [Left 50% | Right 50% | Full Width]:
  - [Structured evidence, quantitative data, or SOP steps following syntax above]
• Layer 2 [Pillar :: Primitive] — [Left 50% | Right 50% | Full Width] (Optional):
  - [Structured evidence, quantitative data, or SOP steps following syntax above]

【Executive Focus】
- Key Risk: [Risk factor] | Recommended Action: [Action Item]
```

---

## 3. Branch D: A4 Executive Decision Blueprint (1-Pager vs. N-Pager)
*(Output Spec: A4 executive format. Confirm target upfront: 1-Pager or N-Pager.)*

> **A4 Capacity Rules (1 or N)**:
> • **1-Pager (3 States)**: `<20` lines (Halt: ask user to supplement) | `30-36` lines (Pass: deliver standard) | `>38` lines (Halt: ask user to condense or split).
> • **N-Pager (1 Rule)**: Preceding pages maintain full density (~30 lines); Final page concludes organically (bottom whitespace is strictly legal; zero padding fluff).

```text
# [Document Title] — A4 Executive Decision Blueprint

【Header & Executive Context】
• Title: [Document Title] | Meta: Date: [YYYY-MM-DD] | Owner: [Team] | Status: [Tag]
• Assertion Subtitle: [Conclusion-led primary claim: 1 sentence stating business value or risk avoided]
• Executive Context: [1~2 lines establishing current pain points or motivation]

---

【Canvas Composition (Lego Modular Assembly)】
(Snap 2~3 blocks; Mechanism explains operational logic, Visual provides single-line non-wrapping evidence)

• Block [No.] [Pillar :: Primitive] — [Grid: 100% Full Width | 50/50 Split]:
  - Band Title: 【[Index]、[Conclusion-Led Assertion Title]】
  - Mechanism (Primary): [1~2 lines explaining architectural logic, causality, or approach]
  - Visual (Auxiliary): [2~3 single-line items following syntax above; zero wrapping]

---

【Anchor Footer (Conclusion & Decision Request)】
• Band Title: 【[Index]、Conclusion & Decision Request: [Core Decision Claim]】
• Decision Statement (Primary): [1~2 lines summarizing business impact or avoided risk]
• Next Actions (Auxiliary): [2~3 concrete actions, deadlines, and contact window]
```
