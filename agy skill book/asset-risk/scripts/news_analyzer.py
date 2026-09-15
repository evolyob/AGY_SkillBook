#!/usr/bin/env python3
"""Cybersecurity News Threat & Vulnerability Matcher via Inverted Index (SKILL_DATA_SPEC compliant)."""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_parameters(param_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads declarative parameters from JSON data store."""
    target = Path(param_path) if param_path else Path(__file__).resolve().parent.parent / "data" / "parameters.json"
    if not target.exists():
        target = Path(__file__).resolve().parent / "parameters.json"
    return json.loads(target.read_text(encoding="utf-8"))


def build_tag_index(param_db: Dict[str, Any]):
    """Auto-builds in-memory inverted index on tags for N > 20 records (SKILL_DATA_SPEC.md)."""
    records = []
    tag_index: Dict[str, List[Dict[str, Any]]] = {}
    for cat_name, cat_data in param_db.get("categories", {}).items():
        for pair in cat_data.get("pairs", []):
            rec = {**pair, "category": cat_name}
            records.append(rec)
            for tag in rec.get("tags", []):
                tag_index.setdefault(tag.strip().lower(), []).append(rec)
    return records, tag_index


def analyze_news(text: str, param_db: Dict[str, Any], *, top_k: int = 3) -> Dict[str, Any]:
    """Matches news text against inverted tag index and canonical pairs to yield top-k results."""
    if not text or not text.strip():
        return {"analyzed_text_snippet": "", "total_evaluated": 0, "matches": []}

    lower_text = text.strip().lower()
    records, tag_index = build_tag_index(param_db)
    scores: Counter = Counter()
    hits: Dict[str, List[str]] = defaultdict(list)

    # 1. Inverted tag index matching
    for tag, recs in tag_index.items():
        if tag in lower_text:
            weight = 3 if len(tag) >= 4 else 1
            for r in recs:
                scores[r["id"]] += weight
                if tag not in hits[r["id"]]:
                    hits[r["id"]].append(tag)

    # 2. Asset type and canonical keywords
    for r in records:
        pid = r["id"]
        if r["type"].lower() in lower_text:
            scores[pid] += 2
            hits[pid].append(r["type"])
        # Direct threat/vuln keyword indicators
        for kw in ["釣魚", "勒索", "mfa", "多因子", "未修補", "注入", "個資", "外洩", "合約", "usb", "機房", "門禁", "廠商"]:
            if kw in lower_text and (kw in r["threat"].lower() or kw in r["vulnerability"].lower()):
                scores[pid] += 3
                if kw not in hits[pid]:
                    hits[pid].append(kw)

    matches = []
    for rank, (pid, score) in enumerate(scores.most_common(top_k), 1):
        rec = next(x for x in records if x["id"] == pid)
        h = hits[pid]
        confidence = "高 (High)" if score >= 6 else ("中 (Medium)" if score >= 3 else "低 (Low)")
        matches.append({
            "rank": rank, "pair_id": pid, "category": rec["category"], "type": rec["type"],
            "threat": rec["threat"], "vulnerability": rec["vulnerability"], "confidence": confidence,
            "score": score, "matched_keywords": h[:6],
            "rationale": f"命中特徵【{', '.join(h[:4])}】，高度符合【{rec['category']}-{rec['type']}】標準樣態。"
        })

    return {
        "analyzed_text_snippet": text.strip()[:100] + ("..." if len(text.strip()) > 100 else ""),
        "total_evaluated": len(records), "matches": matches
    }


def main():
    parser = argparse.ArgumentParser(description="Cybersecurity News Threat/Vuln Matcher")
    parser.add_argument("--text", "-t", help="News text")
    parser.add_argument("--file", "-f", help="News file path")
    parser.add_argument("--top-k", "-k", type=int, default=3, help="Top K matches")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    parser.add_argument("--drill", action="store_true", help="Generate IT4-21 drill scenario for top match")
    parser.add_argument("--param-path", help="Custom parameters.json path")
    args = parser.parse_args()

    raw_text = args.text or (Path(args.file).read_text(encoding="utf-8") if args.file else (sys.stdin.read() if not sys.stdin.isatty() else ""))
    if not raw_text.strip():
        parser.print_usage()
        sys.exit(1)

    param_db = load_parameters(args.param_path)
    result = analyze_news(raw_text, param_db, top_k=args.top_k)

    drill_scenario = None
    if args.drill and result.get("matches"):
        top = result["matches"][0]
        from drill_generator import generate_drill_plan
        drill_scenario = generate_drill_plan(f"受害{top['type']}", top["category"], top["type"], top["threat"], top["vulnerability"])
        result["generated_drill_scenario"] = drill_scenario

    if args.format == "markdown":
        lines = [f"# 資安事件威脅弱點分析報告\n\n**分析摘要**：`{result.get('analyzed_text_snippet')}`\n",
                 "| 排名 | 信心度 | 資產類別與類型 | 對應標準威脅 | 對應標準弱點 | 命中特徵 |",
                 "| :-: | :-: | :--- | :--- | :--- | :--- |"]
        for m in result.get("matches", []):
            lines.append(f"| #{m['rank']} | {m['confidence']} | {m['category']}-{m['type']} | {m['threat']} | {m['vulnerability']} | {', '.join(m['matched_keywords'])} |")
        if drill_scenario:
            from drill_generator import format_as_markdown
            lines.extend(["\n---\n", format_as_markdown(drill_scenario)])
        print("\n".join(lines))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
