---
name: exec-docx
description: Create, read, edit, or convert Word documents (.docx/.dotx) with layout analysis and scope verification.
dependencies: [docx, defusedxml, lxml]
---

# Senior DOCX Engineering Assistant

- All layout schemas, theme tables, component specifications, and API signatures are consolidated in **`references/REFERENCE.md`** (DO NOT inspect `scripts/docx_engine.py` source code).

## Progressive Routing Table

| Task Mode | Scope & Tools | Reference File |
|---|---|---|
| **Create New Document** | Python `DOCXLayoutEngine` (`scripts/docx_engine.py`) with `Noto Sans TC` (11pt standard) & brand palettes | `references/REFERENCE.md` |
| **Edit Existing Document** | Unpack docx archive, merge runs, edit XML, track changes | `references/REFERENCE.md` |
| **Read / Inspect Content** | `pandoc -t markdown <file.docx>` | `references/REFERENCE.md` |

---

## Execution Workflow (4-Step Pipeline)

### Step 1: Analyze & Route
- Inspect task requirements and identify mode: **Create** (Visual-First), **Edit** (XML patch/Track Changes), or **Read** (Pandoc).
- Propose numbered scope before executing broad modifications.

### Step 2: Load Reference
- Load the corresponding section from `references/REFERENCE.md` into context.

### Step 3: Execute Operation
- **Create**: Follow the Visual-First Decision Matrix in `REFERENCE.md`, apply `Noto Sans TC 11pt`, and save to `~/Downloads/<doc_name>.docx`.
- **Edit**: Unpack archive, strip symlinks, run `merge_runs.py`, edit `word/document.xml`, and rezip.
- **Read**: Run `pandoc -t markdown <file.docx>`.

### Step 4: Programmatic Verification & QA
- Execute lightweight validation: `python3 <skill_dir>/scripts/office/validate.py <output_path>`.
- Verify file size $> 0$, valid OOXML structure, and zero XML corruption errors.
- Report deliverable file path and executive summary to the user.
