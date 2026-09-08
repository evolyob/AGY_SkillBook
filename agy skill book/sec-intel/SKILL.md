---
name: sec-intel
description: Authoritative, evidence-based intelligence lookup for IPs, ASNs, Domains, and CVEs via ICANN RDAP, MXToolbox/DNSBL, and ENISA EUVD. Focuses on objective technical facts with zero speculative hallucinations.
---

# Security Intelligence & Vulnerability Lookup (`sec-intel`)

## Core Capabilities
- **ICANN RDAP**: IP, ASN, and Domain registry lookup (RFC 7480-7484).
- **MXToolbox & DNSBL**: SPF, DMARC, MX diagnostics and 5 real-time DNSBL blacklists.
- **ENISA EUVD**: European CVE metadata, CVSS 4.0/3.1, and EPSS exploit probabilities.
- **Web Security & Integrity Monitor**: Web endpoint security snapshot (status, framework, 11 security headers, Cookie flags, CSP supply chain inventory, JS bundle SHA256 integrity, and client-side vulnerability guardrails).

## Operating Rules
1. **Truthfulness Baseline**: Report only verified technical facts. Never speculate attack scenarios without concrete content evidence. Explicitly label registrar default pages as `Domain Parking`.
2. **Intent Gating**:
   - **CVE Targets** (`CVE-xxxx-xxxx`, `EUVD-xxxx-xxxx`): Execute lookup directly.
   - **URL Targets** (`http://...`, `https://...`): Execute Web Security & Integrity Monitor directly.
   - **Non-CVE Targets** (Domain, IP, Hostname): Ask user to choose focus before executing:
     1. ICANN RDAP (Registry & curl probe)
     2. MXToolbox & DNSBL (Email & Blacklists)
     3. Web Security Audit (Headers, Cookies & Integrity Snapshot)
     4. Comprehensive (All)
3. **Output Formatting**: Render probe/connection findings in Markdown tables. Omit non-existent or empty fields entirely (never print placeholder rows like "None" or "N/A").

## CLI Entrypoint
```bash
python3 <skill_dir>/scripts/intel_router.py <TARGET> [--web] [--mxtoolbox] [--no-curl] [--vuln]
```

## References
- [`commands_reference.md`](references/commands_reference.md): Standalone script commands and CLI parameter reference.
- [`abuse_report_template.md`](references/abuse_report_template.md): Takedown notification email templates.
