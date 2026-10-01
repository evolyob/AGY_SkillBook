# Cross-Skill Intent & Scenario Specification (`INTENT_SPEC.md`)

This document defines the 4-facet semantic matrix schema, NER slot naming conventions, and scenario pipeline assembly rules.

---

## 1. The 4-Facet Semantic Schema

| Facet | Definition | Target Extraction Target | Example |
| :--- | :--- | :--- | :--- |
| **Skill (Domain)** | Module identifier | Directory name and `SKILL.md` frontmatter | `audit-skill` |
| **Intent** | Action purpose ID | Normalized verb-noun action identifier | `ast_quality_audit` |
| **Keywords & Slots** | Trigger nouns/verbs and argument slots | `SECURITY.md` flags + bracketed entities `[...]` | `[target_path]`, `--ast` |
| **Utterances** | Natural language user expressions | Phrasing variations and sample prompts | 「檢查這段程式碼的 AST」 |

---

## 2. Standard NER Entity Slots

Standardized bracketed placeholder tokens used across all skills:

- `[target_path]`: Filesystem file or directory path.
- `[URL]`: HTTP/HTTPS web address or git remote URL.
- `[IP]`: IPv4 or IPv6 address.
- `[CVE]`: Common Vulnerabilities and Exposures ID (`CVE-YYYY-NNNNN`).
- `[DOMAIN]`: Fully qualified domain name (`example.com`).
- `[ASN]`: Autonomous System Number (`AS15169`).
- `[content]`: Raw text payload or markdown document.
- `[input_file]`: Raw document (`.docx`, `.pdf`, `.xlsx`, `.md`).

---

## 3. Scenario Pipeline Definition Pattern

Scenarios defined in `data/groups.json` follow this structure:

```json
{
  "id": "scenario_identifier",
  "tags": ["tag1", "tag2", "tag3"],
  "label": "情境名稱",
  "description": "情境簡要描述",
  "utterance_triggers": ["觸發問句1", "觸發問句2"],
  "pipeline": [
    {
      "step": 1,
      "skill": "skill_name",
      "intent": "intent_id",
      "flag": "--flag",
      "slot": "[slot_name]"
    }
  ]
}
```

---

## 4. Collision Detection Heuristics

When two or more skills share trigger keywords:
1. **Critical Collision**: Identical single-word command keyword mapped to disparate skills without qualifying context.
2. **Contextual Overlap**: Shared domain term (e.g. `audit` in `audit-skill` vs `env-audit`) with orthogonal parameters (`[path]` vs `[system]`). Differentiate via parameter slots in `skills_routing.md`.
