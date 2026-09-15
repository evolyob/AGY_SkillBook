"""Information Asset Threat & Vulnerability Selection Engine."""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


def load_parameters(param_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads declarative parameters from JSON data store."""
    target_path = Path(param_path) if param_path else Path(__file__).resolve().parent.parent / "data" / "parameters.json"
    if not target_path.exists():
        target_path = Path(__file__).resolve().parent / "parameters.json"
    return json.loads(target_path.read_text(encoding="utf-8"))


def _infer_category_and_type(
    categories: Dict[str, Any], category: str, asset_type: str, asset_name: str
) -> Tuple[str, str]:
    """Pure core inference: Resolves category and type using tag scoring with head-noun weighting."""
    if category and asset_type:
        valid_types = categories.get(category, {}).get("types", [])
        if asset_type in valid_types:
            return category, asset_type
        clean_type = re.sub(r"[\(（].*?[\)）]", "", asset_type).strip()
        return category, (clean_type if clean_type in valid_types else "")

    if asset_type and not category:
        clean_type = re.sub(r"[\(（].*?[\)）]", "", asset_type).strip()
        for cat_name, cat_data in categories.items():
            if asset_type in cat_data.get("types", []):
                return cat_name, asset_type
            if clean_type in cat_data.get("types", []):
                return cat_name, clean_type
        return "", ""

    clean_name = asset_name.strip().lower().replace(" ", "")
    if not clean_name:
        return (category, categories.get(category, {}).get("default_type", "")) if category else ("", "")

    cat_scores: Dict[str, int] = {}
    best_types: Dict[str, str] = {}

    for cat_name, cat_data in categories.items():
        if category and cat_name != category:
            continue
        max_pair_score = 0
        cat_best_type = cat_data.get("default_type", "")

        for pair in cat_data.get("pairs", []):
            score = 0
            for raw_tag in pair.get("tags", []):
                tag = raw_tag.lower().replace(" ", "")
                if clean_name.endswith(tag):
                    score += 3  # 中文前飾後主：結尾主名詞給予高權重
                elif tag in clean_name:
                    score += 1  # 前置修飾詞給予輔助計分

            if score > max_pair_score:
                max_pair_score = score
                cat_best_type = pair.get("type", cat_best_type)

        if max_pair_score > 0:
            cat_scores[cat_name] = max_pair_score
            best_types[cat_name] = cat_best_type

    if not cat_scores:
        return (category, categories.get(category, {}).get("default_type", "")) if category else ("", "")

    sorted_scores = sorted(cat_scores.items(), key=lambda x: x[1], reverse=True)
    top_cat, top_score = sorted_scores[0]

    # 歧義熔斷：若最高分同分，不隨意猜測，回傳空字串觸發 unresolved
    if len(sorted_scores) > 1 and sorted_scores[1][1] == top_score:
        return ("", "")

    return top_cat, best_types.get(top_cat, "")


def select_pair(
    param_db: Dict[str, Any], category: str, asset_type: str, asset_name: str, *, history: Optional[List[str]] = None
) -> Dict[str, str]:
    """Selects best-fitting threat and vulnerability pair with anti-monotony rotation and break gate."""
    categories = param_db.get("categories", {})
    cat_name, atype = _infer_category_and_type(categories, category, asset_type, asset_name)
    candidate_pairs = categories.get(cat_name, {}).get("pairs", [])

    if not cat_name or not atype or not candidate_pairs:
        return {"asset_name": asset_name, "category": category, "type": asset_type, "pair_id": "", "threat": "", "vulnerability": "", "status": "unresolved"}

    threat_history = history or []
    scored_candidates = []
    clean_name = asset_name.strip().lower().replace(" ", "")

    for pair in candidate_pairs:
        name_hits = 0
        for raw_tag in pair.get("tags", []):
            tag_clean = raw_tag.lower().replace(" ", "")
            if clean_name.endswith(tag_clean):
                name_hits += 2
            elif tag_clean in clean_name:
                name_hits += 1

        type_hits = 1 if pair.get("type", "").lower() == atype.lower() else 0
        penalty = 5 if pair["threat"] in threat_history[-5:] else 0
        scored_candidates.append(((name_hits * 4) + (type_hits * 2) - penalty, pair))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    best_pair = scored_candidates[0][1] if scored_candidates else candidate_pairs[0]

    return {
        "asset_name": asset_name, "category": cat_name, "type": atype,
        "pair_id": best_pair.get("id", ""), "threat": best_pair.get("threat", ""),
        "vulnerability": best_pair.get("vulnerability", ""), "status": "matched",
    }


def output_records(records: List[Dict[str, str]], output_format: str = "json", *, is_batch: bool = False):
    """Outputs matched records in json or csv format."""
    if output_format == "csv":
        fieldnames = ["asset_name", "category", "type", "pair_id", "threat", "vulnerability", "status"]
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    else:
        if len(records) == 1 and not is_batch:
            print(json.dumps(records[0], ensure_ascii=False, indent=2))
        else:
            print(json.dumps(records, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Information Asset Threat & Vulnerability Selection Engine")
    parser.add_argument("--cat", "-c", default="", help="Asset category")
    parser.add_argument("--type", "-t", default="", help="Asset type")
    parser.add_argument("--name", "-n", default="", help="Asset name")
    parser.add_argument("--batch", "-b", help="Batch JSON file path")
    parser.add_argument("--format", "-f", choices=["json", "csv"], default="json", help="Output format (json or csv)")
    args = parser.parse_args()

    param_db = load_parameters()
    if args.batch:
        items = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        matched_records, threat_history = [], []
        for item in items:
            c = item.get("category", item.get("類別", ""))
            t = item.get("type", item.get("類型", ""))
            n = item.get("name", item.get("資訊資產項目", ""))
            record = select_pair(param_db, c, t, n, history=threat_history)
            if record.get("threat"):
                threat_history.append(record["threat"])
            matched_records.append(record)
        output_records(matched_records, args.format, is_batch=True)
        return

    if not args.name:
        parser.print_usage()
        sys.exit(1)

    single_record = [select_pair(param_db, args.cat, args.type, args.name)]
    output_records(single_record, args.format, is_batch=False)


if __name__ == "__main__":
    main()
