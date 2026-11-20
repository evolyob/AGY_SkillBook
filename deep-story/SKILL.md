---
name: deep-story
description: Pure Python 3 and JSON narrative writing engine with long/short workflows, single-ledger dual-timeline tracking, outline/prose quality gates, and cross-chapter consistency review.
dependencies: []
---

# Deep Story: Narrative State & Writing Engine

## Objective
Manage long-form and short-form fiction projects using the pure Python 3 core (`tracking_commit.py`, `storyctl.py`, `outline_view.py`) with strict Single-Source-of-Truth (SSOT) layer separation:
- `data/`: Machine-verified contract rules, narrative pattern definitions, and genre prose profiles (`contracts.json`, `deslop_rules.json`, `genre_cards.json`).
- `templates/`: Sole authoritative blank schemas for project initialization, cards, and outlines.
- `references/`: Filled exemplars, craft diagnostics, and failure-mode repair guides (loaded on demand only).
- `scripts/`: Deterministic CLI verifiers and single-ledger state mutators.

## Hard Invariants (Always Enforce)
1. **No Outline, No Prose**: Never draft a chapter before its detailed outline passes `check_outline_contract.py` (long-form) or follows `templates/short_outline.md` (short-form).
2. **Planning Stop Point**: When asked to plan outlines or settings, deliver the plan and **stop**; do not auto-draft prose or initialize tracking.
3. **Single-Ledger Authority**: Never manually edit derived Markdown files under `tracking/` (`追蹤/`). Always mutate state via `tracking_commit.py` / `storyctl.py chapter commit` and verify via `tracking_commit.py check`.
4. **Epistemic Isolation**: Keep `作者真相.md` separate from `讀者已知.md` and each character's `known` / `misbelieved` / `concealed` fields.
5. **Batch Cap**: Draft at most **3 chapters** per turn in long-form daily mode.

## End-to-End Logical Pipeline (1-to-1 SSOT Routing)

Load **only** the `templates/` skeleton for daily drafting; load `references/` **on demand** only when diagnosing structure, hooks, or flagged prose:

| Stage | Current Task | Authoritative Blank Schema (`templates/`) | On-Demand Craft Guide (`references/`) | Deterministic CLI Gate |
| :--- | :--- | :--- | :--- | :--- |
| **1. Init & Bible** | Initialize ledger, cards & rules | `templates/init.json`, `character_card.md`, `world_rule.md`, `deslop-whitelist` | `references/outline_and_bible_guide.md` | `python3 scripts/tracking_commit.py init --project <dir> --input <init.json>` |
| **2. Book / Vol Outline** | Backward-plan volume & unit arcs | `templates/book_outline.md` *(pick 1 `Genre Profile` from `data/genre_cards.json`)* | `references/outline_and_bible_guide.md` | `python3 scripts/outline_view.py --check <卷綱.md>` |
| **3. Chapter / Short Outline** | Build detailed beats (`禁/放`) | `templates/chapter_outline.md` (long) / `templates/short_outline.md` (short) | `references/opening_and_hooks.md` *(Ch 1–3 / hooks)* | `python3 scripts/check_outline_contract.py --project <dir> --chapter <N>` |
| **4. Draft Prose** | Execute long or short drafting loop | *(Use `追蹤/上下文.md` + outline)* | `references/workflows_and_review.md` / `dialogue_and_scene_craft.md` | `python3 scripts/storyctl.py chapter check --project <dir> --chapter <N> --fix-punctuation` |
| **5. De-Slop & Polish** | Fix flagged prose (logic -> expression) | *(Fix only flagged lines)* | `references/deslop_logic_and_focus.md` -> `references/deslop_expression.md` | Re-run `storyctl.py chapter check` until `blocking_findings == []` |
| **6. Commit & Review** | Persist delta & audit continuity | *(Prepare delta JSON)* | `references/workflows_and_review.md` | `python3 scripts/storyctl.py chapter commit --project <dir> --chapter <N> --input <delta.json>` + `tracking_commit.py check` |
