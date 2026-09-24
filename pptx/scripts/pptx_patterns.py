#!/usr/bin/env python3
"""
PPTX Visual Primitive Builder Module (`pptx_patterns.py`)

Standalone helper module and CLI generator for the 7 Core Declarative Visual Primitives:
1. kpi_row
2. card_grid
3. split_row
4. anchor_card
5. pipeline_flow
6. checklist_grid
7. matrix
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Dynamically resolve layout_engine without modifying its core
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from layout_engine import PPTXLayoutEngine


class PPTXPatterns:
    """High-level builder helper for 7 core presentation primitives."""

    @staticmethod
    def add_kpi_row(
        engine: PPTXLayoutEngine,
        title: str,
        subtitle: str,
        metrics: List[Dict[str, Any]],
        height: float = 5.0
    ) -> Any:
        """1. kpi_row: 3-column metric badges."""
        cols = []
        for m in metrics:
            item = {
                "type": "kpi",
                "label": m.get("label", ""),
                "val": m.get("val", ""),
                "icon": m.get("icon", "gauge")
            }
            if "chg" in m:
                item["chg"] = m["chg"]
            if "note" in m:
                item["note"] = m["note"]
            cols.append(item)
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "cols": cols}])

    @staticmethod
    def add_card_grid(
        engine: PPTXLayoutEngine,
        title: str,
        subtitle: str,
        cards: List[Dict[str, Any]],
        weights: Optional[List[float]] = None,
        height: float = 5.0
    ) -> Any:
        """2. card_grid: 3 or 4 column pillar cards."""
        if weights is None:
            weights = [1.0] * len(cards)
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "weights": weights, "cols": cards}])

    @staticmethod
    def add_split_row(
        engine: PPTXLayoutEngine,
        title: str,
        subtitle: str,
        left_card: Dict[str, Any],
        right_card: Dict[str, Any],
        weights: Optional[List[float]] = None,
        height: float = 5.0
    ) -> Any:
        """3. split_row: 50/50 compare or boundary split."""
        if weights is None:
            weights = [1.0, 1.0]
        return engine.create_slide(title=title, subtitle=subtitle, layers=[{"height": height, "weights": weights, "cols": [left_card, right_card]}])

    @staticmethod
    def add_anchor_card(
        engine: PPTXLayoutEngine,
        title: str,
        subtitle: str,
        anchor_card: Dict[str, Any],
        sub_cards: List[Dict[str, Any]],
        anchor_height: float = 2.2,
        sub_height: float = 2.8,
        weights: Optional[List[float]] = None
    ) -> Any:
        """4. anchor_card: Upper central anchor + lower multi-column cards."""
        if weights is None:
            weights = [1.0] * len(sub_cards)
        return engine.create_slide(
            title=title,
            subtitle=subtitle,
            layers=[
                {"height": anchor_height, "cols": [anchor_card]},
                {"height": sub_height, "weights": weights, "cols": sub_cards}
            ]
        )

    @staticmethod
    def add_pipeline_flow(
        engine: PPTXLayoutEngine,
        title: str,
        subtitle: str,
        steps: List[Dict[str, Any]],
        height: float = 5.0
    ) -> Any:
        """5. pipeline_flow: Linear horizontal SOP flow with step arrows."""
        return engine.create_slide(
            title=title,
            subtitle=subtitle,
            layers=[{"height": height, "content": {"type": "flow", "steps": steps}}]
        )

    @staticmethod
    def add_checklist_grid(
        engine: PPTXLayoutEngine,
        title: str,
        subtitle: str,
        left_gate: Dict[str, Any],
        right_gate: Dict[str, Any],
        weights: Optional[List[float]] = None,
        height: float = 5.0
    ) -> Any:
        """6. checklist_grid: Dual-column verification readiness gates."""
        if weights is None:
            weights = [1.0, 1.0]
        return engine.create_slide(
            title=title,
            subtitle=subtitle,
            layers=[{"height": height, "weights": weights, "cols": [left_gate, right_gate]}]
        )

    @staticmethod
    def add_matrix(
        engine: PPTXLayoutEngine,
        title: str,
        subtitle: str,
        high_impact_cards: List[Dict[str, Any]],
        low_impact_cards: List[Dict[str, Any]],
        high_tag: str = "▲ High Impact",
        low_tag: str = "▼ Low Impact",
        layer_height: float = 2.4
    ) -> Any:
        """7. matrix: 2x2 strategic quadrant decision grid."""
        weights = [1.0] * len(high_impact_cards)
        return engine.create_slide(
            title=title,
            subtitle=subtitle,
            layers=[
                {"height": layer_height, "section_tag": high_tag, "weights": weights, "cols": high_impact_cards},
                {"height": layer_height, "section_tag": low_tag, "weights": weights, "cols": low_impact_cards}
            ]
        )


def build_demo_deck(theme: str = "dark", output_path: Optional[Path] = None) -> Path:
    """Generate a comprehensive 7-slide demo deck showcasing all 7 primitives."""
    if output_path is None:
        download_dir = Path.home() / "Downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        output_path = download_dir / "pptx_7_patterns_demo.pptx"

    engine = PPTXLayoutEngine(theme=theme, font="Noto Sans TC")
    p = PPTXPatterns

    # Slide 1: kpi_row
    p.add_kpi_row(
        engine=engine,
        title="1. KPI Row — Operational Metrics",
        subtitle="Annual Automated Incident Remediation and SLA Telemetry",
        metrics=[
            {"label": "Service Availability", "val": "99.99%", "chg": "▲ +0.5%", "icon": "gauge", "note": "Target: 99.90%"},
            {"label": "Mean Time to Remediate", "val": "4.2m", "chg": "▼ -65%", "icon": "timer", "note": "Baseline: 12.0m"},
            {"label": "Annual Cost Savings", "val": "$2.8M", "chg": "▲ Achieved", "icon": "coin", "note": "Exceeded by 18%"}
        ]
    )

    # Slide 2: card_grid
    p.add_card_grid(
        engine=engine,
        title="2. Card Grid — 3-Pillar Capability Framework",
        subtitle="Core Architecture Pillars of Modern Security Operations Center",
        cards=[
            {
                "title": "Security Orchestration",
                "tag": "CORE",
                "icon": "tree-structure",
                "body": ["• Ingest heterogeneous security feeds", "• Threat intelligence correlation", "• Trigger automated ITSM routing"]
            },
            {
                "title": "Playbook Automation",
                "tag": "AUTO",
                "icon": "gear",
                "body": ["• Block malicious IP perimeter addresses", "• Quarantine phishing emails", "• Eliminate 80% repetitive manual ops"]
            },
            {
                "title": "Incident Response",
                "tag": "RESP",
                "icon": "shield",
                "body": ["• One-click endpoint network isolation", "• Immutable forensic audit trails", "• Meet compliance reporting SLA"]
            }
        ]
    )

    # Slide 3: split_row
    p.add_split_row(
        engine=engine,
        title="3. Split Row — Boundary & Context Isolation",
        subtitle="Segregating Trusted System Directives from Untrusted Payloads",
        left_card={
            "title": "Mixed Context Architecture",
            "tag": "VULNERABLE",
            "icon": "alert-triangle",
            "body": [
                "• Instructions tangled with external inputs",
                "• Indirect prompt injection hijacks flow",
                "• Untrusted content gains implicit authority",
                "• High risk of unmonitored data exfiltration"
            ]
        },
        right_card={
            "title": "Partitioned Context Defense",
            "tag": "HARDENED",
            "icon": "shield-check",
            "body": [
                "• Strict schema separation of directives and data",
                "• Provenance labeling before context injection",
                "• Isolated read-only memory boundary",
                "• Policy gateway verification prior to tool call"
            ]
        }
    )

    # Slide 4: anchor_card
    p.add_anchor_card(
        engine=engine,
        title="4. Anchor Card — Central Mandate Architecture",
        subtitle="Hierarchical Architectural Baseline with Modular Execution Sub-Domains",
        anchor_card={
            "title": "Central SOAR Automation Mandate",
            "tag": "CORE MANDATE",
            "icon": "star",
            "body": ["• All security workflows must register with central orchestrator for audit compliance."]
        },
        sub_cards=[
            {
                "title": "Network & Firewall Layer",
                "tag": "PERIMETER",
                "icon": "firewall",
                "body": ["• Dynamic IP blocklist injection", "• Automated port hygiene enforcement"]
            },
            {
                "title": "Identity & Endpoint Layer",
                "tag": "ACCESS",
                "icon": "lock",
                "body": ["• Risk-based MFA challenge routing", "• Instant endpoint quarantine API"]
            }
        ]
    )

    # Slide 5: pipeline_flow
    p.add_pipeline_flow(
        engine=engine,
        title="5. Pipeline Flow — Incident Remediation SOP",
        subtitle="Linear Multi-Phase Progression from Intake to Decommission",
        steps=[
            {"step": "PHASE 1", "title": "Alert Intake", "icon": "bell", "color": engine.t["p"]},
            {"step": "PHASE 2", "title": "Threat Triage", "icon": "shield-check", "color": engine.t["s"]},
            {"step": "PHASE 3", "title": "Playbook Action", "icon": "rocket-launch", "color": engine.t["a"]},
            {"step": "PHASE 4", "title": "Audit Closure", "icon": "seal-check", "color": engine.t["ok"]}
        ]
    )

    # Slide 6: checklist_grid
    p.add_checklist_grid(
        engine=engine,
        title="6. Checklist Grid — Pre-Deployment Gates",
        subtitle="Multi-Gate Compliance and Operational High-Availability Verification",
        left_gate={
            "title": "Security & Compliance Gate",
            "tag": "BLOCKER",
            "icon": "shield-check",
            "body": [
                "• ✓ Communications enforced on TLS 1.3",
                "• ✓ Static code scan zero high/critical CVEs",
                "• ✓ API tokens injected strictly via env vars",
                "• ✓ Audit logs 3-year immutable retention"
            ]
        },
        right_gate={
            "title": "Operations & SRE Gate",
            "tag": "PASS",
            "icon": "gauge",
            "body": [
                "• ✓ Deterministic unit test suite passes 100%",
                "• ✓ Peak latency sustained under 50ms",
                "• ✓ Active-passive failover zero data loss",
                "• ✓ Production on-call monitoring connected"
            ]
        }
    )

    # Slide 7: matrix
    p.add_matrix(
        engine=engine,
        title="7. Matrix — Strategic Prioritization Quadrants",
        subtitle="2x2 Categorization Across Impact and Implementation Cost",
        high_impact_cards=[
            {
                "title": "P0: Quick Wins",
                "tag": "LOW COST",
                "color": engine.t["ok"],
                "body": ["• Enforce mandatory MFA for all staff", "• Deprecate orphan dormant IAM roles"]
            },
            {
                "title": "P1: Strategic Bets",
                "tag": "HIGH COST",
                "color": engine.t["p"],
                "body": ["• Enterprise Zero Trust identity fabric", "• Real-time automated data masking"]
            }
        ],
        low_impact_cards=[
            {
                "title": "P2: Routine Tasks",
                "tag": "LOW COST",
                "color": engine.t["s"],
                "body": ["• Quarterly social engineering drills", "• SIEM cold storage index rebalancing"]
            },
            {
                "title": "P3: Deprecate",
                "tag": "HIGH COST",
                "color": engine.t["alert"],
                "body": ["• Custom on-premise hardware appliances", "• Legacy monolithic dashboard rewrite"]
            }
        ]
    )

    engine.save(str(output_path))
    return output_path


def main():
    parser = argparse.ArgumentParser(description="PPTX Visual Primitive Builder & Demo Generator")
    parser.add_argument("--demo", action="store_true", help="Generate 7-slide demo presentation")
    parser.add_argument("--theme", choices=["dark", "light", "yellow"], default="dark", help="Color theme preset")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output .pptx path")
    args = parser.parse_args()

    out_file = Path(args.output) if args.output else None
    result = build_demo_deck(theme=args.theme, output_path=out_file)
    print(f"SUCCESS: Generated 7-pattern presentation at: {result}")


if __name__ == "__main__":
    main()
