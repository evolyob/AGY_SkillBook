# Skill Data & Indexing Laws (`skill_data_laws`)

> **Core Directive**: **Pattern A (Flat List) is the UNIVERSAL DEFAULT**. Scripts MUST auto-build an in-memory **Inverted Index** on `tags` when records exceed 20 items.  
> **Core Philosophy**: Zero Envelope Tax is an absolute iron law. Semantic grouping (Pattern B) is strictly an opt-in exception for deep taxonomies.

---

## 1. Storage Patterns: Default vs. Exception

| Storage Pattern | Role & Scope | Physical Structure | Runtime Index Mandate |
| :--- | :--- | :--- | :--- |
| **Pattern A: Flat List** | **DEFAULT**: Plug-and-play, lightweight skills | `[ { "id": "...", "tags": [...] } ]` | Ingest to `tag_index` ($O(1)$ if $N > 20$) |
| **Pattern B: Grouped** | **EXCEPTION**: Hierarchical taxonomies (e.g. multi-tier catalogs) | `{ "categories": { "group": [ ... ] } }` | Extract items into `tag_index` on load |

---

## 2. Minimal Golden Skeletons

### Pattern A: Direct Flat Catalog (The Universal Default)
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

## 3. Thresholded Inverted Index Contract (Python Pattern)

For tiny datasets ($N \le 20$), linear scan is permitted. For $N > 20$, scripts **MUST** build an in-memory inverted index:

```python
# Ingestion: Auto-build index when records > 20 (Flat list or Grouped dictionary)
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

## 4. The 4 Pragmatic Laws

1. **Pattern A Default (MUST)**: Always default to flat Pattern A unless deep hierarchical taxonomy is fundamentally required.
2. **Zero Envelope Tax (IRON LAW)**: Never wrap attributes in arbitrary nesting such as `metadata: { tags: [...] }` or `payload: { ... }`. Keep record attributes flat at the top level.
3. **Thresholded Indexing (MUST)**: Build an in-memory inverted index whenever records exceed 20 items. Linear scan is permitted for $N \le 20$.
4. **Key Invariance & Carrier Nouns (MUST)**: 100% identical keys across all array records. `tags` must be 3~6 concrete domain carrier nouns.
