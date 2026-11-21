# Style Precedence, Causal Logic & Narrative Focus (`deep-story`)

> Pipeline: **Gate 1 (Style & Whitelist)** -> **Gate 2 (6-Dimension Causal Audit)** -> **Gate 3 (Narrative Focus & 3-Test Filter)**. Execution scope is set by caller; review-only mode reports without editing.

---

## Gate 1: Style Precedence & `.deslop-whitelist`

**Precedence Formula**: `Current Request > Book Style (settings/style.md) > Workflow Preferences > Primary Benchmark Style > Genre & References Defaults`
- **Fact vs Expression Separation**: Style governs syntax, POV, punctuation, dialogue formatting, direct emotion, and rhetoric—it **cannot** alter outline beats, established facts, disclosure bounds, word-count ranges, or tracking rules.
- **Book Style Loading**: Read `settings/style.md` (or `settings.md` for short stories). Even one actionable rule counts; blank files or placeholders do not. Pass active `style_resolution` verbatim to polishing/review steps.
- **`.deslop-whitelist` Rules**: UTF-8, one literal snippet per line under `<project>/.deslop-whitelist` (no regex/wildcards, no parent lookup). Precede each entry with `# 來源：…；用途：…`. Default-retained: `……` in dialogue/panels, `——` in dialogue, restrained `……` in narration. Never whitelist broad words (`不是`, `沒有`) to disable a category; factual, word-count, placeholder, engineering-term, truncation, and structure checks are **never** exempted.

---

## Gate 2: Causal Story Logic (`6-Dimension Audit`)

Inspect along actual events without forcing every scene into an opponent/reversal formula (everyday and atmospheric scenes are valid).

| Inspection Target | Audit Question | Failure Signal |
| :--- | :--- | :--- |
| **1. Basis for action** | Given what they knew then, why choose this step? | Sudden trust, rebellion, or personality flip for plot convenience |
| **2. Causal linkage** | Which prior condition triggers this result? | "Then" stringing events without enabling conditions |
| **3. Others' stances** | What is the other party protecting or constrained by? | Bystanders exist only to gasp, hand over clues, or fold |
| **4. Method & outcome** | Are solution, mistake, and gain supported by prior text? | Out-of-nowhere evidence/ability; one request bypassing resistance |
| **5. Change & carry-over** | What shifted, and does subsequent text pick it up? | Scenes reset to zero; same trick works repeatedly without effect |
| **6. Info & chronology** | Who knows what, when, and from what source? | Acting on unrevealed `author_truth.md`; spoiling future causality |

### Triage & Authorization Boundary
- **Missing Link Triage**: *(a)* Basis exists in prior text -> reconnect within POV bounds; *(b)* Insufficient context provided -> mark unknown, do not invent backstory; *(c)* Design lacks conditions -> propose minimal option + downstream impact (never patch with *"he was finally moved"*).
- **Evidence Process Anchor**: `❌` *"Apprentice pulled out a copied ledger, everyone believed him."* -> `✅` Prior setup shows three clerks sealed separate master copies; unsealing and matching bottom-line figures face-to-face proves innocence without inventing secret witnesses or audio recordings.

| Ordinary De-Slopping (Execute Directly) | Requires Plot-Design Authorization (Pause & Propose) |
| :--- | :--- |
| Fix verifiable reference, subject, or chronology slips | Pick between multiple valid motives on author's behalf |
| Reconnect existing causality, conditions, and info sources | Add new promises, evidence, identities, abilities, or events |
| Adjust detail density of established clashes/weighing | Change character decisions, win/loss outcomes, costs, or sequence |
| Present known info within established POV/reveal bounds | Reveal twists early, shift foreshadowing, or invent `進門時發現` to keep info |

---

## Gate 3: Narrative Focus (`3-Test Filter & Element Rules`)

**Center-of-Gravity Formula**: State in one sentence what the scene must let the reader experience; allocate word count to that turning point, not uniform precision.

| Focus Problem | Signal | Fix Formula |
| :--- | :--- | :--- |
| **Secondary processes bloat** | Door-opening, tea-pouring, walking expanded uniformly | Compress to transitions unless establishing space/voice/stakes |
| **Key process swallowed** | *"Worked out an agreement"* replaces negotiation | Expand existing probing, weighing, and concession |
| **Equal effort on peers** | 3–4 people/items get identical word count | Expand the pivotal one; summarize or skip the rest |
| **State spinning** | Fear/anger/silence repeated without changing next step | Merge repetitions; keep only steps altering judgment/action |
| **Abrupt shift** | Refuses in sentence 1, agrees in sentence 2 | Restore missing transition or flag design gap |

### Three Deterministic Edit Tests
1. **Deletion Test**: Cut it if removing it loses zero fact, foreshadowing, causality, space, voice, relationship, emotion duration, or aesthetic texture.
2. **Compression Test**: Do **not** compress if a one-line summary strips away *how* the character arrived at the choice/emotion.
3. **Expansion Test**: Only expand a turn if it changes info, circumstance, judgment, relationship, or feeling. (Keep staged micro-progressions—e.g., testing stepping stones -> second stone sinks -> retreating -> switching to fallen tree—while deleting indiscriminate single-footstep lists.)

### Element Discipline & Endings
- **Action**: Keep actions bringing obstacles, failure, choices, or habits; drop mechanical pick-up/put-down chains.
- **Interiority**: Keep new judgments, misjudgments, and weighing; do not convert all thoughts into physical tics.
- **Dialogue**: Keep lines shifting leverage/info; let narration summarize routine recaps. Never raise tension by forcing profanity.
- **Environment & Groups**: Anchor observation to character's current attention; separate group reactions only when stances differ.
- **Endings**: Stop on an unfinished action, shift, payoff, question, or aftertaste; cut redundant recaps, vague philosophizing, and targetless teasers.
