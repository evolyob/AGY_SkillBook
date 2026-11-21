# Story Bible & Outline Craft Guide (`deep-story`)

> Pipeline: **Stage 1 (Story Bible State Isolation)** -> **Stage 2 (Backward-Planned Book/Vol Outline)** -> **Stage 3 (Detailed Chapter Outline & Bounds)**.

---

## 1. Story Bible Architecture & Single-Dimension Updates

Separate static identity from plot-mutable state; canonize each fact in **one** place only. Create `templates/character_card.md` and `templates/world_rule.md` **only for recurring elements** (leave one-off NPCs in chapter logs).

| Module | Stores | Update Trigger |
| :--- | :--- | :--- |
| **Character Card** | Identity, bottom lines, capability ceiling, long-term goal | Formal setting change |
| **Current State** | Location, resources, relationships, known/misbelieved, unresolved | Valid chapter change |
| **Relationship Table** | Mutual promises, debts, public vs private stances | Action alters relationship |
| **Author Timeline** | Objective chronological order of events | New facts confirmed |
| **Reader Knowledge** | Facts already revealed in prose | Chapter finished |
| **World Rules** | Trigger conditions, exceptions, costs, hard deadlines | Rule established/revised |

### Single-Dimension Update Formula (`Δ Only -> Preserve Rest`)
- **Rule**: When a chapter changes one state (e.g., handing over a duty key), update **only that field** and carry all other rows (location, authority, broken confidentiality, unresolved misbeliefs) forward unchanged. Never imply that handing over an object transfers knowledge or reconciles relationships automatically.
- **Revision & Conflict Priority**: When revising Chapter `X`, recompute affected states forward (`X -> M`). Triage conflicts strictly in order: **(1) Direct plot contradictions -> (2) Hidden causal breaks -> (3) Minor appearance slips -> (4) Overdue foreshadowing reminders**.

---

## 2. Backward-Planned Book & Volume Outline

**Planning Formula**: `Book-Wide Goal -> Endgame Binary Choice -> Volume Climax -> Backward Prerequisites -> Stage Goal -> Adjustable Scene Memos`

| Layer | Governs | Adjustment Scope |
| :--- | :--- | :--- |
| **Book-Wide Spine** | What protagonist must accomplish and why only them | Stable; check written chapters before altering |
| **Volume Route** | Situation shift & volume-end climax | Paths adjustable; never overturn established causes |
| **Scene Memos** | Specific clues/scenes to cross a beat | Revise while drafting; unwritten ideas are not canon |

### Four-Question Agency & Pacing Audit (Run Per Volume / Unit)
1. **Protagonist Agency**: Did the protagonist make the irreversible choice and earn the outcome? (Institutions/allies cannot hijack crisis resolution without explicit strategic trade-offs.)
2. **Credit & Gain Ownership**: Did core gains, leverage, and recognition stay with the protagonist?
3. **Late-Stage Reserve**: Are endgame masterminds, final truths, and power ceilings preserved for later volumes? (Reveal at most one major secret per volume.)
4. **Expectation & Map Continuity**: Did prior promises advance, and when switching maps/arenas, did at least one unresolved goal, debt, or relationship carry over?

### Volume Anchors, Beat Cadence & Failure Fixes
- **Anchors & Cadence**: Place major turns at **1/4** (inciting pressure / first reversal), **1/2** (midpoint raising stakes), and **3/4** (volume climax). Rotate emotional motifs (max 2–3 consecutive chapters of the same tension). For standard 2,200–2,800 char chapters, aim for **4–5 `Plot Beats` per chapter** (~450–600 chars each).

| Common Outline Failure | Root Cause | Fix Formula |
| :--- | :--- | :--- |
| **Leveling = main plot** | Getting stronger has no visible endpoint | Define the concrete task that requires that strength |
| **Writing forward blindly** | Late climax lacks early setup | Lock climax choice first; backward-plan prerequisites |
| **Map-swap resets to zero** | Old stakes vanish every volume | Make Volume N's outcome trigger Volume N+1's trouble |
| **Disconnected subplots** | Word count bloats while main plot stalls | Keep a subplot only if it helps, blocks, or alters main plot |
| **Over-scripted outline** | No room for live drafting sparks | Lock direction and stakes; leave scene execution flexible |

**Sufficiency Gate**: An outline is ready if you can answer: *what is pursued next, who blocks it, what is lost on failure, and what the climax changes*.

---

## 3. Detailed Chapter Outline (`outlines/ch_<NNN>.md`)

**Fill Order**: `Chapter Position + Target Emotion + Protagonist Goal/Key Choice -> Action Beats -> Stakes & Detail Level -> 禁/放 Bounds -> Ending Handoff`

1. **Concrete Emotion & Choice**: Never write bare labels like "hot-blooded" or "sad." Write `start emotion -> end emotion` plus the turning action. Protagonist goal = what they want; key choice = costly on-the-spot trade-off (passive reward/rescue = no choice).
2. **Stakes & Separate Ledgers**: Anchor gains/losses to prior known prices or expenses. Keep distinct valuations separate—never subtract a repair quote (e.g., 3,000) from a buyout offer (e.g., 800) to invent fake profit.
3. **Detail Allocation (`密 / 中 / 疏`)**: Mark which beats expand scene-by-scene (`密`) and which pass in 1–2 lines (`疏`). Beat count is driven by content, never by dividing target word count.
4. **Dual Bounds (`禁 / 放`)**:
   - `禁` (Forbidden): Locks trump cards/secrets that must not leak early and unapproved twists. Write `None` if no leak risk exists—never pad.
   - `放` (Allowed): Grants drafter improvisation room (phrasing, sensory texture) without altering malfunction, ownership, or repair outcome.

> **Condensed Skeleton Example (Ch 12: The 800-Yuan Watch)**:
> `Emotion: Frustrated at age dismissal -> Cathartic craft vindication + rent worry` | `Choice: Open watch in public (break = pay damages & ruin shop)` | `Beats: (1 疏) Quote 3,000 repair; 禁: hide engraving origin -> (2 中) Rival offers 800 buyout; 放: mock her youth -> (3 密) Pledge "break = pay" -> (4 密) Second hand moves; customer refuses 800 -> (5 疏) Promises more watches; appraiser secretly photographs inner lid; 禁: withhold engraving meaning.`

### Common Detailed-Outline Mistakes
- **Blank-form paralysis**: Fill goals, choices, and core beats first; omit optional fields when inapplicable.
- **Uniform pacing / maxing every chapter**: Allow low-pressure breathing chapters as long as an active expectation ties to the next chapter.
- **Treating plans as completed facts**: Preparing to expose someone ≠ having exposed them; scheduling a viewing ≠ having rented the shop.
- **Redundant ending recaps**: Stop once the visual/action hook lands.
