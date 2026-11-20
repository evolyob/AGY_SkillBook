# How to Organize a Novel Story Bible: Templates for Characters, Timelines, and Character Knowledge

A long-form novel's story bible must separate stable facts from states that change with the plot. Character cards store identity, bottom lines, and long-term goals; current state only records the latest status of location, resources, relationships, known information, and unresolved matters; the timeline records events in objective chronological order, while what characters know and what the reader knows are tracked separately. When the plot changes, you only update the corresponding entry, preventing multiple files from contradicting each other.

## A Sufficient Story Bible Setup

| Module | What It Stores | When to Update |
|---|---|---|
| Character Card (角色卡) | Identity, background, ability boundaries, long-term goals | When a setting detail is formally changed |
| Current State (当前状态) | Location, resources, relationships, known info, unresolved matters | Whenever a valid change occurs |
| Relationship Table (关系表) | Mutual promises, debts, public and private stances | When an action affecting the relationship lands |
| Author Timeline (作者时间线) | Objective order and dates of events | When new facts are confirmed |
| Reader Knowledge (读者已知) | Content already revealed in the main text | When a chapter is finished |
| World Rules (世界规则) | Applicable conditions, exceptions, costs | When rules are established or revised |

Each fact is canonized in only one place; other files either reference it or only record the latest outcome.

## Copyable Character State Template

```md
As of Chapter (截至章节):
Current Location & Activity (当前位置与正在做的事):
Current Goal (当前目标):
Abilities & Available Resources (能力与可用资源):
Key Relationships (关键关系): (Write promises, debts, and boundaries for each important person)
Known / Misbelieved / Concealed by Character (本人已知 / 误信 / 隐瞒):
Unresolved Matters (未结事项):
Source of This Change (本次变化来源): (Which chapter and paragraph in the main text)
```

Only create state pages for characters who will appear again later; leave one-off passersby in chapter records so the story bible doesn't bloat over time. When revising old chapters, recalculate affected states forward starting from the modified chapter.

## Original Filled Example: Old Water Station Manager (旧水站管理员)

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

## How to Do This Using This Repository's Skill

The above is the manual maintenance approach. When writing a long-form novel with Oh Story, these states are maintained by [story-long-write](../skills/story-long-write/SKILL.md): after finishing each chapter, the Agent only submits the changes for that chapter, and a script updates the single master ledger file accordingly, then automatically generates files such as character states, foreshadowing, author timeline, and reader knowledge under the book directory's `追踪/` (Tracking) folder. Do not manually edit these auto-generated files, as manual edits will trigger errors during verification. For how the four file layers divide responsibilities, see [How to Keep Character Consistency When Writing Long-Form Novels with AI (AI 写长篇小说怎么不崩人设)](ai-long-novel-character-consistency.md).

If the manuscript wasn't written in Oh Story, import it first with `/story-import`, which organizes existing chapters into a project with settings, outline, and tracking. When you are already in an Oh Story project and want to audit the story bible against the main text, you can say this in Claude Code (replace `/` with `$` in Codex):

> Use /story-long-write to audit the story bible against the written main text, dividing it into stable settings, full state as of Chapter 12, objective events, and what each party knows. Cite the main text for every change, only update what has changed, and keep all other facts that still hold. Do not write main text in this round.

The verification tool can confirm that each tracking file matches the master ledger, but it cannot judge for you whether the novel itself has omissions or misremembered details—the author still needs to read through it at the end.

## Related

- [Tracking state update guide (追踪状态更新说明)](../skills/story-long-write/references/tracking-transaction.md)
- [Verifying states forward from the edited point after revision (改稿后从改动处往后核对状态)](../skills/story-long-write/references/workflow-revision.md)
- [Turning confirmed changes into coherent scenes (把已定的变化写成连贯场景)](../skills/story-long-write/references/writing-craft.md)
- Repository URL: https://github.com/zenstory-ai/oh-story-claudecode
