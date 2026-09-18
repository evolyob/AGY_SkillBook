#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Visual Preview & Graphic Asset Scaffolder (preview_scaffold.py)
Generates standards-compliant, browser-ready Markdown preview files with embedded
CSS design tokens and verified layout archetypes (KPI Grid, Split Cards, Mermaid).
Supports direct multi-format graphic export (SVG/PNG via resvg_py) and 1-stop PDF
compilation with built-in caching to optimize turnaround and eliminate command chaining.
"""

import argparse
import base64
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local Cache Directory for Rendered Mermaid SVGs and PNGs
CACHE_DIR = Path.home() / ".cache" / "mermaid"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# STEP 1 & 2: SSOT ARCHETYPE DICTIONARY (7 Canonical Mermaid Models)
# ----------------------------------------------------------------------
ARCHETYPES: Dict[str, Dict[str, str]] = {
    "flowchart": {
        "title": "1. 網路拓撲與服務流向架構 (Flowchart TD)",
        "desc": "展示多層次隔離網路、閘道路由與核心叢集拓撲。",
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
        "desc": "雙軌數據視覺化：條狀圖對比目標折線圖。",
        "card_title": "2. Dual-Track Chart: Volume vs. Target (xychart-beta)",
        "code": """%%{init: {'theme': 'neutral'}}%%
xychart-beta
    title "Quarterly Throughput vs. Performance Target"
    x-axis ["Q1", "Q2", "Q3", "Q4"]
    y-axis "Processed Units" 0 --> 500
    bar [120, 210, 350, 480]
    line [100, 190, 320, 460]""",
    },
    "gantt": {
        "title": "3. 專案里程碑與排程相依 (Gantt Schedule)",
        "desc": "專案階段里程碑、排程相依性與交付甘特圖。",
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
    "timeline": {
        "title": "4. 年度策略規劃與推進節奏 (Timeline)",
        "desc": "季度關鍵轉折點、架構驗證與演練時間軸。",
        "card_title": "4. Milestone Timeline (timeline)",
        "code": """timeline
    title "Annual Strategic Milestone Roadmap"
    Q1 : Baseline Scoping : Initial Assessment
    Q2 : Architecture PoC : Stress & Penetration Test
    Q3 : Multi-Factor Rollout : Compliance Verification
    Q4 : Disaster Recovery Drill : Annual Retrospective""",
    },
    "sequence": {
        "title": "5. API 認證交握與時序調度 (Sequence Diagram)",
        "desc": "用戶端、API Gateway、IAM 認證中心與資料庫交互時序。",
        "card_title": "5. API Interaction & Authentication Handshake (sequenceDiagram)",
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
    "state": {
        "title": "6. 資產生命週期狀態機 (State Diagram v2)",
        "desc": "從資產發掘、評估審查、上線運行至歸檔除役的狀態機。",
        "card_title": "6. Lifecycle & State Machine (stateDiagram-v2)",
        "code": """stateDiagram-v2
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
    Archived --> [*]""",
    },
    "er": {
        "title": "7. 關聯式資料庫與日誌架構 (ER Diagram)",
        "desc": "實體關係模型、主鍵/外鍵結構與稽核日誌綱要。",
        "card_title": "7. Relational Database Schema (erDiagram)",
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


def render_archetype_card(diagram_key: str) -> str:
    """Renders an archetype card HTML block for Markdown preview."""
    info = ARCHETYPES.get(diagram_key)
    if not info:
        return ""
    return f"""<div class="chart-card">
<h4>{info['card_title']}</h4>

```mermaid
{info['code']}
```

</div>"""


def build_template_c(diagram: str = "all") -> str:
    """Builds Template C: Native Mermaid Visual Archetypes."""
    parts = ['<h3 class="doc-section-title">Visual Models & Architecture (Mermaid Archetypes)</h3>\n']
    
    if diagram == "original":
        keys = ["flowchart", "xychart", "gantt", "timeline"]
    elif diagram == "safe":
        keys = ["flowchart", "xychart", "gantt", "timeline", "sequence", "state", "er"]
    elif diagram in ARCHETYPES:
        keys = [diagram]
    else:  # "all"
        keys = list(ARCHETYPES.keys())
        
    for k in keys:
        if k in ARCHETYPES:
            parts.append(render_archetype_card(k))
            parts.append("")
            
    return "\n".join(parts).strip()


def extract_mermaid_code(card_html: str) -> str:
    """Extracts raw Mermaid DSL code from an archetype card."""
    m = re.search(r"```mermaid\s*\n(.*?)\n```", card_html, re.DOTALL)
    return m.group(1).strip() if m else ""


def render_mermaid_to_svg(mermaid_code: str, *, use_cache: bool = True) -> str:
    """
    Renders Mermaid code into clean SVG. Uses local SHA-256 disk caching to
    eliminate redundant HTTP requests and guarantee high performance.
    """
    cache_key = hashlib.sha256(mermaid_code.strip().encode("utf-8")).hexdigest()[:16]
    cache_file = CACHE_DIR / f"{cache_key}.svg"
    
    if use_cache and cache_file.exists():
        try:
            return cache_file.read_text(encoding="utf-8")
        except Exception:
            pass

    encoded = base64.b64encode(mermaid_code.strip().encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/svg/{encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            svg_str = response.read().decode("utf-8")
    except Exception as err:
        raise RuntimeError(f"Failed to fetch SVG from mermaid.ink: {err}") from err

    try:
        cache_file.write_text(svg_str, encoding="utf-8")
    except Exception:
        pass

    return svg_str


def export_diagram_asset(diagram_type: str, output_file: str, *, use_cache: bool = True) -> Path:
    """Exports a specific Mermaid diagram archetype to an SVG or high-res PNG asset file."""
    if diagram_type not in ARCHETYPES:
        raise ValueError(f"Unknown diagram type '{diagram_type}'. Choose from: {list(ARCHETYPES.keys())}")
    
    code = ARCHETYPES[diagram_type]["code"]
    svg_str = render_mermaid_to_svg(code, use_cache=use_cache)
    
    out_path = Path(output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    if out_path.suffix.lower() == ".svg":
        out_path.write_text(svg_str, encoding="utf-8")
        return out_path
    
    # Rasterize via resvg_py
    try:
        import resvg_py
    except ImportError as err:
        raise RuntimeError("resvg_py is required for PNG rendering. Run: pip install resvg_py") from err

    png_bytes = resvg_py.svg_to_bytes(svg_str)
    out_path.write_bytes(png_bytes)
    return out_path


def export_all_diagrams(output_dir: str, keys: Optional[List[str]] = None, *, use_cache: bool = True) -> List[Path]:
    """Batch exports diagrams into output directory concurrently for maximum performance."""
    target_dir = Path(output_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    diagram_keys = keys or list(ARCHETYPES.keys())
    
    def _worker(item):
        idx, key = item
        p_png = target_dir / f"{idx:02d}_{key}.png"
        p_svg = target_dir / f"{idx:02d}_{key}.svg"
        export_diagram_asset(key, str(p_png), use_cache=use_cache)
        export_diagram_asset(key, str(p_svg), use_cache=use_cache)
        return p_png

    items = [(i, k) for i, k in enumerate(diagram_keys, 1) if k in ARCHETYPES]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(items), 6)) as ex:
        results = list(ex.map(_worker, items))
    return results


def compile_pdf_showcase(
    output_pdf: str,
    diagram_keys: Optional[List[str]] = None,
    *,
    title: str = "Mermaid 視覺架構原生渲染全集",
    subtitle: str = "preview_scaffold.py × ReportLab 7 款架構圖整合手冊",
    theme: str = "light",
) -> Path:
    """
    Compiles a comprehensive ReportLab PDF showcase embedding the Mermaid archetypes.
    Single-invocation end-to-end pipeline: exports assets, formats flowables, generates
    multipage PDF with BoundCanvas headers/footers, and validates against verifier.py.
    """
    from PIL import Image as PILImage

    scripts_dir = Path(__file__).parent.resolve()
    sys.path.insert(0, str(scripts_dir))
    
    try:
        from builder import generate_multipage_report, build_section_heading, build_body
    except ImportError as err:
        raise RuntimeError(f"Could not import builder.py from {scripts_dir}: {err}") from err

    keys = diagram_keys or list(ARCHETYPES.keys())
    temp_dir = CACHE_DIR / "render_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    story: List[Any] = [
        build_section_heading("完整 Mermaid 原生視覺模型總覽 (7 Archetypes Showcase)"),
        build_body(
            "本手冊展示由 preview_scaffold.py 直接自原生 Mermaid DSL 語法編譯，"
            "透過向量渲染引擎光柵化為高解析圖檔，並無縫嵌入 ReportLab 流式排版引擎之完整成果。"
            "涵蓋拓撲、產能趨勢、甘特排程、里程時間軸、時序交握、狀態機與實體關係模型。"
        ),
        build_body("排版具備跨頁自動調適、向量無失真光柵化與頁首頁尾動態綁定能力。"),
    ]

    from reportlab.platypus import Image as RLImage, PageBreak, Spacer

    # Max printable dimensions for A4 with margins
    max_w = 460.0
    max_h = 320.0

    for idx, key in enumerate(keys, 1):
        if key not in ARCHETYPES:
            continue
        info = ARCHETYPES[key]
        png_path = temp_dir / f"{idx:02d}_{key}.png"
        export_diagram_asset(key, str(png_path), use_cache=True)

        with PILImage.open(png_path) as im:
            orig_w, orig_h = im.size

        scale = min(max_w / orig_w, max_h / orig_h, 1.0)
        final_w = max(10.0, orig_w * scale)
        final_h = max(10.0, orig_h * scale)

        story.append(build_section_heading(info["title"]))
        story.append(build_body(info["desc"]))
        story.append(Spacer(1, 10))
        story.append(RLImage(str(png_path), width=final_w, height=final_h))
        if idx < len(keys):
            story.append(PageBreak())

    out_pdf_path = Path(output_pdf).resolve()
    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    generate_multipage_report(
        str(out_pdf_path),
        title=title,
        subtitle=subtitle,
        story_elements=story,
        theme=theme,
    )

    # Automatic Verification Gate Check
    try:
        import verifier
        verifier.verify_pdf(str(out_pdf_path), verbose=True)
    except Exception as e:
        print(f"[*] Note: Verification notice: {e}", file=sys.stderr)

    return out_pdf_path


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
    parser = argparse.ArgumentParser(description="Unified Markdown Preview & Mermaid Asset/PDF Pipeline.")
    parser.add_argument("-o", "--output", help="Output Markdown file path (default: stdout)")
    parser.add_argument("-t", "--title", default="Executive Strategy & Performance Dashboard", help="Document Title")
    parser.add_argument("-s", "--subtitle", default="Operational Baseline · Continuous Verification · Automated Workflow", help="Subtitle")
    parser.add_argument("--template", choices=["all", "a", "b", "c"], default="all", help="Templates to include (default: all)")
    parser.add_argument(
        "--diagram",
        choices=["all", "original", "safe"] + list(ARCHETYPES.keys()),
        default="all",
        help="Mermaid diagram archetype filter (default: all)",
    )
    parser.add_argument("--css-only", action="store_true", help="Print only the CSS <style> block")
    parser.add_argument("--export-diagram", choices=list(ARCHETYPES.keys()), help="Export a specific Mermaid archetype as an image asset")
    parser.add_argument("--export-out", help="Target output file for --export-diagram (.svg or .png)")
    parser.add_argument("--export-dir", help="Export all (or filtered) diagram assets directly into target directory")
    parser.add_argument("--compile-pdf", "--export-pdf", dest="compile_pdf", help="Compile diagrams directly into a verified ReportLab PDF")
    parser.add_argument("--no-cache", action="store_true", help="Bypass local disk cache and force remote re-fetch")
    args = parser.parse_args()

    use_cache = not args.no_cache

    # Mode 1: 1-Stop PDF Compilation
    if args.compile_pdf:
        keys = list(ARCHETYPES.keys()) if args.diagram in ["all", "safe", "original"] else [args.diagram]
        print(f"[+] Compiling 1-stop verified PDF with {len(keys)} diagram archetypes to: {args.compile_pdf}")
        pdf_path = compile_pdf_showcase(args.compile_pdf, keys, title=args.title, subtitle=args.subtitle)
        print(f"[+] Done! PDF compiled successfully at: {pdf_path}")
        sys.exit(0)

    # Mode 2: Batch Export Directory
    if args.export_dir:
        keys = list(ARCHETYPES.keys()) if args.diagram in ["all", "safe", "original"] else [args.diagram]
        print(f"[+] Batch exporting {len(keys)} diagram assets into: {args.export_dir}")
        exported = export_all_diagrams(args.export_dir, keys, use_cache=use_cache)
        print(f"[+] Successfully exported {len(exported)} diagram assets into: {args.export_dir}")
        sys.exit(0)

    # Mode 3: Single Diagram Export
    if args.export_diagram:
        if not args.export_out:
            print("[!] Error: --export-out <file.svg|file.png> is required with --export-diagram", file=sys.stderr)
            sys.exit(1)
        saved = export_diagram_asset(args.export_diagram, args.export_out, use_cache=use_cache)
        print(f"[+] Successfully exported diagram asset: {saved}")
        sys.exit(0)

    # Mode 4: Markdown Preview Scaffold Output
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
