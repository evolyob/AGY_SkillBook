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


def load_pii_parameters(pii_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads declarative PII parameters from JSON data store."""
    target = Path(pii_path) if pii_path else Path(__file__).resolve().parent.parent / "data" / "pii_parameters.json"
    if not target.exists():
        target = Path(__file__).resolve().parent / "pii_parameters.json"
    if not target.exists():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


SPECIAL_PII_KEYWORDS = ["病歷", "醫療", "基因", "性生活", "健檢", "健康檢查", "犯罪", "前科"]


def evaluate_pii_inventory(pii_db: Dict[str, Any], cat: str, atype: str, asset_name: str) -> Dict[str, Any]:
    """Performs natural join between asset category/type and PII parameters."""
    if cat not in ["軟體", "資料", "文件"]:
        return {
            "asset_name": asset_name, "category": cat, "type": atype,
            "is_pii_applicable": False,
            "reason": f"資產「{asset_name}」分類為「{cat}」，非承載個人資料之載體（軟體、資料、文件），無需編製個資盤點表。"
        }

    cat_spec = pii_db.get("categories", {}).get(cat, {})
    clean_name = asset_name.strip()
    has_special_pii = any(k in clean_name for k in SPECIAL_PII_KEYWORDS)

    common_pii = "姓名、電話、地址、Email"
    if cat == "軟體":
        common_pii = "姓名、電話、地址、帳號、消費紀錄"
    elif cat == "資料":
        common_pii = "姓名、身分證字號、金融帳號、交易紀錄"
    elif cat == "文件":
        common_pii = "姓名、身分證字號、簽名、合約內容"

    return {
        "asset_name": asset_name, "category": cat, "type": atype or cat_spec.get("default_type", ""),
        "data_format": cat_spec.get("data_format", ""), "col_h_format": cat_spec.get("col_h_format", ""),
        "default_storage": cat_spec.get("default_storage", ""), "default_disposal": cat_spec.get("default_disposal", ""),
        "has_special_pii": "是" if has_special_pii else "否", "pii_items_candidate": common_pii,
        "controls": cat_spec.get("controls", []), "is_pii_applicable": True
    }


def format_pii_inventory_markdown(records: List[Dict[str, Any]]) -> str:
    """Formats 11-column PII inventory and Controls A~J checklist."""
    out = [f"> [!NOTE]\n> {r.get('reason', '')}" for r in records if not r.get("is_pii_applicable")]
    applicable = [r for r in records if r.get("is_pii_applicable")]
    if applicable:
        out.extend([
            "### 【個人資料資產盤點清冊 (11 欄通用標準版)】\n",
            "| 1. 資產名稱 | 2. 保有依據 | 3. 個資類別 | 4. 特種個資 | 5. 資料形式 | 6. 內部傳送 | 7. 保管方式 | 8. 外部傳送 | 9. 廢棄方式 | 10. 個資數量 | 11. 管控措施 |",
            "| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :---: | :---: |"
        ])
        for r in applicable:
            out.append(f"| {r['asset_name']} | [待業務填寫] | {r['pii_items_candidate']} | **{r['has_special_pii']}** | {r['col_h_format']} | [待業務填寫] | {r['default_storage']} | [待業務填寫] | {r['default_disposal']} | [待業務評定] | 落實 [ ]/10 項 |")
        for r in applicable:
            out.append(f"\n#### 現行安全維護措施查核表 (Controls A~J) - {r['asset_name']} ({r['category']})\n| 編號 | 檢驗控制項目題目 | 實行狀態（預設待覆核） |\n| :---: | :--- | :---: |")
            out.extend([f"| {c['id']} | {c['question']} | [ ] 符合 / [ ] 不符合 |" for c in r.get("controls", [])])
    return "\n".join(out)


def output_pii_records(records: List[Dict[str, Any]], output_format: str = "json", *, is_batch: bool = False):
    """Outputs PII inventory records in json, csv, or markdown format."""
    if output_format == "markdown":
        print(format_pii_inventory_markdown(records))
        return
    if output_format == "csv":
        fieldnames = ["asset_name", "legal_basis", "pii_categories", "has_special_pii", "data_format", "internal_transfer", "storage_method", "external_transfer", "disposal_method", "volume_scale", "controls_summary"]
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            if r.get("is_pii_applicable"):
                writer.writerow({
                    "asset_name": r["asset_name"], "legal_basis": "[待業務填寫]", "pii_categories": r["pii_items_candidate"],
                    "has_special_pii": r["has_special_pii"], "data_format": r["col_h_format"], "internal_transfer": "[待業務填寫]",
                    "storage_method": r["default_storage"], "external_transfer": "[待業務填寫]", "disposal_method": r["default_disposal"],
                    "volume_scale": "[待業務評定]", "controls_summary": "落實 [ ]/10 項"
                })
        return
    data = records[0] if (len(records) == 1 and not is_batch) else records
    print(json.dumps(data, ensure_ascii=False, indent=2))


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

    pii_db = load_pii_parameters()
    for cat_name, cdata in pii_db.get("categories", {}).items():
        if category and cat_name != category:
            continue
        for raw_tag in cdata.get("tags", []):
            tag = raw_tag.lower().replace(" ", "")
            score = 5 if (clean_name == tag or clean_name.endswith(tag)) else (2 if (tag in clean_name or clean_name in tag) else 0)
            if score > cat_scores.get(cat_name, 0):
                cat_scores[cat_name] = score
                best_types[cat_name] = cdata.get("default_type", "")

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


def _attach_drill_if_requested(record: Dict[str, Any], enabled: bool, *, is_pii: bool = False):
    """Generates and attaches DR drill plan to record if drill flag is set."""
    if not enabled or record.get("status") != "matched":
        return
    record["drill_plan"] = generate_drill_plan(
        record["asset_name"], record["category"], record["type"],
        record["threat"], record["vulnerability"], is_pii=is_pii
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
    parser = argparse.ArgumentParser(description="Asset Threat, Vuln & PII Engine")
    parser.add_argument("--cat", "-c", default="", help="Category")
    parser.add_argument("--type", "-t", default="", help="Type")
    parser.add_argument("--name", "-n", default="", help="Asset name")
    parser.add_argument("--batch", "-b", help="Batch JSON file")
    parser.add_argument("--format", "-f", choices=["json", "csv", "markdown"], default="json")
    parser.add_argument("--drill", "-d", action="store_true", help="Generate DR Drill")
    parser.add_argument("--pii", action="store_true", help="PII breach drill mode")
    parser.add_argument("--pii-inventory", action="store_true", help="PII inventory mode")
    parser.add_argument("--param-path", help="Custom parameters.json path")
    parser.add_argument("--pii-param-path", help="Custom pii_parameters.json path")
    args = parser.parse_args()

    param_db = load_parameters(args.param_path)
    raw = json.loads(Path(args.batch).read_text(encoding="utf-8")) if args.batch else ([{"name": args.name, "category": args.cat, "type": args.type}] if args.name else None)
    if not raw:
        parser.print_usage()
        sys.exit(1)

    if args.pii_inventory:
        pii_db = load_pii_parameters(args.pii_param_path)
        pii_recs = []
        for it in raw:
            c, t, n = it.get("category", it.get("類別", "")), it.get("type", it.get("類型", "")), it.get("name", it.get("資訊資產項目", ""))
            r = select_pair(param_db, c, t, n)
            pii_recs.append(evaluate_pii_inventory(pii_db, r["category"], r["type"], r["asset_name"]))
        output_pii_records(pii_recs, args.format, is_batch=bool(args.batch))
        return

    matched, threat_hist = [], []
    for it in raw:
        c, t, n = it.get("category", it.get("類別", "")), it.get("type", it.get("類型", "")), it.get("name", it.get("資訊資產項目", ""))
        r = select_pair(param_db, c, t, n, history=threat_hist)
        if r.get("threat"):
            threat_hist.append(r["threat"])
        _attach_drill_if_requested(r, args.drill, is_pii=args.pii)
        matched.append(r)

    output_records(matched, args.format, is_batch=bool(args.batch))
    if args.drill and args.format == "markdown":
        plans = [format_as_markdown(r["drill_plan"]) for r in matched if "drill_plan" in r]
        if plans:
            print("\n\n---\n\n" + "\n\n---\n\n".join(plans))


if __name__ == "__main__":
    main()
