#!/usr/bin/env python3
"""
PPTX Visual Primitive Builder Module (`pptx_patterns.py`)

Standalone helper module and CLI generator for the 9 Core Declarative Visual Primitives:
1. kpi_row, 2. card_grid, 3. split_row, 4. anchor_card, 5. pipeline_flow,
6. checklist_grid, 7. matrix, 8. table_slide, 9. diagram_slide
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Dynamically resolve layout_engine without modifying its core
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from layout_engine import PPTXLayoutEngine


class PPTXPatterns:
    """High-level builder helper for 9 core presentation primitives."""

    @staticmethod
    def add_kpi_row(engine: PPTXLayoutEngine, title: str, subtitle: str, metrics: List[Dict[str, Any]], height: float = 5.0) -> Any:
        """1. kpi_row: 3-column metric badges with delta indicators."""
        cols = []
        for m in metrics:
            item = {"type": "kpi", "label": m.get("label", ""), "val": m.get("val", ""), "icon": m.get("icon", "gauge")}
            if "chg" in m: item["chg"] = m["chg"]
            if "note" in m: item["note"] = m["note"]
            cols.append(item)
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "cols": cols}])

    @staticmethod
    def add_card_grid(engine: PPTXLayoutEngine, title: str, subtitle: str, cards: List[Dict[str, Any]], weights: Optional[List[float]] = None, height: float = 5.0) -> Any:
        """2. card_grid: 3 or 4 column pillar cards."""
        w = weights if weights is not None else [1.0] * len(cards)
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "weights": w, "cols": cards}])

    @staticmethod
    def add_split_row(engine: PPTXLayoutEngine, title: str, subtitle: str, left_card: Dict[str, Any], right_card: Dict[str, Any], weights: Optional[List[float]] = None, height: float = 5.0) -> Any:
        """3. split_row: 50/50 compare or boundary split."""
        w = weights if weights is not None else [1.0, 1.0]
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "weights": w, "cols": [left_card, right_card]}])

    @staticmethod
    def add_anchor_card(engine: PPTXLayoutEngine, title: str, subtitle: str, anchor_card: Dict[str, Any], sub_cards: List[Dict[str, Any]], anchor_height: float = 2.2, sub_height: float = 2.8, weights: Optional[List[float]] = None) -> Any:
        """4. anchor_card: Upper central anchor + lower multi-column cards."""
        w = weights if weights is not None else [1.0] * len(sub_cards)
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": anchor_height, "cols": [anchor_card]}, {"height": sub_height, "weights": w, "cols": sub_cards}])

    @staticmethod
    def add_pipeline_flow(engine: PPTXLayoutEngine, title: str, subtitle: str, steps: List[Dict[str, Any]], height: float = 5.0) -> Any:
        """5. pipeline_flow: Linear horizontal SOP flow with step arrows."""
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "content": {"type": "flow", "steps": steps}}])

    @staticmethod
    def add_checklist_grid(engine: PPTXLayoutEngine, title: str, subtitle: str, left_gate: Dict[str, Any], right_gate: Dict[str, Any], weights: Optional[List[float]] = None, height: float = 5.0) -> Any:
        """6. checklist_grid: Dual-column verification readiness gates."""
        w = weights if weights is not None else [1.0, 1.0]
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "weights": w, "cols": [left_gate, right_gate]}])

    @staticmethod
    def add_matrix(engine: PPTXLayoutEngine, title: str, subtitle: str, high_impact_cards: List[Dict[str, Any]], low_impact_cards: List[Dict[str, Any]], high_tag: str = "▲ High Impact", low_tag: str = "▼ Low Impact", layer_height: float = 2.4) -> Any:
        """7. matrix: 2x2 strategic quadrant decision grid."""
        w = [1.0] * len(high_impact_cards)
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": layer_height, "section_tag": high_tag, "weights": w, "cols": high_impact_cards}, {"height": layer_height, "section_tag": low_tag, "weights": w, "cols": low_impact_cards}])

    @staticmethod
    def add_table_slide(engine: PPTXLayoutEngine, title: str, subtitle: str, headers: List[str], rows: List[List[Any]], col_weights: Optional[List[float]] = None, zebra: bool = True, height: float = 5.0) -> Any:
        """8. table_slide: Structured two-dimensional data matrix with optional col_weights & zebra striping."""
        tbl: Dict[str, Any] = {"type": "table", "headers": headers, "rows": rows, "zebra": zebra}
        if col_weights: tbl["col_weights"] = col_weights
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "content": tbl}])

    @staticmethod
    def add_diagram_slide(engine: PPTXLayoutEngine, title: str, subtitle: str, image_source: Union[str, Path, bytes], caption: str = "", height: float = 5.2) -> Any:
        """9. diagram_slide: Dedicated high-resolution diagram/vector slot with caption."""
        col: Dict[str, Any] = {"type": "image", "source": str(image_source) if isinstance(image_source, Path) else image_source}
        if caption: col["caption"] = caption
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "cols": [col]}])


def build_demo_deck(theme: str = "dark", output_path: Optional[Path] = None) -> Path:
    """Generate a comprehensive 8-slide demo deck showcasing core primitives."""
    if output_path is None:
        download_dir = Path.home() / "Downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        output_path = download_dir / "pptx_patterns_demo.pptx"

    engine = PPTXLayoutEngine(theme=theme, font="Noto Sans TC")
    p = PPTXPatterns

    # 1. kpi_row
    p.add_kpi_row(engine, "1. KPI Row — Operational Metrics", "Automated Remediation Telemetry", [
        {"label": "Availability", "val": "99.99%", "chg": "▲ +0.5%", "icon": "gauge", "note": "Target: 99.90%"},
        {"label": "MTTR", "val": "4.2m", "chg": "▼ -65%", "icon": "timer", "note": "Baseline: 12.0m"},
        {"label": "Cost Savings", "val": "$2.8M", "chg": "▲ OK", "icon": "coin", "note": "Exceeded by 18%"}
    ])

    # 2. card_grid
    p.add_card_grid(engine, "2. Card Grid — 3-Pillar Framework", "Core Security Operations Pillars", [
        {"title": "SOAR Hub", "tag": "CORE", "icon": "tree-structure", "body": ["• Ingest security telemetry", "• Threat correlation", "• Trigger automated routing"]},
        {"title": "Playbook Automation", "tag": "AUTO", "icon": "gear", "body": ["• Quarantine phishing alerts", "• Dynamic IP blocklist injection", "• Eliminate 80% manual tasks"]},
        {"title": "Incident Response", "tag": "RESP", "icon": "shield", "body": ["• Instant endpoint quarantine", "• Immutable audit trails", "• Meet compliance reporting"]}
    ])

    # 3. split_row
    p.add_split_row(
        engine, "3. Split Row — Boundary Isolation", "Segregating Directives from Payloads",
        {"title": "Mixed Context", "tag": "VULNERABLE", "icon": "alert-triangle", "body": ["• Prompt injection risk", "• Untrusted authority flow", "• High exfiltration surface"]},
        {"title": "Hardened Boundary", "tag": "SECURE", "icon": "shield-check", "body": ["• Strict schema boundary", "• Provenance verification", "• Read-only memory guard"]}
    )

    # 4. anchor_card
    p.add_anchor_card(
        engine, "4. Anchor Card — Central Mandate", "Architectural Baseline & Modular Execution",
        {"title": "Central Security Orchestrator Mandate", "tag": "MANDATE", "icon": "star", "body": ["• All operational workflows must register with central orchestrator."]},
        [
            {"title": "Perimeter Layer", "tag": "NETWORK", "icon": "firewall", "body": ["• Dynamic firewall rules", "• Port hygiene checks"]},
            {"title": "Identity Layer", "tag": "ACCESS", "icon": "lock", "body": ["• Adaptive MFA challenge", "• Zero Trust policies"]}
        ]
    )

    # 5. pipeline_flow
    p.add_pipeline_flow(engine, "5. Pipeline Flow — Incident SOP", "Linear Multi-Phase Progression", [
        {"step": "PHASE 1", "title": "Alert Intake", "icon": "bell", "color": engine.t["p"]},
        {"step": "PHASE 2", "title": "Threat Triage", "icon": "shield-check", "color": engine.t["s"]},
        {"step": "PHASE 3", "title": "Playbook Action", "icon": "rocket-launch", "color": engine.t["a"]},
        {"step": "PHASE 4", "title": "Audit Closure", "icon": "seal-check", "color": engine.t["ok"]}
    ])

    # 6. checklist_grid
    p.add_checklist_grid(
        engine, "6. Checklist Grid — Pre-Deployment Gates", "Multi-Gate High-Availability Verification",
        {"title": "Security Gate", "tag": "BLOCKER", "icon": "shield-check", "body": ["• ✓ TLS 1.3 enforced", "• ✓ Zero high CVEs", "• ✓ Secrets in env vars"]},
        {"title": "Operations Gate", "tag": "PASS", "icon": "gauge", "body": ["• ✓ Unit tests 100% pass", "• ✓ Latency < 50ms", "• ✓ Failover verified"]}
    )

    # 7. matrix
    p.add_matrix(
        engine, "7. Matrix — Strategic Prioritization", "2x2 Impact vs Cost Decision Grid",
        [
            {"title": "P0: Quick Wins", "tag": "LOW COST", "icon": "star", "color": engine.t["ok"], "body": ["• Enforce mandatory MFA", "• Deprecate orphan roles"]},
            {"title": "P1: Strategic Bets", "tag": "HIGH COST", "icon": "key", "color": engine.t["p"], "body": ["• Zero Trust identity fabric", "• Automated data masking"]}
        ],
        [
            {"title": "P2: Routine Tasks", "tag": "LOW COST", "icon": "server", "color": engine.t["s"], "body": ["• Social engineering drills", "• SIEM index rebalancing"]},
            {"title": "P3: Deprecate", "tag": "HIGH COST", "icon": "box", "color": engine.t["alert"], "body": ["• Legacy hardware appliances", "• Monolithic UI rewrite"]}
        ]
    )

    # 8. table_slide
    p.add_table_slide(
        engine, "8. Table Slide — Baseline Matrix", "Security Compliance Verification Status",
        ["Domain", "Standard Requirement", "Status", "Target Due"],
        [
            ["Identity (IAM)", "Mandatory MFA for all admin accounts", "100% Enforced", "2026-Q1"],
            ["Data (DLP)", "AES-256 encryption at rest and in transit", "Compliant", "2026-Q2"],
            ["Vulnerability", "CVSS 9.0+ hotpatch within 48 hours", "Active Monitoring", "2026-Q2"],
            ["Disaster Recovery", "Daily backup with quarterly drill verification", "Passed Verification", "2026-Q3"]
        ],
        col_weights=[1.2, 3.2, 1.6, 1.2],
        zebra=True
    )

    engine.save(str(output_path))
    return output_path


def main():
    parser = argparse.ArgumentParser(description="PPTX Visual Primitive Builder & Demo Generator")
    parser.add_argument("--demo", action="store_true", help="Generate demo presentation showcasing patterns")
    parser.add_argument("--theme", choices=["dark", "light", "yellow"], default="dark", help="Color theme preset")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output .pptx path")
    args = parser.parse_args()

    out_file = Path(args.output) if args.output else None
    result = build_demo_deck(theme=args.theme, output_path=out_file)
    print(f"SUCCESS: Generated pattern presentation at: {result}")


if __name__ == "__main__":
    main()
