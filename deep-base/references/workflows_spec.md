# Deep Base: Operational Specifications & Workflows Reference

> Scope: Level-3 Progressive Disclosure specification for `deep-base`.
> Defines behavioral rules for daily note capture, batch distillation, local-first grounding, and lifecycle maintenance.

---

## 1. Natural Language Intent Routing

Users interact via natural language phrases (or under `/deep-base`) without memorizing subcommands or flags:

| User Intent | Example Natural Phrases | Target Workflow |
| :--- | :--- | :--- |
| **Capture Note** | `記一下：#tech/ebpf ...` / `把這個結論記下來` | Workflow 2.1 (`note`) |
| **Ingest Document** | `收錄這份檔案 <path>` | Workflow 2.2 (`ingest`) |
| **Distill Buffer** | `整理本月筆記` / `提煉筆記` | Workflow 2.3 & 2.4 (`distill`) |
| **Query & Ground** | Any technical question / `查知識庫關於...` | Workflow 3 (`query`) |
| **Audit & Maintain** | `檢查知識庫健康` / `封存舊卡片 <entity>` | Workflow 4 (`lint` & `archive`) |

---

## 2. Workflow 1: Storage Boundaries & Initialization (`init`)

- **Command**: `python3 ~/.gemini/skills/deep-base/scripts/assemble.py --init --path ~/wiki`
- **Backup Policy**: Pure local filesystem at `~/wiki/` backed up via external OS tools (Time Machine, iCloud Drive, Synology Drive). Do not initialize Git inside `~/wiki/`.

| Path | Layer & Role | Linter / Lifecycle Rule |
| :--- | :--- | :--- |
| `raw/notes/YYYY-MM.md` | Active monthly note buffer (unprocessed inbox) | Auto-created on first write of the month; exempt from linter |
| `raw/notes/archive/YYYY-MM.md` | Processed historical note blocks | Moved here after `distill`; exempt from linter |
| `raw/articles/<slug>/chapters/` | Flattened document chapters (`<= 40 KB` each) | Immutable UTF-8 text; source binary deleted after extraction |
| `raw/assets/` | Extracted figures and images from documents | Referenced by source summaries and entity cards |
| `data/glossaries/<domain>.json` | Domain-specific terminology and alias tables | Created on demand from root tag `#<domain>`; fallback `data/glossary.json` |
| `wiki/{entities,topics,sources,comparisons,synthesis,queries}/` | Synthesized knowledge cards (`<= 45 KB` each) | Strictly audited for broken wikilinks, quotes, and capacity |
| `wiki/archive/` | Retired or obsolete entity cards | Valid link target; exempt from orphan page warnings |

---

## 3. Workflow 2 (Write Path): Capture, Ingest & Distillation

### Step 2.1: Daily Fragmented Notes Capture (`note`)
1. **On-Demand Monthly File**: When appending the first note of a month, create `raw/notes/YYYY-MM.md` with `# Notes YYYY-MM` if absent.
2. **Header-Only Block Boundary**: Each note block starts with an H2 timestamp and `#<domain>/<topic>` tag. Parsing splits strictly on `^## \d{4}-\d{2}-\d{2}` headers (do not rely on `---` horizontal rules, which collide with Markdown tables or inner separators):
   ```markdown
   ## YYYY-MM-DD HH:MM | #<domain>/<topic>
   <Note content, parameters, or fenced code blocks>
   ```

### Step 2.2: Binary & Long-Form Document Ingestion (`ingest`)
1. **Deduplication**: Run `cache.py check <file>`. If exit code `0` (`HIT`), read existing summary and stop.
2. **Flattening & Cleanup**: Run `flatten.py <file> --split-dir ~/wiki/raw/articles/<slug>/chapters --json` (`<= 40 KB` per chapter), save extracted images to `raw/assets/`, and delete the original binary file.
3. **Synthesis**: Generate `wiki/sources/<slug>.md` and extract core entities to `wiki/entities/<entity>.md`, then register hash via `cache.py update`.

### Step 2.3: Batch Distillation & Entity Merging (`distill`)
1. **Tag Grouping**: Parse unprocessed blocks in `raw/notes/YYYY-MM.md` by `#<domain>/<topic>`.
2. **Semantic Table & List Merge**:
   - For existing `wiki/entities/<entity>.md`: merge new parameters into existing Markdown tables and rules into specification lists; append provenance line `- Updated YYYY-MM-DD from raw/notes/YYYY-MM.md (#<domain>/<topic>)`.
   - For new entities: create `wiki/entities/<entity>.md` via `templates/entity.template.md` preserving 100% of enumerated items and exact numerical bounds.
3. **Inbox-Zero Move**: Append distilled blocks to `raw/notes/archive/YYYY-MM.md`, clear them from `raw/notes/YYYY-MM.md`, and update `index.md` and `log.md`.

### Step 2.4: On-Demand Domain Glossary Registration
1. **1:1 Root Tag Mapping**: Map newly detected acronyms or terms to `data/glossaries/<domain>.json` matching the root segment of `#<domain>/<topic>` (e.g., `#tech/*` -> `tech.json`, `#academic/*` -> `academic.json`, `#compliance/*` -> `compliance.json`). Do not pre-create empty domain files.
2. **Confirmation Gate**: List candidate terms and target `<domain>.json` after distillation; write only after user confirmation.

---

## 4. Workflow 3 (Read Path): Retrieval, Grounding & Loopback

### Step 3.1: Silent Local-First Gate & Single-Tier Read
1. **Local Check**: Before answering technical questions, silently run `query.py ~/wiki --filter <keyword>` or `--entity <name>`.
2. **Single-Tier Read**: Read only the directly matched card (`wiki/entities/<entity>.md`); do not perform multi-hop recursive reads across wikilinks.
3. **Minimalist Output Format**:
   - Line 1 begins with `已調閱本機知識庫，...` followed by the direct answer.
   - Keep body prose free of footnote markers (`[1]`, `[2]`).
   - Append related navigation at the end: `可進一步查閱 [[關聯實體A]]、[[關聯實體B]]`.

### Step 3.2: Staleness Override & Conversational Loopback
1. **Outdated Local Facts**: When a local card conflicts with newer external standards or software versions, answer directly with the latest accurate information without debating the conflict, and automatically append the correction as a tagged block to `raw/notes/YYYY-MM.md` so the next `distill` updates the card.
2. **Discussion Crystallization**: Valuable debugging resolutions or architectural decisions reached during chat are automatically appended as a tagged block (`## YYYY-MM-DD HH:MM | #<domain>/<topic>`) to `raw/notes/YYYY-MM.md`.

---

## 5. Workflow 4 (Maintenance Path): On-Demand Audit & Lifecycle

1. **On-Demand Health Scan**: Run `lint_links.py ~/wiki --strict --verify-quotes` only when requested by the user.
2. **Dynamic Backlinks**: Query incoming references dynamically via `lint_links.py ~/wiki --backlinks <entity>`; never hardcode backlinks inside entity cards.
3. **Capacity Sharding (`> 45 KB`)**: When a card under `wiki/` exceeds 45 KB (`46,080 bytes`), split by capacity into `<entity>_part1.md` and `<entity>_part2.md` with sequential footer links.
4. **Entity Archival**: Move deprecated or retired entity cards from `wiki/entities/` to `wiki/archive/`.
