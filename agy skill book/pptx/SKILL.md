---
name: pptx
description: Create, read, edit, and analyze PowerPoint presentation files (.pptx, .potx) using automated scripts and custom visual design systems.
dependencies: [pptx, PIL, resvg_py, defusedxml, lxml]
---

# PPTX Creation, Editing, and Visual Analysis

- All layout schemas, theme tables, 2-dimension icon catalogs, decision matrices, and API signatures are consolidated in **`references/pptx_layouts.md`** (DO NOT inspect `scripts/layout_engine.py` source code).

## Execution Workflow (4-Step Pipeline)

### Step 1: Canvas Ground & Theme Selection
- Select theme preset matching the domain: Tech/Architecture → `dark`, Proposals/Pitches → `yellow`, Operations/Reviews → `light`.

### Step 2: Content Outline & Proof-Led Strategy
- **Assertion Titles**: Build a title-only storyboard first; each title must state a conclusion-led claim (never neutral labels like "Overview"), so reading titles sequentially communicates the complete executive narrative.
- **Proof-Led Visuals**: Deliver 1 governing takeaway supported by 1~3 distinct evidence points (avoid forcing 3 equal cards). Select from the 4 Visual Pillars (Cards, Diagrams, Charts, Tables) strictly to prove the claim, front-loading metrics only with clear baselines and sources.

### Step 3: Semantic Intent, Layout & Icon Mapping
- Map each slide's business intent to Single-Layer or Multi-Layer composable grid architectures (Flows, Bento Cards, Charts, Image Slots, KPIs, Tables).
- Assign intuitive semantic icon keywords (e.g. `icon: "shield"`, `icon: "server"`, `icon: "trend"`, `icon: "database"`) or preserve 1:1 original image assets. The Python engine automatically resolves SVG assets via backend fuzzy mapping and renders physical vector icons via `resvg_py`.
- Apply standard BMP symbols (e.g. `• ★`, `• ✓`, `• ✖`) strictly as inline auxiliary scan cues (never substituting for physical card icons); 4-byte SMP emojis are strictly prohibited.

### Step 4: Scripted Generation & Fast QA
- Run Python generation script via `PPTXLayoutEngine` saving deliverable to `~/Downloads/<deck_name>.pptx`.
- Execute lightweight validation: `python3 <skill_dir>/scripts/office/validate.py <output_path>`.
- Report the final file link and layout summary to the user.
