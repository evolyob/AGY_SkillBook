"""
Information Asset Threat & Vulnerability Selection Engine.
Pure Python standard library implementation with anti-monotony rotation.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

INFERENCE_RULES = [
    (r"(紙本|手冊|架構圖|表單|簽呈|白板|立牌)", "文件", "紙本合約"),
    (r"(資料庫|DB|Oracle|MySQL|Postgre|SQL)", "軟體", "資料庫"),
    (r"(防火牆|交換機|Switch|Router|AP|Wi-Fi|網路設備)", "硬體", "網路設備"),
    (r"(主機|伺服器|Server|VMware|ESXi)", "硬體", "主機伺服器"),
    (r"(筆電|電腦|PC|MacBook|工作站)", "硬體", "個人電腦"),
    (r"(工程師|廠商|外包|顧問|人員)", "人員", "外部廠商"),
    (r"(電子檔|名冊|清冊|Log|日誌|參數|設定檔|原始碼|備份)", "資料", "業務交易資料"),
    (r"(App|系統|平台|軟體|Office|Web)", "軟體", "應用系統"),
]


def load_parameters(param_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads declarative parameters from JSON data store."""
    p = Path(param_path) if param_path else Path(__file__).resolve().parent.parent / "data" / "parameters.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _infer_category_and_type(data: Dict[str, Any], category: str, asset_type: str, asset_name: str) -> Tuple[str, str]:
    """Infers category and type if omitted, else resolves canonical category."""
    if category and asset_type:
        return category, asset_type
    if asset_type:
        for cat, content in data["categories"].items():
            if asset_type in content["types"]:
                return cat, asset_type
    for pat, cat, atype in INFERENCE_RULES:
        if re.search(pat, asset_name, re.IGNORECASE):
            return category or cat, asset_type or atype
    return category or "軟體", asset_type or "應用系統"


def select_pair(
    data: Dict[str, Any],
    category: str,
    asset_type: str,
    asset_name: str,
    *,
    history: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Selects best-fitting threat and vulnerability pair with anti-monotony rotation."""
    cat, atype = _infer_category_and_type(data, category, asset_type, asset_name)
    pairs = data["categories"][cat]["pairs"]
    hist = history or []

    scored = []
    for p in pairs:
        score = sum(3 for t in p.get("tags", []) if t.lower() in asset_name.lower() or t.lower() in atype.lower())
        penalty = 5 if p["threat"] in hist[-5:] else 0
        scored.append((score - penalty, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0][1] if scored else {"threat": "", "vulnerability": "", "id": ""}
    return {
        "asset_name": asset_name,
        "category": cat,
        "type": atype,
        "threat": best["threat"],
        "vulnerability": best["vulnerability"],
    }


def main():
    """CLI entrypoint for probing or batch matching."""
    if len(sys.argv) < 2:
        print("Usage: python3 matcher.py [--cat <Cat>] [--type <Type>] --name <AssetName>")
        sys.exit(1)

    data = load_parameters()
    cat, atype, name, batch_file = "", "", "", None

    idx = 1
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        if arg in ("--cat", "-c") and idx + 1 < len(sys.argv):
            cat, idx = sys.argv[idx + 1], idx + 2
        elif arg in ("--type", "-t") and idx + 1 < len(sys.argv):
            atype, idx = sys.argv[idx + 1], idx + 2
        elif arg in ("--name", "-n") and idx + 1 < len(sys.argv):
            name, idx = sys.argv[idx + 1], idx + 2
        elif arg in ("--batch", "-b") and idx + 1 < len(sys.argv):
            batch_file, idx = sys.argv[idx + 1], idx + 2
        else:
            idx += 1

    if batch_file:
        items = json.loads(Path(batch_file).read_text(encoding="utf-8"))
        res, hist = [], []
        for it in items:
            out = select_pair(data, it.get("category", it.get("類別", "")), it.get("type", it.get("類型", "")), it.get("name", it.get("資訊資產項目", "")), history=hist)
            hist.append(out["threat"])
            res.append(out)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    out = select_pair(data, cat, atype, name)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
