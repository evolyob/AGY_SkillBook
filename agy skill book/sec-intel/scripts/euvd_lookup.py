#!/usr/bin/env python3
"""
ENISA European Union Vulnerability Database (EUVD) Client
Authoritative European CVE, CVSS 4.0/3.1, EPSS, and KEV intelligence lookup via REST API.
Pure Python Standard Library (Zero Dependencies).
"""

import json, argparse, re, urllib.request, urllib.parse, urllib.error
from typing import Dict, Any, Optional

EUVD_API_BASE = "https://euvdservices.enisa.europa.eu/api"


def query_euvd_search(
    text: str,
    size: int = 5,
    page: int = 0,
    from_score: Optional[float] = None,
    from_epss: Optional[float] = None,
    timeout: int = 8
) -> Dict[str, Any]:
    params = {"text": text, "size": str(size), "page": str(page)}
    if from_score is not None:
        params["fromScore"] = str(from_score)
    if from_epss is not None:
        params["fromEpss"] = str(from_epss)

    url = f"{EUVD_API_BASE}/search?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "Antigravity-EUVD/1.0 (+https://euvd.enisa.europa.eu)", "Accept": "application/json"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "status_code": e.code}
    except Exception as e:
        return {"error": str(e)}


def query_euvd_by_id(euvd_id: str, timeout: int = 8) -> Dict[str, Any]:
    url = f"{EUVD_API_BASE}/enisaid?id={urllib.parse.quote(euvd_id)}"
    headers = {"User-Agent": "Antigravity-EUVD/1.0 (+https://euvd.enisa.europa.eu)", "Accept": "application/json"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return {"error": str(e)}


def format_vuln_item(item: Dict[str, Any]) -> str:
    euvd_id = item.get("id", "N/A")
    aliases_raw = item.get("aliases", "") or ""
    aliases = [a.strip() for a in aliases_raw.splitlines() if a.strip()]
    alias_str = ", ".join(aliases) if aliases else "N/A"
    
    cvss_score = item.get("baseScore", "N/A")
    cvss_version = item.get("baseScoreVersion", "3.1")
    cvss_vector = item.get("baseScoreVector", "N/A")
    epss_score = item.get("epss", "N/A")
    epss_str = f"{epss_score}%" if epss_score not in (None, "N/A") else "N/A"
    
    assigner = item.get("assigner", "N/A")
    published = item.get("datePublished", "N/A")
    updated = item.get("dateUpdated", "N/A")
    
    products = []
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
    
    desc = (item.get("description") or "No description provided.").strip()
    if len(desc) > 300:
        desc = desc[:297] + "..."

    return "\n".join([
        f"[{euvd_id}] {alias_str}",
        f"  • CVSS Score   : {cvss_score} (v{cvss_version}) | Vector: {cvss_vector}",
        f"  • EPSS Score   : {epss_str} (Exploit Prediction)",
        f"  • Affected     : {product_str}",
        f"  • Assigner     : {assigner}",
        f"  • Published    : {published} (Updated: {updated})",
        f"  • Description  : {desc}",
    ])


def main():
    parser = argparse.ArgumentParser(description="ENISA European Vulnerability Database (EUVD) Query Client")
    parser.add_argument("query", help="CVE identifier (e.g. CVE-2024-3094), EUVD ID, or package keyword")
    parser.add_argument("--size", type=int, default=3, help="Max results to display (default: 3)")
    parser.add_argument("--min-score", type=float, default=None, help="Minimum CVSS base score filter")
    parser.add_argument("--min-epss", type=float, default=None, help="Minimum EPSS score percentage filter")
    parser.add_argument("--json", action="store_true", help="Output raw EUVD JSON response")
    parser.add_argument("--timeout", type=int, default=8, help="HTTP request timeout in seconds (default: 8)")
    
    args = parser.parse_args()
    query = args.query.strip()
    
    if re.fullmatch(r'EUVD-\d{4}-\d+', query, re.I):
        data = query_euvd_by_id(query.upper(), timeout=args.timeout)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif "error" in data:
            print(f"[EUVD Error] {data['error']}")
        else:
            print(format_vuln_item(data))
        return

    data = query_euvd_search(query, size=args.size, from_score=args.min_score, from_epss=args.min_epss, timeout=args.timeout)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
        
    if "error" in data:
        print(f"[EUVD Error] {data['error']}")
        return
        
    items = data.get("items", [])
    total = data.get("total", len(items))
    if not items:
        print(f"[WARNING] No vulnerabilities found in ENISA EUVD matching query: '{query}'")
        return

    print(f"[ENISA European Vulnerability Database] Found {total} records for '{query}':\n")
    for idx, item in enumerate(items, start=1):
        print(format_vuln_item(item))
        if idx < len(items):
            print("\n" + "─" * 60 + "\n")


if __name__ == "__main__":
    main()
