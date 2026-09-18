#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composable Markdown Visual Preview & Mermaid Asset Scaffolder (preview_scaffold.py)
Generates modular preview files with dynamic Lego blocks (KPI, SOP Pipeline, 2x2 Matrix, Charts).
Exports single-diagram SVG/PNG assets with zero hardcoding, strictly aligned with pdf_themes.json.
"""

import argparse
import base64
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict


def clean_text(text: str) -> str:
    """Escapes special characters in dynamic markup to ensure XSS & template hygiene."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def load_data_asset(filename: str) -> Dict[str, Any]:
    """Loads static JSON asset from skill directory with graceful fallback."""
    base = Path(__file__).resolve().parent
    for target in [base.parent / "data" / filename, base / filename]:
        if target.exists():
            try:
                with open(target, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    return {}


_THEME_CFG = load_data_asset("pdf_themes.json")
_ARCHETYPE_CFG = load_data_asset("preview_archetypes.json")

ARCHETYPES: Dict[str, Dict[str, str]] = _ARCHETYPE_CFG.get("archetypes", {})
BLOCK_TEMPLATES: Dict[str, str] = _ARCHETYPE_CFG.get("templates", {})


def get_theme_directive(theme_name: str = "light") -> str:
    """Derives dynamic Mermaid %%{init}%% directive directly from pdf_themes.json SSOT."""
    themes = _THEME_CFG.get("themes", {})
    th = themes.get(theme_name, themes.get("light", {}))
    p, s, txt, card_bg = th.get("p", "#2B5C8F"), th.get("s", "#007A92"), th.get("txt", "#0B0F19"), th.get("card_bg", "#F8FAFC")
    return (
        f"%%{{init: {{'theme': 'base', 'themeVariables': {{"
        f"'primaryColor': '{card_bg}', 'primaryTextColor': '{txt}', 'primaryBorderColor': '{p}', "
        f"'lineColor': '{s}', 'secondaryColor': '{card_bg}', 'tertiaryColor': '{card_bg}', "
        f"'mainBkg': '{card_bg}', 'nodeBorder': '{p}', 'clusterBkg': '{card_bg}', 'titleColor': '{p}'"
        f"}}}}}}%%"
    )


def generate_css_block(theme_name: str = "light") -> str:
    """Generates canonical embedded <style> block supporting all building block grids."""
    themes = _THEME_CFG.get("themes", {})
    th = themes.get(theme_name, themes.get("light", {}))
    bg, card, border, txt, muted = th.get("bg", "#FFFFFF"), th.get("card_bg", "#F8FAFC"), th.get("border", "#CBD5E1"), th.get("txt", "#0B0F19"), th.get("muted", "#64748B")
    p, s, alert, ok = th.get("p", "#2B5C8F"), th.get("s", "#007A92"), th.get("alert", "#E95119"), th.get("ok", "#10B981")

    return f"""<style>
:root {{
  --surface-base: {bg}; --surface-card: {card}; --border-subtle: {border}; --text-main: {txt};
  --text-muted: {muted}; --brand-primary: {p}; --brand-accent: {s}; --kpi-bg: {card};
  --color-alert: {alert}; --color-ok: {ok}; --radius-sm: 6px; --radius-md: 10px;
}}
.doc-header {{ margin-bottom: 1.5rem; border-bottom: 2px solid var(--border-subtle); padding-bottom: 0.8rem; }}
.doc-header h1 {{ margin: 0 0 0.3rem 0; color: var(--brand-primary); font-size: 1.85rem; }}
.doc-header .doc-subtitle {{ color: var(--text-muted); font-size: 0.95rem; margin: 0; }}
.doc-section-title {{ display: flex; align-items: center; gap: 8px; margin: 2rem 0 1rem 0; padding-left: 10px; border-left: 4px solid var(--brand-accent); color: var(--brand-primary); font-size: 1.25rem; font-weight: 700; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin: 1.2rem 0 1.8rem 0; }}
.kpi-card {{ background: var(--kpi-bg); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 0.85rem 0.6rem; text-align: center; }}
.kpi-val {{ font-size: 1.45rem; font-weight: 800; color: var(--brand-primary); line-height: 1.2; }}
.kpi-label {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 4px; }}
.pipeline-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 1.2rem 0 1.8rem 0; }}
.pipeline-step {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1rem 1.1rem; }}
.step-num {{ display: inline-block; background: var(--brand-primary); color: #FFFFFF; font-size: 0.75rem; font-weight: 700; border-radius: 4px; padding: 2px 7px; margin-bottom: 6px; }}
.step-title {{ font-size: 0.95rem; font-weight: 700; color: var(--text-main); margin-bottom: 4px; }}
.step-desc {{ font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; margin: 0; }}
.matrix-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin: 1.2rem 0 1.8rem 0; }}
.matrix-card {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1.1rem 1.3rem; }}
.matrix-tag {{ display: inline-block; font-size: 0.75rem; font-weight: 700; color: var(--brand-accent); background: rgba(0, 122, 146, 0.08); padding: 2px 8px; border-radius: 4px; margin-bottom: 6px; }}
.matrix-card h4 {{ margin: 0 0 0.5rem 0; color: var(--brand-primary); font-size: 1.05rem; }}
.matrix-card ul {{ margin: 0; padding-left: 1.2rem; font-size: 0.85rem; color: var(--text-main); line-height: 1.6; }}
.action-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin: 1.2rem 0 1.8rem 0; }}
.action-card {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1.1rem 1.3rem; }}
.action-card.as-is {{ border-top: 4px solid var(--color-alert); }}
.action-card.to-be {{ border-top: 4px solid var(--color-ok); }}
.action-card h4 {{ margin: 0 0 0.6rem 0; font-size: 1.05rem; }}
.action-card.as-is h4 {{ color: var(--color-alert); }}
.action-card.to-be h4 {{ color: var(--color-ok); }}
.action-card ul {{ margin: 0; padding-left: 1.2rem; font-size: 0.85rem; color: var(--text-main); line-height: 1.6; }}
.table-wrap {{ overflow-x: auto; margin: 1.2rem 0 1.8rem 0; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); }}
.preview-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }}
.preview-table th {{ background: var(--brand-primary); color: #FFF; padding: 8px 12px; font-weight: 700; }}
.preview-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border-subtle); color: var(--text-main); }}
.preview-table tr:nth-child(even) td {{ background: var(--surface-card); }}
.checklist-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin: 1.2rem 0 1.8rem 0; }}
.check-item {{ display: flex; align-items: flex-start; gap: 10px; background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 0.85rem 1rem; }}
.check-badge {{ background: var(--brand-accent); color: #FFF; border-radius: 50%; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; }}
.check-text {{ font-size: 0.85rem; color: var(--text-main); line-height: 1.45; }}
.chart-card {{ background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1rem; overflow-x: auto; margin-bottom: 1.2rem; }}
.chart-card h4 {{ margin: 0 0 0.8rem 0; color: var(--brand-primary); font-size: 1.05rem; }}
</style>"""


def build_charts_block(diagram: str = "all", theme_name: str = "light") -> str:
    """Builds Mermaid charts container block with injected theme directives."""
    parts = ['<h3 class="doc-section-title">Visual Topologies & Architecture Models (Mermaid Archetypes)</h3>\n']
    keys = [diagram] if diagram in ARCHETYPES else list(ARCHETYPES.keys())
    directive = get_theme_directive(theme_name)
    for k in keys:
        if k in ARCHETYPES:
            info = ARCHETYPES[k]
            card = f'<div class="chart-card">\n<h4>{clean_text(info["title"])}</h4>\n\n```mermaid\n{directive}\n{info["code"]}\n```\n\n</div>\n'
            parts.append(card)
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
    
    svg_str = render_mermaid_to_svg(ARCHETYPES[diagram_type]["code"], theme_name=theme_name)
    out_path = Path(output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    if out_path.suffix.lower() == ".svg":
        out_path.write_text(svg_str, encoding="utf-8")
        return out_path
    
    import resvg_py
    out_path.write_bytes(resvg_py.svg_to_bytes(svg_str))
    return out_path


def generate_scaffold(
    title: str = "Executive Strategy & Performance Dashboard",
    subtitle: str = "Operational Baseline | Continuous Verification | Automated Workflow",
    templates: str = "all",
    diagram: str = "all",
    theme: str = "light",
) -> str:
    """Combines CSS block with selected Lego blocks."""
    safe_t, safe_s = clean_text(title), clean_text(subtitle)
    header = f'<div class="doc-header">\n  <h1>{safe_t}</h1>\n  <p class="doc-subtitle">{safe_s}</p>\n</div>'
    parts = [generate_css_block(theme_name=theme), "", header, ""]

    tokens = [t.strip().lower() for t in templates.split(",") if t.strip()]
    canonical_blocks = ["kpi", "action_board", "matrix", "table", "checklist", "pipeline", "charts"]
    selected = canonical_blocks if "all" in tokens else tokens

    for b in selected:
        if b in BLOCK_TEMPLATES:
            parts.extend([BLOCK_TEMPLATES[b], ""])
        elif b in ["charts", "chart"]:
            parts.extend([build_charts_block(diagram=diagram, theme_name=theme), ""])

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Composable Markdown Preview & Mermaid Asset Scaffolder")
    parser.add_argument("-o", "--output", help="Output Markdown file path (default: stdout)")
    parser.add_argument("-t", "--title", default="Executive Strategy & Performance Dashboard", help="Document Title")
    parser.add_argument("-s", "--subtitle", default="Operational Baseline | Continuous Verification | Automated Workflow", help="Subtitle")
    parser.add_argument(
        "--template",
        default="all",
        help="Composable Lego blocks: kpi, action_board, matrix, table, checklist, pipeline, charts, or all",
    )
    parser.add_argument(
        "--diagram",
        choices=["all"] + list(ARCHETYPES.keys()),
        default="all",
        help="Mermaid diagram filter (default: all)",
    )
    parser.add_argument("--theme", default="light", help="Theme key from pdf_themes.json (default: light)")
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
        content = generate_css_block(theme_name=args.theme)
    else:
        content = generate_scaffold(
            title=args.title,
            subtitle=args.subtitle,
            templates=args.template,
            diagram=args.diagram,
            theme=args.theme,
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
