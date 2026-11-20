# Style and Reference Conflict Resolution

Before drafting body text, rewriting, de-slopping, or reviewing, first establish the style requirements in effect for this run. The main session and all subagents share this resolution.

## Precedence for Syntax, Pacing, and Diction

For expression choices, take the first explicit, applicable requirement in the following order of precedence: **Current Request > Book Style/Settings > Applicable Preferences Passed by the Writing Workflow > Primary Benchmark Style > Genre Pack & General `references` Defaults**. Among passed preferences, book-level requirements take precedence over genre, workflow, and global requirements; only undeclared items fall back down the chain. Sentence length, POV, punctuation, dialogue formatting/placement, direct emotional statement, rhetoric/figurative language, narrator commentary, and chapter/scene endings are all decided in this order; default rules and examples in `references` never override explicit authorial choices.

Resolve facts and expression separately: style cannot alter outline beat events, established facts, information-disclosure boundaries, user word-count ranges, rewrite scope, file structure, or tracking protocols. Limited omniscient POV permits switching viewpoints, which does not mean revealing secrets early. When shifting into limited POV, you may temporarily withhold information that the viewpoint character has no way of knowing; do not invent “早已知道” (*had long known*), “後來發現” (*later discovered*), or new observational experiences just to preserve information from the original draft. Reviews still evaluate causality, readability, and emotional effect as usual.

## Loading and Passing Context

1. Determine the book directory from the current body-text path (for novels, the parent directory of `正文/`; for short stories, the directory containing `正文.md`). Read the book's `設定/文風.md`; for short stories, also read the style conventions in `設定.md`. If no file exists, proceed without creating placeholder files or guessing from other books. Even a single actionable preference counts as valid; blank files, bare headings, or "to be added" placeholders do not.
2. `_文風摘要.md` serves only to assist navigation and does not replace the full text; if the summary conflicts with the full text, use the full text.
3. Reuse the applicable preferences and style resolution passed by the caller, resolving each writing choice from narrowest to broadest scope; ask the author only when an unclear conflict occurs within the same scope. When invoked standalone with no passed results, proceed according to the current request and the book's style.
4. Fill `style_resolution` in the existing prompt (listing the active expression requirements and their sources, overridden default clauses, and facts/information boundaries that must be preserved; if there are no conflicts, you may write “按本書文風” / *per book style*), pass it verbatim to the drafting, de-slopping, and prose reviewers, and also pass the full file path of the style document.

## How the Detector Obeys the Resolution

The detector does not understand authorial intent. For hits that are explicitly adopted and serve a function, reuse `.deslop-whitelist` under the **book directory**: UTF-8, one literal original-text snippet per line; blank lines and comment lines starting with `#` are ignored; regex and wildcards are not supported; and parent directories are not searched.

- `……` inside dialogue and system/UI panels, `——` inside dialogue, and restrained `……` in narration are retained by default; when the book's style additionally permits em-dashes in narration, `——` may be registered. For specific rhetorical devices, register the full original sentence permitted to remain—never register broad words like “不是” (*not*) or “沒有” (*no/without*) to disable an entire check category.
- On the line above each entry, explain the basis in the current request or book style using `# 來源：…；用途：…` (*# Source: ...; Purpose: ...*). Register entries only to enforce choices the author has explicitly made, never to auto-pass script alerts; remove conflicting exemptions whenever the current request forbids a given technique.
- Deep scans, punctuation cleanup, and post-write/next-chapter checks all read the same whitelist. An exemption affects only the style check for that matching literal snippet; other issues on the same line are still reported, and checks for facts, word count, placeholders, engineering terms, truncation, and file structure are never exempted.

---

# Story Validity and Change: Diagnosing Causality, Repairing by Authorization

This file examines the relationships among events, actions, information, and outcomes. For sentence- and paragraph-level expression, see [expression.md](deslop_expression.md); for the level of detail of existing content, see [narrative-focus.md](deslop_logic_and_focus.md). Execution scope is determined by the caller; review-only mode only reports.

## Inspect Along the Events, Without Forcing a Conflict Formula

First confirm from the original text and existing design the characters' circumstances, known information, this scene's function, and the outcome, then press further on how the outcome occurs. Characters may be passive, impulsive, mistaken, or yielding/forbearing; everyday, unhurried, and atmospheric scenes also have value. Do not require every scene to have an opponent, a reversal, a cost, or a win/loss.

| Inspection Target | Actionable Questions | Gaps to Pinpoint |
|---|---|---|
| Basis for action | Given what they knew at that moment, why would they choose this step? Do fear, habit, or misjudgment have textual support? | Suddenly trusting, rebelling, or forgiving solely because the author needs it; a character temporarily changing personality for the sake of the outcome |
| Causal linkage | Which condition in the antecedent triggers the consequent? Were the intermediate conditions already written, or do they not exist at all? | "Then" (“然後”) stringing together a chain of events; explanatory sentences claiming success without a process that makes it hold up |
| Others' stances | What is the other party trying to protect, and what constraints do they have? Why do they accept or change their strategy? | Everyone else is only responsible for helping, delivering clues, being astonished, or admitting fault, with no reasons of their own |
| Method and outcome | Are the solution, mistake, and gain supported by prior text? Is the weight of the outcome commensurate with the preparation? | Evidence or ability appearing out of nowhere to solve the problem; a single request bypassing already-established resistance |
| Change and carry-over | After the experience, what changes in relationships, understanding, resources, expectations, emotions, or room for action? Does the subsequent text pick it up? | Consecutive scenes resetting to the original state; the same method working repeatedly; events that already happened having no effect |
| Information and chronology | Who knows what, when, and from what source? When does the reader learn it? | Characters knowing answers ahead of time, treating recollection as on-scene presence, or spoiling causality not yet revealed |

Record items one by one only when there is a problem; normal items can be skipped—do not backtrack to add scenes just to fill out the checklist. Judging something as "too flat" (“過平”) requires pointing out repetition or absence in the original text: for example, repeated requests for help being rejected without ever adjusting the method, or a designed shift in relationship failing to affect later behavior. A single instance of caregiving without conflict cannot be judged flat on that basis.

## Is What's Missing the Writing Technique, or the Enabling Conditions?

When encountering an abrupt shift, first search the preceding text, worldbuilding/settings, and outline provided in this session. There are three possible conclusions:

- **The basis already exists, but the main text failed to connect it**: Restore the linkage within the established information boundaries, avoiding repetitive explanation. If an established promise only appeared in earlier text, the character can be allowed to use it in the current negotiation.
- **Insufficient material; cannot judge for now**: Specify clearly which item is unknown and continue evidence-backed revision; do not judge the entire book as lacking setup just because the full book was not provided, and do not invent prior events on the author's behalf.
- **The current design truly lacks conditions**: Explain which choice or outcome in the original text lacks what support, and give a minimal design option along with its impact. Adding explanations like "he was finally moved" (“他終於被打動”) cannot supply the other party's stance.

Distinguish information gaps from suspense: wet footprints left outside the door while it is not yet known who came form a clear, specific question; you should not guess the answer for the author. Only when the reader cannot even understand why the character is guarding this door or what they are trying to do right now should you check back and supply the already-existing necessary background.

## Determine Diagnostic Depth and Execution Authority Separately

| Can Be Applied in Ordinary De-slopping | Changes Requiring Plot-Design Authorization |
|---|---|
| Fixing verifiable slips in reference, subject, or chronology | Multiple interpretations are all valid, requiring choosing the true motive on the author's behalf |
| Restoring linkage of existing causality, conditions, and information sources | Adding new promises, evidence, character identities, abilities, events, or information sources |
| Expanding established confrontations, weighing of options, and feedback; adjusting level of detail within the same scene | Changing a character's decision, win/loss outcome, relationship trajectory, cost, or event sequence |
| Presenting known information within established revelation boundaries | Revealing the twist/truth early, moving foreshadowing, or changing the order in which reader and characters learn information |

Dialogue wording and necessary micro-links can serve established content; you cannot use a line of dialogue or an incidental action to add a threat, a promise, newly acquired evidence, or a change in character strategy. When switching POV, narrate only the perceptions and cognition supported by that POV—do not add new experiences such as "discovered upon entering the door" (“進門時發現”) or "heard later" (“後來聽說”) just to preserve information.

When the author has explicitly requested a rewrite or permitted plot adjustments, directly execute the authorized part while preserving all other established facts; do not ask for the same authorization again. When key grounds for a choice are still missing, propose minimal reviewable options. A proposed fix must specify which action, which condition, or which outcome it applies to, and explain which subsequent passages it will affect—do not just say "strengthen the conflict" (“加強衝突”). Put suggestions and speculation in the report; do not quietly turn them into main-text facts.

## Grouped Example: Outcomes Need a Process That Holds Up

The following is a synthetic example.

**Original text**: The shopkeeper accused the apprentice of altering the account book. The apprentice pulled out a copied ledger, everyone immediately believed him, and the shopkeeper admitted fault in public.
*(Original: 掌柜指認學徒改了帳。學徒拿出一張抄本，眾人立刻相信他，掌柜當眾認錯。)*

**Pinpointable diagnosis**: Who kept the copied ledger, why it was trustworthy, and on what basis everyone had the ability and standing to verify it are all left unexplained. Simply pulling out a sheet of paper cannot prove what is written on the paper is true, and adding a few more sentences about bystanders being astonished cannot paper it over either.

**Ordinary de-slopping**: Clean out hollow modifiers and keep the established exoneration outcome; check earlier text for ledger-auditing conventions, independent master copies, or witness conditions. When current material lacks these, list the unfixed gap in the report and propose a minimal option plus the conditions that would need to be added, without treating the option as something that already happened.

**With prior setup and author-authorized dramatization**: Previously, three clerks had each sealed their own master copies, and the shopkeeper allowed everyone to audit the accounts face-to-face.

> The apprentice placed his master copy on the counter and asked the other two to unseal those two sheets. The bottom line on all three copies showed the same figure, which did not match the new ledger in the shopkeeper's hands.
>
> Holding those sheets of paper, the shopkeeper admitted that this entry had not been altered by the apprentice.
>
> *(Original: 學徒把自己的底稿放在柜上，請另兩人拆開封存的那兩頁。三份末行都是同一個數，和掌柜手中的新帳對不上。 / 掌柜拿著那几頁紙，承認這一筆不是學徒改的。)*

The weight of the evidence comes from the separately sealed master copies and face-to-face verification, without temporarily adding a secret witness. When the prior setup is already sufficient, write the verification directly—there is no need to manufacture another failure just to "add twists and turns" (“增加波折”).

**Directions that would break it**: Suddenly adding an audio recording, a powerful relative, or a secret deal—making the outcome livelier while altering the story's basis; or changing the exoneration into a failure without authorization in order to "raise the cost" (“增加代价”) and decide consequences on the author's behalf.

## Post-Revision Read-Back

Put the revised passage back into the event chain before and after it, and verify the characters' order of knowing, basis for choice, outcome, and transition into the next scene. In the report, distinguish between gaps already fixed, parts still requiring design, and parts left inconclusive due to insufficient material. Smooth expression does not mean the story gap has disappeared.

---

# Narrative Focus: Putting Word Count Where It Is Worth Experiencing

This file examines the level of detail across scenes and paragraph groups. For expression-level fixes, see [expression.md](deslop_expression.md); when events or character choices need to change, see [story-logic.md](deslop_logic_and_focus.md). Trade-offs and editorial decisions follow the stylistic rulings in [style-resolution.md](deslop_logic_and_focus.md).

## Finding the Center of Gravity from Scene Function

Read through a continuous scene and state in one sentence what it is meant to let the reader experience: a choice, a shift in negotiation, a cooling relationship, discovering a misunderstanding, or else a life circumstance, ease/relaxation, atmosphere, or lingering resonance. Use this only as the basis for the current judgment; do not force the generation of paragraph-by-paragraph labels or new attachments.

Follow the main text to find what most needs to be experienced: when a character changes judgment, which line turns the negotiation, how hesitation arrives at a decision, or how a certain everyday detail pulls a relationship closer or apart. Compare against actual length/word count and point out specific over-elaboration or under-writing. When a scene's center of gravity is not developed, first check whether the original text, surrounding context, or established design already contains the process; you cannot substitute a batch of sensory details in its place.

| Problem | What to Look At | How to Handle It |
|---|---|---|
| Secondary processes occupy space | Opening doors, pouring water, hurrying on a journey, taking inventory item by item are continuously expanded, yet do not change the character's circumstance or the reader's feeling | Compress into necessary transitions, keeping details that establish space, voice/register, relationship, or atmosphere |
| Key processes are swallowed by summary | "They worked out an agreement" (“商量妥了”), "explained clearly in a few words" (“三言兩語解釋清楚”), or "she finally thought it through" (“她終於想通了”) replace choices or confrontations | Expand existing conditions, probing/testing, judgment, and feedback; when supporting basis is missing, switch to story diagnosis rather than fabricating reasons that persuade |
| Equal effort on similar objects | Three people or four objects are each given the same amount of space, so the reader cannot find the center of gravity | Allocate around this scene's function; expand the important object(s), summarize or skip the others, without prescribing a fixed decreasing count |
| State spinning in place | Repeatedly writing fear, anger, or silence while the character's understanding and actions remain the same throughout | Merge repetitions; retain processes that change the next step or accumulate experience |
| Result shown without transition | Refusing in the previous sentence and agreeing in the next; emotions arriving abruptly | Recover existing transitions; if the enabling conditions were never designed, propose a story fix |

"Flatness" (“平”) may come from the center of gravity being written too thinly, or from the story lacking sufficient change. Determine which one it is first, to avoid compressing all slow scenes shorter.

## Separate Tests for Deletion, Compression, and Expansion

**Deletion test**: After deleting it, is there any loss of fact, foreshadowing, causality, spatial orientation, character voice, relationship, emotional duration, or aesthetic experience? If there is no loss, it can be deleted, including an entire paragraph; if there is a loss, retain the effective part or compress the expression. There is no need to invent a subsequent plot purpose for every detail.

**Compression test**: After replacing it with a one-sentence summary, does the reader only know the result without being able to experience how the character got there? If necessary hesitation, confrontation, or emotional arrival is lost, keep the expansion. That facts are not lost is only one check; you cannot flatten out the texture of life on that basis.

**Expansion test**: Does each newly added round/turn cause information, circumstance, judgment, relationship, or feeling to change? The same emotion can persist, and pauses also have a sense of time; reaction chains that only swap wording to emphasize intensity should be pulled back together. Staged changes already present in the original text can be played out in stages; do not judge them as repetitive merely because action, perception, and reaction appear adjacent to one another.

After rearranging, read through the entire scene: can the reader still clearly see who is where, why they stopped, and why the next step happens? When over-deletion produces telegraphic prose, restore necessary subjects, links, and transitions—do not restore formulaic explanations. Respect the word-count range given by the author; when valid content cannot reach the lower bound, report the gap honestly rather than padding with micro-actions or new events. Edit/deletion ratios are only used to record how much was changed; do not leave filler behind just to hit a ratio.

## Details Must Serve This Scene

- **Action**: Keep actions that bring obstacles, failure, choices, relationships, or character habits. There is no need to record reaching out, picking up, putting down, and turning around one by one; if fighting, chasing, or operational steps carry real spatial and causal information, they can be written in detail.
- **Psychology / Interiority**: Keep new judgments, misjudgments, memories, weighing of options, and self-deception. Accurate direct writing can carry transitions; compress repeated translations of what just happened or summaries of the same emotion. Do not convert all inner activity into physical reactions across the board.
- **Dialogue**: Look at what each side is trying to win, what they are unwilling to say, and which response changes the situation. Expand the key moments and let narration carry the rest; do not turn every "he said / she said" (“他說/她說”) in the original text into a separate line of dialogue. Dialogue, narration, and interiority jointly carry this scene—do not replace a scene with neat Q&A exchanges. Do not require every line to talk past the other person, and do not raise intensity by adding profanity.
- **Environment and objects**: Observation should stick to the character's attention at this moment. It can establish the texture of life, sense of time, aesthetics, and relationships; do not require every object to become a clue. Item-by-item display at uniform precision, generic weather, and non-functional decoration should be compressed.
- **Group reactions**: When characters change their actions because of different stances, they are worth separating; having everyone take turns trembling, stepping back, and acting startled is merely repetitive reinforcement. Judgment and weight can be delivered by the person who holds a stance—do not force lines onto everyone.

## Information Delivery and Endings

When a new character, new object, or new worldbuilding/rule element appears, let the reader know the identity, function, or constraint needed for the current action. Both existing in-scene carriers and concise narration may be used; do not force changes into phones, bills/receipts, or administrative bottlenecks. Necessary explanations can be stated directly; when the reader temporarily does not know the answer, they should at least know which question they are waiting on.

Distinguish between what characters know, what the reader knows, and what remains to be revealed. Do not fill in answers for deliberately left suspense, and do not strip necessary transitions down into a vocabulary list. For verification of factual basis and timing of revelation, see [story-logic.md](deslop_logic_and_focus.md).

At the ending, check what the final beat brings: an unfinished action, a shift in relationship, a fulfillment/payoff, an unresolved question, or emotional lingering resonance can all work. Action, dialogue, interiority, and stance-bearing narration can all close a scene; clean out repeated restatements, vague philosophizing, and previews/teasers without a concrete target. For short-form fiction's subjective judgments, "heart-dead" verdicts, and "crematorium" groveling-arc teasers, keep or cut according to the book's selling points—keeping them does not mean letting repetition slide.

## How to Vary Narrative Brushwork for the Same Facts

The following is a synthetic example. Established facts: Yu Zhou has to deliver a letter across a stream; he tests the stepping stones first, retreats after the second stone loosens, switches to crossing via a fallen tree upstream, hangs the letter pouch around his neck, and finally reaches the opposite bank.

**Imbalanced brushwork**: By the stream stood three trees, two with gray-white bark and one covered in moss. Scattered beneath the trees were pebbles, rounder near the bank and flatter farther out. Yu Zhou thought of several methods, spent quite some effort, and finally carried the letter across the stream.
*(Original: 溪邊有三棵樹，兩棵樹皮灰白，一棵長了苔。樹下散著石子，近處圓一些，遠處扁一些。余舟想了几個辦法，費了一番工夫，終於把信帶過溪。)*

**Restored center of gravity**:

> Yu Zhou stepped onto the second stepping stone; the stone sank downward, and he hurried back to the bank.
>
> Upstream, a fallen tree lay across the water. He walked along the stream toward it, hung the letter pouch around his neck, freed his hands to steady himself along the trunk, and edged bit by bit to the opposite bank.
>
> *(Original: 余舟踏上第二塊石墩，石頭往下一沉，他趕緊退回岸邊。 / 上游橫著一棵倒樹。他沿溪走過去，把信袋掛到頸前，空出手扶著樹干，一點點挪到了對岸。)*

Here, only the already-established testing and switching of methods are written out, without adding new rescuers, tools, or accidents. If the source material only says "spent quite some effort" (“費了一番工夫”) and does not even have the attempt or the method, you cannot invent stepping stones and a fallen tree following this example.

**Directions that would break it**: Writing only "he crossed the stream via the fallen tree" (“他從倒樹過了溪”) compresses away both the testing and the switch of method; listing lifting a foot, setting a foot down, and switching hands one by one—indiscriminate actions—will instead steal attention away.

**Slowness worth keeping**: An old man puts away his late wife's tea set, first setting the pieces down in the positions she used to keep them, then picking them up again to wrap in paper. Lingering for this extra moment lets the reader experience habit and loss. Mechanical phrasing can be fixed, but this cannot be deleted merely on the grounds of "little plot advancement" (“事件推進少”).
