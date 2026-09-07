---
name: exec-note
description: Universal two-phase executive assistant tool. Phase 1 logs raw inputs without analytical noise; Phase 2 renders executive meeting briefs or presentation outlines upon finalization.
metadata:
  version: "2.2.0"
  task_type: open-ended
---

# Exec Note — Universal Executive Assistant Tool

A domain-agnostic executive assistant tool featuring a two-state machine (Phase 1 Zero-Analysis Collection -> Phase 2 Finalized Executive Output). Applicable to any meeting notes, strategy discussions, and presentation structuring.

---

## Trigger Keywords

**English**: exec-note, log meeting, update note, finalize, generate meeting brief, executive brief, presentation outline, slide outline  
**繁體中文**: exec-note, 整理會議紀錄, 補充, 修正, 定稿, 生成最終會議紀錄, 生成主管摘要, 簡報大綱, 製作簡報大綱

---

## Two-State Machine Workflow

### Phase 1: Zero-Analysis Collection Phase
- **State Requirement**: Set `current_state = 'collection'`.
- **Guardrails & Constraints**:
  * Strictly suppress analytical padding, extrapolation, or speculation regarding unmentioned owners, budgets, or deadlines.
  * Map missing fields to: `"未於資料中明確說明"` (Not explicitly stated).
  * Map unresolved topics to: `"尚未形成共識"` (No consensus reached).
- **Execution**: Chronologically append new inputs to historical memory, read `[templates.md](references/templates.md)`, and render the **《Collection Template》**.

### Phase 2: Finalized Executive Output Phase
- **Activation Trigger**: Triggered when keywords like `定稿`, `finalize`, `generate meeting brief`, or `presentation outline` are received (`current_state = 'finalized'`).
- **Branch Routing (Referencing `references/templates.md`)**:
  * **Branch A (Executive Brief Mode)**: For meeting notes and decision briefs, route across `Strategic_Business` / `Technical_Product` / `Operations_Governance` domains and render using the **《Executive Brief Template》**.
  * **Branch B (Presentation Outline Mode)**: Strictly aligned with `/pptx` Step 2 & Step 3 Proof-Led Strategy (Assertion Titles storyboard + Lego-like composable canvas blocks: freely assembling Cards, Diagrams, Charts, Tables across layers and columns), generating modular presentation blueprints without rigid templates or redundant text.
- **Humanized Tone & Anti-AI Gate**: Read and apply `[rules_zhtw.json](references/rules_zhtw.json)` (for Traditional Chinese) or `[rules_en.json](references/rules_en.json)` (for English) during Phase 2 rendering. Eliminate formulaic AI filler syntax, replace mainland Chinese buzzwords or English puffery with crisp executive phrasing, and enforce dynamic sentence pacing.
