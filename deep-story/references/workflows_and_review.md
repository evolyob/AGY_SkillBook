# Long-Form Workflow (`deep-story`)

> Scope: Four-state execution loop (`0. Intake` -> `1. Planning` -> `2. Drafting` -> `3. Revision`) using `storyctl.py`, `tracking_commit.py`, and `outline_view.py`.
> **Canonical Project Paths (Pure English ASCII)**:
> - `settings/` (`settings/characters/<slug>.md`, `settings/world/<slug>.md`, `settings/style.md`)
> - `outlines/` (`outlines/book_outline.md`, `outlines/vol_<NN>.md`, `outlines/ch_<NNN>.md`)
> - `chapters/` (`chapters/ch_<NNN>.md`; revision backups: `chapters/ch_<NNN>_bak_<YYYYMMDD>.md`)
> - `tracking/` (`tracking/_tracking-state.json`, `tracking/context.md`, `tracking/foreshadowing.md`, `tracking/characters/`, `tracking/logs/`, `tracking/timeline/author_truth.md`, `tracking/timeline/reader_known.md`)
> - `.story/outline_notes/<unit_id>.md`, `.story/work/ch_<NNN>/`

## State 0: Entry Guard & External Source Intake

1. **Bare Invocation / Scope Guard**:
   - If invoked with no clear task, inspect project state (`settings/`, `outlines/`, `chapters/`, `tracking/`) and offer 2–4 plain-language options (e.g., discuss structure, plan volume/chapters, draft Chapter N, revise Chapter X). Never auto-draft prose.
   - If asked only to discuss structure, deliver structural options and create zero files.
2. **Source Inspection Before Card Selection** (for large external note folders):
   - Inspect only the directory listing, master index, or file headers first—never ingest an entire multi-volume folder at once.
   - Present a **Preliminary Card Selection** for user confirmation: (a) long-form vs short-form; (b) `primary [+ secondary]` genre IDs from `data/story_blocks.json`; (c) initial protagonist/antagonist archetypes; (d) which 1–2 source files to extract for Volume 1 `settings/world/` and `.deslop-whitelist`.

## State 1 (Phase 1–3): Planning & Bible (Stop After Delivery)

1. **Phase 1–2 (Settings & Domain Anchors)**:
   - Create `settings/characters/<slug>.md` (recurring characters only), `settings/world/<slug>.md` (extract trigger conditions, exceptions, costs, and deadlines per volume), and `<project>/.deslop-whitelist` (one literal domain term per line, `#` for comments).
   - Keep `long_term_constraints` (max 6 items) reserved for book-wide selling points and non-negotiable invariants; put detailed statutes/procedures in `settings/world/`.
2. **Phase 3 (Book, Volume & Chapter Outlines)**:
   - Build `outlines/book_outline.md` and `outlines/vol_01.md` per `templates/book_outline.md` (backward-planned from climax), checking the four agency/pacing questions in `references/outline_and_bible_guide.md`. Verify with `python3 scripts/outline_view.py --check outlines/vol_01.md`.
   - **Pre-Outline Supply Check (`寫綱前查缺`)**: Before generating a batch of chapter outlines, complete the 3-item check in `.story/outline_notes/<unit_id>.md` or under the unit card: (1) antagonist continuity; (2) recurring character cards & ability bounds; (3) cited statutes, prices, and deadlines in `settings/world/` (write `無缺口` if none).
   - Build `outlines/ch_<NNN>.md` per `templates/chapter_outline.md` (aim for 4–5 `Plot Beats` per standard 2,200–2,800 char chapter). Verify with `python3 scripts/check_outline_contract.py --project <dir> --chapter <N>`.
   - **Outline Lock & Hard Stop**: Outlines and volume units for already-drafted chapters are locked (append-only for new units unless user confirms edits). Deliver requested outlines and **stop**; do not initialize `tracking/` or draft prose.

## State 2 (Phase 4–5): Beat-Driven Drafting & Commit (Max 3 Chapters/Turn)

1. **First-Chapter Init & Pre-Read Gate**:
   - Before drafting Chapter 1 (if `tracking/_tracking-state.json` is absent), initialize via `python3 scripts/tracking_commit.py init --project <dir> --input <init.json>`.
   - Read `tracking/context.md`, active `tracking/characters/*.md`, `tracking/timeline/reader_known.md`, `outlines/ch_<NNN>.md`, and the unit slice from `python3 scripts/outline_view.py --project <dir> --chapter <N>`.
2. **Beat-Driven Drafting & New-Element Escalation**:
   - Draft `chapters/ch_<NNN>.md` beat-by-beat along `Plot Beats`, honoring `禁/放` bounds and epistemic isolation. Stop once all approved beats land—never pad prose to chase word count.
   - **Three-Tier New-Element Rule**:
     - *Write directly*: Walk-on NPCs, props, one-off scene details (no card, no tracking).
     - *File & track*: Recurring NPCs, factions, reusable rules, new foreshadowing (create card + record in tracking delta).
     - *Ask user first*: New main-plot twists, power-ceiling changes, economic anchors, early truth reveals, or overriding established outline decisions (pause and propose 1–2 options).
3. **Prose Gate & Word-Count Resolution**:
   - Run `python3 scripts/storyctl.py chapter check --project <dir> --chapter <N> --fix-punctuation`.
   - Resolve all `blocking` findings (including AI patterns, degeneration, and engineering-word leaks) in the same turn. Only skip AI-pattern checks if the user explicitly requested it (`<!-- 去味:跳過 -->` within the first 6 lines; degeneration/engineering terms still block).
   - **Out-of-Band Word Count**: If *under* target band, **never pad**—offer the user 3 choices (accept current length / revise outline & redraft / discard). If *over* band, run one pure-deletion pass (`compress-once`, cutting repetition without inventing new plot) and re-check; if still over, ask user whether to `chapter accept-current-length`.
4. **Draft-Prefill & Atomic Commit**:
   - Run `python3 scripts/tracking_commit.py draft --project <dir> --chapter <N>` to pre-fill `.story/work/ch_<NNN>/tracking.json`, update only changed delta/snapshots, then commit via `python3 scripts/storyctl.py chapter commit --project <dir> --chapter <N> --input <tracking.json>`.
   - Verify `python3 scripts/tracking_commit.py check --project <dir>` passes with zero drift.
   - Report to the user in plain story language only (what happened, ending hook, any new recurring elements or decisions needed).

## State 3: Revision & Diagnosis Workflow

1. **Locate & Scope**:
   - If the user cites only reader symptoms without naming a chapter, scan `Opening Hook -> Ending Landing -> Mid-Chapter Turn` against the Symptom Table below and confirm the target chapter before editing.
   - Confirm scope (3 options): `1. Local edit` (touch only named paragraphs; read adjacent chapter ends only) / `2. Full chapter rewrite` (follow existing outline; read full prev/next chapters) / `3. Revise outline first, then rewrite` (unlock outline with user consent).
2. **Backup & Revise**:
   - Copy the original file to `chapters/ch_<NNN>_bak_<YYYYMMDD>.md` before editing.
   - Apply edits and run `python3 scripts/storyctl.py chapter check --project <dir> --chapter <N> --fix-punctuation`. Report explicitly if length changed by >30% or >800 chars.
3. **Cascade Recompute (`mode=revision`)**:
   - Run `tracking_commit.py draft --project <dir> --chapter <N>`, inspect chapters `N..M` (up to latest committed chapter `M`), and merge updated foreshadowing, timeline truths/reader knowledge, and multi-dimensional character snapshots without wiping later chapters' valid state.
   - Commit via `storyctl.py chapter commit`, verify `tracking_commit.py check`, and scan chapters `N+1..M` to flag any prose lines impacted by the revision.

| Reader Symptom | Likely Root Cause | Actionable Fix |
| :--- | :--- | :--- |
| Pacing drags / filler | Previous payoff landed without a new hook; transition lacks active thread | Pull next conflict/clue forward; cut status-quo scenes |
| Payoff feels flat ("that's it?") | Insufficient pressure/stakes before payoff, or weak bystander stakes | Add concrete cost/leverage before turn; show stakeholder reactions |
| Repetitive loop | Same obstacle/solution pattern repeated 3+ units | Keep core emotion, swap antagonist, venue, and tactic |
| Protagonist feels passive / tool-like | Institutions or allies make the key choices and take credit | Restore protagonist's irreversible choice and direct gain |
| Opening fails to hook | Worldbuilding/backstory placed ahead of immediate trouble | Move Ch 1 conflict and personal stakes into first 1,000 chars |

---

# Short-Form Workflow (`deep-story`)

> Scope: Four-phase execution loop for self-contained short stories (`settings.md`, `short_outline.md`, `story.md`).

1. **Phase 1 (Emotional Target & Premise)**: Define target reader emotion, core twist/payoff, and style constraints in `settings.md`.
2. **Phase 2 (Design Gate)**: Populate `settings.md` and `short_outline.md` per `templates/short_outline.md`. **Hard Gate**: Do not draft `story.md` until both are complete.
3. **Phase 3 (Scene Drafting)**: Draft `story.md` following `short_outline.md` and `references/opening_and_hooks.md`.
4. **Phase 4 (Quality Gate)**: Run `check_ai_patterns.py --check --json --fail-on=blocking story.md`, `check_degeneration.py --check --json --fail-on=blocking story.md`, `normalize_punctuation.py --check story.md`, and `check_outline_copy.py --outline short_outline.md story.md`. Resolve all `blocking` findings per `references/deslop_logic_and_focus.md` -> `references/deslop_expression.md`.

---

# Cross-Chapter Consistency Review Rubric (`deep-story`)

- **S1 / S2 (`Must Fix`)**: Direct factual contradictions, broken causality, premature epistemic leaks (`author_truth.md` leaked before reveal), or violated deadlines/statutes.
- **S3 (`Recommended Fix`)**: Pacing imbalance, weak scene payoff, missing `Goal -> Obstacle -> Action -> Cost -> New Expectation` loop, or unfulfilled foreshadowing *(never blocks commit or forces full rewrite)*.
- **S4 (`Optional`)**: Minor wording polish or optional detail alignment.
- **User-Facing Output Rule**: Present findings in plain domain language; for conflicts use `[Upstream Canon (Rule/Ch, "quote")] vs [Downstream Clash (Ch N, "quote")]`, never internal script names or raw `S1-S4` codes in the main body.
