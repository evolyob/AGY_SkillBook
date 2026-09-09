#!/usr/bin/env python3
"""
Industrial-Grade Real DNS & Email Security Auditor (v2.0)
Replaces fake URL concatenation with deterministic POSIX dig queries:
- Real SPF validation & qualifier evaluation
- Real DMARC policy parsing (p=reject/quarantine/none) & spoofing defense grading
- Real DKIM selector lookup (default._domainkey)
- MX priority ordering & Nameserver inventory
- DNSSEC authenticated data (ad flag) validation
- Reverse DNS (PTR) lookup
Pure Python Standard Library + System POSIX dig (Zero External Python Dependencies).
"""

import subprocess
import re
import json
import argparse
from typing import Dict, Any, List, Optional


def run_dig(args: List[str], timeout: int = 4) -> str:
    """Execute system dig command safely with timeout."""
    try:
        res = subprocess.run(
            ["dig"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return res.stdout
    except Exception:
        return ""


def query_dns_txt(record_name: str, timeout: int = 3, server: Optional[str] = None) -> List[str]:
    """Query TXT records via dig +short."""
    cmd = ["+short", "TXT", record_name]
    if server:
        cmd.insert(0, f"@{server}")
    stdout = run_dig(cmd, timeout=timeout)
    results = []
    for line in stdout.splitlines():
        cleaned = line.strip().strip('"')
        if cleaned:
            results.append(cleaned)
    return results


def query_dns_mx(domain: str, timeout: int = 3) -> List[Dict[str, Any]]:
    """Query MX records via dig +short and sort by priority."""
    stdout = run_dig(["+short", "MX", domain], timeout=timeout)
    mx_list = []
    for line in stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0].isdigit():
            mx_list.append({"priority": int(parts[0]), "host": parts[1].rstrip(".")})
    mx_list.sort(key=lambda x: x["priority"])
    return mx_list


def query_dns_ns(domain: str, timeout: int = 3) -> List[str]:
    """Query NS records via dig +short."""
    stdout = run_dig(["+short", "NS", domain], timeout=timeout)
    return [line.strip().rstrip(".") for line in stdout.splitlines() if line.strip()]


def query_dns_ptr(ip: str, timeout: int = 3) -> List[str]:
    """Query reverse DNS PTR record via dig -x +short."""
    stdout = run_dig(["-x", ip.strip(), "+short"], timeout=timeout)
    return [line.strip().rstrip(".") for line in stdout.splitlines() if line.strip()]


def check_dnssec(domain: str, timeout: int = 4, server: str = "1.1.1.1") -> Dict[str, Any]:
    """
    Audit DNSSEC implementation using Cloudflare/Google resolver.
    Checks for the Authenticated Data (ad) flag in DNS response headers.
    """
    stdout = run_dig([f"@{server}", "+dnssec", "+noall", "+comments", domain, "A"], timeout=timeout)
    flags_line = ""
    has_ad_flag = False
    for line in stdout.splitlines():
        if "flags:" in line:
            flags_line = line.strip()
            flags = line.split("flags:")[1].split(";")[0].strip().split()
            if "ad" in flags:
                has_ad_flag = True
            break

    # Also verify if RRSIG or DS records exist
    rrsig_out = run_dig(["+short", "RRSIG", domain], timeout=timeout)
    ds_out = run_dig(["+short", "DS", domain], timeout=timeout)
    has_ds = bool(ds_out.strip())
    has_rrsig = bool(rrsig_out.strip())

    enabled = has_ad_flag or has_ds or has_rrsig
    return {
        "enabled": enabled,
        "authenticated_data_ad_flag": has_ad_flag,
        "has_ds_record": has_ds,
        "has_rrsig": has_rrsig,
        "header_flags": flags_line,
        "status": "VALIDATED (DNSSEC Active & Signed)" if has_ad_flag else (
            "CONFIGURED (DS/RRSIG present, ad flag unconfirmed)" if enabled else "DISABLED (No DNSSEC Validation)"
        )
    }


def audit_domain_email_security(domain: str, dkim_selector: str = "default") -> Dict[str, Any]:
    """
    Comprehensively audit domain email authentication: SPF, DMARC, DKIM, MX, NS, DNSSEC.
    """
    clean_domain = re.sub(r'^https?://', '', domain).split('/')[0].split(':')[0].strip().lower()

    # 1. SPF Lookup
    txt_records = query_dns_txt(clean_domain)
    spf_record = next((r for r in txt_records if r.startswith("v=spf1")), None)
    spf_all_qualifier = "None"
    if spf_record:
        m_all = re.search(r'([~?+-])all\b', spf_record)
        if m_all:
            spf_all_qualifier = m_all.group(0)

    # 2. DMARC Lookup
    dmarc_records = query_dns_txt(f"_dmarc.{clean_domain}")
    dmarc_record = next((r for r in dmarc_records if r.startswith("v=DMARC1")), None)
    dmarc_policy = "none"
    dmarc_rua = None
    if dmarc_record:
        m_p = re.search(r'\bp=([^;\s]+)', dmarc_record)
        if m_p:
            dmarc_policy = m_p.group(1).lower()
        m_rua = re.search(r'\brua=([^;\s]+)', dmarc_record)
        if m_rua:
            dmarc_rua = m_rua.group(1)

    # 3. DKIM Lookup (using selector, default: "default")
    dkim_records = query_dns_txt(f"{dkim_selector}._domainkey.{clean_domain}")
    dkim_record = next((r for r in dkim_records if "v=DKIM1" in r or "p=" in r), None)

    # 4. MX & NS Records
    mx_records = query_dns_mx(clean_domain)
    ns_records = query_dns_ns(clean_domain)

    # 5. DNSSEC Check
    dnssec_status = check_dnssec(clean_domain)

    # 6. Overall Spoofing Defense Rating
    if dmarc_policy == "reject" and spf_record:
        defense_grade = "Strong (High Protection: p=reject enforced)"
    elif dmarc_policy == "quarantine" and spf_record:
        defense_grade = "Moderate (p=quarantine active)"
    elif dmarc_policy == "none" and spf_record:
        defense_grade = "Weak (Monitoring only: p=none does not block spoofing)"
    elif spf_record:
        defense_grade = "Fragile (SPF present but DMARC missing)"
    else:
        defense_grade = "Vulnerable (No SPF or DMARC protection)"

    return {
        "domain": clean_domain,
        "type": "email_dns_security",
        "spf": {
            "configured": bool(spf_record),
            "record": spf_record or "未宣告 (Missing SPF record)",
            "qualifier": spf_all_qualifier
        },
        "dmarc": {
            "configured": bool(dmarc_record),
            "policy": dmarc_policy,
            "record": dmarc_record or "未宣告 (Missing DMARC record)",
            "rua": dmarc_rua
        },
        "dkim": {
            "selector_tested": dkim_selector,
            "configured": bool(dkim_record),
            "record": dkim_record or f"未在選擇器 '{dkim_selector}' 找到記錄 (Selector not found or customized)"
        },
        "mx_records": mx_records,
        "ns_records": ns_records,
        "dnssec": dnssec_status,
        "spoofing_defense_grade": defense_grade
    }


def format_dns_audit_report(data: Dict[str, Any]) -> str:
    domain = data.get("domain", "")
    spf = data.get("spf", {})
    dmarc = data.get("dmarc", {})
    dkim = data.get("dkim", {})
    mx = data.get("mx_records", [])
    ns = data.get("ns_records", [])
    dnssec = data.get("dnssec", {})
    grade = data.get("spoofing_defense_grade", "Unknown")

    lines = [
        f"[DNS & Email Security Audit Report (POSIX dig)] {domain}",
        f"  • 防偽冒防護評級 : {grade}",
        f"  • DNSSEC 狀態    : {dnssec.get('status', 'N/A')}",
        "",
        "  [SPF 來源授權驗證]",
        f"    - 設定狀態     : {'[PASS] 已宣告' if spf.get('configured') else '[FAIL] 未設定 (High Risk)'}",
        f"    - 記錄內容     : {spf.get('record')}",
        f"    - 結尾機制     : {spf.get('qualifier')}",
        "",
        "  [DMARC 阻斷政策審查]",
        f"    - 設定狀態     : {'[PASS] 已宣告' if dmarc.get('configured') else '[FAIL] 未設定 (High Risk)'}",
        f"    - 阻斷政策 (p) : {dmarc.get('policy').upper() if dmarc.get('configured') else 'NONE'}",
        f"    - 記錄內容     : {dmarc.get('record')}",
    ]
    if dmarc.get("rua"):
        lines.append(f"    - 回報信箱     : {dmarc.get('rua')}")

    lines.extend([
        "",
        f"  [DKIM 數位簽章驗證 (Selector: {dkim.get('selector_tested')})]",
        f"    - 設定狀態     : {'[PASS] 已檢出' if dkim.get('configured') else '[INFO] 未檢出 (可能使用客製 Selector)'}",
    ])
    if dkim.get("configured"):
        lines.append(f"    - 記錄內容     : {dkim.get('record')}")

    lines.extend([
        "",
        "  [MX 郵件交換伺服器 (優先級排序)]",
    ])
    if mx:
        for item in mx:
            lines.append(f"    - Priority {item['priority']:2d} : {item['host']}")
    else:
        lines.append("    - (無 MX 記錄)")

    lines.extend([
        "",
        "  [權威名稱伺服器 (NS)]",
    ])
    if ns:
        for n in ns:
            lines.append(f"    - {n}")
    else:
        lines.append("    - (無 NS 記錄)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Industrial-Grade Real DNS & Email Security Auditor (POSIX dig)")
    parser.add_argument("domain", help="Target domain name (e.g. example.com)")
    parser.add_argument("--selector", default="default", help="DKIM selector to test (default: default)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")
    args = parser.parse_args()

    data = audit_domain_email_security(args.domain, dkim_selector=args.selector)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(format_dns_audit_report(data))


if __name__ == "__main__":
    main()
