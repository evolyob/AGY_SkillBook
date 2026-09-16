"""Information Asset Threat & Vulnerability Selection Engine."""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    from drill_generator import generate_drill_plan, format_as_markdown
except ImportError:
    from .drill_generator import generate_drill_plan, format_as_markdown


def load_parameters(param_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads declarative parameters from JSON data store."""
    target = Path(param_path) if param_path else Path(__file__).resolve().parent.parent / "data" / "parameters.json"
    if not target.exists():
        target = Path(__file__).resolve().parent / "parameters.json"
    return json.loads(target.read_text(encoding="utf-8"))


def _infer_category_and_type(
    categories: Dict[str, Any], category: str, asset_type: str, asset_name: str
) -> Tuple[str, str, List[str]]:
    """Resolves category and type using tag scoring with head-noun weighting."""
    if category and asset_type:
        valid = categories.get(category, {}).get("types", [])
        clean = re.sub(r"[\(（].*?[\)）]", "", asset_type).strip()
        resolved = asset_type if asset_type in valid else (clean if clean in valid else "")
        return category, resolved, []

    if asset_type and not category:
        clean = re.sub(r"[\(（].*?[\)）]", "", asset_type).strip()
        for cat_name, cat_data in categories.items():
            types = cat_data.get("types", [])
            if asset_type in types or clean in types:
                return cat_name, (asset_type if asset_type in types else clean), []
        return "", "", []

    clean_name = asset_name.strip().lower().replace(" ", "")
    if not clean_name:
        default_t = categories.get(category, {}).get("default_type", "") if category else ""
        return category, default_t, []

    cat_scores: Dict[str, int] = {}
    best_types: Dict[str, str] = {}

    for cat_name, cat_data in categories.items():
        if category and cat_name != category:
            continue
        max_score, cat_best = 0, cat_data.get("default_type", "")
        for pair in cat_data.get("pairs", []):
            score = 0
            ptype = pair.get("type", "").lower().replace(" ", "")
            if ptype and clean_name.endswith(ptype):
                score += 4
            elif ptype and ptype in clean_name:
                score += 2

            for raw_tag in pair.get("tags", []):
                tag = raw_tag.lower().replace(" ", "")
                if clean_name.endswith(tag):
                    score += 3
                elif tag in clean_name or clean_name in tag:
                    score += 1

            if score > max_score:
                max_score, cat_best = score, pair.get("type", cat_best)

        if max_score > 0:
            cat_scores[cat_name], best_types[cat_name] = max_score, cat_best

    if not cat_scores:
        default_t = categories.get(category, {}).get("default_type", "") if category else ""
        return category, default_t, []

    sorted_scores = sorted(cat_scores.items(), key=lambda x: x[1], reverse=True)
    top_cat, top_score = sorted_scores[0]

    # Ambiguity break gate: equal top scores trigger unresolved with candidates
    if len(sorted_scores) > 1 and sorted_scores[1][1] == top_score:
        return "", "", [c for c, s in sorted_scores if s == top_score]

    return top_cat, best_types.get(top_cat, ""), []


def select_pair(
    param_db: Dict[str, Any], category: str, asset_type: str, asset_name: str, *, history: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Selects best-fitting threat and vulnerability pair with anti-monotony rotation."""
    categories = param_db.get("categories", {})
    cat_name, atype, candidates = _infer_category_and_type(categories, category, asset_type, asset_name)
    candidate_pairs = categories.get(cat_name, {}).get("pairs", [])

    if not cat_name or not atype or not candidate_pairs:
        res: Dict[str, Any] = {
            "asset_name": asset_name, "category": category, "type": asset_type,
            "pair_id": "", "threat": "", "vulnerability": "", "status": "unresolved"
        }
        if candidates:
            res["candidates"] = candidates
        return res

    threat_history = history or []
    scored = []
    clean_name = asset_name.strip().lower().replace(" ", "")

    for pair in candidate_pairs:
        name_hits = 0
        ptype = pair.get("type", "").lower().replace(" ", "")
        if ptype and (clean_name.endswith(ptype) or ptype in clean_name):
            name_hits += 2

        for raw_tag in pair.get("tags", []):
            tag_clean = raw_tag.lower().replace(" ", "")
            if clean_name.endswith(tag_clean):
                name_hits += 2
            elif tag_clean in clean_name:
                name_hits += 1

        type_hits = 1 if pair.get("type", "").lower() == atype.lower() else 0
        penalty = 5 if pair["threat"] in threat_history[-5:] else 0
        scored.append(((name_hits * 4) + (type_hits * 2) - penalty, pair))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_pair = scored[0][1] if scored else candidate_pairs[0]

    return {
        "asset_name": asset_name, "category": cat_name, "type": atype,
        "pair_id": best_pair.get("id", ""), "threat": best_pair.get("threat", ""),
        "vulnerability": best_pair.get("vulnerability", ""), "status": "matched",
    }


def _attach_drill_if_requested(record: Dict[str, Any], enabled: bool):
    """Generates and attaches DR drill plan to record if drill flag is set."""
    if not enabled or record.get("status") != "matched":
        return
    record["drill_plan"] = generate_drill_plan(
        record["asset_name"], record["category"], record["type"],
        record["threat"], record["vulnerability"]
    )


def _print_batch_drills(records: List[Dict[str, Any]], fmt: str, drill: bool):
    """Outputs markdown drill plans for batch execution when drill flag is set."""
    if fmt != "markdown" or not drill:
        return
    plans = [format_as_markdown(r["drill_plan"]) for r in records if "drill_plan" in r]
    if plans:
        print("\n\n---\n\n" + "\n\n---\n\n".join(plans))


def output_records(records: List[Dict[str, Any]], output_format: str = "json", *, is_batch: bool = False):
    """Outputs matched records in json, csv, or markdown format."""
    if output_format == "csv":
        fieldnames = ["asset_name", "category", "type", "pair_id", "threat", "vulnerability", "status"]
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
        return
    if output_format == "markdown":
        print("| 資產名稱 | 類別 | 類型 | 配對編號 | 威脅 | 弱點 | 狀態 |")
        print("| :--- | :--- | :--- | :---: | :--- | :--- | :---: |")
        for r in records:
            print(f"| {r.get('asset_name', '')} | {r.get('category', '')} | {r.get('type', '')} | {r.get('pair_id', '')} | {r.get('threat', '')} | {r.get('vulnerability', '')} | {r.get('status', '')} |")
        return
    data = records[0] if (len(records) == 1 and not is_batch) else records
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Information Asset Threat & Vulnerability Selection Engine")
    parser.add_argument("--cat", "-c", default="", help="Asset category")
    parser.add_argument("--type", "-t", default="", help="Asset type")
    parser.add_argument("--name", "-n", default="", help="Asset name")
    parser.add_argument("--batch", "-b", help="Batch JSON file path")
    parser.add_argument("--format", "-f", choices=["json", "csv", "markdown"], default="json", help="Output format")
    parser.add_argument("--drill", "-d", action="store_true", help="Generate DR Drill Block A & B plan")
    parser.add_argument("--param-path", help="Custom parameters.json path")
    args = parser.parse_args()

    param_db = load_parameters(args.param_path)
    if args.batch:
        items = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        matched_records, threat_hist = [], []
        for item in items:
            c = item.get("category", item.get("類別", ""))
            t = item.get("type", item.get("類型", ""))
            n = item.get("name", item.get("資訊資產項目", ""))
            rec = select_pair(param_db, c, t, n, history=threat_hist)
            if rec.get("threat"):
                threat_hist.append(rec["threat"])
            _attach_drill_if_requested(rec, args.drill)
            matched_records.append(rec)
        output_records(matched_records, args.format, is_batch=True)
        _print_batch_drills(matched_records, args.format, args.drill)
        return

    if not args.name:
        parser.print_usage()
        sys.exit(1)

    rec = select_pair(param_db, args.cat, args.type, args.name)
    _attach_drill_if_requested(rec, args.drill)
    output_records([rec], args.format, is_batch=False)
    if args.drill and args.format == "markdown" and "drill_plan" in rec:
        print("\n---\n" + format_as_markdown(rec["drill_plan"]))


if __name__ == "__main__":
    main()
