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
