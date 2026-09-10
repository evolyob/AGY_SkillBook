# XLSX Technical Reference & Architecture Guide

## 1. Engine & Tooling Responsibility Matrix

| Tool / Module | Responsibility & Scope | Implementation Source |
|---|---|---|
| **`XLSXLayoutEngine`** | Generate new enterprise workbooks with `Noto Sans TC`, KPI blocks, structured zebra tables, and `themes.json`. | `scripts/xlsx_engine.py` |
| **`XLSX_XMLPatcher`** | Lossless in-place XML patching for files with `<extLst>/<x14:dataValidations>`, macros, or cascading dropdowns. | `scripts/xml_patcher.py` |
| **`XLSXSchemaValidator`** | Post-generation OpenXML schema conformance, namespace integrity, and multiline `wrapText` verification. | `scripts/office/validate.py` |
| **`openpyxl`** | Basic cell reading, simple updates, and standard formulas where no `<extLst>` exists. | Python `openpyxl` package |
| **`pandas`** | High-volume tabular ingestion, bulk ETL, and fast data export. | `pandas.read_excel` / `to_excel` |

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

## 4. High-Fidelity XML Patcher (`xml_patcher.py`) & OpenXML Integrity

- **Never Use `xml.etree.ElementTree.tostring()` for Full XLSX Parts**: Re-serializing via ElementTree scrambles namespace prefixes (e.g. creating `xmlns:ns0=...` or altering `xmlns:x14` / `xmlns:xm`), drops `mc:Ignorable` namespaces, and triggers Excel schema corruption error `HRESULT 0x808c0002`.
- **Pure String/Regex Patching**: Always use `XLSX_XMLPatcher` or lossless string transformations to preserve original XML namespace declarations, tag ordering, and `<extLst>/<x14:dataValidations>`.
- **Multi-line Text & WrapText Rules**:
  1. Any cell with `\n` or multiple spaces MUST have `<t xml:space="preserve">`.
  2. The cell style (`cellXfs` in `styles.xml`) MUST include `<alignment vertical="center" wrapText="1"/>` with `applyAlignment="1"`.
  3. Row heights (`ht`) should be scaled proportionally to the line count with `customHeight="1"`.
