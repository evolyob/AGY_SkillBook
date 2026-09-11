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

## Execution Workflow

1. **Input Inspection**: Read asset items, categories, and types.
2. **Deterministic Matching**: Call `matcher.py` with asset rows.
3. **Anti-Monotony Safeguard**: Ensure consecutive rows of identical types rotate through distinct valid pairs.
4. **Handoff**: Pipe JSON output to user or `exec-xlsx/scripts/xml_patcher.py` for template insertion.

## References
- [`ASSET_CATALOG.md`](references/ASSET_CATALOG.md): Taxonomy, causality principles, and anti-monotony rules.
- [`VALUATION_GUIDE.md`](references/VALUATION_GUIDE.md): CIA 5/3/1 criteria and 1~125 risk calculation reference.
