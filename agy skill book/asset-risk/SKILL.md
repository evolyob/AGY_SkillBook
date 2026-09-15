---
name: asset-risk
description: Intelligently categorize information assets and select diverse, causally linked threats and vulnerabilities without repetitive monotony.
dependencies: []
---

# Information Asset Risk Selection Companion (`asset-risk`)

## Mission & Boundary
Intelligently categorize information assets and select fitting, causally-paired threats and vulnerabilities without repetitive monotony.
- **Core Capability**: Given an asset item name (and optional category/type), automatically infer its category and type, and select fitting, causally-paired threats and vulnerabilities with anti-monotony rotation.
- **Zero Calculation Boundary**: Does NOT calculate numeric scores ($V, T, V_u, R$), predict risk tiers, or format Excel files. Excel native formulas handle math; human asset owners judge scores.

## Progressive Routing Table

| Mode | Protocol / Command | Input | Output |
| :--- | :--- | :--- | :--- |
| **Single Probe** | `python3 <skill_dir>/scripts/matcher.py --cat <Cat> --type <Type> --name <Name>` | Single asset row | JSON matching pair |
| **Batch Matching** | `python3 <skill_dir>/scripts/matcher.py --batch <file.json>` | Array of asset rows | JSON with anti-monotony rotation |
| **Path A: DR Drill** | `python3 <skill_dir>/scripts/drill_generator.py` | Internal asset / `id` | Full Delivery (Block A + Block B) |
| **Path B: Threat Intel** | Top-Down Progressive Convergence | Security news / alert URL | Deep Causal Threat & Vuln Mapping |

## Execution Workflow

1. **Input Inspection**: Read asset items, categories, types, or external incident news/alerts.
2. **Deterministic Matching**: Call `matcher.py`. Items with unclear semantics are safely skipped (`status='unresolved'`) to prevent data contamination.
3. **Anti-Monotony & Governance**: Ensure consecutive rows of identical types rotate through distinct valid pairs without envelope tax.
4. **Drill & Incident Analysis**: Route internal assets (Path A) or external news (Path B) per [`DRILL_SCENARIO_FRAMEWORK.md`](references/DRILL_SCENARIO_FRAMEWORK.md).
5. **Handoff & User Clarification**: Write matched pairs via `xml_patcher.py`; prompt the user at the end to clarify any skipped unresolved assets.

## References
- [`DRILL_SCENARIO_FRAMEWORK.md`](references/DRILL_SCENARIO_FRAMEWORK.md): Field-centric disaster recovery drill schema, statutory timelines, and execution step procedures.
- [`ASSET_CATALOG.md`](references/ASSET_CATALOG.md): Taxonomy, causality principles, and anti-monotony rules.
- [`ASSET_RISK_TEMPLATE.md`](references/ASSET_RISK_TEMPLATE.md): Canonical 10-column Markdown template and field schema.
- [`VALUATION_GUIDE.md`](references/VALUATION_GUIDE.md): CIA 5/3/1 criteria and 1~125 risk calculation reference.
