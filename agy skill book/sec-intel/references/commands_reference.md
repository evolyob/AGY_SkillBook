# Sec-Intel Command & Parameter Reference (v2.0)

## 1. Standalone Script Reference

### 1.1 ICANN RDAP (Registry Intelligence)
```bash
# Query IP (IPv4 / IPv6)
python3 <skill_dir>/scripts/icann_rdap_lookup.py 192.0.2.1

# Query Domain
python3 <skill_dir>/scripts/icann_rdap_lookup.py example.com

# Query Autonomous System Number
python3 <skill_dir>/scripts/icann_rdap_lookup.py AS13335
```

### 1.2 Real DNS & Email Security Auditor (POSIX dig)
```bash
# Comprehensive Domain Email & DNS audit (SPF, DMARC, DKIM, MX, NS, DNSSEC)
python3 <skill_dir>/scripts/dns_auditor.py example.com

# Audit with custom DKIM selector
python3 <skill_dir>/scripts/dns_auditor.py example.com --selector google
```

### 1.3 Anti-Noise DNSBL & IP Blacklist Scanner
```bash
# Check IP on 4 active DNSBL blacklists with PTR reverse lookup
python3 <skill_dir>/scripts/mxtoolbox_lookup.py 192.0.2.1

# Domain email security check (delegates to dns_auditor)
python3 <skill_dir>/scripts/mxtoolbox_lookup.py example.com
```

### 1.4 Dual-Engine Vulnerability Intelligence (EUVD & Google OSV)
```bash
# Query specific CVE or EUVD ID (Primary: ENISA EUVD, Fallback: Google OSV.dev)
python3 <skill_dir>/scripts/euvd_lookup.py CVE-2024-3094

# Search package vulnerabilities with filters
python3 <skill_dir>/scripts/euvd_lookup.py OpenSSL --min-score 9.0 --min-epss 50.0 --size 3
```

### 1.5 Web Security & Two-Pass TLS Auditor (web_monitor.py)
```bash
# Snapshot and audit web endpoint: Two-Pass TLS, 11 Security Headers (A~F), Cookies, Script SHA256
python3 <skill_dir>/scripts/web_monitor.py https://example.com
```

---

## 2. Router CLI Options (`intel_router.py`)

| Flag | Type | Description |
| :--- | :--- | :--- |
| `<TARGET>` | Positional | IP, Domain, ASN, URL, or CVE-xxxx-xxxx |
| `--web` | Flag | Run web security, Two-Pass TLS, and header scoring audit |
| `--dns` / `--email` / `--mxtoolbox` | Flag | Run Real DNS audit (SPF/DMARC/MX/DNSSEC) or anti-noise DNSBL |
| `--all` | Flag | Execute comprehensive suite (RDAP + Real DNS + Web Audit) |
| `--no-tls` | Flag | Skip TLS probe for domain/IP |
| `--vuln` | Flag | Search software package across dual-engine vulnerability databases |
| `--json` | Flag | Output raw JSON object |
| `--min-score` | Float | Filter minimum CVSS score |
| `--min-epss` | Float | Filter minimum EPSS exploit probability |
