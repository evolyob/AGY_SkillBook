---
name: exec-xlsx
description: Create, read, edit, format, or clean spreadsheet files (.xlsx/.csv) with formula validation and scope verification.
dependencies: [openpyxl, pandas, defusedxml, lxml]
---

# Senior XLSX Engineering Assistant

## Objective
Act as a Senior Spreadsheet Engineering Assistant to create, read, edit, and analyze Excel files (.xlsx/.csv) using standardized `Noto Sans TC` typography, dynamic theme tokens, KPI blocks, and formula validation.

## Tri-Pillar Decoupled Routing Table

| Track / Mode | Description & Tools | Boundary & Guarantees | Primary Tool |
|---|---|---|---|
| **1. Creation Track (創生軌)** | Generate brand new enterprise workbooks with `Noto Sans TC`, KPI blocks, and Zebra tables. | Only for creating **new** files from scratch. Guarded against overwriting `<extLst>` files. | `scripts/xlsx_engine.py` |
| **2. Mutation Track (修補軌)** | Lossless in-place surgical cell & range editing for existing spreadsheets. | Preserves `<extLst>`, cascading dropdowns, formulas, macros, and styles byte-for-byte. CLI & Python stdlib. | `scripts/xml_patcher.py` |
| **3. Evaluation Track (驗算軌)** | Offline formula evaluation, cache calculation, error detection (`#VALUE!`, `#REF!`, `#N/A`), and schema check. | Read-only evaluation; never alters styling, structure, or data. | `scripts/recalc.py` & `validate.py -v` |

---

## Execution Workflow (4-Step Pipeline)

### Step 1: Mode Selection & Boundary Gate
- **New Workbook**: Choose Track 1 (`xlsx_engine.py`).
- **Existing Workbook**: Choose Track 2 (`xml_patcher.py`). Check `patcher.has_extended_validations()` to confirm `<extLst>` safety. Never call `openpyxl.save()` on existing complex sheets.

### Step 2: Generation or In-Place Mutation
- **Creation**: Use `XLSXLayoutEngine` with standard themes, `Noto Sans TC`, and zebra tables. Always write formulas first (`=SUM(...)`).
- **Mutation**: Use `XLSX_XMLPatcher.update_cells()` or CLI `python3 xml_patcher.py file.xlsx --sheet sheet1.xml --updates '{"A1": "val"}'`. Zero one-off scripts needed.

### Step 3: Fast Verification & Evaluation
- Validate OpenXML schema and namespace integrity: `python3 <skill_dir>/scripts/office/validate.py <file.xlsx> -v`.
- Offline formula recalculation & error diagnosis: `python3 <skill_dir>/scripts/recalc.py <file.xlsx>`.

### Step 4: Report Completion
- Provide deliverable file path under `~/Downloads` and summary of modifications to the user.
