"""Information Asset Threat & Vulnerability Selection Engine."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Tier 1: Domain Entity Lexicon (Ordered: Specific Content -> Generic System)
INFERENCE_RULES = [
    (r"(紙本|手冊|架構圖|表單|簽呈|白板|立牌|合約|正本|副本|公文|用印|簽單|發票|便條紙|便利貼)", "文件", "紙本合約"),
    (r"(卡號|信用卡|PAN|SAD|CVV|Token|代碼化|名冊|清冊|Log|日誌|參數|設定檔|原始碼|備份|個資|身分證|帳務|明細|憑證|金鑰|Key)", "資料", "業務交易資料"),
    (r"(HSM|加密機|硬體安全模組|門禁|感應器|CCTV|監控|UPS|發電機|機櫃|機房|交換機|Switch|Router|AP|Wi-Fi|網路設備|筆電|電腦|PC|MacBook|工作站|POS|刷卡機|EDC|終端|主機|伺服器|Server|儲存設備|硬碟|印表機|事務機)", "硬體", "主機伺服器"),
    (r"(工程師|廠商|外包|顧問|人員|員工|同仁|主管|離職|實習生|維運)", "人員", "員工"),
    (r"(資料庫|DB|Oracle|MySQL|Postgre|SQL|Mongo|Redis)", "軟體", "資料庫"),
    (r"(App|系統|平台|軟體|Office|Web|網頁|API|微服務|Docker|K8s|結帳|Checkout|中台|Core|服務)", "軟體", "應用系統"),
]


def load_parameters(param_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads declarative parameters from JSON data store."""
    target_path = Path(param_path) if param_path else Path(__file__).resolve().parent.parent / "data" / "parameters.json"
    if not target_path.exists():
        target_path = Path(__file__).resolve().parent / "parameters.json"
    return json.loads(target_path.read_text(encoding="utf-8"))


def _infer_category_and_type(param_db: Dict[str, Any], category: str, asset_type: str, asset_name: str) -> Tuple[str, str]:
    """Two-Tier Inference: Rule-based priority followed by cross-category tag voting."""
    if category and asset_type:
        return category, asset_type
    if asset_type:
        for cat_name, content in param_db["categories"].items():
            if asset_type in content["types"]:
                return cat_name, asset_type

    for pattern, cat_name, atype in INFERENCE_RULES:
        if re.search(pattern, asset_name, re.IGNORECASE):
            resolved_cat = category or cat_name
            resolved_type = asset_type or atype
            valid_types = param_db["categories"].get(resolved_cat, {}).get("types", [])
            if resolved_type not in valid_types and valid_types:
                resolved_type = valid_types[0]
            return resolved_cat, resolved_type

    best_cat, max_score = category or "資料", -1
    for cat_name, cat_data in param_db["categories"].items():
        score = sum(1 for p in cat_data["pairs"] for t in p.get("tags", []) if t.lower() in asset_name.lower())
        if score > max_score:
            max_score, best_cat = score, cat_name

    fallback_types = param_db["categories"].get(best_cat, {}).get("types", ["業務交易資料"])
    return best_cat, asset_type or fallback_types[0]


def select_pair(
    param_db: Dict[str, Any],
    category: str,
    asset_type: str,
    asset_name: str,
    *,
    history: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Selects best-fitting threat and vulnerability pair with anti-monotony rotation and relevance guard."""
    cat_name, atype = _infer_category_and_type(param_db, category, asset_type, asset_name)
    pairs = param_db["categories"][cat_name]["pairs"]
    threat_history = history or []

    scored_candidates = []
    for pair in pairs:
        name_hits = sum(1 for tag in pair.get("tags", []) if tag.lower() in asset_name.lower())
        type_hits = sum(1 for tag in pair.get("tags", []) if tag.lower() in atype.lower())
        raw_score = (name_hits * 4) + type_hits
        penalty = 5 if pair["threat"] in threat_history[-5:] else 0
        scored_candidates.append((raw_score - penalty, raw_score, pair))

    scored_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best_pair = (
        pairs[0]
        if (scored_candidates and scored_candidates[0][1] <= 0)
        else (scored_candidates[0][2] if scored_candidates else {"threat": "", "vulnerability": "", "id": ""})
    )

    return {
        "asset_name": asset_name,
        "category": cat_name,
        "type": atype,
        "pair_id": best_pair.get("id", ""),
        "threat": best_pair.get("threat", ""),
        "vulnerability": best_pair.get("vulnerability", ""),
    }


def main():
    parser = argparse.ArgumentParser(description="Information Asset Threat & Vulnerability Selection Engine")
    parser.add_argument("--cat", "-c", default="", help="Asset category")
    parser.add_argument("--type", "-t", default="", help="Asset type")
    parser.add_argument("--name", "-n", default="", help="Asset name")
    parser.add_argument("--batch", "-b", help="Batch JSON file path")
    args = parser.parse_args()

    param_db = load_parameters()
    if args.batch:
        items = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        matched_records, threat_history = [], []
        for item in items:
            record = select_pair(
                param_db,
                item.get("category", item.get("類別", "")),
                item.get("type", item.get("類型", "")),
                item.get("name", item.get("資訊資產項目", "")),
                history=threat_history,
            )
            threat_history.append(record["threat"])
            matched_records.append(record)
        print(json.dumps(matched_records, ensure_ascii=False, indent=2))
        return

    if not args.name:
        parser.print_usage()
        sys.exit(1)

    record = select_pair(param_db, args.cat, args.type, args.name)
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
