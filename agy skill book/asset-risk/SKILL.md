---
name: asset-risk
description: Categorize information assets, assign canonical threat-vulnerability pairs from parameters.json, generate 8-step DR drill plans, or align external threat intelligence.
dependencies: []
---

# Information Asset Risk & DR Drill Companion (`asset-risk`)

## Mission & Boundary
Single Source of Truth for information asset risk categorization, canonical threat-vulnerability pairing, and 8-step disaster recovery drill plans driven by `parameters.json` (60 validated pairs).
- **Zero Calculation Boundary**: Do NOT calculate numeric risk scores ($V \times T$). Excel native formulas handle math; human asset owners judge scores.

---

## Routing & Core Commands

| Feature | Trigger / Scenario | Concrete CLI Command | Primary Deliverable |
| :--- | :--- | :--- | :--- |
| **1. Asset Matching** | Inventory rows, single system review | `python3 <skill_dir>/scripts/matcher.py --name "<Asset>"`<br>`python3 <skill_dir>/scripts/matcher.py --batch <file.json>` | Category, Type, Threat, Vuln, Pair ID (with rolling 5-history anti-monotony) |
| **2. Threat Intel** | External CVE, breach news, incident report | Semantic entity extraction ➔ Query `matcher.py` against `parameters.json` | 3-part debrief: Incident summary, internal standard mapping, existing controls |
| **3. DR Drill Plan** | Compliance audit, DR drill sheet, tabletop | `python3 <skill_dir>/scripts/drill_generator.py --name "<Asset>" --pair-id <ID> --format markdown` | Block A (Planning Table) + Block B (8-Step Execution Table) |
| **4A. PII Inventory** | 個人資料盤點、隱私合規查核 | `python3 <skill_dir>/scripts/matcher.py --name "<Asset>" --pii-inventory -f markdown` | 11 欄通用個資盤點表 + Controls A~J 查核表 |
| **4B. PII Breach Drill** | 重大個資外洩演練、隱私查核 | `python3 <skill_dir>/scripts/matcher.py --name "<Asset>" --drill --pii -f markdown` | 個資外洩專項 Block A + Block B (含72h通報與第12條) |

---

## Concrete Execution Protocols

### 1. Asset Inventory Matching
- **Single Asset**: Run `python3 <skill_dir>/scripts/matcher.py --name "<Asset Name>"`. The script automatically infers Category and Type using head-noun suffix weighting.
- **Batch Processing**: Run `python3 <skill_dir>/scripts/matcher.py --batch <file.json>`. The script tracks recent threat history to prevent consecutive identical rows from receiving duplicate pairs.
- **Ambiguity Handling**: If the asset name is too generic to determine a single category (`status="unresolved"`), prompt the user to specify the asset type instead of guessing.

### 2. External Threat Intel Alignment
When receiving external security news, vulnerability alerts, or incident reports:
1. **Extract Core Target**: Identify the victim asset entity and normalize it to an internal IT keyword.
2. **Lookup Canonical Pair**: Run `python3 <skill_dir>/scripts/matcher.py --name "<Keyword>"` to retrieve standard Category, Type, Threat, Vulnerability, and Pair ID.
3. **Format Debrief**: Incident Summary, Internal Mapping, and Defensive Posture & SOP.

### 3. 8-Step Disaster Recovery Drill Generation
- Run `python3 <skill_dir>/scripts/drill_generator.py --name "<Asset Name>" --pair-id <Pair ID> --format markdown`.
- Deliver Block A (Planning) + Block B (8-step Technical Execution) directly in clean Markdown.

### 4. PII Dual-Branch Protocols
- **Branch 4A (PII Inventory)**: Run `python3 <skill_dir>/scripts/matcher.py --name "<Asset>" --pii-inventory -f markdown`. Natural joins `pii_parameters.json` to generate the 11-column universal inventory and category Controls A~J checklist. Blocks non-PII assets (硬體, 人員).
- **Branch 4B (PII Breach Drill)**: Run `python3 <skill_dir>/scripts/matcher.py --name "<Asset>" --drill --pii -f markdown`. Binds canonical threat/vulnerability while overriding Steps 4–7 with statutory breach containment, 72-hour regulatory reporting, and Article 12 data subject notifications.

---

## References
- [`DRILL_SCENARIO_FRAMEWORK.md`](references/DRILL_SCENARIO_FRAMEWORK.md): 8-step procedure requirements, phase codes, and debrief template.
- [`ASSET_CATALOG.md`](references/ASSET_CATALOG.md): 5 categories, taxonomy rules, and 60 validated causal pairs.
- [`ASSET_RISK_TEMPLATE.md`](references/ASSET_RISK_TEMPLATE.md): Standard 10-column table schema.
- [`PII_INVENTORY_TEMPLATE.md`](references/PII_INVENTORY_TEMPLATE.md): Universal 11-column PII schema and 29-column enterprise mapping.
- [`VALUATION_GUIDE.md`](references/VALUATION_GUIDE.md): CIA rating matrix and risk calculation reference.
