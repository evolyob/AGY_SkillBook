# Short-Form Workflow (`deep-story`)

> Scope: Four-phase execution loop for self-contained short stories (`setting.md`, `outline.md`, `prose.md`) without heavy chapter-by-chapter tracking.

## Phase 1: Emotional Target & Premise
- Define the target reader emotion, core twist/payoff, and genre constraints in `setting.md`.
- Record persistent preferences via `author_memory_commit.py` if requested.

## Phase 2: Design Gate
- Populate `setting.md` (characters, stakes, domain anchors) and `outline.md` (emotional arc, scene beats, payoff/reversal timing).
- **Hard Gate**: Do not draft `prose.md` until both `setting.md` and `outline.md` are complete and verified.

## Phase 3: Scene-by-Scene Drafting
- Draft `prose.md` following `outline.md` and `references/09_` / `10_`.
- Keep every scene advancing conflict, relationship, or reveal.

## Phase 4: Revision & Quality Gate
- Run `check_ai_patterns.py --check --json --fail-on=blocking prose.md`, `check_degeneration.py --check --json --fail-on=blocking prose.md`, `normalize_punctuation.py --check prose.md`, and `check_outline_copy.py --outline outline.md prose.md`.
- Resolve all `blocking` findings and perform a semantic review per `references/12_deslop_expression_guide.md` and `13_deslop_narrative_focus_guide.md`.
