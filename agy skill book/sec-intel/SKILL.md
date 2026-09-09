---
name: sec-intel
description: Authoritative, evidence-based intelligence lookup for IPs, ASNs, Domains, and CVEs via ICANN RDAP, Real DNS (dig), and Dual-Engine EUVD/OSV. Focuses on objective technical facts with zero speculative hallucinations.
---

# Security Intelligence & Vulnerability Lookup (`sec-intel` v2.0)

## Core Capabilities
- **ICANN RDAP**: IP, ASN, and Domain registry lookup (RFC 7480-7484).
- **Real DNS & Anti-Noise DNSBL**: Deterministic POSIX `dig` audit for SPF, DMARC (`p=reject/quarantine/none`), DKIM (`default._domainkey`), MX priorities, NS, and DNSSEC (`ad` Authenticated Data flag), plus parallel anti-noise IP blacklist reputation scanning (filtering `127.255.255.254/255` refusal codes).
- **Dual-Engine Vulnerability Intelligence**: Primary ENISA EUVD (European CVEs, CVSS 4.0/3.1, EPSS exploit predictions) with automatic Anycast CDN fallback to Google OSV.dev for high availability.
- **Web Security & Two-Pass TLS Auditor**: Two-Pass TLS handshake (Pass 1 strict chain verification + Pass 2 degraded forensic probe), 11 security headers with A~F scoring, Cookie security flags (`HttpOnly`, `Secure`, `SameSite`), CSP domain inventory, and script SHA256 integrity baseline.

## Operating Rules
1. **Truthfulness Baseline**: Report only verified technical facts. Never speculate attack scenarios without concrete content evidence. Explicitly label registrar default pages as `Domain Parking`.
2. **Intent Gating (雙向選擇)**:
   - **CVE Targets** (`CVE-xxxx-xxxx`, `EUVD-xxxx-xxxx`): Execute lookup directly.
   - **URL Targets** (`http://...`, `https://...`): Execute Web Security & Two-Pass TLS Auditor directly.
   - **Non-CVE Targets** (Domain, IP, Hostname): Ask user to choose focus before executing:
     1. ICANN RDAP (Registry & Two-Pass TLS probe)
     2. Real DNS & DNSBL (Email Security & Blacklists)
     3. Web Security Audit (Headers A~F, Cookies & Script Integrity)
     4. Comprehensive (All)
3. **Output Formatting**: Render findings in structured text blocks or Markdown tables. Omit non-existent or empty fields entirely (never print placeholder rows like "None" or "N/A").

## CLI Entrypoint
```bash
python3 <skill_dir>/scripts/intel_router.py <TARGET> [--web] [--dns] [--all] [--no-tls] [--vuln]
```

## References
- [`commands_reference.md`](references/commands_reference.md): Standalone script commands and CLI parameter reference.
- [`abuse_report_template.md`](references/abuse_report_template.md): Takedown notification email templates.
