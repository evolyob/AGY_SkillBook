#!/usr/bin/env python3
"""
ICANN RDAP & RapidDNS Security Intelligence Client
Authoritative IP, ASN, and Domain intelligence lookup via RFC 7480-7484 with RapidDNS graceful degradation fallback.
Pure Python Standard Library (Zero Dependencies).
"""

import json
import argparse
import ipaddress
import urllib.request
import re
from typing import Dict, Any, Optional, Tuple, List


def detect_target_type(target: str) -> Tuple[str, str]:
    t = target.strip()
    try:
        ipaddress.ip_address(t)
        return "ip", t
    except ValueError:
        pass
    m = re.fullmatch(r'(?:AS|as)?(\d+)', t)
    if m and int(m.group(1)) > 0 and "." not in t:
        return "autnum", m.group(1)
    return "domain", re.sub(r'^https?://', '', t).split('/')[0].split(':')[0]


def fetch_from_url(url: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    headers = {"User-Agent": "Antigravity-RDAP/1.0 (+https://lookup.icann.org)", "Accept": "application/rdap+json, application/json"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace")) if resp.status == 200 else None
    except Exception:
        return None


def fetch_rapiddns_fallback(target: str, timeout: int = 6) -> Optional[Dict[str, Any]]:
    url = f"https://rapiddns.io/s/{target}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            results = []
            for r in rows[1:6]:
                cols = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)]
                if len(cols) >= 3:
                    results.append({"host": cols[0], "ip": cols[1], "type": cols[2], "date": cols[3] if len(cols) > 3 else ""})
            return {"is_fallback": True, "source": "RapidDNS", "target": target, "records": results} if results else None
    except Exception:
        return None


def get_apex_domain(domain: str) -> str:
    """Extract registered apex domain (e.g. www.example.com -> example.com)."""
    parts = domain.strip().split('.')
    if len(parts) > 2:
        if len(parts) >= 3 and parts[-2].lower() in ('com', 'co', 'net', 'org', 'edu', 'gov', 'idv'):
            return '.'.join(parts[-3:])
        return '.'.join(parts[-2:])
    return domain


def fetch_rdap(query_type: str, target: str, timeout: int = 8) -> Dict[str, Any]:
    targets_to_try = [target]
    if query_type == "domain":
        apex = get_apex_domain(target)
        if apex != target:
            targets_to_try.append(apex)

    for current_target in targets_to_try:
        candidate_urls: List[str] = [f"https://rdap.org/{query_type}/{current_target}"]
        if query_type == "ip":
            candidate_urls.extend([f"https://rdap.apnic.net/ip/{current_target}", f"https://rdap.arin.net/registry/ip/{current_target}", f"https://rdap.db.ripe.net/ip/{current_target}"])
        elif query_type == "autnum":
            candidate_urls.extend([f"https://rdap.apnic.net/autnum/{current_target}", f"https://rdap.arin.net/registry/autnum/{current_target}"])
        elif query_type == "domain":
            candidate_urls.extend([f"https://rdap.verisign.com/com/v1/domain/{current_target}", f"https://rdap.verisign.com/net/v1/domain/{current_target}"])

        for url in candidate_urls:
            data = fetch_from_url(url, timeout=timeout)
            if data and any(k in data for k in ("handle", "name", "ldhName", "events")):
                return data

    fallback = fetch_rapiddns_fallback(target, timeout=timeout)
    return fallback if fallback else {"error": f"Failed to retrieve data for {target}."}


def extract_entities(data: Dict[str, Any]) -> Dict[str, list]:
    entities_by_role: Dict[str, list] = {}
    def parse_entity(entity: Dict[str, Any]):
        vcard = entity.get("vcardArray", [])
        name, email = "", ""
        if len(vcard) > 1 and isinstance(vcard[1], list):
            for item in vcard[1]:
                if not (isinstance(item, list) and len(item) >= 4):
                    continue
                if item[0] == "fn":
                    name = item[3]
                elif item[0] == "email":
                    email = item[3]
        for role in entity.get("roles", ["entity"]):
            entities_by_role.setdefault(role, []).append({"handle": entity.get("handle", ""), "name": name, "email": email})
        for sub in entity.get("entities", []):
            parse_entity(sub)
    for ent in data.get("entities", []):
        parse_entity(ent)
    return entities_by_role


def format_ip_summary(data: Dict[str, Any], ip_str: str) -> str:
    if "error" in data:
        return f"[Lookup Failed] {ip_str}: {data['error']}"
    if data.get("is_fallback"):
        records = "\n".join([f"    - {r['host']} ({r['type']}) [{r.get('date', '')}]" for r in data.get("records", [])])
        return f"[RapidDNS Fallback IP Intelligence] {ip_str}\n  • Resolved Hosts / Reverse DNS:\n{records}"

    handle, name, country = data.get("handle", "N/A"), data.get("name", "N/A"), data.get("country", "N/A")
    ip_v, start, end = str(data.get("ipVersion", "4")).lower().replace("v", ""), data.get("startAddress", ""), data.get("endAddress", "")
    entities = extract_entities(data)
    abuse = ", ".join([f"{c['name'] or c['handle']} <{c['email']}>" for c in entities.get("abuse", []) if c.get('email')]) or "N/A"
    reg_info = ", ".join([c['name'] or c['handle'] for c in entities.get("registrant", []) if c.get('name') or c.get('handle')]) or name

    return "\n".join([
        "[ICANN / RIR RDAP IP Intelligence]",
        f"  • Query Target : {ip_str} (IPv{ip_v})",
        f"  • Network Name : {name} ({handle})",
        f"  • IP Range     : {f'{start} ~ {end}' if start else 'N/A'}",
        f"  • Country Code : {country}",
        f"  • Status       : {', '.join(data.get('status', [])) if isinstance(data.get('status'), list) else data.get('status', 'Active')}",
        f"  • Organization : {reg_info}",
        f"  • Abuse Contact: {abuse}",
        f"  • Port43 WHOIS : {data.get('port43', 'N/A')}",
    ])


def format_domain_summary(data: Dict[str, Any], domain_str: str) -> str:
    if "error" in data:
        return f"[Lookup Failed] {domain_str}: {data['error']}"
    if data.get("is_fallback"):
        records = "\n".join([f"    - {r['host']} -> {r['ip']} ({r['type']})" for r in data.get("records", [])])
        return f"[RapidDNS Fallback Domain Intelligence] {domain_str}\n  • Discovered DNS Records:\n{records}"

    ldh, handle, events = data.get("ldhName", domain_str), data.get("handle", "N/A"), {e.get("eventAction"): e.get("eventDate") for e in data.get("events", []) if isinstance(e, dict)}
    ns_list = [ns.get("ldhName", "") for ns in data.get("nameservers", []) if isinstance(ns, dict) and ns.get("ldhName")]
    entities = extract_entities(data)
    registrar = entities.get("registrar", [{}])[0].get("name", "N/A")
    abuse = ", ".join([c['email'] for c in entities.get("abuse", []) if c.get('email')]) or "N/A"

    return "\n".join([
        "[ICANN RDAP Domain Intelligence]",
        f"  • Domain Name  : {ldh}",
        f"  • Registry ID  : {handle}",
        f"  • Registrar    : {registrar}",
        f"  • Abuse Contact: {abuse}",
        f"  • Status       : {', '.join(data.get('status', [])) if isinstance(data.get('status'), list) else data.get('status', 'Active')}",
        f"  • Created Date : {events.get('registration', 'N/A')}",
        f"  • Expires Date : {events.get('expiration', 'N/A')}",
        f"  • Updated Date : {events.get('last changed', events.get('last update', 'N/A'))}",
        f"  • Nameservers  : {', '.join(ns_list[:4]) if ns_list else 'N/A'}",
        f"  • Port43 WHOIS : {data.get('port43', 'N/A')}",
    ])


def format_asn_summary(data: Dict[str, Any], asn_str: str) -> str:
    if "error" in data:
        return f"[RDAP Lookup Failed] AS{asn_str}: {data['error']}"
    handle, name, country = data.get("handle", f"AS{asn_str}"), data.get("name", "N/A"), data.get("country", "N/A")
    s_aut, e_aut = data.get("startAutnum", asn_str), data.get("endAutnum", asn_str)
    org_name = extract_entities(data).get("registrant", [{}])[0].get("name", name)

    return "\n".join([
        "[ICANN / RIR RDAP ASN Intelligence]",
        f"  • AS Number    : {f'AS{s_aut}' if s_aut == e_aut else f'AS{s_aut} ~ AS{e_aut}'} ({handle})",
        f"  • AS Name      : {name}",
        f"  • Organization : {org_name}",
        f"  • Country Code : {country}",
        f"  • Port43 WHOIS : {data.get('port43', 'N/A')}",
    ])


def main():
    parser = argparse.ArgumentParser(description="Authoritative ICANN RDAP Intelligence Lookup")
    parser.add_argument("target", help="IP address, Domain, or ASN (e.g. AS13335)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON response")
    parser.add_argument("--timeout", type=int, default=5, help="Query timeout in seconds")
    
    args = parser.parse_args()
    q_type, cleaned = detect_target_type(args.target)
    raw_data = fetch_rdap(q_type, cleaned, timeout=args.timeout)
    
    if args.json:
        print(json.dumps(raw_data, indent=2, ensure_ascii=False))
    elif q_type == "ip":
        print(format_ip_summary(raw_data, cleaned))
    elif q_type == "domain":
        print(format_domain_summary(raw_data, cleaned))
    elif q_type == "autnum":
        print(format_asn_summary(raw_data, cleaned))


if __name__ == "__main__":
    main()
