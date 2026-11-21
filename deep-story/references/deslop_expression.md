# Expression: Language & De-Slop Execution (`deep-story`)

> Pipeline: **Step 1 (Fix Telegraphic Chop)** -> **Step 2 (Evaluate Contextual Risk Patterns)** -> **Step 3 (Voice & Emotion Channels)** -> **Step 4 (POV Bounds & Detector Flags)**. Resolve conflicts per Gate 1 of [deslop_logic_and_focus.md](deslop_logic_and_focus.md).

---

## Step 1: Fix Telegraphic Style & Choppy Sentences

**Repair Formula**: `[Embed conditions/reasons into central action clause] -> [Break only after complete thought]`
- Telegraphic prose also hides inside long comma-strung clauses where location, cause, and action are broadcast one by one.
- **Anchor**: `❌` *"貨車在南門，她在北門，地址發錯。司機打電話問能不能開到北門。北門修路開不過來，她讓他等，抱箱跑向南門。"* -> `✅` *"司機照著她發錯的地址開到了南門，打電話過來時，她還在北門。北門這邊正在修路，貨車沒法過來，她只好讓司機留在南門，自己抱起紙箱跑過去。"*
- **Keep**: Single-sentence paragraphs carrying a complete thought, punchlines/reveals, short dialogue, and deliberate white space. Merge only 3–5 char fragmented remnants. Never pad function words or gestures just to hit sentence-length quotas.

---

## Step 2: Contextual Risk Patterns & Modifier Retention

Circle the sentence, identify what it repeats or obscures, then delete, compress, or rewrite—never rotate synonyms mechanically.

| Risk Pattern | Judgment & Handling Formula |
| :--- | :--- |
| **Negative -> Positive** (`不是 A，而是 B`) | Cut if negating a strawman nobody cares about; **keep** if correcting a misconception, defending, ruling out guesses, or marking a judgment shift. |
| **Neat Parallelism** | Merge if repeating the same conclusion; **keep** if carrying escalation, voice, or clear contrast. |
| **All-Purpose Adverbials / Voice Tags** | Cut generic tags (`帶著一絲…`, `聲音不大卻不容置疑`); keep recognizable tone. Neutral `說` needs no action replacement. |
| **Scare-Quote Emphasis** | Remove quotes on ordinary nouns (`"機會"`, `"蛻變"`); keep for quotes, codenames, UI notices, term definitions, and irony. |
| **Template Metaphors / Grandiosity** | Compress inflated clichés (`潮水般湧來`, `命運的齒輪`) into concrete description; keep fresh character-specific sensations. |
| **Bureaucratese** | Revise affected phrasing (`基於當前情況推進後續事項`) to character register; keep genuine statutory/system registers intact. |

- **Preserve Functional Modifiers**: Words like `才`, `很`, `連`, `彷彿`, `似乎`, `原來` and distinguishing attributes (`白色藥片`, `那截鏈子`) often carry timing, degree, or POV uncertainty—never strip them blindly.

---

## Step 3: Voice & Emotion Channels

- **Voice Calibration**: Check every line against **Addressee + Setting + Immediate Intent**. Restore distinct voices via status, jargon, and stance—never by sprinkling slang, profanity, or catchphrases onto everyone. Never alter communicative intent (e.g., turning an explanation into a provocation).
- **Direct Emotion & Anti-Action-Padding Test**:
  - Accurate direct statements (`他很緊張`, `她感到/意識到`) are valid when setting up the next step; delete only if surrounding context already conveys it with zero new function.
  - **Physical Reaction Deletion Test**: Delete stock tics (`指尖輕叩`, `指節泛白`, `目光移開`, `摩挲杯沿`) that alter no feeling, characterization, action condition, or physical result. Replace with direct emotion, mental calculation (`算帳`), or dialogue—never invent cup-smashing, door-locking, or audio-recording. Keep consequential details (injury hindering grip, spotted habit).

---

## Step 4: POV Bounds, Fact Preservation & Detector Flags

- **POV & Carriers**: Never leak facts outside the active POV (`author_truth.md` hidden bounds). Keep explanations supplying causal linkage or term function; cut redundant summaries (`這意味著`, `真正重要的是`). Preserve existing in-scene carriers (letters, bills, logs) without inventing forms.

| Original Sentence | Acceptable De-Slop | Broken Rewrite (Forbidden) |
| :--- | :--- | :--- |
| `她不是不肯還鑰匙，而是忘在家裡了。“我明天帶來。”` | `她把鑰匙忘在家裡了。“我明天帶來。”` *(keep contrast if replying to accusation)* | `“愛等就等。”她說。` *(alters commitment)* |
| `她推門。屋裡沒開燈。她摸到桌邊。把藥盒拿起來。` | `進屋後，她摸黑走到桌邊，拿起藥盒。` | `她摸黑吞了兩片藥。` *(invents action & quantity)* |

### Detector Flag Index (`blocking` in bold)
- **`not-is-comparison`**, **`reverse-not-is`**, **`negation-parade`**, `negation-pair-tic` -> Step 2 (Negative -> Positive)
- **`voice-contrast`** -> Step 2 (All-Purpose Adverbials)
- **`em-dash`**, `ellipsis-density-tic` -> Replace narrator em-dashes with commas/colons/sentences; compress flooding ellipses
- **`trailer-ending`**, **`trailer-summary`** -> Step 4 (Cut empty teasers/recaps; route weight to `deslop_logic_and_focus.md`)
- `formulaic-parallelism`, `quote-emphasis-tic`, `cliche-density-tic`, `metaphor-density-tic` -> Step 2
- `stock-reaction-tic`, `micro-action-tic`, `action-list-tic` -> Step 3 (Anti-Action-Padding)
- `period-stutter`, `overcompressed-prose-tic`, `low-connective-density-tic`, `long-paragraph` -> Step 1 (Break `long-paragraph` at shot boundaries)
- `abstract-summary-tic`, `reasoning-chain-tic`, `system-notice-formality-tic` -> Step 4 (Route causal gaps to `deslop_logic_and_focus.md`)

> *Note*: Author-chosen `blocking` lines must be whitelisted in `.deslop-whitelist` (or chapter exempted via `<!-- 去味:跳過 -->`); zero detector hits do not guarantee strong craft.
