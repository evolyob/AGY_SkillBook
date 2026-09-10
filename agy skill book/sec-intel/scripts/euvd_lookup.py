#!/usr/bin/env python3
"""
Resilient Vulnerability Intelligence Client (v2.0)
Dual-Engine Fallback: ENISA EUVD (EPSS & CVSS) + Google OSV.dev (Anycast CDN).
"""

import json, argparse, re, urllib.request, urllib.parse, urllib.error
from typing import Dict, Any, Optional

EUVD_API_BASE = "https://euvdservices.enisa.europa.eu/api"
OSV_API_BASE = "https://api.osv.dev/v1/vulns"



def fetch_from_osv(cve_or_id: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Fallback Engine: Google OSV.dev Anycast CDN API."""
    target = cve_or_id.strip().upper()
    url = f"{OSV_API_BASE}/{urllib.parse.quote(target)}"
    headers = {"User-Agent": "SecIntel-Resilient/2.0 (+https://osv.dev)", "Accept": "application/json"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            if not data or not data.get("id"):
                return None

            cvss_score, cvss_ver = "參見細節", "N/A"
            for sev in data.get("severity", []):
                s_type = sev.get("type", "")
                if s_type in ("CVSS_V3", "CVSS_V4", "CVSS_V2"):
                    cvss_ver = s_type.replace("CVSS_", "")
                    m = re.search(r'CVSS:[0-9.]+/.*?/([0-9.]+)', sev.get("score", ""))
                    cvss_score = m.group(1) if m else sev.get("score", "")

            products = []
            for aff in data.get("affected", []):
                p_name = aff.get("package", {}).get("name") or aff.get("database_specific", {}).get("cpe", [""])[0]
                if p_name:
                    products.append(p_name)

            aliases = data.get("aliases", [])
            return {
                "source": "Google OSV.dev (Fallback CDN)",
                "id": data.get("id", target),
                "aliases": "\n".join(aliases),
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
    """Query vulnerability by CVE or EUVD ID with automatic Google OSV.dev fallback."""
    target = cve_or_euvd_id.strip().upper()
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
        pass
    osv_data = fetch_from_osv(target, timeout=timeout)
    return osv_data if osv_data else {"error": f"雙引擎查詢皆無此漏洞紀錄 (ENISA EUVD & Google OSV.dev): '{target}'"}


def query_euvd_search(
    text: str, size: int = 5, page: int = 0,
    from_score: Optional[float] = None, from_epss: Optional[float] = None, timeout: int = 6
) -> Dict[str, Any]:
    """Search EUVD vulnerability records with fallback to direct OSV lookup if query is a CVE ID."""
    clean_text = text.strip()
    if re.fullmatch(r'(?:CVE|EUVD)-\d{4}-\d+', clean_text, re.I):
        single = query_euvd_by_id(clean_text, timeout=timeout)
        return single if "error" in single else {"items": [single], "total": 1, "source": single.get("source")}

    params = {"text": clean_text, "size": str(size), "page": str(page)}
    if from_score is not None: params["fromScore"] = str(from_score)
    if from_epss is not None: params["fromEpss"] = str(from_epss)

    url = f"{EUVD_API_BASE}/search?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "SecIntel-Resilient/2.0 (+https://euvd.enisa.europa.eu)", "Accept": "application/json"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            data["source"] = "ENISA EUVD (Primary)"
            return data
    except Exception as e:
        return {"error": f"ENISA EUVD 查詢連線異常: {e}"}


def format_vuln_item(item: Dict[str, Any]) -> str:
    aliases = [a.strip() for a in (item.get("aliases") or "").splitlines() if a.strip()]
    epss = item.get("epss", "N/A")
    epss_str = f"{epss}%" if epss not in (None, "N/A") and not str(epss).startswith("N/A") else str(epss)
    products = item.get("products", [])
    if not products:
        for p in item.get("enisaIdProduct", []):
            p_name = p.get("product", {}).get("name", "")
            if p_name:
                v = p.get("product", {}).get("vendor", {}).get("name", "")
                ver = p.get("product_version", "")
                lbl = f"{v} {p_name}".strip()
                products.append(f"{lbl} ({ver})" if ver else lbl)
    desc = (item.get("description") or "無詳細敘述。").strip()
    if len(desc) > 350: desc = desc[:347] + "..."

    return "\n".join([
        f"[{item.get('id', 'N/A')}] {', '.join(aliases) if aliases else 'N/A'}  (資料來源: {item.get('source', 'ENISA EUVD')})",
        f"  • CVSS 評分    : {item.get('baseScore', 'N/A')} (v{item.get('baseScoreVersion', '3.1')}) | Vector: {item.get('baseScoreVector', 'N/A')}",
        f"  • EPSS 機率    : {epss_str} (利用預測指標)",
        f"  • 受影響產品   : {', '.join(products[:3]) if products else 'N/A'}",
        f"  • 發佈/修訂    : {item.get('datePublished', 'N/A')} (更新: {item.get('dateUpdated', 'N/A')}) | 權責機構: {item.get('assigner', 'N/A')}",
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
        if args.json: print(json.dumps(data, indent=2, ensure_ascii=False))
        elif "error" in data: print(f"[Vulnerability Error] {data['error']}")
        else: print(format_vuln_item(data))
        return

    data = query_euvd_search(query, size=args.size, from_score=args.min_score, from_epss=args.min_epss, timeout=args.timeout)
    if args.json: return print(json.dumps(data, indent=2, ensure_ascii=False))
    if "error" in data: return print(f"[Vulnerability Error] {data['error']}")
    items = data.get("items", [])
    if not items: return print(f"[WARNING] 雙引擎資料庫皆無符合項目: '{query}'")

    print(f"[Vulnerability Intelligence Report] 共計找到 {data.get('total', len(items))} 筆紀錄:\n")
    for idx, item in enumerate(items, start=1):
        print(format_vuln_item(item))
        if idx < len(items): print("\n" + "─" * 60 + "\n")


if __name__ == "__main__":
    main()
