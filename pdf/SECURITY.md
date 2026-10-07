# Security Policy: pdf

## Scope
This skill provides process, inspect, extract, merge, split, and ocr pdf documents, or generate composable a4 pdf reports (reportlab) and browser markdown previews (css bento cards, kpi grids, mermaid topologies). It operates on local files or declared network targets provided via arguments. It does not collect telemetry, run silent daemons, or mutate unauthorized paths.

## Dependencies
- Standard library prioritized (Python >= 3.13).
- Declared dependencies: `[reportlab, pypdf, pdfplumber, pandas, pytesseract, pdf2image, resvg_py]`.
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 2s). In-memory execution with explicit outputs directed to designated targets.
- Validated execution flags: `---`, `--css-only`, `--diagram`, `--export-diagram`, `--export-out`, `--fix`, `--min-font`, `--min-size`, `--output`, `--pages`, `--quiet`, `--subtitle`, `--template`, `--theme`, `--title`.
