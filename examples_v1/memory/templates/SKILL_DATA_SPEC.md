# Skill Data & Progressive Disclosure Laws (`skill_data_laws`)

> **Core Directives**:
> 1. **Progressive Disclosure is the MANDATORY ARCHITECTURE**: Context budget is finite. All skills must stratify knowledge into Level 1 (Index), Level 2 (Decision), and Level 3 (On-Demand Payloads).
> 2. **Pattern A (Flat List) is the UNIVERSAL DEFAULT**: Scripts MUST auto-build an in-memory **Inverted Index** on `tags` when records exceed 20 items.  
> 3. **Zero Envelope Tax is an IRON LAW**: Never wrap attributes in arbitrary nesting.

---

## 1. Three-Tier Progressive Disclosure Hierarchy

All skills must partition content to keep idle Context consumption at zero:

| Level | File Targets | Loading Timing | Token Budget Cap | Primary Responsibility |
| :---: | :--- | :--- | :---: | :--- |
| **Level 1** | `SKILL.md` | Session Start (Always Loaded) | **$\le$ 4,000 tokens** | Mental models, command routing table, and chapter/module catalog. |
| **Level 2** | `patterns.md`<br>`cheatsheet.md`<br>`glossary.md` | On Cross-Cutting Decision | **$\le$ 2,000 tokens** | Design patterns, anti-patterns, decision matrices, and exact terminology. |
| **Level 3** | `modules/*.md`<br>`chapters/*.md` | On-Demand Explicit Query | **$\le$ 1,560 tokens / file** | Deep domain payloads. Loaded only when user targets a specific sub-topic. |

---

## 2. Storage Patterns: Default vs. Exception

| Storage Pattern | Role & Scope | Physical Structure | Runtime Index Mandate |
| :--- | :--- | :--- | :--- |
| **Pattern A: Flat List** | **DEFAULT**: Plug-and-play, lightweight skills | `[ { "id": "...", "tags": [...] } ]` | Ingest to `tag_index` ($O(1)$ if $N > 20$) |
| **Pattern B: Grouped** | **EXCEPTION**: Hierarchical taxonomies (e.g. multi-tier catalogs) | `{ "categories": { "group": [ ... ] } }` | Extract items into `tag_index` on load |

---

## 3. Minimal Golden Skeletons

### Level 1 & 2: Pattern A Flat Catalog (The Universal Default)
```json
[
  {
    "id": "ITEM_001",
    "tags": ["backup_host", "database_node"],
    "summary": "Primary DB timeout",
    "action": "Failover to replica"
  }
]
```

### Pattern B: Semantic Grouped Taxonomy (Strict Exception Only)
```json
{
  "categories": {
    "compute": [
      {
        "id": "COMP_001",
        "type": "instance",
        "tags": ["web_server", "linux"],
        "description": "Primary application host",
        "action": "Auto-restart on failure"
      }
    ]
  }
}
```

---

## 4. Thresholded Inverted Index Contract (Python Pattern)

For tiny datasets ($N \le 20$), linear scan is permitted. For $N > 20$, scripts **MUST** build an in-memory inverted index:

```python
# Ingestion: Auto-build index when records > 20
records = data if isinstance(data, list) else [
    item for group in data.get("categories", {}).values()
    for item in (group if isinstance(group, list) else group.get("items", []))
]
tag_index = {}
if len(records) > 20:
    for r in records:
        for tag in r.get("tags", []):
            tag_index.setdefault(tag.strip().lower(), []).append(r)

# Query: O(1) index lookup when available; fallback to linear scan if N <= 20
def find(token: str):
    t = token.strip().lower()
    return tag_index.get(t, []) if tag_index else [r for r in records if t in [x.lower() for x in r.get("tags", [])]]
```

---

## 5. The 5 Pragmatic Laws

1. **Progressive Disclosure & Token Caps (MANDATORY)**: Respect Level 1 ($\le$ 4k), Level 2 ($\le$ 2k), and Level 3 ($\le$ 1,560/file) token boundaries.
2. **Pattern A Default (MUST)**: Always default to flat Pattern A unless deep hierarchical taxonomy is fundamentally required.
3. **Zero Envelope Tax (IRON LAW)**: Never wrap attributes in arbitrary nesting such as `metadata: { tags: [...] }` or `payload: { ... }`. Keep record attributes flat at the top level.
4. **Thresholded Indexing (MUST)**: Build an in-memory inverted index whenever records exceed 20 items. Linear scan is permitted for $N \le 20$.
5. **Key Invariance & Carrier Nouns (MUST)**: 100% identical keys across all array records. `tags` must be 3~6 concrete domain carrier nouns.
