#!/usr/bin/env python3
"""
Resilient Vulnerability Intelligence Client (v2.0)
Dual-Engine Fallback Architecture:
- Primary Engine: ENISA European Union Vulnerability Database (EUVD) with EPSS & CVSS
- Fallback Engine: Google OSV.dev (Global Anycast CDN) for high availability and zero single-point-of-failure.
Pure Python Standard Library (Zero Dependencies).
"""

import json
import argparse
import re
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional

EUVD_API_BASE = "https://euvdservices.enisa.europa.eu/api"
OSV_API_BASE = "https://api.osv.dev/v1/vulns"


def fetch_from_osv(cve_or_id: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Fallback Engine: Google OSV.dev
    High availability Anycast CDN API providing Open Source Vulnerability and CVE metadata.
    """
    target = cve_or_id.strip().upper()
    url = f"{OSV_API_BASE}/{urllib.parse.quote(target)}"
    headers = {
        "User-Agent": "SecIntel-Resilient/2.0 (+https://osv.dev)",
        "Accept": "application/json"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                if not data or not data.get("id"):
                    return None

                # Extract CVSS score
                cvss_score = "參見細節"
                cvss_ver = "N/A"
                for sev in data.get("severity", []):
                    if sev.get("type") in ("CVSS_V3", "CVSS_V4", "CVSS_V2"):
                        cvss_ver = sev.get("type").replace("CVSS_", "")
                        m = re.search(r'CVSS:[0-9.]+/.*?/([0-9.]+)', sev.get("score", ""))
                        if m:
                            cvss_score = m.group(1)
                        else:
                            cvss_score = sev.get("score", "")

                # Extract affected products
                products = []
                for aff in data.get("affected", []):
                    pkg = aff.get("package", {})
                    p_name = pkg.get("name") or aff.get("database_specific", {}).get("cpe", [""])[0]
                    if p_name:
                        products.append(p_name)

                aliases = data.get("aliases", [])
                alias_str = "\n".join(aliases)

                return {
                    "source": "Google OSV.dev (Fallback CDN)",
                    "id": data.get("id", target),
                    "aliases": alias_str,
                    "description": data.get("details") or data.get("summary") or "無詳細敘述",
                    "datePublished": data.get("published", "N/A"),
                    "dateUpdated": data.get("modified", "N/A"),
                    "baseScore": cvss_score,
                    "baseScoreVersion": cvss_ver,
                    "baseScoreVector": "N/A",
                    "epss": "N/A (OSV.dev 備援模式)",
                    "assigner": data.get("database_specific", {}).get("cna_assigner", "OSV.dev"),
                    "products": products[:3]
                }
    except Exception:
        return None


def query_euvd_by_id(cve_or_euvd_id: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Query vulnerability by CVE or EUVD ID with automatic Google OSV.dev fallback.
    """
    target = cve_or_euvd_id.strip().upper()

    # 1. Try Primary Engine: ENISA EUVD
    url = f"{EUVD_API_BASE}/enisaid?id={urllib.parse.quote(target)}"
    headers = {"User-Agent": "SecIntel-Resilient/2.0 (+https://euvd.enisa.europa.eu)", "Accept": "application/json"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                if data and not data.get("error"):
                    data["source"] = "ENISA EUVD (Primary)"
                    return data
    except Exception:
        pass  # Trigger resilient fallback

    # 2. Try Fallback Engine: Google OSV.dev
    osv_data = fetch_from_osv(target, timeout=timeout)
    if osv_data:
        return osv_data

    return {"error": f"雙引擎查詢皆無此漏洞紀錄 (ENISA EUVD & Google OSV.dev): '{target}'"}


def query_euvd_search(
    text: str,
    size: int = 5,
    page: int = 0,
    from_score: Optional[float] = None,
    from_epss: Optional[float] = None,
    timeout: int = 6
) -> Dict[str, Any]:
    """
    Search EUVD vulnerability records with fallback to direct OSV lookup if query is a CVE ID.
    """
    clean_text = text.strip()
    if re.fullmatch(r'(?:CVE|EUVD)-\d{4}-\d+', clean_text, re.I):
        single_result = query_euvd_by_id(clean_text, timeout=timeout)
        if "error" in single_result:
            return single_result
        return {"items": [single_result], "total": 1, "source": single_result.get("source")}

    params = {"text": clean_text, "size": str(size), "page": str(page)}
    if from_score is not None:
        params["fromScore"] = str(from_score)
    if from_epss is not None:
        params["fromEpss"] = str(from_epss)

    url = f"{EUVD_API_BASE}/search?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "SecIntel-Resilient/2.0 (+https://euvd.enisa.europa.eu)", "Accept": "application/json"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            data["source"] = "ENISA EUVD (Primary)"
            return data
    except Exception as e:
        return {"error": f"ENISA EUVD 查詢連線異常: {str(e)}"}


def format_vuln_item(item: Dict[str, Any]) -> str:
    vuln_id = item.get("id", "N/A")
    source = item.get("source", "ENISA EUVD")
    aliases_raw = item.get("aliases", "") or ""
    aliases = [a.strip() for a in aliases_raw.splitlines() if a.strip()]
    alias_str = ", ".join(aliases) if aliases else "N/A"

    cvss_score = item.get("baseScore", "N/A")
    cvss_version = item.get("baseScoreVersion", "3.1")
    cvss_vector = item.get("baseScoreVector", "N/A")
    epss_score = item.get("epss", "N/A")
    epss_str = f"{epss_score}%" if epss_score not in (None, "N/A") and not str(epss_score).startswith("N/A") else str(epss_score)

    assigner = item.get("assigner", "N/A")
    published = item.get("datePublished", "N/A")
    updated = item.get("dateUpdated", "N/A")

    # Extract products
    products = item.get("products", [])
    if not products:
        for p in item.get("enisaIdProduct", []):
            p_info = p.get("product", {})
            p_name = p_info.get("name", "")
            v_name = p_info.get("vendor", {}).get("name", "")
            p_ver = p.get("product_version", "")
            if p_name:
                label = f"{v_name} {p_name}".strip()
                if p_ver:
                    label = f"{label} ({p_ver})"
                products.append(label)
    product_str = ", ".join(products[:3]) if products else "N/A"

    desc = (item.get("description") or "無詳細敘述。").strip()
    if len(desc) > 350:
        desc = desc[:347] + "..."

    return "\n".join([
        f"[{vuln_id}] {alias_str}  (資料來源: {source})",
        f"  • CVSS 評分    : {cvss_score} (v{cvss_version}) | Vector: {cvss_vector}",
        f"  • EPSS 機率    : {epss_str} (利用預測指標)",
        f"  • 受影響產品   : {product_str}",
        f"  • 發佈/修訂    : {published} (更新: {updated}) | 權責機構: {assigner}",
        f"  • 漏洞描述     : {desc}",
    ])


def main():
    parser = argparse.ArgumentParser(description="Resilient Vulnerability Client (EUVD & OSV Fallback)")
    parser.add_argument("query", help="CVE identifier (e.g. CVE-2024-3094), EUVD ID, or keyword")
    parser.add_argument("--size", type=int, default=3, help="Max results to display (default: 3)")
    parser.add_argument("--min-score", type=float, default=None, help="Minimum CVSS base score filter")
    parser.add_argument("--min-epss", type=float, default=None, help="Minimum EPSS score percentage filter")
    parser.add_argument("--json", action="store_true", help="Output raw JSON response")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout in seconds (default: 5)")

    args = parser.parse_args()
    query = args.query.strip()

    if re.fullmatch(r'(?:CVE|EUVD)-\d{4}-\d+', query, re.I):
        data = query_euvd_by_id(query.upper(), timeout=args.timeout)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif "error" in data:
            print(f"[Vulnerability Error] {data['error']}")
        else:
            print(format_vuln_item(data))
        return

    data = query_euvd_search(query, size=args.size, from_score=args.min_score, from_epss=args.min_epss, timeout=args.timeout)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if "error" in data:
        print(f"[Vulnerability Error] {data['error']}")
        return

    items = data.get("items", [])
    total = data.get("total", len(items))
    if not items:
        print(f"[WARNING] 雙引擎資料庫皆無符合項目: '{query}'")
        return

    print(f"[Vulnerability Intelligence Report] 共計找到 {total} 筆紀錄:\n")
    for idx, item in enumerate(items, start=1):
        print(format_vuln_item(item))
        if idx < len(items):
            print("\n" + "─" * 60 + "\n")


if __name__ == "__main__":
    main()
