---
name: pdf
description: Process, inspect, extract, merge, split, and OCR PDF documents, or generate composable A4 PDF reports (ReportLab) and browser Markdown previews (CSS Bento cards, KPI grids, Mermaid topologies).
dependencies: [reportlab, pypdf, pdfplumber, pandas, pytesseract, pdf2image, resvg_py]
---

# Senior PDF Engineering Assistant

## Objective
Act as a Senior PDF Engineering Assistant to inspect, manipulate, extract, fill, and create PDF documents with modern UI component layouts using optimal command-line tools or Python ReportLab libraries.

## Tool Priority Matrix
- **Text & Table Extraction**: `pdfplumber` > `pdftotext` > `pypdf`
- **Page Manipulation (Merge/Split/Rotate/Encrypt)**: `pypdf` > `qpdf`
- **PDF Creation & Report Layout**: `reportlab` (via `scripts/builder.py` and `references/pdf_generate.md`)
- **Scanned PDF (OCR)**: `pytesseract` + `pdf2image`

---

## Progressive Routing Table (Tri-Mode)

Choose the target reference file based on your input/output mode:

| Task Mode | Scope & Description | Reference Target File |
|---|---|---|
| **Preview: Browser / Markdown** | Fast browser preview, Web CSS cards, KPI grids & Mermaid charts | `references/md_preview.md` |
| **Output: Generate New PDF** | ReportLab canvas, Platypus flowables, modern UI dashboard, cards & layouts | `references/pdf_generate.md` |
| **Input: Existing PDF** | Text/table extraction, OCR scanned PDFs, merge, split, rotate, encrypt, form filling | `references/pdf_process.md` |

---

## Execution Workflow

### Step 1: Analyze & Route
- **Action**: Inspect task requirements and select:
  - `references/md_preview.md` (Fast Markdown/Browser visual preview)
  - `references/pdf_generate.md` (Formal A4 1-pager PDF output)
  - `references/pdf_process.md` (Inspect / extract / merge existing PDFs)
- **Criteria**: Target mode determined; reference target selected.

### Step 2: Load Reference
- **Action**: Read ONLY the selected target reference file.
- **Criteria**: Reference syntax loaded into context with zero token waste.

### Step 3: Execute Operation
- **Action**: 
  - For Markdown preview: Execute `scripts/preview_scaffold.py -o preview.md`, populate content, and verify with `scripts/verifier.py preview.md`.
  - For PDF generation: Author Python build script using `builder.py` APIs adhering to `references/pdf_generate.md`, and compile via `python3 build_pdf.py <output.pdf>`.
  - For PDF processing: Execute `pypdf`, `pdfplumber`, or CLI commands.
- **Criteria**: Exit code 0; target deliverable produced.

### Step 4: Binary Verifiable Verification SOP
- **Action**: Run automated verification via `scripts/verifier.py <target_file>`:
  - **PDF Mode (6-Gate)**: Binary integrity, page count, typography $\ge$ 10.5pt, Unicode glyphs, AI detox.
  - **Markdown Mode (5-Gate)**: Tag/fence symmetry, layout orphan check, content balance ratio, AI detox (supports `--fix`).
  - **Tooling Invariants**: `python3 -m unittest discover tests` verifies layout math and verifier sensitivity.
- **Criteria**: Target deliverable passes verification gates with Exit Code 0.
