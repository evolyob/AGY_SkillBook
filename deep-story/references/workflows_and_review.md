# Long-Form Workflow (`deep-story`)

> Scope: Five-phase execution loop for multi-chapter serialized fiction using `storyctl.py`, `tracking_commit.py`, and `outline_view.py`.
> **Directory & Filename Invariant**: The Python engine enforces canonical project directory names: `設定/` (`設定/角色/`), `大綱/` (`大綱/卷綱_第X卷.md`, `大綱/細綱_第001章.md`), `正文/` (`正文/第001章_章名.md`), and `追蹤/` (`追蹤/_tracking-state.json`, `追蹤/上下文.md`, `追蹤/伏筆.md`, `追蹤/角色狀態/`, `追蹤/時間線/作者真相.md`, `追蹤/時間線/讀者已知.md`). Always use these exact folder names.

## Phase 1–3: Planning (Stop After Delivery)

1. **Phase 1 (Premise & Preferences)**: Lock core selling point, genre rules, and book-level style preferences inside `tracking_commit.py` (`long_term_constraints`).
2. **Phase 2 (Settings)**: Create character cards (`設定/角色/{名}.md`), world rules (`設定/世界觀/`), and domain anchors (statutes, deadlines, forensic hashes).
   - **External Source Anchoring**: When the user provides external notes, manuals, or reference folders, extract verifiable rules, timelines, and technical constraints into `設定/世界觀/` and `long_term_constraints` without binding the skill to machine-specific paths.
   - **Book-Local Term Whitelist**: For domain-heavy fiction (legal statutes, technical protocols, proper nouns), list literal terms (one per line, `#` for comments) in `<project>/.deslop-whitelist` so `check_ai_patterns.py` and `normalize_punctuation.py` preserve them verbatim.
3. **Phase 3 (Outlines)**:
   - Book-wide & Volume outlines (`大綱/大綱.md`, `大綱/卷綱_第一卷.md`) per `templates/book_outline.md` (backward-planned from climax).
   - **寫綱前查缺**：每批產生章細綱前，須先在 `.story/排綱筆記/{unit_id}.md`（或卷綱該劇情段下）填寫「寫綱前查缺」小節，核對是否缺少設定、道具或伏筆前提；無缺口則明寫 `無缺口`。
   - Chapter detailed outlines (`大綱/細綱_第001章.md`) per `templates/chapter_outline.md` with required metadata labels (`- 核心事件:`, `- 字數目標:`, `- 屬於哪段劇情:`, `- 目標情緒:`, `- 主角目標/關鍵選擇:`, `- 章首鉤子:`, `- 爽點:`, `- 本章禁止提前釋放:`) and subsections (`### 這章怎麼走`, `### 情節安排`, `### 人物關係和出場順序`, `### 情節細化` with numbered table).
   - Verify with `python3 scripts/check_outline_contract.py --project <dir> --chapter <N>`.
   - **Hard Stop**: Deliver requested outlines and wait for explicit user approval before entering Phase 4.

## Phase 4: Single-Chapter Drafting

1. **Pre-Read Gate**: Read `追蹤/上下文.md`, active `追蹤/角色狀態/*.md`, `追蹤/時間線/讀者已知.md`, `大綱/細綱_第NNN章.md`, and the unit slice from `python3 scripts/outline_view.py --project <dir> --chapter <N>`.
2. **Draft Prose**: Write `正文/第NNN章_章名.md` honoring `禁/放` bounds and epistemic isolation (characters cannot act on `追蹤/時間線/作者真相.md` facts absent from `追蹤/時間線/讀者已知.md` or their character state).
3. **Prose Gate**: Run `python3 scripts/storyctl.py chapter check --project <dir> --chapter <N> --fix-punctuation`.
   - Resolve all `blocking` findings (`check_ai_patterns.py`, `check_degeneration.py`, `normalize_punctuation.py`) and inspect `check_outline_copy.py` advisories per `references/deslop_logic_and_focus.md` -> `references/deslop_expression.md`.

## Phase 5: Delta Commit & Integrity

1. Prepare the chapter delta JSON payload and commit via `python3 scripts/storyctl.py chapter commit --project <dir> --chapter <N> --input <delta.json>`.
2. Verify `python3 scripts/tracking_commit.py check --project <dir>` passes with zero drift.
3. Cap at **3 chapters** per turn.

---

# Short-Form Workflow (`deep-story`)

> Scope: Four-phase execution loop for self-contained short stories (`setting.md`, `小節大綱.md`, `正文.md`) without heavy chapter-by-chapter tracking.

## Phase 1: Emotional Target & Premise
- Define the target reader emotion, core twist/payoff, and genre constraints in `setting.md`.
- Record any style preferences directly in `setting.md`.

## Phase 2: Design Gate
- Populate `setting.md` (characters, stakes, domain anchors) and `小節大綱.md` per `templates/short_outline.md` (emotional arc, scene beats, payoff/reversal timing).
- **Hard Gate**: Do not draft `正文.md` until both `setting.md` and `小節大綱.md` are complete and verified.

## Phase 3: Scene-by-Scene Drafting
- Draft `正文.md` following `小節大綱.md` and `references/opening_and_hooks.md`.
- Keep every scene advancing conflict, relationship, or reveal.

## Phase 4: Revision & Quality Gate
- Run `check_ai_patterns.py --check --json --fail-on=blocking 正文.md`, `check_degeneration.py --check --json --fail-on=blocking 正文.md`, `normalize_punctuation.py --check 正文.md`, and `check_outline_copy.py --outline 小節大綱.md 正文.md`.
- Resolve all `blocking` findings and perform a semantic review per `references/deslop_expression.md` and `deslop_logic_and_focus.md`.

---

# Cross-Chapter Consistency Review Rubric (`deep-story`)

> Scope: Deterministic and semantic continuity audit across chapters, timelines, statutes, and character motivations.

## Severity Levels (Internal -> User-Facing Translation)
- **S1 / S2 (`Must Fix`)**: Direct factual contradictions, broken causality, premature epistemic leaks (character knows `作者真相` before reveal), or violated deadlines/statutes.
- **S3 (`Recommended Fix`)**: Pacing imbalance, weak scene payoff, missing `Goal -> Obstacle -> Action -> Cost -> New Expectation` loop, or unfulfilled foreshadowing.
- **S4 (`Optional`)**: Minor wording polish or optional detail alignment.

## Review Checklist
1. **Epistemic & Timeline Integrity**: Cross-check `prose` against `時間線/作者真相.md`, `時間線/讀者已知.md`, and `角色狀態/*.md`. Flag any character acting on unrevealed information.
2. **Plot Loop & Climax**: Verify tight chapters contain `Goal -> Obstacle -> Action -> Cost/Feedback -> New Expectation`.
3. **Narrative Focus**: Flag scenes where minor logistics are over-detailed while key confrontations are summarized.
4. **User-Facing Output Rule**: Present findings in plain domain language citing `Chapter N, "quote"`, never internal script names or raw `S1-S4` codes in the main body.
