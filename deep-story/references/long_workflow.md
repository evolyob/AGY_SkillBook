# Long-Form Workflow (`deep-story`)

> Scope: Five-phase execution loop for multi-chapter serialized fiction using `storyctl.py`, `tracking_commit.py`, and `outline_view.py`.

## Phase 1–3: Planning (Stop After Delivery)

1. **Phase 1 (Premise & Preferences)**: Lock core selling point, genre rules, and book-level style preferences inside `tracking_commit.py` (`long_term_constraints`).
2. **Phase 2 (Settings)**: Create character cards, world rules, and domain anchors (statutes, deadlines, forensic hashes).
3. **Phase 3 (Outlines)**:
   - Book-wide & Volume outlines per `references/07_web_novel_outline_template.md` (backward-planned from climax).
   - Chapter detailed outlines per `references/08_novel_chapter_outline_template.md` with numbered Plot Beats and `禁/放` bounds.
   - Verify with `python3 scripts/check_outline_contract.py <outline_file>`.
   - **Hard Stop**: Deliver requested outlines and wait for explicit user approval before entering Phase 4.

## Phase 4: Single-Chapter Drafting

1. **Pre-Read Gate**: Read `上下文.md`, active `角色状态/*.md`, `时间线/读者已知.md`, the current chapter detailed outline, and the unit slice from `python3 scripts/outline_view.py`.
2. **Draft Prose**: Write the chapter honoring `禁/放` bounds and epistemic isolation (characters cannot act on `作者真相.md` facts absent from `读者已知.md` or their character state).
3. **Prose Gate**: Run `python3 scripts/storyctl.py chapter check --project <dir> --chapter <N> --fix-punctuation`.
   - Resolve all `blocking` findings (`check_ai_patterns.py`, `check_degeneration.py`, `normalize_punctuation.py`) and inspect `check_outline_copy.py` advisories per `references/12_`–`15_`.

## Phase 5: Delta Commit & Integrity

1. Prepare the chapter delta JSON payload and commit via `python3 scripts/storyctl.py chapter commit --project <dir> --chapter <N> --input <delta.json>`.
2. Verify `python3 scripts/tracking_commit.py check --project <dir>` passes with zero drift.
3. Cap at **3 chapters** per turn.
