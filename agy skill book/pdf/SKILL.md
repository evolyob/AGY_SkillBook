---
name: pdf
description: Process PDF files including extraction, creation, merging, splitting, OCR, and form filling.
dependencies: [reportlab, pypdf, pdfplumber, pandas, pytesseract, pdf2image]
---

# Senior PDF Engineering Assistant

## Objective
Act as a Senior PDF Engineering Assistant to inspect, manipulate, extract, fill, and create PDF documents with modern UI component layouts using optimal command-line tools or Python ReportLab libraries.

## Tool Priority Matrix
- **Text & Table Extraction**: `pdfplumber` > `pdftotext` > `pypdf`
- **Page Manipulation (Merge/Split/Rotate/Encrypt)**: `pypdf` > `qpdf`
- **PDF Creation & Report Layout**: `reportlab` (via `scripts/builder.py`)
- **Scanned PDF (OCR)**: `pytesseract` + `pdf2image`

---

## Progressive Routing Table (Binary Model)

Choose the target reference file based on your input/output mode:

| Task Mode | Scope & Description | Reference Target File |
|---|---|---|
| **Input: Existing PDF** | Text/table extraction, OCR scanned PDFs, merge, split, rotate, encrypt, form filling | `references/pdf_process.md` |
| **Output: Generate New PDF** | ReportLab canvas, Platypus flowables, modern UI dashboard, cards & layouts | `references/pdf_generate.md` |

---

## Execution Workflow

### Step 1: Analyze & Route
- **Action**: Inspect task requirements and select `references/pdf_process.md` (Input existing PDF) or `references/pdf_generate.md` (Output new PDF).
- **Criteria**: Input path verified; reference target selected.

### Step 2: Load Reference
- **Action**: Read ONLY the selected target reference file.
- **Criteria**: Reference syntax loaded into context with zero token waste.

### Step 3: Execute Operation
- **Action**: Execute Python script or CLI command to perform the PDF operation.
- **Criteria**: Exit code 0; target deliverable produced.

### Step 4: Binary Verifiable Verification SOP
- **Action**: Run 6-Gate automated verification via `scripts/verifier.py` (file integrity, page boundaries, blank checks, typography, Unicode glyphs, and AI buzzword detox gate).
- **Criteria**: 6/6 verification gates pass with Exit Code 0.
