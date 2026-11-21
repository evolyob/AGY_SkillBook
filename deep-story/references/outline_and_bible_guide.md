# Story Bible & Outline Craft Guide

> Use `templates/` for daily drafting; consult this guide when diagnosing structural or pacing issues.

---

# How to Organize a Novel Story Bible: Templates for Characters, Timelines, and Character Knowledge

A long-form novel's story bible must separate stable facts from states that change with the plot. Character cards store identity, bottom lines, and long-term goals; current state only records the latest status of location, resources, relationships, known information, and unresolved matters; the timeline records events in objective chronological order, while what characters know and what the reader knows are tracked separately. When the plot changes, you only update the corresponding entry, preventing multiple files from contradicting each other.

## A Sufficient Story Bible Setup

| Module | What It Stores | When to Update |
|---|---|---|
| Character Card | Identity, background, ability boundaries, long-term goals | When a setting detail is formally changed |
| Current State | Location, resources, relationships, known info, unresolved matters | Whenever a valid change occurs |
| Relationship Table | Mutual promises, debts, public and private stances | When an action affecting the relationship lands |
| Author Timeline | Objective order and dates of events | When new facts are confirmed |
| Reader Knowledge | Content already revealed in the main text | When a chapter is finished |
| World Rules | Applicable conditions, exceptions, costs | When rules are established or revised |

Each fact is canonized in only one place; other files either reference it or only record the latest outcome.

## Character State Schema & Lifecycle Rules

> **Authoritative Blank Schema (SSOT)**: Use [templates/character_card.md](../templates/character_card.md) for character cards/states and [templates/world_rule.md](../templates/world_rule.md) for world rules.

Only create state pages for characters who will appear again later; leave one-off passersby in chapter records so the story bible doesn't bloat over time. When revising old chapters, recalculate affected states forward starting from the modified chapter.

## Original Filled Example: Old Water Station Manager

```md
As of Chapter: Chapter 12
Current Location & Activity: Old water station duty room, preparing to close the North Line valve
Current Goal: Prove the contamination comes from the return pipe before the maintenance team arrives
Abilities & Available Resources: Duty key, pressure gauge logs from the past three days; no sampling authority
Key Relationships: Owes the residents' representative a public explanation; verbal confidentiality agreement with the station chief has broken down
Known / Misbelieved / Concealed by Character: Knows North Line nighttime pressure is abnormal; misbelieves the maintenance team has received the complete records
Unresolved Matters: Who deleted the early-morning data; why the key was duplicated by someone
Source of This Change: Chapter 12, duty room scene
```

This card omits childhood and appearance, keeping only the facts that will constrain the protagonist's actions in the next chapter.

## Update One Change Without Wiping Other Facts

Continuing the example above. In Chapter 13's main text, the residents' representative reaches out for the key in the duty room. The protagonist hands it over, keeps the pressure gauge logs in front of themselves, and says the public explanation is still owed while they continue checking the records. This handoff only changed who holds the key:

| State | Chapter 12 | Chapter 13 |
|---|---|---|
| Key | Held by protagonist | Handed to residents' representative, noting the handoff scene in the main text |
| Location & Authority | At the water station, no sampling authority | Still at the water station, authority unchanged |
| Relationships & Unresolved Matters | Confidentiality agreement broken; duplicated key issue unresolved | Both retained; handing over the key does not automatically bring reconciliation |
| Known & Misbelieved | Still misbelieves the maintenance team has complete records | Not corrected in this chapter; retained as is |

When updating, only change the key row and carry all other items over to Chapter 13 as is. Similarly, the residents' representative getting the key does not mean all residents know the full investigation; only record the handoff that actually happened, who was present, and what was actually said. Events planned for later in the outline are stored separately in the outline and not written into the state.

## How to Prioritize When Conflicts Are Found

First locate the explicit facts in the main text, then cross-check rule conditions, chronological order, causality, and costs. Fix direct contradictions or conflicts that damage the main plot first; hidden causal breaks second; note minor appearance discrepancies separately; and treat overdue foreshadowing merely as reminders. For each issue, clearly state the premise, triggering event, and point of contradiction; the story bible only lays out the before-and-after facts clearly, while the author makes the final call on where the plot goes.

---

# How to Write a Web Novel Outline: Long-Form Novel Outline Template & Volume Examples

Do not write a web novel outline straight through from Chapter 1 onward. First define in one sentence what the protagonist must accomplish, then decide the ending and each volume's climax, and work backward to determine the situation that must change in every volume; only at the end should you arrange adjustable scenes. The book's overall direction should stay stable, volume-level paths can be revised, and specific dialogue and small scenes should be left until writing time.

## Which Layer of a Long-Form Outline Should You Write First?

An outline is meant to anchor the direction of a long-form work, not to pre-write the main text. It is generally divided into three layers—whatever names you use are up to your habit:

| Layer | Purpose & Scope of Adjustment |
|---|---|
| Book-Wide Spine | What the protagonist must ultimately accomplish and why it has to be them; sets the overarching direction. When changing it midway, first check against already written chapters and reader expectations. |
| Volume Route | How far this volume pushes the situation and how the volume-end climax plays out; specific paths can be adjusted, but do not overturn previously established causes. |
| Scene Memos | Which scene, clue, or dialogue you plan to use to cross a beat; revise as you write. Ideas not yet written into the main text do not count as established facts. |

This has a different division of labor from the [Detailed Chapter Outline Template](../templates/chapter_outline.md): the book-wide outline governs the big direction, while the detailed outline governs how to write the next few chapters. This article recommends deciding the climax first and working backward, though you can also start by exploring characters or trial-writing the opening and then converge on the endpoint once the flow feels right; do not force yourself to invent unused secrets, abilities, or subplots just to fill out a form.

## Long-Form Novel Outline Schema & Planning Order

> **Authoritative Blank Schema (SSOT)**: Use [templates/book_outline.md](../templates/book_outline.md) for book-wide spines and volume/unit cards.

Write the endgame choice and each volume's climax first, then work backward to the characters, abilities, relationships, and evidence that need to be established in advance. Never conjure endgame authority or resources out of thin air; each volume's outcome must trigger the next volume's trouble, and only detail the current writing window rather than pre-filling later volumes' dialogue and minor scenes.

## From Blank Page to Writable: Working Backward from the Ending for Key Plot Points

First set the protagonist's starting point and endpoint to widen the before-and-after contrast; then think through what trade-off they must make in the book's biggest conflict, rather than writing a vague "ultimate showdown." Next, work backward: what gives them the leverage to make that decision? The skills, connections, and hard evidence they currently lack get broken down into milestones to capture in earlier volumes.

Plan each volume the same way: set the volume-end climax first, then give the start of the volume a reachable stage goal, and place hard obstacles in the middle that force the protagonist to change tactics. Keep a subplot only if it helps the main plot, adds cost to the protagonist, or merges back into the main plot at the end. If you drift off course mid-writing, first check whether the current action still advances the volume's goal, instead of reflexively scrapping and rewriting the entire volume.

## Common Long-Form Outline Failures & Fixes

| Problem | Diagnosis & Fix |
|---|---|
| Treating "leveling up / getting stronger" as the main plot | Why it stalls: Getting stronger is only a means, with no visible endpoint; Fix: Clearly write "which specific task must be accomplished after getting stronger." |
| Pushing forward from the opening wherever the pen leads | Why it stalls: Reaching a late-stage climax only to realize setup is missing; Fix: Decide the climax choice first, then work backward for prerequisites. |
| Every volume just swaps maps and starts over | Why it stalls: After one round, everything resets to zero with no accumulation; Fix: Make the outcome of the previous volume trigger the new trouble of the next volume. |
| Many subplots that never touch each other | Why it stalls: Word count grows while the main plot stands still; Fix: Specify whether each subplot ultimately helps, blocks, or rewrites the main plot. |
| Writing the outline like full-text scenes | Why it stalls: Great ideas pop up while drafting the main text, but there's no room to fit them in; Fix: Lock down the big direction and leave maneuvering room for specific scenes. |

To judge whether an outline is sufficient, simply check if you can answer: what is being pursued in the next stage, who is blocking it, what will be lost upon failure, and what will the climax change.

## Four-Question Agency & Pacing Audit (Run Per Volume / Unit)

1. **Protagonist Agency**: Did the protagonist make the irreversible choice and earn the outcome? (If institutions or allies resolve the crisis without strategic trade-offs, fix the outline.)
2. **Credit & Gain Ownership**: Did core gains, leverage, or recognition stay with the protagonist rather than being hijacked by bystanders or coincidence?
3. **Late-Stage Reserve**: Did this volume/unit accidentally burn endgame masterminds, final truths, or power ceilings meant for later volumes? (Reveal at most one major secret per volume.)
4. **Expectation & Map Continuity**: Did prior promises advance or pay off, and if switching maps/arenas, did at least one unresolved goal, debt, or relationship carry over?

### Volume Anchors & Beat Cadence
- Anchor major turning points at **1/4** (inciting pressure / first reversal), **1/2** (midpoint shift raising stakes), and **3/4** (volume climax). Rotate emotional motifs so the same tension (e.g., pure courtroom or pure grief) does not repeat >2–3 chapters consecutively.
- For standard 2,200–2,800 char chapters, aim for **4–5 concrete `Plot Beats` per chapter** (~450–600 chars per scene/beat) so pacing stays crisp and easy to adapt.

---

# How to Write a Novel Detailed Outline: Chapter Template and Fill-in Example

A detailed outline (`細綱`, *xìgāng*) breaks upcoming chapters down into an actionable plan you can draft from directly: where the reader's emotions travel from and to, what choices the characters face, which plot beats need to be expanded in full, and which trump cards must stay hidden for now. A chapter outline (`章綱`, *zhānggāng*) can be as rough as one line stating a single purpose, and different authors use different names for these layers. This guide provides a practical fill-in template; if you use Oh Story to draft the main text, the skill will save outlines using the project's built-in detailed outline template. Stakes/trade-offs, foreshadowing payoffs, and pacing/detail allocation are used as needed—you do not have to fill in every field for every chapter.

## What Is the Difference Between a Detailed Outline and a Chapter Outline?

A chapter outline governs the broad direction, while a detailed outline governs how you actually put pen to paper for that specific chapter. In web-novel circles there is no strict boundary between the two terms; in this guide, a rough one-line or one-paragraph plan is called a chapter outline, and a breakdown down to individual plot beats is called a detailed outline.

| Layer | Purpose and Contents |
|---|---|
| Chapter Outline | One sentence plus a purpose tag, or one paragraph governing a single event; notes the chapter range, hooks, and foreshadowing. How many chapters it covers is decided by the event itself, not fixed to three to five chapters. |
| Detailed Outline | Clearly states the target emotion, character choices, plot beats, what to withhold for now, and where the ending stops—ready to draft prose from immediately. |

There is no need to write two sets of duplicate content. Oh Story's long-form novel project uses a full-book outline, volume outlines, and per-chapter files saved at `大綱/細綱_第XXX章.md`. When you are only discussing ideas or planning, it stops once the outline is delivered and will not automatically proceed to drafting the chapter prose.

### Quick Chapter Outline Table

| Chapter | Event, Purpose, and Next-Chapter Handoff |
|---|---|
| Chapter 12 | The apprentice repairs a pocket watch declared "beyond saving" in front of a crowd; purpose is to pay off craftsmanship; at chapter end, the appraiser photographs the engraving inside the lid. |
| Chapter N or Chapter Range | Clearly state what happens, the function of this segment, and which expectation is planted or paid off. |

Expand into a detailed outline when you need more specific choices and actions.

## Detailed Chapter Outline Schema & Beat Rules

> **Authoritative Blank Schema (SSOT)**: Use [templates/chapter_outline.md](../templates/chapter_outline.md) for long-form chapter outlines and [templates/short_outline.md](../templates/short_outline.md) for short-form story outlines.

The number of beats is decided by content, not divided evenly by target word count. The native project schema separates beat number (`#`), plot beat (`情節點`), function tag (`作用`), and execution boundaries (`分寸`) into distinct columns. "放" (Allowed) marks where the drafter can improvise freely without locking down every tiny detail; "禁" (Forbidden) marks facts that must not be revealed prematurely.

### 5. Optional Additions as Needed

- Stakes & pricing: How to let the reader intuitively see how heavy this transaction/stake is; not every chapter needs two sets of valuations.
- Payoff progress: Where acquisition, use, visible effect, and valuation stand; omit when not applicable.
- Detail & pacing allocation: Which beats get full scene-by-scene treatment, which get only one or two details, and which are brushed over in a line; not every climax has to be written in slow motion.
- Drafter free zone: On-the-spot actions, sounds, or phrasing that can be expanded freely, while holding fast to established events and character knowledge.

Chapter openings and chapter endings carry different jobs; next you can read [How to Write Hooks](opening_and_hooks.md).

## How to Write a Detailed Outline: Fill-in Order and Key Fields

First lock in chapter position, target emotion, and character choice, then work backward to the actions that must be written. Finally, arrange the ending and next-chapter handoff; if this chapter is not an overt satisfaction-beat chapter, you can also work backward from relationship shifts, problem-sorting, or daily-life goals without forcing a reversal.

### Make Target Emotion and Key Choice Concrete First

Merely writing "hot-blooded" or "sad" is just slapping on a label. Replace it with "holding breath in frustration for her → seeing her craft acknowledged, while still worrying about the rent", and mark which action brings about the shift. The goal is what the character wants; the choice is how they make a call on the spot. In multi-character cooperative scenes, different characters can make their own calls—the protagonist does not have to monopolize every action.

### Let Readers Understand the Stakes First

When a transaction, gain, or loss is involved, anchor it against prices, investments, or immediate expenses the character has seen earlier. You do not need to do accounting in every chapter; also, do not lump together a watch repair fee, an offer to buy the whole watch, and the value of follow-up orders into a single ledger.

### Match Detail Level to Scene Effect

Clearly mark which beats should be opened up and written in full, and which should pass in a sentence or two. Once a point is established, do not repeat it; chapters that genuinely need to slow down for hesitation or long dialogue should still be given full room. Where to write in detail and where to summarize depends on what the chapter needs—do not mark every plot beat as detailed.

### Use "Forbidden" and "Allowed" to Guard Two Boundaries

"Forbidden" locks down trump cards that must not be spoken aloud yet and plot twists that must not be added at whim; "Allowed" gives room for on-the-scene improvisation. Allowing improvisation on watch-disassembly details does not mean you can swap out the malfunction, the owner, or the repair outcome on the fly. A trump card saved in the outline for a later reveal must not be written as something the characters already know now.

## Detailed Outline Example: An Original Chapter Outline (Condensed)

A condensed detailed outline for Chapter 12 of an original urban-fiction novel. Kuang Xiaohe is an apprentice at an old-street watch shop; her master is hospitalized, the rent is unpaid, and the watch store across the street wants to buy out their shop.

> Chapter 12: The Eight-Hundred-Yuan Watch
> Core event: In front of the customer and the appraiser from the rival watch store across the street, Kuang Xiaohe repairs a pocket watch declared "beyond saving" and earns the customer's promise to bring more watches next week.
> Chapter-opening hook: Opens with suspenseful dialogue as the customer sets the pocket watch on the counter: "Every other shop said it's beyond saving. Do you still fix it?"
> Position / Chapter positioning: Beat 3 of the "Defending the Shop" arc; progression chapter.
> Target emotion: Holding breath in frustration for her (treated as just a kid minding the counter) → cathartic relief, plus a touch of suspense; advances the arc link "looked down upon → turning the tables through craft."
> Protagonist goal / Key choice: Keep this order to scrape together rent; whether to open the watch in front of everyone—if she breaks it, she has to pay damages, and the shop's reputation is ruined.
> Chapter pricing: The customer says another shop quoted 3,000 to replace the movement; the appraiser offers 800 to buy the watch. The first is a repair quote and the second is a purchase offer—they cannot be subtracted directly to calculate profit; each separately shows the customer's burden and the appraiser's judgment of the old watch.
> Payoff progress: Acquisition (taking the order), Use (repairing the watch), and Visible Effect (the watch starts running) complete in this chapter; Valuation is held back—how much this watch and this customer are truly worth is uncovered in Chapter 13 along with the origin of the engraving.
> Forbidden from early release in this chapter: The meaning of the engraving inside the watch lid; the master appearing or calling.
> Drafter free zone: Technique and rhythm of disassembling the watch, how badly the appraiser loses composure, her small talk with the customer.
> Satisfaction beat: Fixed on the spot in front of everyone, overturning the "beyond saving" verdict.
> Ending: Before leaving, the appraiser raises his phone and photographs the engraving inside the watch lid.
> Chapter-ending hook: Mysterious object; neither what the engraving says nor what he recognized is explained; medium intensity; Chapter 13 opens with him walking into his own watch store.
> Beat 1 (Setup, sparse / `鋪墊，疏`): The customer quotes the other shop's 3,000 price to replace the movement. Forbidden: Do not reveal the watch's origin early.
> Beat 2 (Setup, medium / `鋪墊，中`): The rival store's appraiser declares the movement rusted solid and offers 800 to buy the watch. Allowed: He can use Kuang Xiaohe's young age against her in front of the customer.
> Beat 3 (Characterization, dense / `人物塑造，密`): Kuang Xiaohe decides to open the watch. Allowed: She can declare in public, "If I break it, I pay," putting the stakes right on the counter.
> Beat 4 (Satisfaction beat, dense / `爽點，密`): Mainspring resets; the second hand starts moving. Allowed: The customer can say on the spot that he won't replace the 3,000 movement and won't sell for 800 either.
> Beat 5 (Setup, sparse / `鋪墊，疏`): The customer agrees to bring several other watches from home next week; the appraiser takes his leave. Forbidden: Do not reveal the contents of the engraving.

Once the second hand moves, the reader sees the "beyond saving" verdict overturned. That still does not prove how much the pocket watch is worth, nor has the apprentice received 3,000 or 800. The customer promising to return next week is only a new opportunity; actual repair fees, orders, and rent will land in later chapters. The watch's origin is handed off to that photograph at the chapter's end. For how a detailed outline becomes prose, see From Chapter Outline to Prose.

## Common Detailed-Outline Mistakes and How to Fix Them

- **Refusing to write until every field is filled**: Write concrete goals, choices, and essential beats first, then fill other fields as the task requires; do not invent plot just for the form.
- **Writing every beat the same way**: Check for duplicated functions, then divide detail and brevity by scene effect; keep a slow pace intact whenever the author explicitly needs it.
- **Relying only on gasps to show stakes**: Let the reader see the outcome and its actual impact; when using a benchmark, clarify whether it measures price, opportunity, or relationship.
- **Maxing out every single chapter**: Low-pressure chapters can let characters catch their breath, sort information, or live their lives, as long as they retain an expectation tied to what follows.
- **Redundant explanations at the ending**: If the scene already made it clear to the reader, cut the repetitive summary; whether to keep direct rendering or narrator commentary depends on the book's style and actual effect.
- **Mechanically filling the withhold list**: Only list information with a real leak risk in this chapter; write "None" if there is none—do not pad to three or five items.
- **Treating a plan as an accomplished fact**: Preparing to expose something is not the same as having exposed it; obtaining permission is not the same as having completed the action.

Check the opening chapters separately against opening-chapter tasks; see [Novel Openings](opening_and_hooks.md).
