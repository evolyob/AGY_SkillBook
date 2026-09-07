---
name: pptx
description: Create, read, edit, and analyze PowerPoint presentation files (.pptx, .potx) using automated scripts and custom visual design systems.
dependencies: [pptx, PIL, resvg_py, defusedxml, lxml]
---

# PPTX Creation, Editing, and Visual Analysis

- All layout schemas, theme tables, 2-dimension icon catalogs, decision matrices, and API signatures are consolidated in **`references/pptx_layouts.md`** (DO NOT inspect `scripts/layout_engine.py` source code).

## Execution Workflow (4-Step Pipeline)

### Step 1: Canvas Ground & Theme Selection
- Select the global canvas ground and theme preset from `references/pptx_layouts.md` matching the domain (Tech/Architecture → `dark`, Proposals/Pitches → `yellow`, Operations/Reviews → `light`).

### Step 2: Content Outline & Visual-First Strategy
- Scope with the title, communicate the conclusion visually at a glance (Diagrams, Charts), prove it with evidence, then use concise text only where necessary.
- Parse input content into slide-by-slide Key Takeaways (synthesized into 3 core points), front-loading quantified metrics (e.g. `85% Cycle Time Reduction`, `100+ Hours Saved`) as auxiliary scan cues.

### Step 3: Semantic Intent, Layout & Icon Mapping
- Map each slide's business intent to Single-Layer or Multi-Layer composable grid architectures (Flows, Bento Cards, Charts, Image Slots, KPIs, Tables) via `references/pptx_layouts.md`.
- Assign intuitive semantic icon keywords (e.g. `icon: "shield"`, `icon: "server"`, `icon: "trend"`, `icon: "database"`) or preserve 1:1 original image assets. The Python engine automatically resolves SVG assets via backend fuzzy mapping and renders physical vector icons via `resvg_py`.
- Apply standard BMP symbols (e.g. `• ★`, `• ✓`, `• ✖`) strictly as inline auxiliary scan cues (never substituting for physical card icons); 4-byte SMP emojis are strictly prohibited.

### Step 4: Scripted Generation & Fast QA
- Declare design tokens (Palette 60-30-10, Typography, Container Cards, Vector Icon Cache) and execute Python generation via `PPTXLayoutEngine` saving to `~/Downloads/<deck_name>.pptx`.
- Execute lightweight validation: `python3 <skill_dir>/scripts/office/validate.py <output_path>`.
- Report the final file link and layout summary to the user.
