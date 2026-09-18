# PDF Composable Layout & UI Specification (`pdf_generate.md`)

Single Source of Truth (SSOT) for design tokens, pure-geometry layout solver, and declarative multimodal layout engine.

---

## 1. Themes & Surface Tokens (`get_theme_palette()`)
Centrally loaded from `data/pdf_themes.json`. Printable canvas width: `total=540.0pt` (A4/Letter portrait).

| Theme | Ground (`bg`) | Cards (`card`) | Primary (`p`) | Pink Alert | Green OK | Best For |
|---|---|---|---|---|---|---|
| **`light`** | `#FFFFFF` | `#F8FAFC` | `#2B5C8F` | `#FEF2F2` / `#DC2626` | `#ECFDF5` / `#059669` | Executive 1-Pagers, Reports |
| **`dark`** | `#0B0F19` | `#1E293B` | `#00F0FF` | `#FF0080` | `#10B981` | Technical Whitepapers |

- **Typography Scale**: Document Title `22.0pt` (Bold), Section H1 `15.0pt`, Card Title `13.0~14.5pt`.
- **Min Typography Rule**: Body, Subtitle, Badges, Checklists, and Flow Steps must strictly enforce $\ge 10.5\text{pt}$ (fontSize `10.5~11.5pt`, leading `14.5~15.5pt`).
- **Inline BMP Glyphs**: Use ASCII or 2-byte BMP unicode symbols (`• ✓` green, `• ✖` pink, `• ★` / `• ▶` navy). Never emit 4-byte SMP emojis.

---

## 2. Core Layout Specifications & Capacity Guardrails

All page layouts decompose strictly into **6 orthogonal categories**. Enforce the specifications, grid proportions, vertical line cost budgets, and capacity guardrails below:

### Category 1: Card (Enclosed Single Container)
- **API**: `build_card(content, width, height, bg, border, radius, pad)`
- **Grid / Cost**: `100%` full width (540pt) / ~**4 lines**.
- **Use Case**: Standalone executive declarations, primary summaries, or full-width takeaway cards.

### Category 2: Grid 50/50 (Symmetric Dual-Column Grid)
- **APIs**:
  - `build_checklist_grid(items)` (Cost: ~**6 lines** / Dual-column circular numbered checklist)
  - `build_split_row(cols_content, weights)` (Cost: ~**4~6 lines** / Custom dual-column proportional split)
- **Capacity Guardrail**: Dual-column symmetrical layout. Keep checklist items terse ($\le$ 25 characters per item). The text length ratio between left and right columns must not exceed **1.5x** to preserve visual balance.

### Category 3: Grid 100% (Full-Width Multi-Column Grid)
- **APIs**:
  - `build_kpi_row(kpis)` (Cost: ~**4 lines** / 3~4 column high-impact metric counters)
  - `build_pipeline_flow(steps)` (Cost: ~**4 lines** / 4-phase horizontal workflow pipeline)
  - `build_card_grid(cards, cols)` (Cost: ~**6 lines** / 2~3 column modular strategy cards)
- **Capacity Guardrail**: Keep KPI metric labels concise (e.g. `99.98%`, `< 15ms`); descriptive subtitle labels must be $\le$ 8 words.

### Category 4: Data (Structured Zebra Table)
- **API**: `build_zebra_table(headers, rows, total, col_widths)`
- **Grid / Cost**: `100%` full width (540pt) / ~**6~8 lines**.
- **Use Case**: Alternating row backgrounds for compliance matrices, control audits, and inventory tables. Cell typography strictly $\ge 10.5\text{pt}$.

### Category 5: Chart (Local Quantitative Charts)
- **APIs**: 
  - `build_bar_chart(data, categories, width, height, is_vertical)` (Vertical / horizontal bar charts)
  - `build_pie_chart(data, labels, width, height)` (Pie chart with legends)
- **Grid / Cost**: `50/50` dual charts side-by-side (width 265pt, height 130pt) or `100%` full width / ~**8~10 lines**.
- **Role**: Pure quantitative metric statistics. 100% local ReportLab vector rendering with zero external network dependencies.

### Category 6: Mermaid (External Vector Topology Diagram)
- **Pipeline**: `python3 scripts/preview_scaffold.py --export-diagram <key> --export-out assets/<file>.png`
- **Embed**: `build_card(RLImage('assets/<file>.png', width=520, height=...))`
- **Grid / Cost**: `100%` full width (520~540pt) / ~**8~12 lines**.
- **Supported Topologies**: Strictly limited to 3 core topologies:
  1. **`flowchart`** (Microservice architecture, network perimeter, decision trees)
  2. **`sequence`** (API authentication, HTTPS handshakes, inter-service protocols)
  3. **`er`** (Database entity-relationship models, capped at $\le$ 6 entities)

---

## 3. Python Generation Archetype (1-Page Infographic)

A4 1-page vertical height budget control: `Header (~4 lines) + 3~4 functional bands (~24 lines) = Total height strictly budgeted within 28~30 lines` to guarantee zero page overflow:

```python
import sys; sys.path.insert(0, '/path/to/pdf/scripts')
import builder
from reportlab.platypus import Spacer

story = [
    # Top (~15%): Header Band (Cost: 4 lines)
    builder.build_document_header('Executive Strategy Title', '2026 Operational Baseline', 'Date: 2026-08-31'),
    Spacer(1, 6),
    
    # Band 1 (Category 4: Data): 100% Full-Width Zebra Table (Cost: 6 lines)
    builder.build_pill_badge('【 I. Baseline Compliance Matrix 】'), Spacer(1, 3),
    builder.build_zebra_table(headers, rows),
    Spacer(1, 6),
    
    # Band 2 (Category 3: Grid 100%): Strategic Pillars in 3 Cards (Cost: 6 lines)
    builder.build_pill_badge('【 II. Strategic Pillars & Focus Areas 】'), Spacer(1, 3),
    builder.build_card_grid([
        {"badge": "SEC-01", "title": "Zero Trust Perimeter", "body": ["Enforce device identity", "Least-privilege network access"]},
        {"badge": "OPS-02", "title": "Continuous Delivery", "body": ["Automated test gates", "Deterministic build artifacts"]},
        {"badge": "GOV-03", "title": "Compliance & Audit", "body": ["Immutable audit logs", "Continuous posture reporting"]}
    ], cols=3),
    Spacer(1, 6),
    
    # Band 3 (Category 5: Chart): 50/50 Native Dual Charts in Cards (Cost: 8 lines)
    builder.build_pill_badge('【 III. Threat & Metric Visuals 】'), Spacer(1, 3),
    builder.build_split_row([
        builder.build_card([builder._p('<b>Distribution</b>'), builder.build_pie_chart([45, 55], ['A', 'B'])], width=265, height=130),
        builder.build_card([builder._p('<b>Quarterly Trend</b>'), builder.build_bar_chart([35, 65], ['Q1', 'Q2'])], width=265, height=130)
    ], total=540, gap=10),
    Spacer(1, 6),
    
    # Band 4 (Category 3: Grid 100%): 4-Phase Roadmap (Cost: 4 lines)
    builder.build_pill_badge('【 IV. Execution Roadmap 】'), Spacer(1, 3),
    builder.build_pipeline_flow(steps)
]

# 1-Pager Infographic (Zero Margin Overflow)
builder.generate_infographic_1pager('output.pdf', story)
```

---

## 4. Quality Verification SOP
Always run automated 6-Gate verification:
```bash
python3 scripts/verifier.py <output.pdf>
# Must output: [Verification PASSED] 6/6 Gates OK (Includes Gate 6 AI Detox)
```
