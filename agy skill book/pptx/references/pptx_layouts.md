# PPTX Composable Layout & UI Specification (`pptx_layouts.md`)

Single Source of Truth (SSOT) for design tokens, dynamic geometry solver, declarative layout engine, and editorial vector diagram patterns.

---

## 1. Themes & Surface Tokens (`engine.t`)
Loaded centrally from `scripts/themes.json`.

| Theme | Ground (`bg`) | Cards (`card`) | Accent (`cyan`) | Alert (`pink`) | Success (`emerald`) | Best For |
|---|---|---|---|---|---|---|
| **`light`** | `#FFFFFF` | `#F1F5F9` | `#2B5C8F` | `#EE1818` | `#10B981` | Management briefs, quarterly reviews |
| **`dark`** | `#0B0F19` | `#1E293B` | `#00F0FF` | `#FF0080` | `#10B981` | Tech architecture, executive keynotes |
| **`yellow`** | `#F5E050` | `#FFFFFF` | `#2B5C8F` | `#E95119` | `#10B981` | High-impact pitches, strategic proposals |

- **Typography Scale**: **Slide Title `28.0 ~ 32.0pt` (Bold)**, **Subtitle `14.0 ~ 18.0pt` (Regular)**, Card Title `15.5 ~ 18.0pt` (Bold), Body `13.5 ~ 14.5pt`, Minimum badge/tag `>= 13.5pt` (Hard Floor), KPI Big Numbers `24.0 ~ 28.0pt`.
- **Inline BMP Cues**: `• ✓` (emerald), `• ✖` (pink), `• ★` / `• ◆` (cyan). Strictly prohibit 4-byte SMP emojis.

---

## 2. Ratio-Aware Containers & Icons
Icons load automatically from `assets/icons/` via engine backend semantic mapping (or 1:1 image bytes). AI specifies intuitive icon keywords (`icon: "shield"`, `icon: "server"`).

| Aspect Ratio | Dimensions | Morphology | Role / Best For |
|---|---|---|---|
| **`5:1 ~ 8:1`** | `1.8" x 0.34"` | **Capsule / Pill** | Section tag delimiters (`【 Section Title 】`), status badges |
| **`3:1 ~ 4:1`** | `4.1" x 1.1"` | **Compact Card** | Vertically stacked findings, itemized checklists |
| **`4:3 ~ 1:1`** | `3.8" x 3.8"` | **Bento / Asset Box** | Multi-column pillars, contain-scaled images, charts |
| **`1:1`** | `0.5" x 0.5"` | **Node Circle** | Step indicators, timeline flow anchors |

---

## 3. Core Engine Invocations & Composable Slide API

### 3.1 Lifecycle & Execution Template

```python
import sys
from pathlib import Path

# Dynamically resolve <skill_dir>/scripts
_SCRIPTS_DIR = Path("~/.gemini/config/skills/pptx/scripts").expanduser()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from layout_engine import PPTXLayoutEngine

# 1. Initialize Engine (themes: 'dark', 'light', 'yellow')
engine = PPTXLayoutEngine(theme="dark", font="Noto Sans TC")

# 2. Build Slides Declaratively
engine.create_slide(
    title="Main Title (100% Full Width)", subtitle="Subtitle | Project Date",
    layers=[
        # Layer 1: Horizontal SOP Flow (height=1.5")
        {"height": 1.5, "section_tag": "Process Analysis", "content": {"type": "flow", "steps": [
            {"step": "STEP 01", "title": "Scan Vulnerabilities", "icon": "key", "color": engine.t["amber"]},
            {"step": "STEP 02", "title": "Verify Remediation", "icon": "radar", "color": engine.t["cyan"]}
        ]}},
        # Layer 2: Multimodal Multi-Column Grid (height=3.8")
        {"height": 3.8, "section_tag": "Remediation & Evidence", "cols": [
            [card1_dict, card2_dict, card3_dict],               # Col 1: Layer Stack / Tiered Cards
            {"type": "image", "source": img1, "caption": "..."}, # Col 2: Contain-scaled Image / Vector Slot
            {"type": "image", "source": img2, "caption": "..."}  # Col 3: Contain-scaled Image / Vector Slot
        ]}
    ]
)

# 3. Save Output Deck
output_path = engine.save("~/Downloads/presentation_name.pptx")
```

---

## 4. The 4 Core Visual Pillars (Cards, Diagrams, Charts, Tables)

All layouts and components in `/pptx` map directly to one of the 4 fundamental visual pillars:

### 4.1 Pillar 1: Cards (Structured Content & Containers)
Focuses on structured business text, policy clauses, and decision frameworks. Rendered using 100% native editable PowerPoint shapes.

| Card Pattern | Declarative `engine.create_slide(...)` Configuration | Description & Structure |
|---|---|---|
| **Executive Bento** | `layers=[{"height": 2.7, "cols": [3 Cards]}, {"height": 2.3, "cols": [2 Metrics]}]` | Top-level management overview: upper strategic pillars + lower quantified big-number metric cards. |
| **Quadrant Matrix (2x2)** | `layers=[{"height": 2.5, "section_tag": "▲ High Impact", "cols": [p0_card, p1_card]}, {"height": 2.5, "section_tag": "▼ Low Impact", "cols": [p2_card, p3_card]}]` | Strategic 2x2 decision grid: cost vs benefit priority quadrants (P0/P1/P2/P3). |
| **Split Compare / Layer Stack** | `layers=[{"height": 5.2, "cols": [left_panel, right_panel], "weights": [1.2, 1.0]}]` | Balanced dual containers: Before vs After, Problem vs Solution, or tiered vertical feature stack. |

### 4.2 Pillar 2: Diagrams (Topology, Geometry & Process)
Focuses on system logic, architectures, and process flows. Rendered following Swiss editorial standards (orthogonal routing, strictly 1-2 focal accents, font size `>= 14.5pt`).

| Diagram Pattern | Declarative Configuration / Pipeline | Description & Visual Rules |
|---|---|---|
| **Editorial Tree** | `layers=[{"height": 5.2, "cols": [{"type": "image", "source": tree_vector, "caption": "..."}]}]` | Structural hierarchy: top root node + orthogonal 90° T-split branches + leaf detail cards. |
| **Editorial Timeline** | `layers=[{"height": 5.2, "cols": [{"type": "image", "source": timeline_vector, "caption": "..."}]}]` | Temporal evolution: central horizontal baseline + alternating milestone cards. |
| **SOP Pipeline** | `layers=[{"content": {"type": "flow", "steps": [...]}}]` | Linear operational procedure: horizontal pipeline steps, status indicators, and transition arrows. |

### 4.3 Pillar 3: Charts (Quantitative Metrics & Gauges)
Focuses on data comparisons, SLA completion rates, and quantified scorecards.

| Chart Pattern | Declarative Slot Configuration | Description & Visual Rules |
|---|---|---|
| **KPI Big Numbers** | `{"type": "kpi", "label": "...", "val": "2.4M", "chg": "▲ +12%", "icon": "gauge"}` | High-level 24~28pt quantified metrics with trend cues and auxiliary notes. |
| **Bento Bars** | `{"type": "bars", "bars": [["Group A", 98.5], ["Group B", 92.0]], "insight": "..."}` | Comparative horizontal value bars with insight callout badge. |
| **Donut & Progress Gauges** | `{"type": "donut", "val": 96.5, "icon": "shield-check"}` / `{"type": "progress", "val": 85}` | Circular percentage completion rings and linear progress bars. |

### 4.4 Pillar 4: Tables (Two-Dimensional Matrices & Structured Logs)
Focuses on feature comparisons, status summaries, and operational registries with zebra striping.

| Table Pattern | Declarative Slot Configuration | Description & Visual Rules |
|---|---|---|
| **Zebra Data Matrix** | `{"type": "table", "headers": ["Col 1", "Col 2"], "rows": [["A1", "B1"], ["A2", "B2"]], "zebra": True}` | Clean multi-column matrix with auto-aligned alternating row fills. |
| **Weighted Registry** | `{"type": "table", "headers": [...], "rows": [...], "col_weights": [2, 1, 1]}` | Explicit column width weighting for primary descriptions + compact metrics. |
