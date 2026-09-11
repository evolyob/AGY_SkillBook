# XLSX Technical Reference & Architecture Guide

## 1. Tri-Pillar Responsibility Matrix

| Track | Module | Scope & Invariants | Implementation |
|---|---|---|---|
| **1. Creation** | `XLSXLayoutEngine` | Create brand new workbooks with `Noto Sans TC`, KPI blocks, zebra tables, and `themes.json`. Guarded against overwriting `<extLst>` files. | `scripts/xlsx_engine.py` |
| **2. Mutation** | `XLSX_XMLPatcher` | Lossless in-place surgical cell & range patching. Preserves `<extLst>`, cascading dropdowns, formulas, macros, and styles byte-for-byte. Zero external dependencies. | `scripts/xml_patcher.py` |
| **3. Evaluation** | `recalc.py` + `validate.py` | Offline formula recalculation via LibreOffice headless, error diagnosis (`#VALUE!`, `#REF!`, `#N/A`), and OpenXML schema verification. | `scripts/recalc.py` & `scripts/office/validate.py` |

---

## 2. Formula Standards & Openpyxl Gotchas

- **Always Use Formulas**: Write `=SUM(B2:B9)`, never hardcoded Python calculation values.
- **Formula Compatibility**:
  - Prefer classic Excel functions: `SUMIFS`, `INDEX`, `MATCH`, `IFERROR`, `SUMPRODUCT`.
  - Prefix modern functions: `_xlfn.TEXTJOIN`, `_xlfn.CONCAT`, `_xlfn.IFS`, `_xlfn.SWITCH`.
  - Avoid spilling array functions (`XLOOKUP`, `SORT`, `FILTER`, `UNIQUE`) in static templates.
- **Two-Pass Reading Rule**:
  - `load_workbook(data_only=False)`: Reads formula syntax strings.
  - `load_workbook(data_only=True)`: Reads cached evaluation values.

---

## 3. Financial Modeling Number Formats

- **Currency**: `$#,##0` or `$#,##0;($#,##0);"-"`
- **Percentage**: `0.0%` (stored as decimal fraction `0.15` for 15.0%)
- **Multiples**: `0.0"x"`
- **Years / Identifiers**: Plain text format `@` (e.g. `"2026"`, never `2,026`)

---

## 4. Universal Mutation Engine (`xml_patcher.py`) & Subtraction Rules

- **Zero One-Off Scripts**: Use `XLSX_XMLPatcher.update_cells()` or CLI `python3 xml_patcher.py <file.xlsx> --sheet <sheet> --updates '{"A1": "val"}'`. Never write scratch zip/regex scripts in `/tmp`.
- **Pure Function Core**: `patch_sheet_xml(xml_content, cell_updates)` handles string mutation in-memory, auto-escaping XML entities, and preserving cell styles (`s="xxx"`).
- **Never Re-Serialize Full XML with ElementTree**: Python ElementTree rewrites namespace prefixes (converting `x14ac`/`xr` to `ns0`/`ns1`), destroying Office 2010+ extensions.
- **Anti-Monotony Rule**: When batch populating categories or threat profiles, avoid uniform fallbacks. Use declarative rule tables and round-robin modulo distribution to prevent identical value streaks ($\ge 4$).

