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
- `--template <blocks>`: Composable Lego blocks (comma-separated): `kpi`, `matrix`, `table`, `checklist`, `pipeline`, `charts`, or `all` (e.g. `--template kpi,matrix,table`).
- `--diagram <type>`: Choose Mermaid chart (`all` or single chart: `flowchart`, `sequence`, `er`).
- `--export-diagram <type>`: Export a specific Mermaid chart as an asset (`flowchart`, `sequence`, `er`).
- `--export-out <file>`: Output path for exported graphic (.svg or .png).
- `--css-only`: Output only the CSS block.

### Phase 2: Refine & Verify
1. Populate actual business metrics, narratives, and Mermaid topologies into `preview.md`.
2. Verify quality gates before user delivery:
```bash
python3 scripts/verifier.py preview.md
```

### Phase 3: Transition to PDF Generation
When the visual structure and content are approved in Markdown preview:
1. Switch to `references/pdf_generate.md` for formal ReportLab layout rules.
2. Author `build_pdf.py` using `builder.py` APIs adhering to the 6-Category layout budget.
3. Compile and verify the final A4 deliverable:
```bash
python3 build_pdf.py output.pdf
python3 scripts/verifier.py output.pdf
```
