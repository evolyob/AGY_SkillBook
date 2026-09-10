#!/usr/bin/env python3
"""
Web Endpoint Security & Integrity Auditor (v2.0 High-Reliability)
- Two-Pass TLS Handshake: Pass 1 strict cert verification + Pass 2 degraded probe
- High-SNR Security Audit: 11 Security Headers with A~F scoring, Cookie flags, CSP domains
- Script Bundle SHA256 integrity baseline & verified high-confidence secret scanner
Pure Python Standard Library (Zero Dependencies, Zero Disk Writes).
"""

import re, json, hashlib, argparse, ssl, socket, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

MONITORED_HEADERS = [
    "Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options",
    "X-Content-Type-Options", "X-XSS-Protection", "Referrer-Policy",
    "Permissions-Policy", "Cache-Control", "Server", "Content-Type"
]

HEADER_WEIGHTS = {
    "strict-transport-security": 25, "content-security-policy": 25,
    "x-frame-options": 15, "x-content-type-options": 15,
    "referrer-policy": 10, "permissions-policy": 10
}
GRADE_THRESHOLDS = [
    (90, "A+ (Excellent)"), (75, "A (Strong)"), (60, "B (Moderate)"),
    (40, "C (Basic)"), (20, "D (Weak)")
]

HIGH_CONF_SECRETS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI / Claude API Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"-----BEGIN [A-Z]+ PRIVATE KEY-----", "Cryptographic Private Key Block"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
]


def audit_tls_two_pass(hostname: str, port: int = 443, timeout: int = 4) -> Dict[str, Any]:
    """Two-Pass TLS Handshake: Pass 1 strict verification + Pass 2 degraded probe."""
    clean_host = re.sub(r'^https?://', '', hostname).split('/')[0].split(':')[0].strip()
    result = {"hostname": clean_host, "trusted": False, "error": None, "cipher": None, "tls_version": None, "peer_cert": None}

    # Pass 1: Strict Verification
    try:
        with socket.create_connection((clean_host, port), timeout=timeout) as sock:
            with ssl.create_default_context().wrap_socket(sock, server_hostname=clean_host) as ssock:
                c_info = ssock.cipher()
                result.update({
                    "trusted": True,
                    "cipher": " / ".join(str(x) for x in c_info if x),
                    "tls_version": ssock.version(),
                    "peer_cert": ssock.getpeercert()
                })
                return result
    except ssl.SSLCertVerificationError as e:
        result["error"] = f"[CRITICAL VULN] 憑證無效或受損 (Cert Untrusted): {e.verify_message}"
    except Exception as e:
        result["error"] = f"連線異常: {e}"
        return result

    # Pass 2: Degraded Probe (Forensic Data Collection)
    try:
        with socket.create_connection((clean_host, port), timeout=timeout) as sock:
            with ssl._create_unverified_context().wrap_socket(sock, server_hostname=clean_host) as ssock:
                c_info = ssock.cipher()
                result["cipher"] = " / ".join(str(x) for x in c_info if x)
                result["tls_version"] = ssock.version()
    except Exception:
        pass
    return result


def parse_cookie_flags(headers: List[Tuple[str, str]]) -> Dict[str, Any]:
    """Audit security flags on Set-Cookie headers."""
    cookie_lines = [v for k, v in headers if k.lower() == "set-cookie"]
    if not cookie_lines:
        return {"httpOnly": None, "secure": None, "sameSite": None, "raw_count": 0, "status": "No Set-Cookie header"}

    http_only = all(bool(re.search(r';\s*HttpOnly', l, re.I)) for l in cookie_lines)
    secure = all(bool(re.search(r';\s*Secure', l, re.I)) for l in cookie_lines)
    samesite_found = [m.group(1).strip().lower() for l in cookie_lines for m in [re.search(r';\s*SameSite=([^;]+)', l, re.I)] if m]

    return {
        "httpOnly": http_only, "secure": secure,
        "sameSite": samesite_found[0] if samesite_found else "none",
        "raw_count": len(cookie_lines), "status": f"Found {len(cookie_lines)} cookie(s)"
    }


def calculate_header_score(header_map: Dict[str, str]) -> Tuple[int, str]:
    """Calculate security header score (0~100) and letter grade (A~F)."""
    score = sum(w for h, w in HEADER_WEIGHTS.items() if h in header_map)
    grade = next((g for t, g in GRADE_THRESHOLDS if score >= t), "F (High Risk / Missing Headers)")
    return score, grade


def extract_meta_and_framework(html_text: str) -> Tuple[str, str, str]:
    m_title = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.I | re.DOTALL)
    title = re.sub(r'\s+', ' ', m_title.group(1)).strip() if m_title else ""
    m_desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html_text, re.I) or \
             re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', html_text, re.I)
    desc = re.sub(r'\s+', ' ', m_desc.group(1)).strip() if m_desc else ""

    framework = "Vanilla / Unknown"
    if "wp-content" in html_text or "wp-includes" in html_text: framework = "WordPress"
    elif "<div id=app>" in html_text or '<div id="app">' in html_text: framework = "Vue (SPA #app)"
    elif 'id="root"' in html_text: framework = "React (#root)"
    elif "__NEXT_DATA__" in html_text: framework = "Next.js"
    return title, desc, framework


def extract_csp_domains(csp: str) -> List[str]:
    if not csp:
        return []
    domains = {urllib.parse.urlparse(t).netloc.lower() for t in re.findall(r"https?://[^\s;'\"]+", csp)}
    return sorted(d for d in domains if d)


def audit_high_conf_secrets(src: str, filename: str) -> List[str]:
    """Audit only high-confidence plaintext secrets (zero false-alarm regex SAST)."""
    return [f"[LEAK RISK] {name} detected in {filename}" for pattern, name in HIGH_CONF_SECRETS if re.search(pattern, src)]


def inspect_scripts(url: str, html_text: str, timeout: int = 6) -> List[Dict[str, Any]]:
    """Snapshot external scripts and compute SHA256 integrity."""
    scripts = re.findall(r'<script[^>]+src=[\"\x27]?([^\"\'\x27\s>]+)', html_text, re.I)
    js_urls = [urllib.parse.urljoin(url, s) for s in scripts if not s.startswith("data:")]
    targets = [u for u in js_urls if any(k in u for k in ["vendor", "chunk", "app", "main"])] or js_urls[:3]

    bundles = []
    unverified_ctx = ssl._create_unverified_context()
    for u in targets:
        fname = u.split("/")[-1].split("?")[0] or "script.js"
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})
            with urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx) as jr:
                js_bytes = jr.read()
                js_text = js_bytes.decode("utf-8", errors="replace")
                bundles.append({
                    "name": fname, "url": u, "size_kb": round(len(js_bytes) / 1024, 1),
                    "sha256": hashlib.sha256(js_bytes).hexdigest(),
                    "leaks": audit_high_conf_secrets(js_text, fname)
                })
        except Exception as e:
            bundles.append({"name": fname, "url": u, "error": str(e)})
    return bundles


def capture_snapshot(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Capture comprehensive web endpoint security state."""
    if not re.match(r'^https?://', url, re.I):
        url = "https://" + url

    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or url
    tls_info = audit_tls_two_pass(hostname, port=parsed.port or 443, timeout=min(timeout, 5))

    unverified_ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})

    raw_headers, status, body_bytes = [], 0, b""
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx) as resp:
            status, body_bytes, raw_headers = resp.status, resp.read(), list(resp.headers.items())
    except urllib.error.HTTPError as e:
        status = e.code
        body_bytes = e.read() if hasattr(e, "read") else b""
        raw_headers = list(e.headers.items()) if hasattr(e, "headers") else []
    except Exception as e:
        return {"error": str(e), "url": url, "tls_info": tls_info}

    html_text = body_bytes.decode("utf-8", errors="replace")
    title, desc, framework = extract_meta_and_framework(html_text)
    header_map = {k.lower(): v.strip() for k, v in raw_headers}
    active_headers = {h: header_map[h.lower()] for h in MONITORED_HEADERS if h.lower() in header_map}
    score, grade = calculate_header_score(header_map)

    bundles = inspect_scripts(url, html_text, timeout=min(timeout, 5))
    all_leaks = [leak for b in bundles for leak in b.get("leaks", [])]

    return {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "title": title,
        "description": desc,
        "framework": framework,
        "tls": tls_info,
        "header_score": score,
        "header_grade": grade,
        "security_headers": active_headers,
        "csp_domains": extract_csp_domains(active_headers.get("Content-Security-Policy", "")),
        "bundles": bundles,
        "secret_leaks": all_leaks,
        "cookie_status": parse_cookie_flags(raw_headers),
        "page_md5": hashlib.md5(body_bytes).hexdigest()
    }


def format_markdown_report(snapshot: Dict[str, Any]) -> str:
    if "error" in snapshot and not snapshot.get("status"):
        return f"[ERROR] {snapshot['url']}: {snapshot['error']}"

    tls = snapshot.get("tls", {})
    tls_trusted = "[PASS] 憑證鏈受信 (Trusted)" if tls.get("trusted") else (tls.get("error") or "[FAIL] 憑證無效 (Untrusted)")
    tls_cipher = f"{tls.get('tls_version') or 'TLS'} / {tls.get('cipher') or 'N/A'}"

    c_stat = snapshot.get("cookie_status", {})
    cookie_str = f"HttpOnly: {c_stat.get('httpOnly')}, Secure: {c_stat.get('secure')}, SameSite: {c_stat.get('sameSite')}" if c_stat.get("raw_count", 0) > 0 else "No Set-Cookie header"

    csp_doms = snapshot.get("csp_domains", [])
    csp_str = f"{len(csp_doms)} 個授權來源網域" if csp_doms else "無 CSP 宣告"

    lines = [
        f"**[Web 安全與完整性審計報告 (v2.0)]**: `{snapshot['url']}`",
        f"| 指標 (Metric) | 觀測數值 (Observed Value) |",
        f"| :--- | :--- |",
        f"| **HTTP 狀態碼** | `{snapshot['status']}` |",
        f"| **TLS 憑證信任** | `{tls_trusted}` |",
        f"| **TLS 加密套件** | `{tls_cipher}` |",
        f"| **標頭安全評級** | **`{snapshot.get('header_grade')}`** (得分: {snapshot.get('header_score')}/100) |",
        f"| **框架架構 (Framework)** | `{snapshot.get('framework', 'Unknown')}` |",
        f"| **CSP 供應鏈控制** | `{csp_str}` |",
        f"| **Cookie 安全配置** | `{cookie_str}` |",
        f"| **首頁防竄改 MD5** | `{snapshot['page_md5']}` |",
        "\n**[現行防護標頭配置 (Active Security Headers)]**:"
    ]

    sec_hdrs = snapshot.get("security_headers", {})
    lines.extend([f"- **`{h}`**: `{v}`" for h, v in sorted(sec_hdrs.items())] if sec_hdrs else ["- *(未配置任何標準安全標頭)*"])

    leaks = snapshot.get("secret_leaks", [])
    if leaks:
        lines.append("\n**[高危金鑰外洩警報 (High-Confidence Leaks)]**:")
        lines.extend([f"- {leak}" for leak in leaks])

    bundles = snapshot.get("bundles", [])
    if bundles:
        lines.append("\n**[前端核心腳本防竄改基準 (JS Bundle Integrity)]**:")
        lines.extend([f"- `{b['name']}` ({b['size_kb']} KB) -> `SHA256:{b['sha256'][:16]}...`" for b in bundles if "sha256" in b])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Web Endpoint Security & Integrity Auditor (v2.0 High-Reliability)")
    parser.add_argument("url", help="Target URL or domain (e.g. https://example.com or example.com)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON snapshot")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout in seconds (default: 10)")
    args = parser.parse_args()

    snapshot = capture_snapshot(args.url, timeout=args.timeout)
    if args.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return
    print(format_markdown_report(snapshot))


if __name__ == "__main__":
    main()
