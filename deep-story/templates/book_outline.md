# Book Spine (`<project>/outlines/book_outline.md`)

> **Output**: Split into `<project>/outlines/book_outline.md` (spine) and `<project>/outlines/vol_<NN>.md` (volume/unit cards).
> **Gate**: `python3 scripts/outline_view.py --check <project>/outlines/vol_<NN>.md`

- **Genre Profile**: <primary_id> [+ <optional secondary_id>] (from data/story_blocks.json)
- **Core Selling Point**: <Unique reader hook>
- **Protagonist Starting Point**: <Current lack, constraint, and fear>
- **Book-Wide Goal**: <One concrete objective with clear pass/fail>
- **Endgame Binary Choice**: <Climax trade-off contrasting the opening>
- **Ending State**: <External situation, key relationships, and mindset>
- **Cross-Volume Arcs**: <Which secret or relationship advances and resolves in which volume>

### Volume Overview
| Vol | Role | Core Event | Start -> End State | Held-Back / Revealed |
| :--- | :--- | :--- | :--- | :--- |
| 1 | <Opening/Setup> | <One-sentence core clash> | <Start> -> <End> | <What stays hidden until later vols> |

---

# Volume Outline (`<project>/outlines/vol_01.md`)

## Volume Arc <!-- 全卷 -->
- **Volume Goal**: <Situation shift required by volume end>
- **Major Obstacle**: <Primary antagonist or structural resistance>
- **New Strategy**: <Tactic forced upon the protagonist>
- **Climax Showdown**: <Direct confrontation at volume end>
- **Partial Payoff & Remaining Pressure**: <Resolved stake and next-volume trigger>
- **Forbidden Early Reveals**: <Secrets, masterminds, or power ceilings held for later volumes>

### Unit 1: <Unit Name> <!-- L1-01 -->
- **章節範圍**：第 1-3 章
- **單元情緒引擎**：<Expected emotional arc for this unit>
- **主導權與關鍵點**：<Protagonist agency check; 1/4, midpoint, 3/4 beat placement>
- **單元節拍/章功能分配**：
  - Chapter 1: <Opening event and hook>
  - Chapter 2: <Escalation and counter-move>
  - Chapter 3: <Unit climax and cliffhanger>

#### 寫綱前查缺
- **Antagonist**: <Who opposes the protagonist in this batch>
- **Characters & Abilities**: <All recurring characters in next 3 chapters have cards and consistent ability bounds>
- **World Rules & Timelines**: <All cited statutes, costs, and deadlines exist in `settings/world/`> (write `無缺口` if none)
