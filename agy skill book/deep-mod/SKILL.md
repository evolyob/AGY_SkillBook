---
name: deep-mod
description: Universal interactive deep research, architecture visualization, and surgical diff review pipeline with Anti-AI enforcement.
metadata:
  task_type: open-ended
dependencies: []
---

# Deep Mod: Universal Research, Architecture & Code Review Pipeline

## Objective
Execute domain-agnostic interactive research, architecture visualization, and code review with Shift-Left Anti-AI enforcement.

## Execution Workflow

### Step 1: Intake & Intent Routing
- If input contains review keywords (`diff`, `review`, `架構圖`, `重構`):
  Execute **Fast-Track**: Ask ONE boundary question, freeze scope, and proceed directly to Step 3 (Branch 2).
- Otherwise, execute default **Deep Research**:
  Proceed sequentially through Phase 1 to Phase 3 (ONE Socratic question per turn).

### Step 2: Investigation (Default Mode Only)
- Phase 1: Socratic Requirement Clarification (`references/socratic_protocol.md`).
- Phase 2: Systematic Data Collection & Source Review (`references/search_protocol.md`).
- Phase 3: Evidence-Based Fact-Checking (`references/fact_check_rules.md`).

### Step 3: Phase 4 Finalized Output
Deliver finalized content directly to `~/agy/download/` with Anti-AI verification (`references/synthesis_rules.md`):
- **Branch 1 (Deep Research)**: Cross-Department Synthesis & Gap Audit Report.
- **Branch 2 (Architecture & Review)**: Auto-routed sub-track (`references/visual_archetypes.md`):
  - **B1 (Explore)**: Mermaid topology, sequence diagram, ASCII directory tree, or pseudocode.
  - **B2 (Diff)**: Before vs After Minimal-Diff + drop-in replacement block.
  - **B3 (Explain)**: Visual diagram + 3~5 sentence plain-language walkthrough.
