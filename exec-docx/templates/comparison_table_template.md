# Regulatory Amendment Comparison Table Execution Specification
# Template ID: comparison_table_template

This template defines the exact operational rules, layout parameters, XML attributes, and comparison syntax for generating enterprise / regulatory amendment comparison tables (修正對照表).

---

## 1. Document Level Specifications

- **Orientation**: Landscape A4
  - Page Width (`w:pgSz w:w`): `16838` dxa (297 mm)
  - Page Height (`w:pgSz w:h`): `11906` dxa (210 mm)
  - Orientation (`w:pgSz w:orient`): `landscape`
- **Margins (`w:pgMar`)**:
  - Top: `1361` dxa (2.4 cm)
  - Bottom: `1361` dxa (2.4 cm)
  - Left: `1021` dxa (1.8 cm)
  - Right: `1021` dxa (1.8 cm)
  - Available Printable Width: `14796` dxa
- **Typography Standards**:
  - Chinese / East Asian Font (`w:rFonts w:eastAsia`): `標楷體` (DFKai-SB) or `Noto Sans TC`
  - Latin / Number Font (`w:rFonts w:ascii`, `w:rFonts w:hAnsi`): `Times New Roman`
  - Title Font: 14pt (`w:sz w:val="28"`), Bold
  - Revision / Date Font: 12pt (`w:sz w:val="24"`), Regular
  - Body Text Font: 12pt (`w:sz w:val="24"`), Regular

---

## 2. Table Architecture & Column Widths

The table consists of 3 columns split evenly across the printable area:

| Column Index | Column Name | Width (dxa) | Width (%) | Alignment | Description |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **Col 0** | 修正條文 (Amended Clause) | `4912` | ~33.2% | Left / Vertical Center | Contains the new version of the clause, highlighting additions |
| **Col 1** | 現行條文 (Current Clause) | `4912` | ~33.2% | Left / Vertical Center | Contains the original version of the clause, highlighting deletions |
| **Col 2** | 說明 (Explanation / Reason) | `4913` | ~33.6% | Left / Vertical Center | Action type (`新增。` / `調整。` / `刪除。`) and detailed business reasons |

---

## 3. Amendment Markup & Highlighting Rules

Follow statutory and ISO27001 internal control amendment markup conventions:

1. **Partial Addition (新增部分文字)**:
   - In `Col 0 (修正條文)`: Apply **Underline + Red Font** (`<w:u w:val="single"/><w:color w:val="FF0000"/>`).
   - In `Col 1 (現行條文)`: Leave existing text unchanged (no red/underline).
   - In `Col 2 (說明)`: Prepend with `新增。` followed by explanation.

2. **Partial Deletion (刪除部分文字)**:
   - In `Col 0 (修正條文)`: Omit deleted text.
   - In `Col 1 (現行條文)`: Apply **Underline + Red Font** (`<w:u w:val="single"/><w:color w:val="FF0000"/>`) on the deleted text.
   - In `Col 2 (說明)`: Prepend with `刪除。` followed by explanation.

3. **Partial Replacement / Modification (文字抽換與調修)**:
   - In `Col 0 (修正條文)`: Apply Underline + Red Font on the replacement text.
   - In `Col 1 (現行條文)`: Apply Underline + Red Font on the original text being replaced.
   - In `Col 2 (說明)`: Prepend with `調整。` followed by explanation.

4. **Entire Article / Chapter Added (整條新增)**:
   - In `Col 0 (修正條文)`: Present the entire newly added article in regular font.
   - In `Col 1 (現行條文)`: Write `（無）` or leave blank.
   - In `Col 2 (說明)`: Mark the action token with **Underline + Red Font**: `<ins><font color="#FF0000">整條新增。</font></ins>`, followed by explanation.

5. **Entire Article / Chapter Deleted (整條刪除)**:
   - In `Col 0 (修正條文)`: Write `（刪除）` or `（本條刪除）`.
   - In `Col 1 (現行條文)`: Present the original article.
   - In `Col 2 (說明)`: Mark the action token with **Underline + Red Font**: `<ins><font color="#FF0000">整條刪除。</font></ins>`, followed by explanation.

---

## 4. Header & Footnote Structure

### Document Header
```text
[文件編號] [文件名稱]修正對照表
[民國年.月.日]修正第[版次]版
```

### Table Header Row
- Cell 0: `修正條文` (Bold, centered or left)
- Cell 1: `現行條文` (Bold, centered or left)
- Cell 2: `說明` (Bold, centered or left)

### Footnotes (Appended directly beneath the table)
```text
註：
新增：修正條文新增內容，請於修正條文欄劃底線＋紅字。
刪除：現行條文於修正時部分刪除者，請於現行條文欄劃底線＋紅字。
整條新增或刪除者，請於說明欄劃底線＋紅字。
說明欄請說明條文修正理由。
```

---

## 5. Execution Pipeline for Agent

When requested to create or update a comparison table:
1. **Diff Extraction**: Extract text diff between old and new DOCX files at paragraph and character levels.
2. **Hierarchy Resolution**: Resolve chapter/section numbering (e.g. `肆、三、（一）4.`).
3. **Run Assembly**: Tag addition runs (`is_red=True`, `underline=True`) in Col 0, deletion runs in Col 1.
4. **Table Construction**: Construct 3-column table matching `4912 / 4912 / 4913` dxa widths with `vAlign="center"`.
5. **QA Verification**: Run `validate.py` on deliverable to confirm zero XML corruption.
