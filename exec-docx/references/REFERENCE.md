# DOCX Technical Reference & Architecture Guide

## 1. Visual & Structure First Decision Matrix

> [!IMPORTANT]
> **Visual-First Rule**: Prohibit generating dense, unformatted walls of text. Always extract metrics, contrasts, stages, and comparisons into structured visual components:

| Content Intent & Business Goal | Optimal Visual Component | Grid Pattern | Target API Method |
|---|---|---|---|
| **Executive Quantified Metrics (1~4 Stats)** | Large numeric callout cards with accent left border | `100%` (3~4 cols) | `engine.add_kpi_cards()` |
| **As-Is vs To-Be / Pros vs Cons Comparison** | Side-by-side dual colored cards with bullet highlights | `50 / 50` Split | `engine.add_split_comparison()` |
| **Pillars / Capabilities / Themes (2~4 Cards)** | Adaptive cards with transparent gutters | `50/50` or `100%` | `engine.add_card_grid(cols=2/3/4)` |
| **Roadmap / Implementation Stages (01➔04)** | Horizontal sequential workflow cards with chevrons | `100%` Full | `engine.add_pipeline_flow()` |
| **Vertical Timeline / Step-by-Step Guide** | Vertical numbered badges with left accent line | `100%` Full | `engine.add_step_flow()` |
| **Multi-Dimensional Matrix / Audit Checklist** | Structured table with themed header & zebra stripes | `100%` Full | `engine.add_table(col_weights=...)` |
| **SDK Usage / Terminal Scripts / Configs** | Dark slate container with Consolas cyan text | `100%` Full | `engine.add_code_block()` |
| **Security Warnings / Regulatory Notes** | Shaded callout block with custom border accent | `100%` Full | `engine.add_callout()` |
| **Architectural Diagrams / High-DPI Charts** | Centered high-resolution image with caption | `100%` Full | `engine.add_picture()` |

---

## 2. Enterprise Document Generation (`DOCXLayoutEngine`)

The Python engine in `scripts/docx_engine.py` dynamically loads `scripts/themes.json` (SSOT) with universal `Noto Sans TC` typography (11pt base standard) and brand palettes (`ocean_executive`, `corporate_blue`, `warm_orange`).

### Core Engine API Signatures & Invocation

```python
import sys
from pathlib import Path

# Resolve <skill_dir>/scripts dynamically relative to script or execution root
_SKILL_SCRIPTS = Path(__file__).resolve().parent / "scripts" if "__file__" in globals() else Path("~/.gemini/config/skills/exec-docx/scripts").expanduser()
if str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from docx_engine import DOCXLayoutEngine

# 1. Initialize Engine
engine = DOCXLayoutEngine(theme="ocean_executive", font="Noto Sans TC")

# 2. Executive Title Block
engine.add_title(
    title="AI Governance Architecture Report",
    subtitle="2026 Technical Evaluation & Implementation Manual",
    category="GOVERNANCE BRIEF"
)

# 3. Section Headings (Orphan-Safe)
engine.add_heading("1. Core Quantitative Metrics", level=1)
engine.add_heading("1.1 Evaluation Benchmark Dimensions", level=2)

# 4. Standard Paragraph (11pt Base)
engine.add_paragraph("This section outlines key architectural metrics and performance benchmarks.")

# 5. KPI Stat Cards (with Accent Left Border & Change Badges)
engine.add_kpi_cards([
    {"label": "Overall Throughput", "val": "14.2k req/s", "chg": "+15.2%", "color": "#007A92"},
    {"label": "p99 Response Latency", "val": "38.5 ms", "chg": "-4.8%", "color": "#2B5C8F"},
    {"label": "Service Availability", "val": "99.98%", "chg": "+0.02%", "color": "#EC6A00"}
])

# 6. Structured Table with Zebra Stripes, Group Rows, Alignments & Rich Atoms (Progress/Badges)
engine.add_table(
    headers=["Module Name", "Owner Team", "Refactor Progress", "Status"],
    rows=[
        ["Core Identity & Payment Services"], # Single-element group header row spanning all columns
        ["Auth0 RBAC Gateway", "Security", {"progress": 100}, {"badge": "DONE", "status": "success"}],
        ["Payment Engine Async Decoupling", "FinTech", {"progress": 85}, {"badge": "REVIEW", "status": "info"}],
        ["Redis Cluster Replication", "Infra", {"progress": 40}, {"badge": "BLOCKED", "status": "danger"}]
    ],
    col_weights=[0.35, 0.2, 0.25, 0.2], # Dynamic width weights (or col_widths=[2.4, 1.2, 2.2, 1.2])
    alignments=["left", "center", "center", "center"] # Supports 'left', 'center', 'right'
)

# 7. Adaptive Card Grid (2, 3, or 4 columns with transparent gutters)
engine.add_card_grid([
    {"title": "As-Is Baseline Pain Points", "body": ["Manual verification checklists", "Fragmented audit logs"], "badge": "AS-IS", "color": "#2B5C8F"},
    {"title": "To-Be Target Architecture", "body": ["Automated CI/CD validation gates", "Unified immutable audit trails"], "badge": "TO-BE", "color": "#007A92"}
], cols=2)

# 8. Horizontal Pipeline Flow (Process Stages)
engine.add_pipeline_flow([
    {"step": "01", "title": "Scoping", "desc": "Establish threat model and regulatory boundary", "acc": "#007A92"},
    {"step": "02", "title": "Implementation", "desc": "Deploy controls with automated unit tests", "acc": "#2B5C8F"},
    {"step": "03", "title": "Quality Gate", "desc": "5-Gate verification and compliance audit", "acc": "#EC6A00"},
    {"step": "04", "title": "Production Release", "desc": "Canary deployment and executive signoff", "acc": "#059669"}
])

# 9. Two-Column Split Comparison Cards
engine.add_split_comparison(
    left_title="Legacy Baseline",
    left_items=["Manual verification checklists", "Fragmented audit trails"],
    right_title="Target Architecture",
    right_items=["Automated CI/CD validation gates", "Unified immutable audit logs"]
)

# 10. Terminal-Style Code Block
engine.add_code_block([
    "from docx_engine import DOCXLayoutEngine",
    "engine = DOCXLayoutEngine(theme='corporate_blue')",
    "engine.save('output.docx')"
], title="Python SDK Usage")

# 11. Callout Box (Bordered with Accent Stripe)
engine.add_callout(
    text="This report is compiled in accordance with enterprise cybersecurity governance standards.",
    title="Security Notice",
    border_color="#007A92"
)

# 12. Save Document
engine.save("~/Downloads/report.docx")
```

---

## 3. Editing Existing Documents & XML Gotchas

```bash
unzip -q doc.docx -d unpacked/
find unpacked -type l -delete   # Strip symlink entries for untrusted archives
python <skill_dir>/scripts/merge_runs.py unpacked/   # Merge fragmented runs
# Edit unpacked/word/document.xml in place — DO NOT reformat or pretty-print
(cd unpacked && rm -f ../out.docx && zip -Xr ../out.docx .)
python <skill_dir>/scripts/office/validate.py out.docx --original doc.docx
```

### Tracked Changes & Comments
- **Tracked changes**: Wrap runs in `<w:ins>`/`<w:del>` with `w:id`, `w:author`, `w:date`. Inside `<w:del>`, use `<w:delText>`. Validate with `--author "<name>"`.
- **Clean copy**: Run `python <skill_dir>/scripts/accept_changes.py in.docx out.docx`.
- **Comments helper**:
  ```bash
  python <skill_dir>/scripts/comment.py unpacked/ "Comment text" --parent 0
  ```

---

## 4. Fast Programmatic Validation

Validate OOXML integrity and schema compliance directly:
```bash
python3 <skill_dir>/scripts/office/validate.py <output_deck_or_docx>
```

