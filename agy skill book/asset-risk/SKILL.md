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

| Mode | Command | Input | Output |
| :--- | :--- | :--- | :--- |
| **Single Probe** | `python3 <skill_dir>/scripts/matcher.py --cat <Cat> --type <Type> --name <Name>` | Single asset row | JSON matching pair |
| **Batch Matching** | `python3 <skill_dir>/scripts/matcher.py --batch <file.json>` | Array of asset rows | JSON with anti-monotony rotation |
| **Drill Generator** | `python3 <skill_dir>/scripts/drill_generator.py --name <Name> --cat <Cat> --type <Type> --threat <Threat> --vuln <Vuln>` | High-risk asset threat/vuln | IT4-21 standardized drill plan & 11 execution steps |
| **News Analyzer** | `python3 <skill_dir>/scripts/news_analyzer.py --text "<NewsText>" [--top-k 3] [--drill]` | Raw incident / news text | Canonical threat/vuln pairs via Inverted Index (+ optional drill) |

## Execution Workflow

1. **Input Inspection**: Read asset items, categories, types, or raw incident alerts/news text.
2. **Deterministic Matching / Inverted Index**:
   - For assets: Call `matcher.py`. Items with unclear semantics are safely skipped (`status='unresolved'`) to prevent data contamination.
   - For news/alerts: Call `news_analyzer.py` utilizing the in-memory inverted index ($N=60 > 20$) to extract evidence and map to top-k canonical pairs.
3. **Anti-Monotony & Governance**: Ensure consecutive rows of identical types rotate through distinct valid pairs without envelope tax.
4. **Drill Scenario Generation**: For high-risk inventory items or critical incident alerts, run `drill_generator.py` (or `news_analyzer.py --drill`) to generate schema-driven, field-centric IT4-21 disaster recovery drill plans and statutory execution steps.
5. **Handoff & User Clarification**: Write matched pairs via `xml_patcher.py`; prompt the user at the end to clarify any skipped unresolved assets.

## References
- [`DRILL_SCENARIO_FRAMEWORK.md`](references/DRILL_SCENARIO_FRAMEWORK.md): Field-centric IT4-21 disaster recovery drill schema, statutory timelines, and execution step procedures.
- [`ASSET_CATALOG.md`](references/ASSET_CATALOG.md): Taxonomy, causality principles, and anti-monotony rules.
- [`ASSET_RISK_TEMPLATE.md`](references/ASSET_RISK_TEMPLATE.md): Canonical 10-column Markdown template and field schema.
- [`VALUATION_GUIDE.md`](references/VALUATION_GUIDE.md): CIA 5/3/1 criteria and 1~125 risk calculation reference.
