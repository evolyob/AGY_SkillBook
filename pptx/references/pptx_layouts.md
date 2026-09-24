# PPTX Visual Design & Layout Specification (`pptx_layouts.md`)

Single Source of Truth (SSOT) for design tokens, typography rules, container ratios, and the 9 core visual primitives.

---

## 1. Themes & Surface Tokens (`engine.t`)
Loaded centrally from `scripts/themes.json`.

| Theme | Ground (`bg`) | Cards (`card_bg`) | Primary (`p`) | Secondary (`s`) | Accent (`a`) | Alert (`alert`) | OK (`ok`) | Best For |
|---|---|---|---|---|---|---|---|---|
| **`light`** | `#FFFFFF` | `#F8FAFC` | `#2B5C8F` | `#007A92` | `#EC6A00` | `#E95119` | `#10B981` | Management briefs, quarterly reviews |
| **`dark`** | `#0B0F19` | `#1E293B` | `#00F0FF` | `#38BDF8` | `#F5E050` | `#FF0080` | `#10B981` | Tech architecture, executive keynotes |
| **`yellow`** | `#F5E050` | `#FFFFFF` | `#2B5C8F` | `#007A92` | `#EC6A00` | `#E95119` | `#10B981` | High-impact pitches, strategic proposals |

- **Typography Scale**: **Slide Title `28.0 ~ 32.0pt` (Bold)**, **Subtitle `14.0 ~ 18.0pt` (Regular)**, Card Title `15.5 ~ 18.0pt` (Bold), Body `13.5 ~ 14.5pt`, Minimum badge/tag `>= 13.5pt` (Hard Floor), KPI Big Numbers `24.0 ~ 28.0pt`.
- **Inline BMP Cues**: `• ✓` (ok), `• ✖` (alert), `• ★` / `• ◆` (p). Strictly prohibit 4-byte SMP emojis.

---

## 2. Ratio-Aware Containers & Icons
Icons load automatically from `assets/icons/` via engine backend semantic mapping. Specify intuitive icon keywords (`icon: "shield"`, `icon: "server"`).

| Aspect Ratio | Dimensions | Morphology | Role / Best For |
|---|---|---|---|
| **`5:1 ~ 8:1`** | `1.8" x 0.34"` | **Capsule / Pill** | Section tag delimiters (`【 Section Title 】`), status badges |
| **`3:1 ~ 4:1`** | `4.1" x 1.1"` | **Compact Card** | Vertically stacked findings, itemized checklists |
| **`4:3 ~ 1:1`** | `3.8" x 3.8"` | **Bento / Asset Box** | Multi-column pillars, contain-scaled images, charts |
| **`1:1`** | `0.5" x 0.5"` | **Node Circle** | Step indicators, timeline flow anchors |

---

## 3. Execution Template

```python
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from layout_engine import PPTXLayoutEngine
from pptx_patterns import PPTXPatterns

engine = PPTXLayoutEngine(theme="dark", font="Noto Sans TC")
p = PPTXPatterns

# Build slides using the 9 Core Primitives (or raw engine.create_slide for custom geometry)
p.add_card_grid(engine, title="Title", subtitle="Subtitle", cards=[...])
engine.save("~/Downloads/presentation_name.pptx")
```

---

## 4. The 9 Core Visual Primitives (Implemented in `scripts/pptx_patterns.py`)

| # | Primitive | `PPTXPatterns` Function | Description & Slot Requirements |
|---|---|---|---|
| 1 | **KPI Row** | `p.add_kpi_row(engine, ...)` | 3 metric badges with delta indicators. (`metrics=[{"label", "val", "chg", "icon", "note"}]`) |
| 2 | **Card Grid** | `p.add_card_grid(engine, ...)` | 3 or 4 column pillar capability cards. (`cards=[{"title", "tag", "icon", "body"}]`) |
| 3 | **Split Row** | `p.add_split_row(engine, ...)` | 50/50 comparison & boundary isolation. (`left_card={...}, right_card={...}`) |
| 4 | **Anchor Card** | `p.add_anchor_card(engine, ...)` | Top central mandate + bottom modular cards. (`anchor_card={...}, sub_cards=[...]`) |
| 5 | **Pipeline Flow** | `p.add_pipeline_flow(engine, ...)` | 4 horizontal sequential SOP steps. (`steps=[{"step", "title", "icon", "color"}]`) |
| 6 | **Checklist Grid** | `p.add_checklist_grid(engine, ...)` | Dual-gate verification readiness. (`left_gate={...}, right_gate={...}`) |
| 7 | **Matrix** | `p.add_matrix(engine, ...)` | 2x2 impact vs cost decision quadrants. (`high_impact_cards=[...], low_impact_cards=[...]`) |
| 8 | **Table Slide** | `p.add_table_slide(engine, ...)` | Structured registry with zebra striping. (`headers=[...], rows=[...], zebra=True`) |
| 9 | **Diagram Slide** | `p.add_diagram_slide(engine, ...)` | Dedicated slot for Mermaid vector diagrams. (`image_source="...", caption="..."`) |
