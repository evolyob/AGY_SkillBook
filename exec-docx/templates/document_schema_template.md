# Document Schema & Markdown Bidirectional Mapping Specification
# Template ID: document_schema_template

This template defines the bidirectional syntax mapping, heading hierarchy, inline formatting, table schemas, and callout structures between DOCX OOXML and Markdown (GFM).

---

## 1. Document Metadata (Frontmatter)

```yaml
---
title: "Document Title (e.g. Software Development Security Guidelines)"
document_id: "IT3-03"
classification: "Internal / General Operations"
version: "V2.0"
effective_date: "2026-10-21"
status: "Active"
---
```

---

## 2. Heading & Hierarchy Mapping

| Regulatory Level | DOCX Style & Visual Cue | Markdown Syntax | Hierarchy Notes |
| :--- | :--- | :--- | :--- |
| **Document Title** | Style `Title`, or `Normal` Bold $\ge 14\text{pt}$ | `# <Title>` | Document root title; unique |
| **Chapter / Major Level** | Style `Heading 1`, or prefix `壹、`, `貳、`, `參、` | `## 壹、<Title>` | Level 1 division |
| **Section / Medium Level** | Style `Heading 2`, or prefix `一、`, `二、`, `三、` | `### 一、<Title>` | Level 2 division |
| **Subsection / Clause** | Style `Heading 3`, or prefix `（一）`, `(一)` | `#### （一）<Title>` | Level 3 clause group |
| **Item / Paragraph** | Style `Heading 4`, or prefix `1.`, `2.`, `3.` | `1. <Text>` | Ordered list / item |
| **Sub-item** | Indented item, or prefix `(1)`, `（1）` | `   * (1) <Text>` | Nested list / sub-item |

---

## 3. Inline Typography Mapping

| Formatting Intent | OOXML Tag / Attribute | Markdown Syntax | Render Example |
| :--- | :--- | :--- | :--- |
| **Bold Emphasis** | `<w:b/>` | `**text**` | **Bold text** |
| **Italic** | `<w:i/>` | `*text*` | *Italic text* |
| **Underline** | `<w:u w:val="single"/>` | `<u>text</u>` | <u>Underlined text</u> |
| **Red Font (Revision)** | `<w:color w:val="FF0000"/>` | `<font color="#FF0000">text</font>` | <font color="#FF0000">Red revision</font> |
| **Red Underline (Addition)** | `<w:color w:val="FF0000"/><w:u/>` | `<ins><font color="#FF0000">text</font></ins>` | <ins><font color="#FF0000">Added text</font></ins> |
| **Inline Code** | Font `Consolas` / `Courier New` | `` `code` `` | `TLS 1.2` |
| **Strikethrough** | `<w:strike/>` | `~~text~~` | ~~Deprecated clause~~ |

---

## 4. Table Representation

### OOXML Requirements
- First row designated as Header Row (`<w:tblHeader/>`).
- Multiline content within cells preserved with `<br>` tags.
- Pipe characters (`|`) inside cell text escaped as `&#124;`.
- Inline formatting (bold, red, underline) inside table cells must be fully preserved.

### GFM Table Schema
```markdown
| Column A Header | Column B Header | Column C Header |
| :--- | :--- | :--- |
| Cell A1 content<br>Line 2 | Cell B1 <ins><font color="#FF0000">revised</font></ins> | **Note**<br>Reason details |
```

---

## 5. Callouts & Notes

### Footnote / Callout Schema
```markdown
> [!NOTE]
> Notes:
> 1. Additions: Underline + Red in the Amended Column.
> 2. Deletions: Underline + Red in the Current Column.
> 3. Whole clause changes: Underline + Red in the Explanation Column.
```

---

## 6. Execution Protocol for Agent

1. **DOCX -> Markdown Parsing**:
   - Inspect paragraph style names first (`Heading 1~4`, `Title`, `List Paragraph`).
   - If style is `Normal`, evaluate prefix patterns (`壹、`, `一、`, `（一）`, `1.`) to assign correct `#` depth.
   - Iterate run-level formatting to map bold, italic, underline, and color tags.
   - Convert tables to pipe tables with `<br>` line breaks.

2. **Markdown -> DOCX Assembly**:
   - Map `#` to Title / Heading styles or appropriate font sizes.
   - Map inline `**`, `<u>`, `<font color="#FF0000">` to run properties (`w:b`, `w:u`, `w:color`).
   - Render pipe tables as OOXML tables with consistent column widths.
