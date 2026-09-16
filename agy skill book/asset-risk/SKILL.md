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

---

## Concrete Execution Protocols

### 1. Asset Inventory Matching
- **Single Asset**: Run `python3 <skill_dir>/scripts/matcher.py --name "<Asset Name>"`. The script automatically infers Category and Type using head-noun suffix weighting.
- **Batch Processing**: Run `python3 <skill_dir>/scripts/matcher.py --batch <file.json>`. The script tracks recent threat history to prevent consecutive identical rows from receiving duplicate pairs.
- **Ambiguity Handling**: If the asset name is too generic to determine a single category (`status="unresolved"`), prompt the user to specify the asset type instead of guessing.

### 2. External Threat Intel Alignment
When receiving external security news, vulnerability alerts, or incident reports:
1. **Extract Core Target**: Identify the victim asset entity and normalize it to an internal IT keyword (e.g., "ESXi ransomware" ➔ "虛擬環境"; "CrowdStrike BSOD" ➔ "主機作業系統").
2. **Lookup Canonical Pair**: Run `python3 <skill_dir>/scripts/matcher.py --name "<Keyword>"` to retrieve the standard Category, Type, Threat, Vulnerability, and Pair ID from `parameters.json`.
3. **Format Debrief**:
   - **Incident Summary**: 2–3 sentences detailing the attack vector, exploited flaw, and business impact.
   - **Internal Mapping**: Exact `parameters.json` values (Category, Type, Threat, Vulnerability, Pair ID).
   - **Defensive Posture & SOP**: Map mitigation actions to existing drill controls (Step 2 containment, Step 7 restore).

### 3. 8-Step Disaster Recovery Drill Generation
- Run `python3 <skill_dir>/scripts/drill_generator.py --name "<Asset Name>" --pair-id <Pair ID> --format markdown`.
- Deliver both blocks directly in clean Markdown:
  - **Block A (Planning)**: Drill theme, scope, trigger scenario exploiting Vulnerability, standard 8-step flow.
  - **Block B (Execution)**: 8 standard procedures (收到通報 ➔ 緊急阻斷 ➔ 隔離保全 ➔ 受害清查 ➔ 事故判定 ➔ 通報主管機關 ➔ 修補還原 ➔ 驗證重啟). Keep `unit_role` and `duration` empty (`-`).

---

## References
- [`DRILL_SCENARIO_FRAMEWORK.md`](references/DRILL_SCENARIO_FRAMEWORK.md): 8-step procedure requirements, phase codes, and debrief template.
- [`ASSET_CATALOG.md`](references/ASSET_CATALOG.md): 5 categories, taxonomy rules, and 60 validated causal pairs.
- [`ASSET_RISK_TEMPLATE.md`](references/ASSET_RISK_TEMPLATE.md): Standard 10-column table schema.
- [`VALUATION_GUIDE.md`](references/VALUATION_GUIDE.md): CIA rating matrix and risk calculation reference.
