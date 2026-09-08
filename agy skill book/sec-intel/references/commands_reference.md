# Sec-Intel Command & Parameter Reference

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

### 1.2 MXToolbox & DNSBL (Email & Blacklist Diagnostics)
```bash
# Check IP on 5 global DNSBL blacklists
python3 <skill_dir>/scripts/mxtoolbox_lookup.py 192.0.2.1

# Check Domain MX, SPF, and DMARC diagnostics
python3 <skill_dir>/scripts/mxtoolbox_lookup.py example.com
```

### 1.3 ENISA EUVD (Vulnerability Database)
```bash
# Query specific CVE or EUVD ID
python3 <skill_dir>/scripts/euvd_lookup.py CVE-2024-3094

# Search package vulnerabilities with filters
python3 <skill_dir>/scripts/euvd_lookup.py OpenSSL --min-score 9.0 --min-epss 50.0 --size 3
```

### 1.4 Web Security & Integrity Auditor (web_monitor.py)
```bash
# Snapshot and audit web endpoint security headers, cookies, and client code
python3 <skill_dir>/scripts/web_monitor.py https://example.com
```

---

## 2. Router CLI Options (`intel_router.py`)

| Flag | Type | Description |
| :--- | :--- | :--- |
| `<TARGET>` | Positional | IP, Domain, ASN, URL, or CVE-xxxx-xxxx |
| `--web` | Flag | Run web security & integrity audit |
| `--mxtoolbox` / `--blacklist` | Flag | Run MXToolbox & DNSBL diagnostics |
| `--no-curl` | Flag | Disable curl probe for domain/IP |
| `--vuln` | Flag | Search software package in EUVD |
| `--json` | Flag | Output raw JSON object |
| `--min-score` | Float | Filter minimum CVSS score |
| `--min-epss` | Float | Filter minimum EPSS exploit probability |
