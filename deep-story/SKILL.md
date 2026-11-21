---
name: deep-story
description: Pure Python 3 and JSON narrative writing engine with long/short workflows, single-ledger dual-timeline tracking, outline/prose quality gates, and cross-chapter consistency review.
dependencies: []
---

# Deep Story: Narrative State & Writing Engine

## Objective
Manage long-form and short-form fiction projects using the pure Python 3 core (`tracking_commit.py`, `storyctl.py`, `outline_view.py`) with strict Single-Source-of-Truth (SSOT) layer separation:
- `data/`: Machine-verified contract rules, narrative pattern definitions, and composable story building blocks (`contracts.json`, `deslop_rules.json`, `story_blocks.json`).
- `templates/`: Sole authoritative blank schemas for project initialization, cards, and outlines.
- `references/`: Filled exemplars, craft diagnostics, and failure-mode repair guides (loaded on demand only).
- `scripts/`: Deterministic CLI verifiers and single-ledger state mutators.

## Hard Invariants (Always Enforce)
1. **Entry Guard & Planning Stop Point**: On bare invocation with no clear intent, diagnose the project and offer 2–4 plain-language options without auto-drafting. When asked only to discuss structure, create no files; when asked to plan settings or outlines, deliver the plan and **stop** (do not auto-draft prose or initialize `tracking/`).
2. **No Outline, No Prose**: Never draft a chapter before its detailed outline passes `check_outline_contract.py` (long-form) or follows `templates/short_outline.md` (short-form). Lock outlines and volume units of already-drafted chapters; modify only with explicit user confirmation.
3. **Single-Ledger Authority**: Never manually edit derived Markdown files under `tracking/`. Always mutate state via `tracking_commit.py draft` -> `storyctl.py chapter commit` and verify via `tracking_commit.py check`.
4. **Epistemic & Engineering Isolation**: Keep `tracking/timeline/author_truth.md` separate from `tracking/timeline/reader_known.md` and each character's `known` / `misbelieved` / `concealed` fields. Never leak pipeline/engineering terms (e.g., 細綱, 情節點, 本章, 下一章, 伏筆) into prose outside chapter headings.
5. **New-Element Escalation & Batch Cap**: Handle newly invented elements in three tiers: (a) one-off details -> write directly; (b) recurring characters/rules/foreshadowing -> file card + commit in tracking; (c) main-plot shifts, power ceilings, or early reveals -> pause and ask the user. Draft at most **3 chapters** per turn in long-form daily mode.
6. **De-Slop Exemption**: Only skip AI-pattern checks when the user explicitly requests it by placing `<!-- 去味:跳過 -->` within the first 6 lines of the chapter; degeneration and engineering-term checks still apply.

## End-to-End Logical Pipeline (1-to-1 SSOT Routing)

Load **only** the `templates/` skeleton for daily drafting; load `references/` **on demand** only when diagnosing structure, hooks, or flagged prose:

| Stage | Current Task | Authoritative Blank Schema (`templates/`) | On-Demand Craft Guide (`references/`) | Deterministic CLI Gate |
| :--- | :--- | :--- | :--- | :--- |
| **0. Intake & Triage** | Inspect external sources & select cards | *(View source TOC/headers first)* | `references/workflows_and_review.md` | Confirm scope (`discuss` / `plan` / `draft` / `revise`) & genre mix |
| **1. Bible & Rules** | Create character cards, world rules & whitelist | `character_card.md` *(compose from `data/story_blocks.json`)*, `world_rule.md`, `deslop-whitelist` | `references/outline_and_bible_guide.md` | Verify source-to-rule extraction (per-volume scope) |
| **2. Book / Vol Outline** | Backward-plan volume & unit arcs | `templates/book_outline.md` *(pick `primary [+ secondary]` genre from `data/story_blocks.json`)* | `references/outline_and_bible_guide.md` | `python3 scripts/outline_view.py --check outlines/vol_01.md` |
| **3. Chapter / Short Outline** | Build detailed beats (`禁/放`, 4–5 beats/ch) | `templates/chapter_outline.md` (long) / `templates/short_outline.md` (short) | `references/opening_and_hooks.md` *(Ch 1–3 / hooks)* | `python3 scripts/check_outline_contract.py --project <dir> --chapter <N>` |
| **4. Init & Draft Prose** | Init ledger (Ch 1 only) & draft beats | `templates/init.json` + `tracking/context.md` + outline | `references/workflows_and_review.md` / `dialogue_and_scene_craft.md` | `python3 scripts/tracking_commit.py init` *(Ch 1)* + `storyctl.py chapter check --project <dir> --chapter <N> --fix-punctuation` |
| **5. De-Slop & Polish** | Fix flagged prose (logic -> expression) | *(Fix only flagged lines)* | `references/deslop_logic_and_focus.md` -> `references/deslop_expression.md` | Re-run `storyctl.py chapter check` until `blocking_findings == []` |
| **6. Commit / Revise** | Persist delta or cascade revision | *(Pre-fill via `tracking_commit.py draft`)* | `references/workflows_and_review.md` | `python3 scripts/storyctl.py chapter commit --project <dir> --chapter <N> --input <delta.json>` + `tracking_commit.py check` |
