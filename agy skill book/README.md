# Antigravity (AGY) Skill Book

A collection of production-ready agentic skills, document layout engines, and governance configurations for Google Antigravity (AGY).

---

## 1. Skills Catalog & Capabilities Matrix

The following skills are available in this directory:

| Skill | Category | Primary Mission & Scope | Core Tools & Technologies |
| :--- | :--- | :--- | :--- |
| **[`audit-skill`](audit-skill/)** | Governance & Quality | 12-Gate automated AST static code and skill auditor (<20ms). Enforces coding standards, dynamic line budgets, and security guardrails. | Python AST, Regex, Static Analysis |
| **[`exec-docx`](exec-docx/)** | Document Engineering | High-fidelity Word (.docx) generation, structured tables, and ISO/IEC 29500 OpenXML redlining validation. | `python-docx`, ISO XSD Validators |
| **[`exec-xlsx`](exec-xlsx/)** | Spreadsheet Engineering | Enterprise Excel (.xlsx/.csv) layout engine with Noto Sans TC typography, KPI cards, CJK auto-width, lossless `<extLst>` XML patching, and headless formula recalculation. | `openpyxl`, `xml_patcher`, LibreOffice (`soffice`) |
| **[`pptx`](pptx/)** | Presentation Engineering | Declarative layout engine for modern slide decks with dynamic grid solvers, WCAG auto-contrast, and polymorphic card slots. | `python-pptx`, `resvg-py`, `Pillow` |
| **[`pdf`](pdf/)** | Document Engineering | High-precision PDF document creation, Platypus flowable layouts, UI dashboards, OCR scanning, and 5-Gate schema verification. | `reportlab`, `pdfplumber`, `pypdf` |
| **[`noai-note`](noai-note/)** | Executive Communication | Two-phase executive assistant for meeting notes, executive briefs, proof-led presentation outlines, and 1-pager visual blueprints. | Markdown, Shift-Left Anti-AI Heuristics |
| **[`sec-intel`](sec-intel/)** | Security & Threat Intel | Authoritative, evidence-based intelligence lookup for IPs, ASNs, Domains, and CVEs via ICANN RDAP, real DNS resolution, and dual-engine EUVD/OSV. | ICANN RDAP, `dnspython`, EUVD, OSV |
| **[`asset-risk`](asset-risk/)** | Security & Risk Assessment | Intelligently categorize information assets and select diverse, causally linked threats and vulnerabilities without repetitive monotony. | Python Stdlib, Anti-Monotony Round-Robin |
| **[`deep-grill`](deep-grill/)** | Strategic Decision-Making | Socratic interview protocol designed to challenge proposed plans, designs, and architectures to surface hidden risks and assumptions one question at a time. | Socratic Interview Heuristics |
| **[`deep-mod`](deep-mod/)** | Research & Synthesis | Universal 4-stage interactive deep research pipeline: requirement clarification, systematic data collection, evidence-based fact-checking, and cross-department synthesis. | Structured Multi-Agent Protocols |

---

## 2. Reference Architectures & Examples (`examples/`)

The [`examples/`](../examples/) directory provides reference implementations and foundational infrastructure templates:

| Component | Path | Description |
| :--- | :--- | :--- |
| **Coding Standards** | [`examples/coding-standards.md`](../examples/coding-standards.md) | The production architectural governance guide and AST static audit specifications (Return Early, Keyword-only arguments, Spec-First boundaries, Defensive bounds, Functional cores, and Small diffs). |
| **Automation & Quality Hooks** | [`examples/hooks/`](../examples/hooks/) | Automated lifecycle event handlers and guardrails:<ul><li>`hooks.json`: Lifecycle hook configurations (`pre_tool_call`, `post_tool_call`, `on_user_message`).</li><li>`anti_blind_mutation.py`: Prevents destructive, unvalidated code edits.</li><li>`post_tool_quality_guard.py`: Post-tool execution verification and quality filter.</li></ul> |
| **Persistent Memory Framework** | [`examples/memory/`](../examples/memory/) | Structured 3-tier long-term memory system (Load -> Save -> Recall):<ul><li>`core.md`: Master index and routing table for persistent memory.</li><li>`topics/agent_behavior.md`: Agent persona, communication style, and boundary directives.</li><li>`topics/engineering_and_delivery_standards.md`: Delivery routing, file conventions, and verification standards.</li></ul> |
