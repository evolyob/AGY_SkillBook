#!/usr/bin/env python3
"""
MXToolbox & Anti-Noise DNSBL Blacklist Reputation Diagnostic Client (v2.0)
- Parallel DNSBL reputation scanning (Spamhaus, Barracuda, SpamCop, UCEPROTECT-1)
- Public DNS refusal recognition (127.255.255.254/255) to eliminate false positives
- Real-time DNS & Email Security audit via native dig (delegated to dns_auditor)
- Reverse DNS (PTR) lookup
Pure Python Standard Library (Zero Dependencies).
"""

import json
import argparse
import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from dns_auditor import audit_domain_email_security, format_dns_audit_report, query_dns_ptr

# Active, operational authoritative DNSBL nodes (Sorbs removed after 2024 shutdown)
ACTIVE_DNSBL_SERVERS = [
    ("Spamhaus ZEN", "zen.spamhaus.org"),
    ("Barracuda RBL", "b.barracudacentral.org"),
    ("SpamCop BL", "bl.spamcop.net"),
    ("UCEPROTECT-1", "dnsbl-1.uceprotect.net"),
]


def is_ip(target: str) -> bool:
    try:
        ipaddress.ip_address(target.strip())
        return True
    except ValueError:
        return False


def query_single_rbl(rev_ip: str, name: str, host: str, timeout: float = 2.0) -> Dict[str, Any]:
    """Query a single DNSBL server with timeout and public DNS refusal detection."""
    query_host = f"{rev_ip}.{host}"
    try:
        # Resolve using socket with timeout
        socket.setdefaulttimeout(timeout)
        resolved_ip = socket.gethostbyname(query_host)

        # Detect public DNS rejection code (e.g. 8.8.8.8 hitting Spamhaus query limit)
        if resolved_ip in ("127.255.255.254", "127.255.255.255"):
            return {
                "rbl": name,
                "status": "QUERY_REFUSED",
                "detail": "公用遞迴 DNS 遭拒絕查詢 (Public DNS Blocked)",
                "resolved": resolved_ip
            }

        return {
            "rbl": name,
            "status": "LISTED",
            "detail": f"Return Code: {resolved_ip}",
            "resolved": resolved_ip
        }
    except socket.gaierror:
        return {"rbl": name, "status": "CLEAN", "detail": "未列入 (Clean)", "resolved": None}
    except socket.timeout:
        return {"rbl": name, "status": "TIMEOUT", "detail": "查詢超時 (Timeout)", "resolved": None}
    except Exception as e:
        return {"rbl": name, "status": "ERROR", "detail": str(e), "resolved": None}


def check_ip_blacklist(ip: str) -> Dict[str, Any]:
    """
    Perform fast, concurrent, anti-noise DNSBL scan for an IPv4 address.
    """
    clean_ip = ip.strip()
    if ":" in clean_ip:
        return {
            "target": clean_ip,
            "type": "ip",
            "is_ipv6": True,
            "status": "IPv6 (DNSBL 僅支援 IPv4，自動略過)",
            "is_clean": True,
            "clean_count": 0,
            "total_rbls": 0,
            "listed_on": [],
            "ptr": query_dns_ptr(clean_ip)
        }

    rev_ip = ".".join(reversed(clean_ip.split(".")))
    with ThreadPoolExecutor(max_workers=len(ACTIVE_DNSBL_SERVERS)) as executor:
        futures = [
            executor.submit(query_single_rbl, rev_ip, name, host)
            for name, host in ACTIVE_DNSBL_SERVERS
        ]
        results = [f.result() for f in futures]

    clean_count = sum(1 for r in results if r["status"] == "CLEAN")
    listed_on = [r for r in results if r["status"] == "LISTED"]
    refused_on = [r for r in results if r["status"] == "QUERY_REFUSED"]
    ptr_records = query_dns_ptr(clean_ip)

    return {
        "target": clean_ip,
        "type": "ip",
        "is_clean": len(listed_on) == 0,
        "clean_count": clean_count,
        "total_rbls": len(ACTIVE_DNSBL_SERVERS),
        "listed_on": listed_on,
        "refused_on": refused_on,
        "all_results": results,
        "ptr": ptr_records,
        "mxtoolbox_url": f"https://mxtoolbox.com/SuperTool.aspx?action=blacklist:{clean_ip}"
    }


def check_domain_email_sec(domain: str) -> Dict[str, Any]:
    """
    Perform authoritative, real-time DNS & email security audit on domain.
    """
    data = audit_domain_email_security(domain)
    # Retain helper links for convenience while providing 100% real DNS audit data
    cleaned = data["domain"]
    data["mxtoolbox_links"] = {
        "mx": f"https://mxtoolbox.com/SuperTool.aspx?action=mx:{cleaned}",
        "spf": f"https://mxtoolbox.com/SuperTool.aspx?action=spf:{cleaned}",
        "dmarc": f"https://mxtoolbox.com/SuperTool.aspx?action=dmarc:{cleaned}",
        "blacklist": f"https://mxtoolbox.com/SuperTool.aspx?action=blacklist:{cleaned}"
    }
    return data


def format_mxtoolbox_report(data: Dict[str, Any]) -> str:
    target = data.get("target") or data.get("domain", "")

    if data.get("type") == "ip":
        is_clean = data.get("is_clean", True)
        listed = data.get("listed_on", [])
        refused = data.get("refused_on", [])
        ptr = data.get("ptr", [])
        ptr_str = ", ".join(ptr) if ptr else "(無反解記錄 / No PTR)"

        if is_clean:
            status_line = "[PASS] Clean (未列入任何運作中之黑名單)"
        else:
            rbl_names = [item["rbl"] for item in listed]
            status_line = f"[WARN] 列入 {len(listed)} 個黑名單資料庫: {', '.join(rbl_names)}"

        lines = [
            f"[DNSBL 黑名單信譽與反解報告] {target}",
            f"  • 整體狀態 : {status_line}",
            f"  • 黑名單比 : {data.get('clean_count', 0)}/{data.get('total_rbls', 0)} Clean",
            f"  • IP 反解  : {ptr_str}",
            f"  • 參考連結 : {data.get('mxtoolbox_url', '')}",
        ]

        if listed:
            lines.append("  • 命中黑名單項目:")
            for item in listed:
                lines.append(f"    - [LISTED] {item['rbl']} -> {item['detail']}")

        if refused:
            lines.append("  • 查詢拒絕項目 (抗干擾過濾，非黑名單命中):")
            for item in refused:
                lines.append(f"    - [INFO] {item['rbl']} -> {item['detail']} (建議自備獨立遞迴 DNS)")

        return "\n".join(lines)

    # Domain / Email Security Report
    return format_dns_audit_report(data)


def main():
    parser = argparse.ArgumentParser(description="MXToolbox & Anti-Noise DNSBL Reputation Client (v2.0)")
    parser.add_argument("target", help="IP address or Domain name")
    parser.add_argument("--json", action="store_true", help="Output raw JSON response")

    args = parser.parse_args()
    target = args.target.strip()

    if is_ip(target):
        data = check_ip_blacklist(target)
    else:
        data = check_domain_email_sec(target)

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(format_mxtoolbox_report(data))


if __name__ == "__main__":
    main()
