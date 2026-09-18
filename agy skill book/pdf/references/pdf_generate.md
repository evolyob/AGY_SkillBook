# PDF Composable Layout & UI Specification (`pdf_generate.md`)

SSOT for design tokens, pure-geometry dynamic solver, and declarative multimodal layout engine.

---

## 1. Themes & Surface Tokens (`get_theme_palette()`)
Loaded centrally from `data/pdf_themes.json`. Printable canvas width: `total=540pt` (A4/Letter).

| Theme | Ground (`bg`) | Cards (`card`) | Primary (`p`) | Pink Alert | Green OK | Best For |
|---|---|---|---|---|---|---|
| **`light`** | `#FFFFFF` | `#F8FAFC` | `#2B5C8F` | `#FEF2F2` / `#DC2626` | `#ECFDF5` / `#059669` | Executive 1-Pagers, Reports |
| **`dark`** | `#0B0F19` | `#1E293B` | `#00F0FF` | `#FF0080` | `#10B981` | Technical whitepapers |

- **Typography Scale**: Doc Title `22.0pt` (Bold), Section H1 `15.0pt`, Card Title `13.0~14.5pt`, **Min Typography $\ge$ 10.5pt Rule** (Body / Subtitle / Badges / Checklist / Flow Steps: `10.5~11.5pt`, Leading `14.5~15.5pt`).
- **Inline BMP Cues**: `• ✓` (green), `• ✖` (pink), `• ★` / `• ▶` (navy). No 4-byte SMP emojis.

---

## 2. Dynamic Capacity & Golden Quad-Core Archetypes

- **Dynamic Capacity Principle**: A4 1-Pager strictly follows `Header + 3~4 Functional Bands` (Dual-Grid layouts: `100% Full-Width` or `50/50 Symmetrical Split`). Every band follows `Band = Band Title + Function`:
- **Golden Quad-Core Archetypes**:
  1. **`Quadrant Matrix (2x2)`**: 四象限決策矩陣 (`build_split_row` × 2, P0~P3 資源分配)
  2. **`Multimodal Grid`**: 非對稱多模態混排 (`weights=[0.65, 0.35]`, 主架構表 + 雙層 KPI 堆疊)
  3. **`SOP Pipeline`**: 橫向四階段流程 (`build_pipeline_flow`, 步驟與 `▶` 導航)
  4. **`Editorial Timeline`**: 時間軸與里程碑檢核 (`build_checklist_grid`)

| Primitive | API Function | Line Cost | Grid Pattern | Use Case & Role |
| :--- | :--- | :---: | :---: | :--- |
| **Cards** | `build_kpi_row(kpis, total)` | **4 lines** | `100%` (3~4 cols) | Critical KPI metric cards (Large numbers + trend delta) |
| **Cards** | `build_card_grid(cards, cols, total)` | **6 lines** | `100%` (3~4 cols) | 3~4 horizontal topic cards for strategic pillars/themes |
| **Cards** | `build_action_board(as_is, to_be, total)` | **6 lines** | `50/50` Split | ✖ As-Is (Pink Painpoints) vs. ✔ To-Be (Green Actions) contrast board |
| **Cards** | `build_split_row([card_l, card_r], total)` | **6 lines** | `50/50` Split | Dual symmetrical topic cards (Scope vs. Target) |
| **Cards** | `build_card(content, width, height, ...)` | **4 lines** | `100%` Full | Full-width anchor card for policies, formulas, or execution roadmaps |
| **Grid** | `build_zebra_table(headers, rows, total)` | **6–8 lines** | `100%` Full | High-density zebra comparison table / compliance matrix |
| **Grid** | `build_checklist_grid(items, total, cols=2)` | **6–8 lines** | `50/50` Split | Dual-column structured checklist with numbered node badges |
| **Flow** | `build_pipeline_flow(steps, total)` | **4 lines** | `100%` Full | 4-phase sequential roadmap with `▶` directional arrows |
| **Charts** | `build_pie_chart(data, labels, w, h)` | **8–10 lines** | `50/50` or `100%` | Decoupled native ReportLab Pie Flowable with theme palette |
| **Charts** | `build_bar_chart(data, cats, w, h, vert)` | **8–10 lines** | `50/50` or `100%` | Decoupled native ReportLab Bar Flowable (Vertical or Horizontal) |

---

## 3. Python Generation Archetype (1-Page Infographic vs Multi-Page)

```python
import sys; sys.path.insert(0, '/path/to/pdf/scripts')
import builder
from reportlab.platypus import Spacer

story = [
    # Top (~15%): Header Block
    builder.build_document_header('Executive Strategy Title', '2026 Operational Baseline', 'Date: 2026-08-31'),
    Spacer(1, 6),
    # Band 1: 100% Full-Width Zebra Table
    builder.build_pill_badge('【 I. Baseline Compliance Matrix 】'), Spacer(1, 3),
    builder.build_zebra_table(headers, rows),
    Spacer(1, 6),
    # Band 2: 50/50 Symmetrical Action Board
    builder.build_pill_badge('【 II. Architecture: As-Is vs To-Be 】'), Spacer(1, 3),
    builder.build_action_board(as_is_dict, to_be_dict),
    Spacer(1, 6),
    # Band 3: 50/50 Dual Charts in Cards
    builder.build_pill_badge('【 III. Threat & Metric Visuals 】'), Spacer(1, 3),
    builder.build_split_row([
        builder.build_card([builder._p('<b>Distribution</b>'), builder.build_pie_chart([45, 55], ['A', 'B'])], width=265, height=130),
        builder.build_card([builder._p('<b>Quarterly Trend</b>'), builder.build_bar_chart([35, 65], ['Q1', 'Q2'])], width=265, height=130)
    ], total=540, gap=10),
    Spacer(1, 6),
    # Bottom (~20%): 4-Phase Roadmap or Anchor Card
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
