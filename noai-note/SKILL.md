---
name: noai-note
description: Two-phase executive assistant tool for meeting notes, executive briefs, presentation outlines (PPTX), revision comparison tables, and 1-pager visual blueprints (PDF/DOCX) with Shift-Left Anti-AI filtering.
metadata:
  task_type: open-ended
---

# NoAI Note — Universal Executive Assistant & Revision Tool

Two-state pipeline (Phase 1 Collection -> Phase 2 Executive Output).

---

## Control Flow & Pipeline

### Phase 1: Zero-Analysis Collection
- **Default State**: Set `current_state = 'collection'`.
- **Execution Rules**: Parse explicit facts only (zero extrapolation). Omit missing fields without placeholders.
- **Workflow**: Append key points chronologically and render **Collection Template** from `[templates.md](references/templates.md)`.

---

### Phase 2: Finalized Executive Output
Triggered ONLY on explicit finalization commands (options 2~5 or keywords `定稿`/`finalize`).

1. **Branch Assembly (Standup Voice)**:
   Assemble points into the target branch template using active verbs and verified metrics:
   - **Branch A (Executive Brief) [Option 2]**: Reference `[templates.md: Section 2](references/templates.md)`.
   - **Branch B (Presentation Outline) [Option 3]**: Reference `[visual_templates.md: Section 2](references/visual_templates.md)`.
   - **Branch C (Revision Coach) [Option 4]**: Reference `[templates.md: Section 3](references/templates.md)`.
   - **Branch D (1-Pager Blueprint) [Option 5]**: Reference `[visual_templates.md: Section 3](references/visual_templates.md)`.

2. **Deterministic Script Gate**:
   Execute `python3 scripts/scan.py --text "<finalized_text>"`. If flagged, follow the script's prescription to rewrite the offending sentence/paragraph. Never load JSON rule files.

3. **Delivery & Chat Summary**:
   Write documents to `~/agy/download/[filename]` (UTF-8/UTF-16). In chat, output ONLY a concise executive decision summary and relative path `download/[filename]`.
