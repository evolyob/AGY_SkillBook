#!/usr/bin/env python3
"""
Web Endpoint Security & Integrity Auditor (Lean Engine - Route B)
Stateless in-memory auditor: HTTP snapshot, TLS version, cipher & key exchange,
security headers, cookie flags, CSP supply chain count, JS bundle SHA256 integrity,
tech stack fingerprinting, and client-side vulnerability scanning.
Pure Python Standard Library (Zero Dependencies, Zero Disk Writes).
"""

import re, json, hashlib, argparse, ssl, subprocess
import urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

MONITORED_HEADERS = [
    "Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options",
    "X-Content-Type-Options", "X-XSS-Protection", "Cache-Control", "Server",
    "Content-Type", "Content-Length", "Connection", "Accept-Ranges"
]
SECRETS = [r"sk-[a-zA-Z0-9]{20,}", r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z]+ PRIVATE KEY-----"]
PKG_RE = re.compile(
    r'(?:\b(?:import|from)\s+["\x27]|require\s*\(\s*["\x27]|import\s*\(\s*["\x27]|'
    r'/\*!\s*(?:\*\s*)?(?:@license\s+)?|github\.com/[^/]+/|'
    r'(?:jsdelivr\.net/npm/|unpkg\.com/|cdnjs\.cloudflare\.com/ajax/libs/))'
    r'((?:@[a-zA-Z0-9_.-]+/)?[a-zA-Z0-9][a-zA-Z0-9_.-]*?)(?:@[^/"\x27]+)?(?:["\x27]|/|\s)'
)


def parse_cookie_flags(headers: List[Tuple[str, str]]) -> Dict[str, Any]:
    cookie_lines = [v for k, v in headers if k.lower() == "set-cookie"]
    if not cookie_lines:
        return {"httpOnly": None, "secure": None, "sameSite": None, "raw_count": 0}

    http_only, secure, samesite = False, False, "none"
    for line in cookie_lines:
        if re.search(r';\s*HttpOnly', line, re.I):
            http_only = True
        if re.search(r';\s*Secure', line, re.I):
            secure = True
        m_ss = re.search(r';\s*SameSite=([^;]+)', line, re.I)
        if m_ss:
            samesite = m_ss.group(1).strip().lower()

    return {"httpOnly": http_only, "secure": secure, "sameSite": samesite, "raw_count": len(cookie_lines)}


def extract_meta_and_framework(html_text: str) -> Tuple[str, str, str]:
    m_title = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.I | re.DOTALL)
    title = re.sub(r'\s+', ' ', m_title.group(1)).strip() if m_title else ""
    m_desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html_text, re.I) or \
             re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', html_text, re.I)
    desc = re.sub(r'\s+', ' ', m_desc.group(1)).strip() if m_desc else ""

    framework = "WordPress" if ("wp-content" in html_text or "wp-includes" in html_text) else (
        "Vue (SPA #app)" if ("<div id=app>" in html_text or '<div id="app">' in html_text) else (
            "React (#root)" if 'id="root"' in html_text else (
                "Next.js" if "__NEXT_DATA__" in html_text else "Vanilla / Unknown"
            )
        )
    )
    return title, desc, framework


def extract_csp_domains(csp: str) -> List[str]:
    if not csp:
        return []
    domains = set()
    for token in re.findall(r"https?://[^\s;'\"]+", csp):
        host = urllib.parse.urlparse(token).netloc.lower()
        if host:
            domains.add(host)
    return sorted(domains)


def filter_security_headers(raw_headers: List[Tuple[str, str]]) -> Tuple[Dict[str, str], str]:
    header_map = {k.lower(): v for k, v in raw_headers}
    matched = [f"{h}: {header_map[h.lower()].strip()}" for h in MONITORED_HEADERS if h.lower() in header_map]
    matched.sort()
    h_hash = hashlib.md5("\n".join(matched).encode("utf-8")).hexdigest() if matched else "none"
    return {h: header_map[h.lower()] for h in MONITORED_HEADERS if h.lower() in header_map}, h_hash


def audit_js_code(src: str, filename: str) -> Tuple[List[str], List[str], List[str]]:
    blockers, warnings = [], []
    if any(re.search(s, src) for s in SECRETS):
        blockers.append(f"Plaintext secret / API key detected ({filename})")
    if re.search(r"\b(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)\b", src):
        warnings.append(f"Internal private IP exposed ({filename})")
    if ("/Us" + "ers/") in src or ("/ho" + "me/") in src:
        blockers.append(f"Hardcoded local user path ({filename})")
    if re.search(r"\b(openDatabase|showModalDialog)\s*\(", src):
        blockers.append(f"Dead Web API call ({filename})")
    if re.search(r"document\.write\s*\(", src):
        blockers.append(f"Dangerous document.write call ({filename})")
    if re.search(r'\beval\s*\(|new\s+Function\s*\(', src):
        blockers.append(f"Dynamic code execution eval/new Function ({filename})")
    if re.search(r"(\.innerHTML\s*=|v-html|dangerouslySetInnerHTML)", src) and "DOMPurify" not in src:
        blockers.append(f"Unsanitized HTML/rich-text assignment ({filename})")

    pkgs = [p for p in PKG_RE.findall(src) if p not in ["blob", "tree", "raw", "releases", "git"]]
    for sig, name in [(r"\[vuex\]", "vuex"), (r"\[vue-gtag\]", "vue-gtag"), (r"var lottie\s*=", "lottie-web"), (r"DOMPurify", "DOMPurify")]:
        if re.search(sig, src) and name not in pkgs:
            pkgs.append(name)
    return pkgs, blockers, warnings


def inspect_js_bundles(url: str, html_text: str, ctx: ssl.SSLContext, timeout: int = 10) -> Tuple[List[Dict[str, Any]], List[str], List[str], List[str]]:
    scripts = re.findall(r'<script[^>]+src=[\"\x27]?([^\"\'\x27\s>]+)', html_text, re.I)
    js_urls = [urllib.parse.urljoin(url, s) for s in scripts if not s.startswith("data:")]
    targets = [u for u in js_urls if any(k in u for k in ["vendor", "chunk", "app"])] or js_urls[:3]

    bundles, all_pkgs, all_blockers, all_warnings = [], set(), set(), set()
    for u in targets:
        fname = u.split("/")[-1].split("?")[0] or (u.split("?")[-1].split("=")[0] if "?" in u else "script.js")
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as jr:
                js_bytes = jr.read()
                js_text = js_bytes.decode("utf-8", errors="replace")
                sha256 = hashlib.sha256(js_bytes).hexdigest()
                pkgs, b, w = audit_js_code(js_text, fname)
                bundles.append({"name": fname, "url": u, "size_kb": round(len(js_bytes) / 1024, 1), "sha256": sha256})
                all_pkgs.update(pkgs)
                all_blockers.update(b)
                all_warnings.update(w)
        except Exception as e:
            bundles.append({"name": fname, "url": u, "error": str(e)})

    return bundles, sorted(all_pkgs), sorted(all_blockers), sorted(all_warnings)


def probe_tls_cipher(url: str, fallback_sock: Any = None, timeout: int = 3) -> str:
    clean_host = re.sub(r'^https?://', '', url).split('/')[0].split(':')[0]
    cmd = ["curl", "-v", "-k", "--connect-timeout", str(timeout), "-s", "-o", "/dev/null", f"https://{clean_host}"]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout + 2)
        m = re.search(r'SSL connection using\s+([^\r\n]+)', res.stdout)
        if m:
            parts = [p.strip() for p in m.group(1).split('/')]
            return " / ".join(parts[:3])
    except Exception:
        pass
    if fallback_sock and hasattr(fallback_sock, "cipher"):
        c_info = fallback_sock.cipher()
        if c_info:
            tls_ver = fallback_sock.version() or c_info[1]
            return f"{tls_ver} / {c_info[0]}"
    return "N/A"


def capture_snapshot(url: str, timeout: int = 15) -> Dict[str, Any]:
    if not re.match(r'^https?://', url, re.I):
        url = "https://" + url

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})

    tls_cipher, raw_headers = None, []
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            sock = getattr(getattr(resp, "fp", None), "raw", None)
            s = getattr(sock, "_sock", None) or sock
            status, body_bytes, raw_headers = resp.status, resp.read(), list(resp.headers.items())
            tls_cipher = probe_tls_cipher(url, fallback_sock=s)
    except urllib.error.HTTPError as e:
        status, body_bytes = e.code, e.read() if hasattr(e, "read") else b""
        raw_headers = list(e.headers.items()) if hasattr(e, "headers") else []
        tls_cipher = probe_tls_cipher(url)
    except Exception as e:
        return {"error": str(e), "url": url}

    html_text = body_bytes.decode("utf-8", errors="replace")
    title, desc, framework = extract_meta_and_framework(html_text)
    active_headers, header_md5 = filter_security_headers(raw_headers)
    csp_domains = extract_csp_domains(active_headers.get("Content-Security-Policy", ""))
    bundles, pkgs, blockers, warnings = inspect_js_bundles(url, html_text, ctx, timeout=min(timeout, 10))

    return {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "title": title,
        "description": desc,
        "framework": framework,
        "tls_cipher": tls_cipher,
        "target_header_md5": header_md5,
        "security_headers": active_headers,
        "csp_domains": csp_domains,
        "bundles": bundles,
        "packages": pkgs,
        "security_blockers": blockers,
        "security_warnings": warnings,
        "page_md5": hashlib.md5(body_bytes).hexdigest(),
        "cookie_status": parse_cookie_flags(raw_headers)
    }


def format_markdown_report(snapshot: Dict[str, Any]) -> str:
    if "error" in snapshot:
        return f"[ERROR] {snapshot['url']}: {snapshot['error']}"

    c_stat = snapshot.get("cookie_status", {})
    cookie_str = f"HttpOnly: {c_stat.get('httpOnly')}, Secure: {c_stat.get('secure')}, SameSite: {c_stat.get('sameSite')}"
    if c_stat.get("raw_count", 0) == 0:
        cookie_str = "No Set-Cookie header"

    pkgs = snapshot.get("packages", [])
    pkg_str = ", ".join(pkgs) if pkgs else "None detected"
    csp_doms = snapshot.get("csp_domains", [])
    csp_count_str = f"{len(csp_doms)} 個" if csp_doms else "0 個"

    lines = [
        f"**[Web Security & Integrity Snapshot (Route B)]**: `{snapshot['url']}`",
        f"| 指標 (Metric) | 觀測數值 (Observed Value) |",
        f"| :--- | :--- |",
        f"| **HTTP 狀態碼** | `{snapshot['status']}` |",
        f"| **TLS 加密套件 (Cipher)** | `{snapshot.get('tls_cipher') or 'N/A'}` |",
        f"| **框架架構 (Framework)** | `{snapshot.get('framework', 'Unknown')}` |",
        f"| **第三方函式庫 (Libs)** | `{pkg_str}` |",
        f"| **供應鏈授權網域 (CSP)** | `{csp_count_str}` |",
        f"| **安全標頭 MD5** | `{snapshot['target_header_md5']}` |",
        f"| **HTML MD5** | `{snapshot['page_md5']}` |",
        f"| **Cookie 安全配置** | `{cookie_str}` |"
    ]

    blockers = snapshot.get("security_blockers", [])
    warnings = snapshot.get("security_warnings", [])
    lines.append("\n**[客戶端代碼安全審計 (Client-Side Guardrails)]**:")
    if not blockers and not warnings:
        lines.append("- [PASS] 無偵測到阻斷級弱點 (All Guardrails Passed)")
    for b in blockers:
        lines.append(f"- [BLOCKER] {b}")
    for w in warnings:
        lines.append(f"- [ADVISORY] {w}")

    bundles = snapshot.get("bundles", [])
    if bundles:
        lines.append("\n**[前端核心腳本防竄改基準 (JS Bundle Integrity)]**:")
        for b in bundles:
            if "sha256" in b:
                lines.append(f"- `{b['name']}` ({b['size_kb']} KB) -> `SHA256:{b['sha256'][:16]}...`")

    sec_hdrs = snapshot.get("security_headers", {})
    if sec_hdrs:
        lines.append("\n**[現行安全標頭配置 (Active Security Headers)]**:")
        for h, v in sorted(sec_hdrs.items()):
            lines.append(f"- **`{h}`**: `{v}`")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Web Endpoint Security & Integrity Auditor (sec-intel Route B)")
    parser.add_argument("url", help="Target URL or domain (e.g. https://example.com or example.com)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON snapshot")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds (default: 15)")
    args = parser.parse_args()

    snapshot = capture_snapshot(args.url, timeout=args.timeout)
    if args.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return

    print(format_markdown_report(snapshot))


if __name__ == "__main__":
    main()
