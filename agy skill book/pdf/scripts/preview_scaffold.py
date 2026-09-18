#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composable Visual Preview & Graphic Asset Scaffolder (preview_scaffold.py)
Generates modular, browser-ready Markdown preview files with composable building blocks:
- KPI Grid (4-metric performance dashboard)
- SOP Pipeline (linear execution phases 01 -> 04)
- Quadrant Matrix (2x2 strategic prioritization grid)
- Native Mermaid Visual Archetypes (5 canonical models)
All visual tokens and colors are dynamically derived from pdf_themes.json SSOT.
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

# ----------------------------------------------------------------------
# SSOT ARCHETYPE DICTIONARY (5 Canonical Mermaid Models)
# ----------------------------------------------------------------------
ARCHETYPES: Dict[str, Dict[str, str]] = {
    "flowchart": {
        "title": "1. 網路拓撲與服務流向架構 (Flowchart TD)",
        "card_title": "1. Architecture Topology & Flow (flowchart TD)",
        "code": """flowchart TD
    ext["Untrusted Ingress / Clients"] --> gateway["Edge Gateway / Load Balancer"]
    gateway <==> tier1["Service Cluster 01"]
    gateway <==> tier2["Service Cluster 02"]
    tier1 --> core["Core Processing Worker"]
    tier2 ==> core
    admin(((Management Console))) -.-> |mTLS / Bastion| core
    core ==> storage[("Persistent Database / Storage")]""",
    },
    "xychart": {
        "title": "2. 季產能與效能目標趨勢 (XYChart Beta)",
        "card_title": "2. Dual-Track Chart: Volume vs. Target (xychart-beta)",
        "code": """xychart-beta
    title "Quarterly Throughput vs. Performance Target"
    x-axis ["Q1", "Q2", "Q3", "Q4"]
    y-axis "Processed Units" 0 --> 500
    bar [120, 210, 350, 480]
    line [100, 190, 320, 460]""",
    },
    "gantt": {
        "title": "3. 專案里程碑與排程相依 (Gantt Schedule)",
        "card_title": "3. Phased Roadmap & Dependency Schedule (gantt)",
        "code": """gantt
    title "Project Execution & Phased Delivery"
    dateFormat YYYY-MM-DD
    section Discovery & Scoping
      Baseline Audit :a1, 2026-01-01, 30d
      Risk Assessment :after a1, 14d
    section Implementation & Rollout
      Infrastructure Migration :2026-02-15, 25d
      Final Acceptance :15d""",
    },
    "sequence": {
        "title": "4. API 認證交握與時序調度 (Sequence Diagram)",
        "card_title": "4. API Interaction & Authentication Handshake (sequenceDiagram)",
        "code": """sequenceDiagram
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
    Svc-->>User: 9. 200 OK JSON Response""",
    },
    "er": {
        "title": "5. 關聯式資料庫與日誌架構 (ER Diagram)",
        "card_title": "5. Relational Database Schema (erDiagram)",
        "code": """erDiagram
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
    }""",
    },
}


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


def get_theme_directive(theme_name: str = "light") -> str:
    """Derives dynamic Mermaid %%{init}%% directive directly from pdf_themes.json SSOT."""
    cfg = load_theme_config()
    themes = cfg.get("themes", {})
    th = themes.get(theme_name, themes.get("light", {}))
    p = th.get("p", "#2B5C8F")
    s = th.get("s", "#007A92")
    txt = th.get("txt", "#0B0F19")
    card_bg = th.get("card_bg", "#F8FAFC")
    return (
        f"%%{{init: {{'theme': 'base', 'themeVariables': {{"
        f"'primaryColor': '{card_bg}', 'primaryTextColor': '{txt}', 'primaryBorderColor': '{p}', "
        f"'lineColor': '{s}', 'secondaryColor': '{card_bg}', 'tertiaryColor': '{card_bg}', "
        f"'mainBkg': '{card_bg}', 'nodeBorder': '{p}', 'clusterBkg': '{card_bg}', 'titleColor': '{p}'"
        f"}}}}}}%%"
    )


def generate_css_block(theme_name: str = "light") -> str:
    """Generates canonical embedded <style> block supporting all building block grids."""
    cfg = load_theme_config()
    themes = cfg.get("themes", {})
    th = themes.get(theme_name, themes.get("light", {}))

    bg = th.get("bg", "#FFFFFF")
    card = th.get("card_bg", "#F8FAFC")
    border = th.get("border", "#CBD5E1")
    txt = th.get("txt", "#0B0F19")
    muted = th.get("muted", "#64748B")
    p = th.get("p", "#2B5C8F")
    s = th.get("s", "#007A92")
    alert = th.get("alert", "#E95119")
    ok = th.get("ok", "#10B981")

    return f"""<style>
:root {{
  --surface-base: {bg};
  --surface-card: {card};
  --border-subtle: {border};
  --text-main: {txt};
  --text-muted: {muted};
  --brand-primary: {p};
  --brand-accent: {s};
  --kpi-bg: {card};
  --color-alert: {alert};
  --color-ok: {ok};
  --radius-sm: 6px;
  --radius-md: 10px;
}}
.doc-header {{ margin-bottom: 1.5rem; border-bottom: 2px solid var(--border-subtle); padding-bottom: 0.8rem; }}
.doc-header h1 {{ margin: 0 0 0.3rem 0; color: var(--brand-primary); font-size: 1.85rem; }}
.doc-header .doc-subtitle {{ color: var(--text-muted); font-size: 0.95rem; margin: 0; }}
.doc-section-title {{ display: flex; align-items: center; gap: 8px; margin: 2rem 0 1rem 0; padding-left: 10px; border-left: 4px solid var(--brand-accent); color: var(--brand-primary); font-size: 1.25rem; font-weight: 700; }}

/* Building Block 1: KPI Grid */
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin: 1.2rem 0 1.8rem 0; }}
.kpi-card {{ background: var(--kpi-bg); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 0.85rem 0.6rem; text-align: center; }}
.kpi-val {{ font-size: 1.45rem; font-weight: 800; color: var(--brand-primary); line-height: 1.2; }}
.kpi-label {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }}

/* Building Block 2: SOP Pipeline */
.pipeline-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 1.2rem 0 1.8rem 0; }}
.pipeline-step {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1rem 1.1rem; position: relative; }}
.step-num {{ display: inline-block; background: var(--brand-primary); color: #FFFFFF; font-size: 0.75rem; font-weight: 700; border-radius: 4px; padding: 2px 7px; margin-bottom: 6px; }}
.step-title {{ font-size: 0.95rem; font-weight: 700; color: var(--text-main); margin-bottom: 4px; }}
.step-desc {{ font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; margin: 0; }}

/* Building Block 3: Quadrant Matrix (2x2) */
.matrix-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin: 1.2rem 0 1.8rem 0; }}
.matrix-card {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1.1rem 1.3rem; }}
.matrix-tag {{ display: inline-block; font-size: 0.75rem; font-weight: 700; color: var(--brand-accent); background: rgba(0, 122, 146, 0.08); padding: 2px 8px; border-radius: 4px; margin-bottom: 6px; }}
.matrix-card h4 {{ margin: 0 0 0.5rem 0; color: var(--brand-primary); font-size: 1.05rem; }}
.matrix-card ul {{ margin: 0; padding-left: 1.2rem; font-size: 0.85rem; color: var(--text-main); line-height: 1.6; }}

/* Building Block 4: Charts Container */
.chart-card {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1rem; overflow-x: auto; margin-bottom: 1.2rem; }}
.chart-card h4 {{ margin: 0 0 0.8rem 0; color: var(--brand-primary); font-size: 1.05rem; }}
</style>"""


def build_block_header(title: str, subtitle: str) -> str:
    """Builds Document Title Header block."""
    return f"""<div class="doc-header">
  <h1>{title}</h1>
  <p class="doc-subtitle">{subtitle}</p>
</div>"""


def build_block_kpi() -> str:
    """Building Block: 4-Column Performance KPI Grid."""
    return """<h3 class="doc-section-title">關鍵量化指標 (Key Performance Indicators)</h3>
<div class="kpi-grid">
  <div class="kpi-card"><div class="kpi-val">99.98%</div><div class="kpi-label">服務妥善率 (Availability)</div></div>
  <div class="kpi-card"><div class="kpi-val">&lt; 15ms</div><div class="kpi-label">平均請求延遲 (Latency)</div></div>
  <div class="kpi-card"><div class="kpi-val">12 個</div><div class="kpi-label">核心運行單元 (Active Units)</div></div>
  <div class="kpi-card"><div class="kpi-val">0 件</div><div class="kpi-label">重大資安事件 (Critical Incidents)</div></div>
</div>"""


def build_block_pipeline() -> str:
    """Building Block: SOP Execution Pipeline (Phase 01 -> 04)."""
    return """<h3 class="doc-section-title">標準作業程序管線 (SOP Execution Pipeline)</h3>
<div class="pipeline-grid">
  <div class="pipeline-step">
    <span class="step-num">PHASE 01</span>
    <div class="step-title">事件判定與通報</div>
    <p class="step-desc">監控觸發異常警報，完成風險等級初判並召集應變小組。</p>
  </div>
  <div class="pipeline-step">
    <span class="step-num">PHASE 02</span>
    <div class="step-title">隔離遏阻與止血</div>
    <p class="step-desc">切斷受害節點網路連接，阻斷惡意流量蔓延並保存證據日誌。</p>
  </div>
  <div class="pipeline-step">
    <span class="step-num">PHASE 03</span>
    <div class="step-title">修復回滾與驗證</div>
    <p class="step-desc">重灌乾淨映像檔或備援切換，校驗資料完整性後重新上線。</p>
  </div>
  <div class="pipeline-step">
    <span class="step-num">PHASE 04</span>
    <div class="step-title">事後覆盤與歸檔</div>
    <p class="step-desc">產出根本原因分析 (RCA) 報告，更新自動化防禦規則與演練手冊。</p>
  </div>
</div>"""


def build_block_matrix() -> str:
    """Building Block: Quadrant Matrix 2x2 (Strategic Prioritization / Risk vs Impact)."""
    return """<h3 class="doc-section-title">決策優先級象限矩陣 (Quadrant Matrix 2x2)</h3>
<div class="matrix-grid">
  <div class="matrix-card">
    <span class="matrix-tag">象限 I (高影響 · 低成本)</span>
    <h4>優先執行 (Quick Wins)</h4>
    <ul>
      <li>關鍵管理存取強制啟用多因子認證 (MFA)</li>
      <li>自動化漏洞掃描與弱點排程熱修補</li>
    </ul>
  </div>
  <div class="matrix-card">
    <span class="matrix-tag">象限 II (高影響 · 高成本)</span>
    <h4>重大專案 (Strategic)</h4>
    <ul>
      <li>異地多活備援架構升級與災防演練</li>
      <li>零信任 (Zero Trust) 身分邊界全面導入</li>
    </ul>
  </div>
  <div class="matrix-card">
    <span class="matrix-tag">象限 III (低影響 · 低成本)</span>
    <h4>日常維運 (Fill-Ins)</h4>
    <ul>
      <li>端點資產清冊定時校對與盤點</li>
      <li>例行性系統日誌備份完整性抽檢</li>
    </ul>
  </div>
  <div class="matrix-card">
    <span class="matrix-tag">象限 IV (低影響 · 高成本)</span>
    <h4>暫緩推遲 (Deprioritize)</h4>
    <ul>
      <li>非核心歷史系統自研介面翻新</li>
      <li>過度客製化監控腳本重複造輪子</li>
    </ul>
  </div>
</div>"""


def render_archetype_card(diagram_key: str, theme_name: str = "light") -> str:
    """Renders an archetype card HTML block for Markdown preview with theme colors from pdf_themes.json."""
    info = ARCHETYPES.get(diagram_key)
    if not info:
        return ""
    directive = get_theme_directive(theme_name)
    return f"""<div class="chart-card">
<h4>{info['card_title']}</h4>

```mermaid
{directive}
{info['code']}
```

</div>"""


def build_block_charts(diagram: str = "all", theme_name: str = "light") -> str:
    """Building Block: Native Mermaid Visual Archetypes."""
    parts = ['<h3 class="doc-section-title">視覺拓撲與架構模型 (Mermaid Archetypes)</h3>\n']
    keys = [diagram] if diagram in ARCHETYPES else list(ARCHETYPES.keys())
        
    for k in keys:
        if k in ARCHETYPES:
            parts.append(render_archetype_card(k, theme_name=theme_name))
            parts.append("")
            
    return "\n".join(parts).strip()


def render_mermaid_to_svg(mermaid_code: str, theme_name: str = "light") -> str:
    """Renders Mermaid DSL to SVG using mermaid.ink endpoint, dynamically applying colors from pdf_themes.json."""
    if not mermaid_code.strip().startswith("%%{init:"):
        directive = get_theme_directive(theme_name)
        mermaid_code = f"{directive}\n{mermaid_code.strip()}"
    encoded = base64.b64encode(mermaid_code.strip().encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/svg/{encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read().decode("utf-8")


def export_diagram_asset(diagram_type: str, output_file: str, theme_name: str = "light") -> Path:
    """Exports a Mermaid archetype to SVG or PNG (via resvg_py) with dynamic theme colors from pdf_themes.json."""
    if diagram_type not in ARCHETYPES:
        raise ValueError(f"Unknown diagram type '{diagram_type}'. Choose from: {list(ARCHETYPES.keys())}")
    
    code = ARCHETYPES[diagram_type]["code"]
    svg_str = render_mermaid_to_svg(code, theme_name=theme_name)
    
    out_path = Path(output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    if out_path.suffix.lower() == ".svg":
        out_path.write_text(svg_str, encoding="utf-8")
        return out_path
    
    import resvg_py
    png_bytes = resvg_py.svg_to_bytes(svg_str)
    out_path.write_bytes(png_bytes)
    return out_path


def generate_scaffold(
    title: str = "Executive Strategy & Performance Dashboard",
    subtitle: str = "Operational Baseline · Continuous Verification · Automated Workflow",
    templates: str = "all",
    diagram: str = "all",
    theme: str = "light",
) -> str:
    """Combines CSS block with selected building blocks like Lego blocks."""
    parts = [generate_css_block(theme_name=theme), "", build_block_header(title, subtitle), ""]

    raw_tokens = [t.strip().lower() for t in templates.split(",") if t.strip()]
    
    if "all" in raw_tokens:
        selected_blocks = ["kpi", "pipeline", "matrix", "charts"]
    else:
        selected_blocks = raw_tokens

    block_map = {
        "kpi": lambda: build_block_kpi(),
        "pipeline": lambda: build_block_pipeline(),
        "matrix": lambda: build_block_matrix(),
        "charts": lambda: build_block_charts(diagram=diagram, theme_name=theme),
    }

    for b in selected_blocks:
        if b in block_map:
            parts.append(block_map[b]())
            parts.append("")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Composable Markdown Preview & Mermaid Asset Scaffolder")
    parser.add_argument("-o", "--output", help="Output Markdown file path (default: stdout)")
    parser.add_argument("-t", "--title", default="Executive Strategy & Performance Dashboard", help="Document Title")
    parser.add_argument("-s", "--subtitle", default="Operational Baseline · Continuous Verification · Automated Workflow", help="Subtitle")
    parser.add_argument(
        "--template",
        default="all",
        help="Composable building blocks (comma-separated): kpi, pipeline, matrix, charts, or all (default: all)",
    )
    parser.add_argument(
        "--diagram",
        choices=["all"] + list(ARCHETYPES.keys()),
        default="all",
        help="Mermaid diagram filter (default: all)",
    )
    parser.add_argument("--css-only", action="store_true", help="Print only the CSS <style> block")
    parser.add_argument("--export-diagram", choices=list(ARCHETYPES.keys()), help="Export a specific Mermaid archetype as an image asset")
    parser.add_argument("--export-out", help="Target output file for --export-diagram (.svg or .png)")
    args = parser.parse_args()

    if args.export_diagram:
        if not args.export_out:
            print("[!] Error: --export-out <file.svg|file.png> is required with --export-diagram", file=sys.stderr)
            sys.exit(1)
        saved = export_diagram_asset(args.export_diagram, args.export_out)
        print(f"[+] Successfully exported diagram asset: {saved}")
        sys.exit(0)

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
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"[+] Successfully generated Markdown preview scaffold: {out_path}")
    else:
        print(content)


if __name__ == "__main__":
    main()
