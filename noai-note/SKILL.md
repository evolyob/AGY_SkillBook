---
name: noai-note
description: Two-phase executive assistant tool for meeting notes, executive briefs, presentation outlines (PPTX), and 1-pager visual blueprints (PDF/DOCX) with Shift-Left Anti-AI filtering.
metadata:
  task_type: open-ended
dependencies: ["openpyxl", "pypdf"]
---

# NoAI Note — Universal Executive Assistant & Blueprint Tool

## Objective
Two-state pipeline (Phase 1 Collection -> Phase 2 Executive Output) for meeting minutes and executive blueprints with deterministic Anti-AI scanning.

## Execution Workflow

### Phase 1: Zero-Analysis Collection
- **Default State**: Set `current_state = 'collection'`.
- **Execution Rules**: Parse explicit facts only (zero extrapolation). Omit missing fields without placeholders.
- **Workflow**: Append key points chronologically and render **Collection Template** from `[templates.md](references/templates.md)`.
- **Large Input Circuit Breaker**: For inputs `> 25 pages` or `> 6,500 tokens`, execute `python3 scripts/ingest.py <input> --split-dir /tmp/meeting_work/` for parallel processing.

### Phase 2: Finalized Executive Output
Triggered ONLY on explicit finalization commands (options 2~4 or keywords `定稿`/`finalize`).

1. **Branch Assembly (Standup Voice)**:
   Assemble points into the target branch template using active verbs and verified metrics:
   - **Branch A (Executive Brief) [Option 2]**: Reference `[templates.md: Section 2](references/templates.md)`.
   - **Branch B (Presentation Outline) [Option 3]**: Reference `[visual_templates.md: Section 2](references/visual_templates.md)`.
   - **Branch C (1-Pager Blueprint) [Option 4]**: Reference `[visual_templates.md: Section 3](references/visual_templates.md)`.

2. **Deterministic Script Gate**:
   Execute `python3 scripts/scan.py --text "<finalized_text>"`. If flagged, follow prescription to rewrite.

3. **Delivery & Chat Summary**:
   Write deliverables to `~/Downloads/[filename]`.
