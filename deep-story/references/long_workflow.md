# Long-Form Workflow (`deep-story`)

> Scope: Five-phase execution loop for multi-chapter serialized fiction using `storyctl.py`, `tracking_commit.py`, and `outline_view.py`.
> **Directory & Filename Invariant**: The Python engine enforces canonical project directory names: `设定/` (`设定/角色/`), `大纲/` (`大纲/卷纲_第X卷.md`, `大纲/细纲_第001章.md`), `正文/` (`正文/第001章_章名.md`), and `追踪/` (`追踪/_tracking-state.json`, `追踪/上下文.md`, `追踪/伏笔.md`, `追踪/角色状态/`, `追踪/时间线/作者真相.md`, `追踪/时间线/读者已知.md`). Always use these exact folder names.

## Phase 1–3: Planning (Stop After Delivery)

1. **Phase 1 (Premise & Preferences)**: Lock core selling point, genre rules, and book-level style preferences inside `tracking_commit.py` (`long_term_constraints`).
2. **Phase 2 (Settings)**: Create character cards (`设定/角色/{名}.md`), world rules (`设定/世界观/`), and domain anchors (statutes, deadlines, forensic hashes).
3. **Phase 3 (Outlines)**:
   - Book-wide & Volume outlines (`大纲/大纲.md`, `大纲/卷纲_第一卷.md`) per `references/07_web_novel_outline_template.md` (backward-planned from climax).
   - Chapter detailed outlines (`大纲/细纲_第001章.md`) per `references/08_novel_chapter_outline_template.md` with required metadata labels (`- 核心事件:`, `- 字数目标:`, `- 属于哪段剧情:`, `- 目标情绪:`, `- 主角目标/关键选择:`, `- 章首钩子:`, `- 爽点:`, `- 本章禁止提前释放:`) and subsections (`### 这章怎么走`, `### 情节安排`, `### 人物关系和出场顺序`, `### 情节细化` with numbered table).
   - Verify with `python3 scripts/check_outline_contract.py --project <dir> --chapter <N>`.
   - **Hard Stop**: Deliver requested outlines and wait for explicit user approval before entering Phase 4.

## Phase 4: Single-Chapter Drafting

1. **Pre-Read Gate**: Read `追踪/上下文.md`, active `追踪/角色状态/*.md`, `追踪/时间线/读者已知.md`, `大纲/细纲_第NNN章.md`, and the unit slice from `python3 scripts/outline_view.py --project <dir> --chapter <N>`.
2. **Draft Prose**: Write `正文/第NNN章_章名.md` honoring `禁/放` bounds and epistemic isolation (characters cannot act on `追踪/时间线/作者真相.md` facts absent from `追踪/时间线/读者已知.md` or their character state).
3. **Prose Gate**: Run `python3 scripts/storyctl.py chapter check --project <dir> --chapter <N> --fix-punctuation`.
   - Resolve all `blocking` findings (`check_ai_patterns.py`, `check_degeneration.py`, `normalize_punctuation.py`) and inspect `check_outline_copy.py` advisories per `references/12_`–`15_`.

## Phase 5: Delta Commit & Integrity

1. Prepare the chapter delta JSON payload and commit via `python3 scripts/storyctl.py chapter commit --project <dir> --chapter <N> --input <delta.json>`.
2. Verify `python3 scripts/tracking_commit.py check --project <dir>` passes with zero drift.
3. Cap at **3 chapters** per turn.
