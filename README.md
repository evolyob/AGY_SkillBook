# Antigravity (AGY) Skill Book

A collection of production-ready agentic skills, document layout engines, and research pipelines for Google Antigravity (AGY).

---

## 1. Skills Catalog & Capabilities Matrix

The following skills are available in this repository:

| Skill | Category | Primary Mission & Scope | Core Tools & Technologies |
| :--- | :--- | :--- | :--- |
| **[`audit-skill`](audit-skill/)** | Governance & Quality | 12-Gate automated AST static code and skill auditor (<20ms). Enforces coding standards, dynamic line budgets, and security guardrails. | Python AST, Regex, Static Analysis |
| **[`exec-docx`](exec-docx/)** | Document Engineering | High-fidelity Word (.docx) generation, structured tables, and ISO/IEC 29500 OpenXML redlining validation. | `python-docx`, ISO XSD Validators |
| **[`exec-xlsx`](exec-xlsx/)** | Spreadsheet Engineering | Enterprise Excel (.xlsx/.csv) layout engine with Noto Sans TC typography, KPI cards, CJK auto-width, lossless `<extLst>` XML patching, and headless formula recalculation. | `openpyxl`, `xml_patcher`, LibreOffice (`soffice`) |
| **[`pptx`](pptx/)** | Presentation Engineering | Declarative layout engine for modern slide decks with dynamic grid solvers, WCAG auto-contrast, and polymorphic card slots. | `python-pptx`, `resvg-py`, `Pillow` |
| **[`pdf`](pdf/)** | Document Engineering | High-precision PDF document creation, Platypus flowable layouts, UI dashboards, OCR scanning, and 5-Gate schema verification. | `reportlab`, `pdfplumber`, `pypdf` |
| **[`noai-note`](noai-note/)** | Executive Communication | Two-phase executive assistant for meeting notes, executive briefs, proof-led presentation outlines, and 1-pager visual blueprints. | Markdown, Shift-Left Anti-AI Heuristics |
| **[`deep-mod`](deep-mod/)** | Research & Synthesis | Universal 4-stage interactive deep research pipeline: requirement clarification, systematic data collection, evidence-based fact-checking, and cross-department synthesis. | Structured Multi-Agent Protocols |
