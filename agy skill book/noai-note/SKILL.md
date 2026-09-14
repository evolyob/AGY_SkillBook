---
name: noai-note
description: Two-phase executive assistant for meeting notes, briefs, presentation outlines, revision cards, and 1-pager visual blueprints with deterministic detox gate.
---

# NoAI Note Pipeline

Two-state executive assistant: Phase 1 Collection -> Phase 2 Executive Output.

## Phase 1: Zero-Analysis Collection
- **Default State**: `current_state = 'collection'`.
- **Rules**:
  1. **Zero Extrapolation**: Parse only explicit facts; never invent owners, dates, or budgets.
  2. **Omit Missing Fields**: Do not generate placeholders.
  3. **Implicit Fallback**: Input without explicit branch selection (options 2~5) continues collection.
- **Action**: Append incremental key points; render Collection Template from `[templates.md](references/templates.md)`.

## Phase 2: Finalized Executive Output
Triggered on user selection (options 2~5) or keywords (`定稿`, `finalize`).

### Step 1: Deterministic Detox Gate
- Run gate check on candidate assertions and prose:
  `python3 scripts/scan.py --text "<draft_text>"`
- On `[FAIL]`: Holistically rewrite the flagged snippet in standup voice per script directive.
- **Zero-Token Rule**: Never load `data/rules_*.json` via `view_file`; rely strictly on `scan.py`.

### Step 2: Branch Assembly & Delivery
- **Branch A (Executive Brief) [2]**: Reference `[templates.md: Section 2](references/templates.md)`.
- **Branch B (Presentation Outline) [3]**: Reference `[templates.md: Section 3](references/templates.md)`.
- **Branch C (Revision Coach) [4]**: Reference `[templates.md: Section 4](references/templates.md)`.
- **Branch D (1-Pager Blueprint) [5]**: Reference `[pdf_template.md](references/pdf_template.md)`.
- **Delivery**: Save to `~/agy/download/`. Reply with concise summary, key decisions, and relative path `download/[file]`.
