#!/usr/bin/env python3
"""Standardized Disaster Recovery Drill Field Generator driven by parameters.json keywords."""

import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

STEPS_SCHEMA = [
    (1, "收到通報", "接獲{name}異常通報，研判與「{threat}」相符，完成內部初報並立案管制編號。"),
    (2, "緊急阻斷", "針對{name}啟動緊急應變阻斷措施，終止異常連線並防止「{threat}」災情擴大。"),
    (3, "隔離保全", "實施受害標的隔離與存取限制，保全揮發性跡證與日誌快照防止損害蔓延。"),
    (4, "受害清查", "調閱{name}稽核日誌與軌跡，分析針對「{vuln}」遭利用狀況與受影響範圍。"),
    (5, "事故判定", "跨部門研商確認事故損害層級，判定是否符合重大資安事故或法定通報要件。"),
    (6, "通報主管機關", "依規定於法定時限內向目的事業主管機關及外部權責單位完成資安通報。"),
    (7, "修補還原", "徹底修補「{vuln}」弱點並自安全備份復原{name}，重設安全驗證組態。"),
    (8, "驗證重啟", "驗證系統完整性與業務功能無虞，正式恢復{name}正常營運服務。"),
]


def load_parameters(param_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads declarative parameters from JSON data store."""
    target = Path(param_path) if param_path else Path(__file__).resolve().parent.parent / "data" / "parameters.json"
    if not target.exists():
        target = Path(__file__).resolve().parent / "parameters.json"
    return json.loads(target.read_text(encoding="utf-8"))


def resolve_asset_keywords(
    param_db: Dict[str, Any], *, pair_id: Optional[str] = None, name: Optional[str] = None,
    cat: Optional[str] = None, atype: Optional[str] = None, threat: Optional[str] = None, vuln: Optional[str] = None
) -> Tuple[str, str, str, str, str]:
    """Extracts canonical keywords from parameters.json by pair_id or raw arguments."""
    if pair_id:
        for cname, cdata in param_db.get("categories", {}).items():
            for p in cdata.get("pairs", []):
                if p.get("id") == pair_id:
                    return name or p.get("tags", [p["type"]])[0], cname, p["type"], p["threat"], p["vulnerability"]
    return name or "核心系統", cat or "軟體", atype or "系統", threat or "遭惡意程式攻擊", vuln or "未及時安裝修補更新"


def generate_drill_plan(
    asset_name: str, category: str, asset_type: str, threat: str, vulnerability: str
) -> Dict[str, Any]:
    """Binds canonical keywords into standard planning fields and execution steps."""
    name, c, t, th, v = asset_name.strip(), category.strip(), asset_type.strip(), threat.strip(), vulnerability.strip()
    kwargs = {"name": name, "category": c, "type": t, "threat": th, "vuln": v}

    planning = {
        "drill_theme": f"【{name}面臨「{th}」之災害復原演練】",
        "target_and_scope": f"模擬{name}（{c}-{t}）因「{v}」遭遇「{th}」之緊急應變與災害復原。",
        "scenario_description": f"模擬{name}因存在「{v}」之安全弱點，遭遇「{th}」，引發異常警報與未授權操作風險，威脅業務正常營運之災害情境。",
        "playbook_flow": "收到通報 ➔ 緊急阻斷 ➔ 隔離保全 ➔ 受害清查 ➔ 事故判定 ➔ 通報主管機關 ➔ 修補還原 ➔ 驗證重啟"
    }

    steps = [
        {"step_no": no, "phase_code": phase, "unit_role": "", "duration": "",
         "procedure": tpl.format(**kwargs)}
        for no, phase, tpl in STEPS_SCHEMA
    ]

    return {"asset_name": name, "category": c, "type": t, "threat": th, "vulnerability": v,
            "planning_fields": planning, "execution_steps": steps}


def format_as_markdown(plan: Dict[str, Any]) -> str:
    """Formats drill plan into readable Markdown tables."""
    p = plan.get("planning_fields", {})
    md = [
        "# 災害復原演練暨處理報告單\n",
        f"**演練主題**：{p.get('drill_theme', '')}\n**資產對象**：{plan['asset_name']} ({plan['category']} - {plan['type']})\n",
        "## 區塊 A：演練規劃表\n| 演練規劃項目 | 規劃內容 |\n| :--- | :--- |",
        f"| **演練目標與範圍** | {p.get('target_and_scope', '')} |",
        f"| **情境說明** | {p.get('scenario_description', '')} |",
        f"| **演練腳本** | {p.get('playbook_flow', '')} |\n",
        "## 區塊 B：演練暨處理執行表\n| 項次 | 演練執行項目 | 負責單位 | 所需時間 | 執行程序 |\n| :-: | :--- | :---: | :---: | :--- |",
    ]
    for s in plan.get("execution_steps", []):
        unit = s.get("unit_role") or "-"
        dur = s.get("duration") or "-"
        md.append(f"| {s['step_no']} | **{s['phase_code']}** | {unit} | {dur} | {s['procedure']} |")
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="DR Drill Field Generator (parameters.json Keyword Binder)")
    parser.add_argument("--pair-id", "-p", help="Lookup pair ID directly from parameters.json (e.g. 軟體_01, 資料_02, 硬體_11)")
    parser.add_argument("--name", "-n", help="Asset name")
    parser.add_argument("--cat", "-c", help="Category")
    parser.add_argument("--type", "-t", help="Type")
    parser.add_argument("--threat", help="Threat")
    parser.add_argument("--vuln", help="Vulnerability")
    parser.add_argument("--high-risk-file", help="Batch JSON file of high-risk items")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    parser.add_argument("--param-path", help="Custom parameters.json path")
    args = parser.parse_args()

    param_db = load_parameters(args.param_path)
    if args.high_risk_file:
        items = json.loads(Path(args.high_risk_file).read_text(encoding="utf-8"))
        plans = []
        for i in items:
            name, c, t, th, v = resolve_asset_keywords(
                param_db, pair_id=i.get("pair_id") or i.get("id"), name=i.get("name") or i.get("asset_name"),
                cat=i.get("category"), atype=i.get("type"), threat=i.get("threat"), vuln=i.get("vulnerability")
            )
            plans.append(generate_drill_plan(name, c, t, th, v))
    else:
        name, c, t, th, v = resolve_asset_keywords(
            param_db, pair_id=args.pair_id, name=args.name,
            cat=args.cat, atype=args.type, threat=args.threat, vuln=args.vuln
        )
        plans = [generate_drill_plan(name, c, t, th, v)]

    if args.format == "markdown":
        print("\n\n---\n\n".join(format_as_markdown(p) for p in plans))
    else:
        print(json.dumps(plans[0] if len(plans) == 1 and not args.high_risk_file else plans, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
