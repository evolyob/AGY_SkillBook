#!/usr/bin/env python3
"""
Unified Security Intelligence Router (v2.0 High-Reliability)
Dispatches queries across 4 core industrial-grade pillars:
1. ICANN RDAP: IP/Domain/ASN Registry & Two-Pass TLS verification
2. Real DNS & Anti-Noise DNSBL: POSIX dig SPF/DMARC/DKIM/MX/DNSSEC & Parallel Blacklists
3. Dual-Engine Vulnerability Intelligence: ENISA EUVD + Google OSV.dev Fallback
4. Web Endpoint Security & Integrity Auditor: 11 Security Headers (A~F), Cookies & Scripts
Pure Python Standard Library (Zero Dependencies).
"""

import sys
import re
import json
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from icann_rdap_lookup import fetch_rdap, format_ip_summary, format_domain_summary, format_asn_summary
from euvd_lookup import query_euvd_search, query_euvd_by_id, format_vuln_item
from dns_auditor import format_dns_audit_report
from mxtoolbox_lookup import check_ip_blacklist, check_domain_email_sec, format_mxtoolbox_report, is_ip as is_ip_addr
from web_monitor import capture_snapshot, format_markdown_report, audit_tls_two_pass

def probe_tls_status(target: str, timeout: int = 4) -> str:
    """Perform Two-Pass TLS check for domain connection status."""
    clean_host = re.sub(r'^https?://', '', target).split('/')[0].split(':')[0]
    tls_info = audit_tls_two_pass(clean_host, timeout=timeout)
    lines = [f"[HTTPS & TLS Probe (Two-Pass)] https://{clean_host}:"]
    if tls_info["trusted"]:
        lines.append("  • 憑證驗證 : [PASS] 信任鏈有效 (Valid Certificate)")
    elif tls_info.get("error"):
        lines.append(f"  • 憑證驗證 : {tls_info['error']}")
    else:
        lines.append("  • 憑證驗證 : [FAIL] 未能完成信任鏈驗證")

    if tls_info.get("tls_version") or tls_info.get("cipher"):
        lines.append(f"  • 加密協議 : {tls_info.get('tls_version') or 'N/A'}")
        lines.append(f"  • 密碼套件 : {tls_info.get('cipher') or 'N/A'}")

    return "\n".join(lines)

def is_cve_or_euvd(target: str) -> bool:
    return bool(re.fullmatch(r'(?:CVE|EUVD)-\d{4}-\d+', target, re.I))

def is_asn(target: str) -> bool:
    return bool(re.fullmatch(r'(?:AS|as)?\d+', target)) and not is_ip_addr(target)

def is_domain(target: str) -> bool:
    clean = re.sub(r'^https?://', '', target).split('/')[0].split(':')[0]
    return bool(re.fullmatch(r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}', clean)) and not is_ip_addr(clean)

def dispatch_vuln(target: str, args) -> None:
    """Handle Dual-Engine Vulnerability lookup (EUVD + Google OSV fallback)."""
    if is_cve_or_euvd(target):
        data = query_euvd_by_id(target.upper())
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return
        if "error" in data:
            print(f"[Vulnerability Error] {data['error']}", file=sys.stderr)
            return
        print(format_vuln_item(data))
        return

    data = query_euvd_search(target, size=args.size, from_score=args.min_score, from_epss=args.min_epss)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    if "error" in data:
        print(f"[Vulnerability Error] {data['error']}", file=sys.stderr)
        return
    items = data.get("items", [])
    if not items:
        print(f"[WARNING] 雙引擎資料庫皆無符合 '{target}' 之紀錄")
        return
    print(f"[Vulnerability Intelligence Report (Dual-Engine)] 關鍵字: '{target}':\n")
    for idx, item in enumerate(items, start=1):
        print(format_vuln_item(item))
        if idx < len(items):
            print("\n" + "─" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="Unified Security Intelligence Router (v2.0: RDAP / Real DNS / Dual-Engine Vuln / Web Audit)"
    )
    parser.add_argument("target", help="IP address, Domain name, ASN, URL, or CVE/EUVD ID")
    parser.add_argument("--web", action="store_true", help="Web endpoint security & integrity snapshot (11 headers, cookies, scripts)")
    parser.add_argument("--mxtoolbox", "--dns", "--email", dest="mxtoolbox", action="store_true",
                        help="Run Real DNS (SPF/DMARC/DKIM/MX/DNSSEC) or anti-noise DNSBL scan")
    parser.add_argument("--all", "--comprehensive", dest="all_checks", action="store_true",
                        help="Execute comprehensive suite (RDAP + Real DNS + Web Audit)")
    parser.add_argument("--no-tls", action="store_true", help="Skip TLS certificate probe for domains")
    parser.add_argument("--vuln", action="store_true", help="Explicit package/software vulnerability lookup")
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

    # 1. Dispatch Real DNS / DNSBL
    if args.mxtoolbox:
        data = check_ip_blacklist(target) if is_ip_addr(target) else check_domain_email_sec(target)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(format_mxtoolbox_report(data))
        return

    # 2. Dispatch CVE or EUVD ID
    if is_cve_or_euvd(target):
        dispatch_vuln(target, args)
        return

    # 3. Comprehensive check for domain or IP
    if args.all_checks:
        print("=" * 60)
        print("【1. ICANN RDAP 註冊資訊】")
        if is_ip_addr(target):
            rdap_data = fetch_rdap("ip", target)
            print(format_ip_summary(rdap_data, target))
            print("\n" + "=" * 60)
            print("【2. DNSBL 黑名單信譽與反解】")
            dnsbl_data = check_ip_blacklist(target)
            print(format_mxtoolbox_report(dnsbl_data))
        else:
            cleaned = re.sub(r'^https?://', '', target).split('/')[0].split(':')[0]
            rdap_data = fetch_rdap("domain", cleaned)
            print(format_domain_summary(rdap_data, cleaned))
            print("\n" + "=" * 60)
            print("【2. Real DNS & 郵件安全審計 (SPF/DMARC/DKIM/DNSSEC)】")
            dns_data = check_domain_email_sec(cleaned)
            print(format_dns_audit_report(dns_data))
            print("\n" + "=" * 60)
            print("【3. Web 端點與 Two-Pass TLS 審計】")
            web_snap = capture_snapshot(target)
            print(format_markdown_report(web_snap))
        return

    # 4. Dispatch IP -> ICANN RDAP
    if is_ip_addr(target):
        data = fetch_rdap("ip", target)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(format_ip_summary(data, target))
        return

    # 5. Dispatch ASN -> ICANN RDAP
    if is_asn(target):
        cleaned_asn = re.sub(r'^(?:AS|as)', '', target)
        data = fetch_rdap("autnum", cleaned_asn)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(format_asn_summary(data, cleaned_asn))
        return

    # 6. Dispatch Domain -> ICANN RDAP + Two-Pass TLS probe
    if is_domain(target):
        cleaned_dom = re.sub(r'^https?://', '', target).split('/')[0].split(':')[0]
        data = fetch_rdap("domain", cleaned_dom)
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return
        print(format_domain_summary(data, cleaned_dom))
        if not args.no_tls:
            print("\n" + probe_tls_status(cleaned_dom))
        return

    # 7. Explicit Software Package Vulnerability Search in EUVD
    if args.vuln:
        dispatch_vuln(target, args)
        return

    print(f"[WARNING] 無法識別標靶格式: '{target}'。\n• 若為 IP/網域/ASN/CVE，請檢查格式輸入。\n• 若欲搜尋軟體套件漏洞，請加上 --vuln 參數。")

if __name__ == "__main__":
    main()
