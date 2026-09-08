#!/usr/bin/env python3
"""
Unified Security Intelligence Router
Dispatches queries to 4 core pillars:
1. ICANN RDAP (IP/Domain/ASN Registry & TLS probe)
2. MXToolbox & DNSBL (Email Security & Blacklists)
3. ENISA EUVD (CVE & EPSS Exploit Intelligence)
4. Web Endpoint & Client Security Auditor (web_monitor.py)
Pure Python Standard Library (Zero Dependencies).
"""

import sys, re, json, argparse, subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from icann_rdap_lookup import fetch_rdap, format_ip_summary, format_domain_summary, format_asn_summary
from euvd_lookup import query_euvd_search, query_euvd_by_id, format_vuln_item
from mxtoolbox_lookup import check_ip_blacklist, check_domain_email_sec, format_mxtoolbox_report, is_ip as is_ip_addr
from web_monitor import capture_snapshot, format_markdown_report


def probe_curl(target: str, timeout: int = 3) -> str:
    """Lightweight curl -v -k probe for HTTP status & TLS certificate details."""
    clean_host = re.sub(r'^https?://', '', target).split('/')[0].split(':')[0]
    cmd = ["curl", "-v", "-k", "--connect-timeout", str(timeout), "-s", "-o", "/dev/null", f"https://{clean_host}"]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout + 2)
        lines = []
        for line in res.stdout.splitlines():
            line_str = line.strip()
            if any(k in line_str for k in ("subject:", "issuer:", "expire date:", "start date:", "< HTTP/", "SSL connection using", "ALPN: server accepted")):
                lines.append("  " + line_str)
            elif ("Timeout was reached" in line_str or "connect timeout" in line_str) and not any("Timeout" in l for l in lines):
                lines.append(f"  [WARN] Timeout (連線逾時 > {timeout}s)")
            elif "Failed to connect" in line_str and not any("Refused" in l for l in lines):
                lines.append("  [WARN] Connection Refused")
        if not lines:
            return f"[HTTPS Probe] https://{clean_host}: (無回應或無法連線)"
        return f"[HTTPS Probe & Certificate] https://{clean_host}:\n" + "\n".join(lines)
    except Exception as e:
        return f"[HTTPS Probe] https://{clean_host}: 探測失敗 ({e})"


def is_cve_or_euvd(target: str) -> bool:
    return bool(re.fullmatch(r'(?:CVE|EUVD)-\d{4}-\d+', target, re.I))


def is_asn(target: str) -> bool:
    return bool(re.fullmatch(r'(?:AS|as)?\d+', target)) and not is_ip_addr(target)


def is_domain(target: str) -> bool:
    clean = re.sub(r'^https?://', '', target).split('/')[0].split(':')[0]
    return bool(re.fullmatch(r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}', clean)) and not is_ip_addr(clean)


def dispatch_euvd(target: str, args) -> None:
    """Handle EUVD lookup and output formatting."""
    if re.fullmatch(r'EUVD-\d{4}-\d+', target, re.I):
        data = query_euvd_by_id(target.upper())
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return
        if "error" in data:
            print(f"[EUVD Error] {data['error']}", file=sys.stderr)
            return
        print(format_vuln_item(data))
        return

    data = query_euvd_search(target, size=args.size, from_score=args.min_score, from_epss=args.min_epss)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    if "error" in data:
        print(f"[EUVD Error] {data['error']}", file=sys.stderr)
        return
    items = data.get("items", [])
    if not items:
        print(f"[WARNING] No records found in EUVD for '{target}'")
        return
    print(f"[ENISA EUVD Vulnerability Intelligence] Query: '{target}':\n")
    for idx, item in enumerate(items, start=1):
        print(format_vuln_item(item))
        if idx < len(items):
            print("\n" + "─" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Unified Security Intelligence Router (RDAP / MXToolbox / EUVD / Web Audit)")
    parser.add_argument("target", help="IP address, Domain name, ASN, or CVE/EUVD ID")
    parser.add_argument("--web", action="store_true", help="Web endpoint security & integrity snapshot")
    parser.add_argument("--mxtoolbox", action="store_true", help="Query MXToolbox (Blacklist / Email Security)")
    parser.add_argument("--no-curl", action="store_true", help="Skip HTTPS curl connection probe for domains")
    parser.add_argument("--vuln", action="store_true", help="Explicit package/software vulnerability lookup in ENISA EUVD")
    parser.add_argument("--size", type=int, default=3, help="Max vulnerability results (default: 3)")
    parser.add_argument("--min-score", type=float, default=None, help="Min CVSS base score")
    parser.add_argument("--min-epss", type=float, default=None, help="Min EPSS probability percentage")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")
    args = parser.parse_args()

    target = args.target.strip()

    # 0. Dispatch Web Monitor (Explicit or URL targets)
    if args.web or target.startswith(("http://", "https://")):
        snap = capture_snapshot(target)
        if args.json:
            print(json.dumps(snap, indent=2, ensure_ascii=False))
            return
        print(format_markdown_report(snap))
        return

    # 1. Dispatch MXToolbox
    if args.mxtoolbox:
        data = check_ip_blacklist(target) if is_ip_addr(target) else check_domain_email_sec(target)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(format_mxtoolbox_report(data))
        return

    # 2. Dispatch CVE or EUVD ID
    if is_cve_or_euvd(target):
        dispatch_euvd(target, args)
        return

    # 3. Dispatch IP -> ICANN RDAP
    if is_ip_addr(target):
        data = fetch_rdap("ip", target)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(format_ip_summary(data, target))
        return

    # 4. Dispatch ASN -> ICANN RDAP
    if is_asn(target):
        cleaned_asn = re.sub(r'^(?:AS|as)', '', target)
        data = fetch_rdap("autnum", cleaned_asn)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(format_asn_summary(data, cleaned_asn))
        return

    # 5. Dispatch Domain -> ICANN RDAP + simple curl probe
    if is_domain(target):
        cleaned_dom = re.sub(r'^https?://', '', target).split('/')[0].split(':')[0]
        data = fetch_rdap("domain", cleaned_dom)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return
        print(format_domain_summary(data, cleaned_dom))
        if not args.no_curl:
            print("\n" + probe_curl(target))
        return

    # 6. Explicit Software Package Vulnerability Search in EUVD
    if args.vuln:
        data = query_euvd_search(target, size=args.size, from_score=args.min_score, from_epss=args.min_epss)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return
        items = data.get("items", [])
        if not items:
            print(f"[WARNING] No intelligence records found matching target: '{target}'")
            return
        print(f"[ENISA EUVD Vulnerability Intelligence] Keyword: '{target}':\n")
        for idx, item in enumerate(items, start=1):
            print(format_vuln_item(item))
            if idx < len(items):
                print("\n" + "─" * 60 + "\n")
        return

    print(f"[WARNING] 無法識別標靶格式: '{target}'。\n• 若為 IP/網域/ASN/CVE，請檢查格式輸入。\n• 若欲搜尋軟體套件漏洞，請加上 --vuln 參數。")


if __name__ == "__main__":
    main()
