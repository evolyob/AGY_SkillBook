---
name: deep-story
description: Pure Python 3 and JSON narrative writing engine with long/short workflows, single-ledger dual-timeline tracking, outline/prose quality gates, and cross-chapter consistency review.
dependencies: []
---

# Deep Story: Narrative State & Writing Engine

## Objective
Manage long-form and short-form fiction projects using the battle-tested Python 3 core (`tracking_commit.py`, `storyctl.py`, `outline_view.py`) driven by `data/contracts.json` and `data/deslop_rules.json`.

## Hard Invariants (Always Enforce)
1. **No Outline, No Prose**: Never draft a chapter before its detailed outline passes `check_outline_contract.py`.
2. **Planning Stop Point**: When asked to plan outlines or settings, deliver the plan and **stop**; do not auto-draft prose or initialize tracking.
3. **Single-Ledger Authority**: Never manually edit derived Markdown files under `tracking/`. Always mutate state via `tracking_commit.py` / `storyctl.py chapter commit` and verify via `tracking_commit.py check`.
4. **Epistemic Isolation**: Keep `timeline_author` (truth) separate from `timeline_reader` (revealed) and each character's `known` / `misbelieved` / `concealed` fields.
5. **Batch Cap**: Draft at most **3 chapters** per turn in long-form daily mode.

## By-Moment Reference Routing (Read Only What This Turn Needs)

| Execution Moment | Target File | Load Condition |
| :--- | :--- | :--- |
| **Long-Form Planning & Drafting** | `references/long_workflow.md` | Long-form project (multi-chapter serialization) |
| **Short-Form Drafting** | `references/short_workflow.md` | Short-form project (`setting.md`, `outline.md`, `prose.md`) |
| **Cross-Chapter Consistency Review** | `references/review_rubric.md` | Auditing continuity, deadlines, or `S1-S4` conflicts |
| **Dialogue & Scene Craft** | `references/dialogue_and_scene_craft.md` | Drafting power-asymmetric dialogue, interrogations, or subtext |
| **Story Bible & Outline Specs** | `references/06_*.md` to `10_*.md` | Designing settings, backward outlines, beats, or hooks |
| **3-Layer De-Slop & Style Rules** | `references/12_*.md` to `15_*.md` | Fixing flagged prose or resolving style conflicts |

## Deterministic CLI Workflow (`scripts/`, Pure Python 3)

| Step | Command | Purpose |
| :--- | :--- | :--- |
| **1. Init Ledger** | `python3 scripts/tracking_commit.py init --project <dir> --input <init.json>` | Initialize `_tracking-state.json` and derived views |
| **2. Outline Slice** | `python3 scripts/outline_view.py --project <dir> --chapter <N>` | Extract only the current unit slice from volume outline |
| **3. Outline Check** | `python3 scripts/check_outline_contract.py <outline_file>` | Verify required outline fields and Plot Beats table |
| **4. Chapter Check** | `python3 scripts/storyctl.py chapter check --project <dir> --chapter <N> [--fix-punctuation]` | Measure word count + run AI-pattern, degeneration, punctuation, and outline-copy checks |
| **5. Chapter Commit** | `python3 scripts/storyctl.py chapter commit --project <dir> --chapter <N> --input <delta.json>` | Commit state delta and regenerate all derived views |
