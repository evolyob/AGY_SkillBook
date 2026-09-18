# Markdown Visual Preview Protocol (`md_preview.md`)

Fast, browser-ready preview protocol using modern Web CSS design tokens and native Mermaid diagrams. Designed for immediate inspection in HackMD or any browser Markdown previewer before compiling to formal PDF.

---

## 1. Modular Architecture & Responsibilities

| Tool / Script | Core Responsibility | Quality Standard |
|---|---|---|
| **`scripts/preview_scaffold.py`** | **MD Preview Generation**: Emits CSS design tokens (from `pdf_themes.json` SSOT), KPI cards, and Mermaid charts. | Tag symmetry, zero token bloat, CommonMark compliant. |
| **`scripts/verifier.py`** | **Quality Gate Auditing**: Verifies 5-Gate tag balance, detox checks, and layout constraints. | `5/5 Gates PASSED` mandatory. |
| **`scripts/builder.py`** | **PDF Compilation**: Compiles Markdown / structured stories into print-ready A4 PDF via ReportLab. | `6/6 Gates PASSED` (A4, zero overflow). |

---

## 2. Standard 3-Phase Execution Workflow

### Phase 1: Generate Scaffold
Invoke `preview_scaffold.py` to produce a fully styled, verified starter file:
```bash
python3 scripts/preview_scaffold.py -t "Project Title" -s "Subtitle" -o preview.md
```
*Optional flags*:
- `--template a`: Only Header & KPI Dashboard Grid.
- `--template b`: Only As-Is vs To-Be Split Cards.
- `--template c`: Only Native Mermaid Charts.
- `--diagram <type>`: Choose Mermaid chart (`all`, `original`, `safe`, or single chart: `flowchart`, `xychart`, `gantt`, `timeline`, `sequence`, `state`, `er`).
- `--export-dir <dir>`: Batch export diagram SVG/PNG assets concurrently.
- `--compile-pdf <file.pdf>`: 1-stop pipeline compiling diagrams directly into a verified ReportLab PDF.
- `--css-only`: Output only the CSS block.

### Phase 2: Refine & Verify
1. Populate actual business metrics, narratives, and Mermaid topologies into `preview.md`.
2. Verify quality gates before user delivery:
```bash
python3 scripts/verifier.py preview.md
```

### Phase 3: Compile to PDF
When preview is accepted, compile to formal deliverable:
```bash
python3 scripts/builder.py preview.md -o output.pdf
python3 scripts/verifier.py output.pdf
```
