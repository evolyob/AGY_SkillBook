"""Information Asset Threat & Vulnerability Selection Engine."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

INFERENCE_RULES = [
    (r"(紙本|手冊|架構圖|表單|簽呈|白板|立牌|合約|正本|副本|公文|用印|簽單|發票|便條紙|便利貼)", "文件", "紙本合約"),
    (r"(卡號|信用卡|Token|代碼化|名冊|清冊|Log|日誌|參數|設定檔|原始碼|備份|個資|身分證|帳務|明細|金流|憑證|金鑰|Key)", "資料", "業務交易資料"),
    (r"(HSM|加密機|硬體安全模組|門禁|感應器|CCTV|監控|UPS|發電機|機櫃|機房|交換機|Switch|Router|AP|Wi-Fi|網路設備|筆電|電腦|PC|MacBook|工作站|POS|刷卡機|EDC|終端|主機|伺服器|Server|儲存設備|硬碟|印表機|事務機)", "硬體", "主機伺服器"),
    (r"(工程師|廠商|外包|顧問|人員|員工|同仁|主管|組長|營運長|離職|實習生|維運|業務|客服)", "人員", "員工"),
    (r"(資料庫|DB|Oracle|MySQL|Postgre|SQL|Mongo|Redis)", "軟體", "資料庫"),
    (r"(App|系統|平台|軟體|Office|Web|網頁|API|微服務|Docker|K8s|結帳|Checkout|中台|Core|服務)", "軟體", "應用系統"),
]


def load_parameters(param_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads declarative parameters from JSON data store."""
    target_path = Path(param_path) if param_path else Path(__file__).resolve().parent.parent / "data" / "parameters.json"
    if not target_path.exists():
        target_path = Path(__file__).resolve().parent / "parameters.json"
    return json.loads(target_path.read_text(encoding="utf-8"))


def _infer_category_and_type(
    categories: Dict[str, Any], category: str, asset_type: str, asset_name: str
) -> Tuple[str, str]:
    """Pure core inference: Resolves category and type using hierarchical guard clauses."""
    if category and asset_type:
        valid_types = categories.get(category, {}).get("types", [])
        if asset_type in valid_types:
            return category, asset_type
        clean_type = re.sub(r"[\(（].*?[\)）]", "", asset_type).strip()
        if clean_type in valid_types:
            return category, clean_type
        return category, ""

    if asset_type and not category:
        clean_type = re.sub(r"[\(（].*?[\)）]", "", asset_type).strip()
        for cat_name, cat_data in categories.items():
            if asset_type in cat_data.get("types", []):
                return cat_name, asset_type
            if clean_type in cat_data.get("types", []):
                return cat_name, clean_type
        return "", ""

    if category:
        cat_data = categories.get(category, {})
        best_type, max_hits = None, 0
        for pair in cat_data.get("pairs", []):
            hits = sum(1 for tag in pair.get("tags", []) if tag.lower() in asset_name.lower())
            if hits > max_hits:
                max_hits, best_type = hits, pair.get("type")
        return category, (best_type if max_hits > 0 else cat_data.get("default_type", ""))

    for pattern, cat_name, atype in INFERENCE_RULES:
        if re.search(pattern, asset_name, re.IGNORECASE):
            valid_types = categories.get(cat_name, {}).get("types", [])
            return cat_name, atype if atype in valid_types else categories.get(cat_name, {}).get("default_type", atype)

    best_cat, best_type, max_score = "", "", 0
    for cat_name, cat_data in categories.items():
        for pair in cat_data.get("pairs", []):
            hits = sum(1 for tag in pair.get("tags", []) if tag.lower() in asset_name.lower())
            if hits > max_score:
                max_score, best_cat, best_type = hits, cat_name, pair.get("type", "")

    if max_score <= 0 or not best_cat:
        return "", ""
    return best_cat, best_type or categories[best_cat].get("default_type", "")


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
    for pair in candidate_pairs:
        name_hits = sum(1 for tag in pair.get("tags", []) if tag.lower() in asset_name.lower())
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
            c, t, n = item.get("category", item.get("類別", "")), item.get("type", item.get("類型", "")), item.get("name", item.get("資訊資產項目", ""))
            record = select_pair(param_db, c, t, n, history=threat_history)
            if record.get("threat"):
                threat_history.append(record["threat"])
            matched_records.append(record)
        print(json.dumps(matched_records, ensure_ascii=False, indent=2))
        return

    if not args.name:
        parser.print_usage()
        sys.exit(1)

    print(json.dumps(select_pair(param_db, args.cat, args.type, args.name), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
