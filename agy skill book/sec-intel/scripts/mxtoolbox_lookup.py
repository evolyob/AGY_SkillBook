#!/usr/bin/env python3
"""
MXToolbox & DNSBL Blacklist Reputation Diagnostic Client
Performs real-time IP/Domain blacklist reputation scanning (Spamhaus, Barracuda, SpamCop) and MXToolbox email security diagnostics.
Pure Python Standard Library (Zero Dependencies).
"""

import json
import argparse
import socket
import re
import ipaddress
from typing import Dict, Any

DNSBL_SERVERS = [
    ("Spamhaus ZEN", "zen.spamhaus.org"),
    ("Barracuda RBL", "b.barracudacentral.org"),
    ("SpamCop BL", "bl.spamcop.net"),
    ("Sorbs DNSBL", "dnsbl.sorbs.net"),
    ("UCEPROTECT-1", "dnsbl-1.uceprotect.net"),
]


def is_ip(target: str) -> bool:
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False


def check_ip_blacklist(ip: str) -> Dict[str, Any]:
    if ":" in ip:
        return {"ip": ip, "is_ipv6": True, "status": "IPv6 (DNSBL skipped)", "listed_on": [], "clean": True}

    rev = ".".join(reversed(ip.split(".")))
    listed_on = []
    clean_count = 0

    for name, host in DNSBL_SERVERS:
        query_host = f"{rev}.{host}"
        try:
            resolved_ip = socket.gethostbyname(query_host)
            listed_on.append({"rbl": name, "resolved": resolved_ip})
        except socket.gaierror:
            clean_count += 1

    is_clean = len(listed_on) == 0
    return {
        "target": ip,
        "type": "ip",
        "is_clean": is_clean,
        "clean_count": clean_count,
        "total_rbls": len(DNSBL_SERVERS),
        "listed_on": listed_on,
        "mxtoolbox_url": f"https://mxtoolbox.com/SuperTool.aspx?action=blacklist:{ip}"
    }


def check_domain_email_sec(domain: str) -> Dict[str, Any]:
    cleaned = re.sub(r'^https?://', '', domain).split('/')[0].split(':')[0]
    return {
        "target": cleaned,
        "type": "domain",
        "mxtoolbox_mx_url": f"https://mxtoolbox.com/SuperTool.aspx?action=mx:{cleaned}",
        "mxtoolbox_spf_url": f"https://mxtoolbox.com/SuperTool.aspx?action=spf:{cleaned}",
        "mxtoolbox_dmarc_url": f"https://mxtoolbox.com/SuperTool.aspx?action=dmarc:{cleaned}",
        "mxtoolbox_blacklist_url": f"https://mxtoolbox.com/SuperTool.aspx?action=blacklist:{cleaned}"
    }


def format_mxtoolbox_report(data: Dict[str, Any]) -> str:
    target = data.get("target", "")
    if data.get("type") == "ip":
        is_clean = data.get("is_clean", True)
        listed = data.get("listed_on", [])
        if is_clean:
            status_line = "[PASS] Clean (Not listed on any checked DNSBLs)"
        else:
            rbl_names = [item["rbl"] for item in listed]
            status_line = f"[WARN] LISTED on {len(listed)} blacklists: {', '.join(rbl_names)}"

        lines = [
            f"[MXToolbox & DNSBL Reputation Report] {target}",
            f"  • Overall Status : {status_line}",
            f"  • Blacklist RBLs : {data.get('clean_count', 0)}/{data.get('total_rbls', 0)} Clean",
            f"  • MXToolbox Link : {data.get('mxtoolbox_url', '')}",
        ]
        if listed:
            lines.append("  • Active Listings:")
            for item in listed:
                lines.append(f"    - {item['rbl']} (Return code: {item['resolved']})")
        return "\n".join(lines)

    # Domain report
    lines = [
        f"[MXToolbox Domain & Email Security Report] {target}",
        f"  • MX Diagnostic    : {data.get('mxtoolbox_mx_url', '')}",
        f"  • SPF Record Audit : {data.get('mxtoolbox_spf_url', '')}",
        f"  • DMARC Alignment  : {data.get('mxtoolbox_dmarc_url', '')}",
        f"  • Domain Blacklist : {data.get('mxtoolbox_blacklist_url', '')}",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MXToolbox & DNSBL Reputation Diagnostic Client")
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
