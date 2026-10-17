# Deep Base: Operational & Synthesis Specifications

> Scope: Level-2 operational decision matrices, schemas, and synthesis rules for `deep-base`. Loaded on demand from `SKILL.md`.

---

## 1. Natural Language Intent Routing Matrix

Route conversational requests directly to the corresponding workflow without requiring subcommand flags:

| Detected Intent | Trigger Condition / Natural Input | Target Workflow | Primary Storage Target |
| :--- | :--- | :--- | :--- |
| **Capture Note (`note`)** | Quick note, snippet, or high-value chat conclusion | Workflow 2.1 | `~/wiki/raw/notes/YYYY-MM.md` |
| **Ingest File (`ingest`)** | Document path provided (PDF, DOCX, XLSX, HTML, MD) | Workflow 2.2 | `~/wiki/raw/articles/<slug>/chapters/` |
| **Distill Buffer (`distill`)** | Request to organize or distill buffered notes | Workflow 2.3 | `~/wiki/wiki/entities/<entity_slug>.md` |
| **Query & Ground (`query`)** | Any technical question or local lookup request | Workflow 3 | Read `~/wiki/wiki/` + loopback to `raw/notes/` |
| **Audit & Archive (`lint`)** | Request to check link health, size, or retire an entity | Workflow 4 | `~/wiki/wiki/archive/<entity_slug>.md` |

---

## 2. Card Dispatch & Template Matrix (`~/wiki/wiki/`)

Every synthesized file under `~/wiki/wiki/` must stay within `45 KB` (`46,080 bytes`) and follow its assigned template:

| Directory | Card Role | Trigger Condition | Template Path |
| :--- | :--- | :--- | :--- |
| `wiki/sources/` | Source chapter map & key takeaways | Created once per ingested document `<slug>` | `templates/source.template.md` |
| `wiki/entities/` | Atomic tool, spec, module, or standard | Extracted from documents or `#<domain>/<entity_slug>` notes | `templates/entity.template.md` |
| `wiki/topics/` | Cross-entity conceptual architecture | Connects multiple related entity cards | `templates/topic.template.md` |
| `wiki/comparisons/` | Multi-subject tradeoff matrix | Side-by-side benchmark or architecture comparison | `templates/synthesis.template.md` |
| `wiki/synthesis/` | Long-term architectural conclusion | Complex multi-turn engineering decision or debate | `templates/synthesis.template.md` |
| `wiki/queries/` | High-frequency Q&A cache | Reusable deterministic answer for recurring lookups | `templates/query.template.md` |
| `wiki/archive/` | Retired or obsolete entity cards | Moved from `wiki/entities/` when deprecated | Retains original entity structure |

---

## 3. Workflow 2: Ingestion, Daily Notes & Glossary Rules

### 3.1 Daily Fragmented Notes & Tag Anatomy (`note` & `distill`)
1. **Monthly Buffer Creation**: On the first note of a month, create `~/wiki/raw/notes/YYYY-MM.md` with `# Notes YYYY-MM` if absent.
2. **Tag Anatomy (`#<domain>/<entity_slug>`)**:
   - `<domain>` (e.g., `tech`, `academic`, `compliance`): maps to the `tags` array in `data/glossary.json`.
   - `<entity_slug>` (e.g., `ebpf`, `iso27001`): maps directly to target card `wiki/entities/<entity_slug>.md`.
3. **Header-Only Block Schema**: Split blocks strictly on `^## \d{4}-\d{2}-\d{2}` headers (do not use `---` horizontal rules as block delimiters):
   ```markdown
   ## YYYY-MM-DD HH:MM | #<domain>/<entity_slug>
   <Note content, parameters, or fenced code blocks>
   ```
4. **Batch Distillation (`distill`)**:
   - Group unprocessed blocks in `raw/notes/YYYY-MM.md` by `#<domain>/<entity_slug>`.
   - Merge new parameters into existing `wiki/entities/<entity_slug>.md` Markdown tables and rules into specification lists; append provenance line `- Updated YYYY-MM-DD from raw/notes/YYYY-MM.md (#<domain>/<entity_slug>)`.
   - Move distilled blocks to `raw/notes/archive/YYYY-MM.md` and clear them from active `raw/notes/YYYY-MM.md`.

### 3.2 Document Flattening & Zero-Lookback Synthesis (`ingest`)
1. **Binary Cleanup**: After `flatten.py` exports `<= 40 KB` UTF-8 chapters to `raw/articles/<slug>/chapters` and extracts figures to `raw/assets/`, delete the original binary file to save disk space. If `flatten.py --list-only` exits with code `3` (`OCR_REQUIRED`), run OCR first.
2. **Write-Isolated Dispatch**:
   - `single_agent` (`<= 80 KB` and `<= 6` chapters): synthesize directly.
   - `subagent_parallel`: dispatch subagents by `recommended_batches`; each subagent writes exclusively to its assigned `wiki/entities/<entity_slug>.md` and returns JSON metadata to prevent race conditions on `index.md` and `log.md`.
3. **No-Elision Enumeration & Quantitative Fidelity**: Preserve 100% of enumerated items (modules, APIs, CLI flags, algorithm steps, clauses) in Markdown tables and retain exact numbers, bounds, formulas, and defaults so `wiki/` requires zero `raw/` lookback.

### 3.3 Pattern A Glossary Schema (`data/glossary.json`)
After distillation or ingestion, list newly detected acronyms/terms for user confirmation before appending to `data/glossary.json` using these 7 invariant keys:
```json
{
  "term_zh": "模型上下文協定",
  "term_en": "Model Context Protocol",
  "abbr": "MCP",
  "entity": "mcp",
  "tags": ["tech", "ai"],
  "aliases": ["上下文協定", "Anthropic MCP"],
  "definition": "Open protocol connecting LLM applications with external data sources and tools."
}
```

---

## 4. Workflow 3: Local-First Query & Grounding Rules (`query`)

1. **Silent Local-First Gate**: Execute `query.py ~/wiki --filter <keyword>` or `--entity <name>` before any external search. Query external sources strictly for missing deltas.
2. **Single-Tier Read & Minimalist Citation**:
   - Read only the directly matched card (`wiki/entities/<entity_slug>.md`); do not perform automatic multi-hop recursive reads.
   - Open Line 1 with local grounding confirmation followed immediately by the direct answer.
   - Keep body prose free of inline footnote numbers (`[1]`, `[2]`), and list optional related hops (`[[entity_a]]`, `[[entity_b]]`) at the bottom.
3. **Staleness Override & Loopback**: When local card specifications conflict with newer external standards or software versions, answer directly using the latest accurate external facts without debating the conflict, and append the correction as a tagged block to `raw/notes/YYYY-MM.md` for the next distillation cycle.

---

## 5. Workflow 4: Audit, Capacity Sharding & Archival Rules (`lint`)

1. **On-Demand Audit**: Run `lint_links.py ~/wiki --strict --verify-quotes` on user request to validate wikilinks, table/fence syntax, and source quotes.
2. **Capacity Sharding (`<= 45 KB`)**: When a card exceeds `46,080 bytes`, shard into sequential parts (`<entity_slug>_part1.md`, `<entity_slug>_part2.md`) linked at the footer, or split by sub-domain connected via `templates/topic.template.md`.
3. **Deprecation Archival**: Move retired entity cards from `wiki/entities/<entity_slug>.md` to `wiki/archive/<entity_slug>.md`.
