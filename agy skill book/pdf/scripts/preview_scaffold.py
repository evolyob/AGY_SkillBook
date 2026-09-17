#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Visual Preview Scaffolder (preview_scaffold.py)
Generates standards-compliant, browser-ready Markdown preview files with embedded
CSS design tokens and verified layout archetypes (KPI Grid, Split Cards, Mermaid).
100% aligned with pdf_themes.json SSOT and verifier.py 5-Gate quality standards.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


def load_theme_config() -> Dict[str, Any]:
    """Loads themes from pdf_themes.json following search hierarchy."""
    candidates = [
        Path(__file__).parent / "pdf_themes.json",
        Path.home() / ".gemini/config/skills/pdf/scripts/pdf_themes.json",
        Path.home() / ".gemini/skills/pdf/scripts/pdf_themes.json",
    ]
    for p in candidates:
        if p and p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    return {}


def generate_css_block(light_theme: str = "light", dark_theme: str = "dark") -> str:
    """Generates the embedded canonical <style> block derived from pdf_themes.json SSOT."""
    cfg = load_theme_config()
    themes = cfg.get("themes", {})
    lt = themes.get(light_theme, {})
    dt = themes.get(dark_theme, {})

    bg_l = lt.get("bg", "#FFFFFF")
    card_l = lt.get("card_bg", "#F8FAFC")
    border_l = lt.get("border", "#CBD5E1")
    txt_l = lt.get("txt", "#0B0F19")
    muted_l = lt.get("muted", "#64748B")
    p_l = lt.get("p", "#2B5C8F")
    s_l = lt.get("s", "#007A92")

    bg_d = dt.get("bg", "#0B1120")
    card_d = dt.get("card_bg", "#1E293B")
    border_d = dt.get("border", "#334155")
    txt_d = dt.get("txt", "#F8FAFC")
    muted_d = dt.get("muted", "#94A3B8")
    p_d = dt.get("p", "#38BDF8")
    s_d = dt.get("s", "#60A5FA")

    return f"""<style>
:root {{
  --surface-base: {bg_l};
  --surface-card: {card_l};
  --border-subtle: {border_l};
  --text-main: {txt_l};
  --text-muted: {muted_l};
  --brand-primary: {p_l};
  --brand-accent: {s_l};
  --kpi-bg: {card_l};
  --color-alert: #E95119;
  --color-ok: #10B981;
  --radius-sm: 6px;
  --radius-md: 10px;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --surface-base: {bg_d};
    --surface-card: {card_d};
    --border-subtle: {border_d};
    --text-main: {txt_d};
    --text-muted: {muted_d};
    --brand-primary: {p_d};
    --brand-accent: {s_d};
    --kpi-bg: {bg_d};
    --color-alert: #FF0080;
    --color-ok: #10B981;
  }}
}}
body.ui-dark, body.theme-dark, [data-theme="dark"] {{
  --surface-base: {bg_d};
  --surface-card: {card_d};
  --border-subtle: {border_d};
  --text-main: {txt_d};
  --text-muted: {muted_d};
  --brand-primary: {p_d};
  --brand-accent: {s_d};
  --kpi-bg: {bg_d};
  --color-alert: #FF0080;
  --color-ok: #10B981;
}}
.doc-header {{ margin-bottom: 1.5rem; border-bottom: 2px solid var(--border-subtle); padding-bottom: 0.8rem; }}
.doc-header h1 {{ margin: 0 0 0.3rem 0; color: var(--brand-primary); font-size: 1.85rem; }}
.doc-header .doc-subtitle {{ color: var(--text-muted); font-size: 0.95rem; margin: 0; }}
.doc-section-title {{ display: flex; align-items: center; gap: 8px; margin: 2rem 0 1rem 0; padding-left: 10px; border-left: 4px solid var(--brand-accent); color: var(--brand-primary); font-size: 1.25rem; font-weight: 700; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin: 1.2rem 0 1.8rem 0; }}
.kpi-card {{ background: var(--kpi-bg); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 0.85rem 0.6rem; text-align: center; }}
.kpi-val {{ font-size: 1.45rem; font-weight: 800; color: var(--brand-primary); line-height: 1.2; }}
.kpi-label {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }}
.card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 1.8rem; }}
.card {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1.2rem 1.4rem; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); }}
.card.col-span-2 {{ grid-column: 1 / -1; }}
.card h4 {{ margin-top: 0; color: var(--brand-primary); font-size: 1.05rem; }}
.card p, .card li {{ color: var(--text-main); line-height: 1.6; }}
.chart-card {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1rem; overflow-x: auto; margin-bottom: 1.2rem; }}
</style>"""


def build_template_a(title: str, subtitle: str) -> str:
    """Builds Template A: Document Header & KPI Dashboard Grid."""
    return f"""<div class="doc-header">
  <h1>{title}</h1>
  <p class="doc-subtitle">{subtitle}</p>
</div>
<div class="kpi-grid">
  <div class="kpi-card"><div class="kpi-val">99.98%</div><div class="kpi-label">Service Availability</div></div>
  <div class="kpi-card"><div class="kpi-val">&lt; 15ms</div><div class="kpi-label">Average Latency</div></div>
  <div class="kpi-card"><div class="kpi-val">12 Units</div><div class="kpi-label">Active Modules</div></div>
  <div class="kpi-card"><div class="kpi-val">0</div><div class="kpi-label">Critical Incidents</div></div>
</div>"""


def build_template_b() -> str:
    """Builds Template B: Split Cards (As-Is vs. To-Be / Contrast)."""
    return """<h3 class="doc-section-title">Operational Challenges & Mitigation Plan</h3>
<div class="card-grid">
  <div class="card">
    <h4>✖ As-Is (Bottlenecks & Gaps)</h4>
    <ul>
      <li>Manual review cycle averages 3.5 days, delaying deployment.</li>
      <li>Asset inventory relies on spreadsheets without live drift tracking.</li>
    </ul>
  </div>
  <div class="card">
    <h4>✔ To-Be (Target Architecture)</h4>
    <ul>
      <li>Automated policy engine reduces verification turnaround to &lt; 15 minutes.</li>
      <li>Continuous IAM auditing pipeline detects unauthorized config drift daily.</li>
    </ul>
  </div>
</div>"""


def build_mermaid_xychart() -> str:
    return """<div class="chart-card">
<h4>1. Dual-Track Chart: Volume vs. Target (xychart-beta)</h4>

```mermaid
%%{init: {'theme': 'neutral'}}%%
xychart-beta
    title "Quarterly Throughput vs. Performance Target"
    x-axis ["Q1", "Q2", "Q3", "Q4"]
    y-axis "Processed Units" 0 --> 500
    bar [120, 210, 350, 480]
    line [100, 190, 320, 460]
```

</div>"""


def build_mermaid_flowchart() -> str:
    return """<div class="chart-card">
<h4>2. Architecture Topology & Flow (flowchart TD)</h4>

```mermaid
flowchart TD
    ext["Untrusted Ingress / Clients"] --> gateway["Edge Gateway / Load Balancer"]
    gateway <==> tier1["Service Cluster 01"]
    gateway <==> tier2["Service Cluster 02"]
    tier1 --> core["Core Processing Worker"]
    tier2 ==> core
    admin(((Management Console))) -.-> |mTLS / Bastion| core
    core ==> storage[("Persistent Database / Storage")]
```

</div>"""


def build_mermaid_gantt() -> str:
    return """<div class="chart-card">
<h4>3. Phased Roadmap & Dependency Schedule (gantt)</h4>

```mermaid
gantt
    title "Project Execution & Phased Delivery"
    dateFormat YYYY-MM-DD
    section Discovery & Scoping
      Baseline Audit :a1, 2026-01-01, 30d
      Risk Assessment :after a1, 14d
    section Implementation & Rollout
      Infrastructure Migration :2026-02-15, 25d
      Final Acceptance :15d
```

</div>"""


def build_mermaid_timeline() -> str:
    return """<div class="chart-card">
<h4>4. Milestone Timeline (timeline)</h4>

```mermaid
timeline
    title "Annual Strategic Milestone Roadmap"
    Q1 : Baseline Scoping : Initial Assessment
    Q2 : Architecture PoC : Stress & Penetration Test
    Q3 : Multi-Factor Rollout : Compliance Verification
    Q4 : Disaster Recovery Drill : Annual Retrospective
```

</div>"""


def build_mermaid_requirement() -> str:
    return """<div class="chart-card">
<h4>5. Specification & Requirement Traceability (requirementDiagram)</h4>

```mermaid
requirementDiagram
    requirement req_p0 {
      id: REQ-001-CORE
      text: Critical access must enforce dual-factor auth and automated audit logging
      risk: High
      verifymethod: Test
    }
    element auth_gateway {
      type: Component
    }
    auth_gateway - satisfies -> req_p0
```

</div>"""


def build_mermaid_sequence() -> str:
    return """<div class="chart-card">
<h4>6. API Interaction & Authentication Handshake (sequenceDiagram)</h4>

```mermaid
sequenceDiagram
    autonumber
    actor User as Client User
    participant GW as API Gateway
    participant Auth as Identity Provider (IAM)
    participant Svc as Core API Service
    participant DB as Secure Vault Storage

    User->>GW: 1. HTTPS POST /login
    GW->>Auth: 2. Validate Credentials & MFA
    Auth-->>GW: 3. Issue Signed JWT Bearer Token
    GW-->>User: 4. 200 OK (JWT Token)
    User->>GW: 5. GET /api/v1/assets (Bearer Token)
    GW->>Svc: 6. Forward Authorized Request
    Svc->>DB: 7. Query Encrypted Records
    DB-->>Svc: 8. Return Dataset
    Svc-->>User: 9. 200 OK JSON Response
```

</div>"""


def build_mermaid_state() -> str:
    return """<div class="chart-card">
<h4>7. Lifecycle & State Machine (stateDiagram-v2)</h4>

```mermaid
stateDiagram-v2
    [*] --> Draft: Asset Discovered
    Draft --> InReview: Submit for Review
    InReview --> Approved: Risk Assessment Passed
    InReview --> Rejected: Findings Require Fix
    Rejected --> Draft: Remediate Findings
    Approved --> Active: Production Deployment
    Active --> UnderAudit: Periodic Compliance Audit
    UnderAudit --> Active: Audit Passed
    UnderAudit --> Deprecated: EOL Notice
    Active --> Deprecated: Service Sunset
    Deprecated --> Archived: Encrypted Backup & Purge
    Archived --> [*]
```

</div>"""


def build_mermaid_class() -> str:
    return """<div class="chart-card">
<h4>8. Domain Object Model (classDiagram)</h4>

```mermaid
classDiagram
    class AssetRecord {
        +String assetId
        +String hostname
        +String ipAddress
        +String tierLevel
        +scanVulnerabilities()
        +updateComplianceStatus()
    }
    class VulnerabilityFinding {
        +String cveId
        +Float cvssScore
        +String severityRating
        +evaluateExploitability()
    }
    class DrillPlan {
        +String drillId
        +Date scheduledDate
        +String rtoObjective
        +executeDrill()
    }
    AssetRecord "1" *-- "many" VulnerabilityFinding : maps
    AssetRecord "1" o-- "many" DrillPlan : schedules
```

</div>"""


def build_mermaid_er() -> str:
    return """<div class="chart-card">
<h4>9. Relational Database Schema (erDiagram)</h4>

```mermaid
erDiagram
    ASSET_SYSTEM ||--o{ AUDIT_LOG : tracks
    ASSET_SYSTEM }|--|| ASSET_GROUP : belongs_to
    ASSET_SYSTEM ||--o{ VULN_FINDING : contains
    VULN_FINDING ||--|| CVE_REFERENCE : references

    ASSET_SYSTEM {
        string asset_id PK
        string hostname
        string ip_address
        string owner_dept
        string env_tier
    }
    AUDIT_LOG {
        int log_id PK
        string asset_id FK
        datetime timestamp
        string event_type
        string operator_id
    }
    VULN_FINDING {
        string finding_id PK
        string asset_id FK
        string cve_id FK
        string remediation_status
    }
    CVE_REFERENCE {
        string cve_id PK
        float cvss_score
        string severity_level
    }
```

</div>"""


def build_template_c(diagram: str = "all") -> str:
    """Builds Template C: Native Mermaid Visual Archetypes."""
    charts = {
        "xychart": build_mermaid_xychart,
        "flowchart": build_mermaid_flowchart,
        "gantt": build_mermaid_gantt,
        "timeline": build_mermaid_timeline,
        "requirement": build_mermaid_requirement,
        "sequence": build_mermaid_sequence,
        "state": build_mermaid_state,
        "class": build_mermaid_class,
        "er": build_mermaid_er,
    }
    parts = ['<h3 class="doc-section-title">Visual Models & Architecture (Mermaid Archetypes)</h3>\n']
    
    if diagram == "original":
        for key in ["xychart", "flowchart", "gantt", "timeline", "requirement"]:
            parts.append(charts[key]())
            parts.append("")
    elif diagram == "safe":
        for key in ["flowchart", "sequence", "state", "class", "er", "xychart"]:
            parts.append(charts[key]())
            parts.append("")
    elif diagram in charts:
        parts.append(charts[diagram]())
    else:  # "all"
        for fn in charts.values():
            parts.append(fn())
            parts.append("")
            
    return "\n".join(parts).strip()


def generate_scaffold(
    title: str = "Executive Strategy & Performance Dashboard",
    subtitle: str = "Operational Baseline · Continuous Verification · Automated Workflow",
    templates: str = "all",
    diagram: str = "all",
) -> str:
    """Combines CSS block with selected templates into a complete, verified Markdown preview document."""
    parts = [generate_css_block(), ""]

    if templates in ["a", "all", "header"]:
        parts.append(build_template_a(title, subtitle))
        parts.append("")

    if templates in ["b", "all", "cards"]:
        parts.append(build_template_b())
        parts.append("")

    if templates in ["c", "all", "charts"]:
        parts.append(build_template_c(diagram=diagram))
        parts.append("")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Generate standards-compliant Markdown preview files.")
    parser.add_argument("-o", "--output", help="Output Markdown file path (default: stdout)")
    parser.add_argument("-t", "--title", default="Executive Strategy & Performance Dashboard", help="Document Title")
    parser.add_argument("-s", "--subtitle", default="Operational Baseline · Continuous Verification · Automated Workflow", help="Subtitle")
    parser.add_argument("--template", choices=["all", "a", "b", "c"], default="all", help="Templates to include (default: all)")
    parser.add_argument(
        "--diagram",
        choices=["all", "original", "safe", "xychart", "flowchart", "gantt", "timeline", "requirement", "sequence", "state", "class", "er"],
        default="all",
        help="Mermaid diagram archetype (default: all, 'original': user's 5 charts, 'safe': 6 artifact-safe charts)",
    )
    parser.add_argument("--css-only", action="store_true", help="Print only the CSS <style> block")
    args = parser.parse_args()

    if args.css_only:
        content = generate_css_block()
    else:
        content = generate_scaffold(
            title=args.title,
            subtitle=args.subtitle,
            templates=args.template,
            diagram=args.diagram,
        )

    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Successfully generated Markdown preview scaffold: {out_path}")
    else:
        print(content)


if __name__ == "__main__":
    main()
