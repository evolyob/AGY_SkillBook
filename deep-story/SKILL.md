---
name: deep-story
description: Pure Python 3 and JSON narrative writing engine with long/short workflows, single-ledger dual-timeline tracking, outline/prose quality gates, and cross-chapter consistency review.
dependencies: []
---

# Deep Story: Narrative State & Writing Engine

## Objective
Manage long-form and short-form fiction projects using the pure Python 3 core (`tracking_commit.py`, `storyctl.py`, `outline_view.py`) driven by `data/contracts.json` and `data/deslop_rules.json`.

## Hard Invariants (Always Enforce)
1. **No Outline, No Prose**: Never draft a chapter before its detailed outline passes `check_outline_contract.py`.
2. **Planning Stop Point**: When asked to plan outlines or settings, deliver the plan and **stop**; do not auto-draft prose or initialize tracking.
3. **Single-Ledger Authority**: Never manually edit derived Markdown files under `tracking/` (`追蹤/`). Always mutate state via `tracking_commit.py` / `storyctl.py chapter commit` and verify via `tracking_commit.py check`.
4. **Epistemic Isolation**: Keep `作者真相.md` separate from `讀者已知.md` and each character's `known` / `misbelieved` / `concealed` fields.
5. **Batch Cap**: Draft at most **3 chapters** per turn in long-form daily mode.

## End-to-End Logical Pipeline (1-to-1 SSOT Routing)

Load **only** the single reference file mapped to your current stage:

| Stage | Current Task | Single Authoritative Reference | Deterministic CLI Gate |
| :--- | :--- | :--- | :--- |
| **1. Init & Bible** | Initialize ledger & character cards | `references/06_novel_story_bible_template.md` | `python3 scripts/tracking_commit.py init --project <dir> --input <init.json>` |
| **2. Book / Vol Outline** | Backward-plan volume arcs | `references/07_web_novel_outline_template.md` | `python3 scripts/outline_view.py --project <dir> --chapter <N>` |
| **3. Chapter Outline** | Build detailed beats (`禁/放`) | `references/08_novel_chapter_outline_template.md` | `python3 scripts/check_outline_contract.py --project <dir> --chapter <N>` |
| **3a. Ch 1–3 / Hooks** | Opening check / ending timer | `references/09_web_novel_golden_three_chapters.md` / `10_web_novel_chapter_ending_hooks.md` | *(Load only for Ch 1–3 or hook selection)* |
| **4. Draft Prose** | Execute long or short drafting loop | `references/long_workflow.md` or `short_workflow.md` | `python3 scripts/storyctl.py chapter check --project <dir> --chapter <N> --fix-punctuation` |
| **4a. High-Tension Dialogue** | Subtext, trials, power asymmetry | `references/dialogue_and_scene_craft.md` | *(Load only when scene is dialogue-driven)* |
| **5. De-Slop & Polish** | Fix flagged prose (in strict order) | `15_deslop_style_resolution.md` -> `14_deslop_story_logic_guide.md` -> `13_deslop_narrative_focus_guide.md` -> `12_deslop_expression_guide.md` | Re-run `storyctl.py chapter check` until `blocking_findings == []` |
| **6. Commit & Review** | Persist delta & audit continuity | `references/review_rubric.md` | `python3 scripts/storyctl.py chapter commit --project <dir> --chapter <N> --input <delta.json>` + `tracking_commit.py check` |
