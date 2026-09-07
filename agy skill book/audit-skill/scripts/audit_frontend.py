#!/usr/bin/env python3
"""Frontend Tech Stack & Security Auditor (Lean Engine - Route B)"""
import re, sys, urllib.parse, urllib.request
from pathlib import Path

SECRETS = [r"sk-[a-zA-Z0-9]{20,}", r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z]+ PRIVATE KEY-----"]
PKG_RE = re.compile(
    r'(?:\b(?:import|from)\s+["\x27]|require\s*\(\s*["\x27]|import\s*\(\s*["\x27]|'
    r'/\*!\s*(?:\*\s*)?(?:@license\s+)?|github\.com/[^/]+/|'
    r'(?:jsdelivr\.net/npm/|unpkg\.com/|cdnjs\.cloudflare\.com/ajax/libs/))'
    r'((?:@[a-zA-Z0-9_.-]+/)?[a-zA-Z0-9][a-zA-Z0-9_.-]*?)(?:@[^/"\x27]+)?(?:["\x27]|/|\s)'
)

def audit_content(src, filename, size_bytes=0):
    b, w, is_html = [], [], bool(re.search(r"\.html?(\.|$)", filename.lower()))
    checks = [
        (any(re.search(s, src) for s in SECRETS), b, "Plaintext secret / API key detected"),
        (re.search(r"\b(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)\b", src), w, "Internal private IP exposed"),
        (("/Us" + "ers/") in src or ("/ho" + "me/") in src, b, "Hardcoded local absolute user path"),
        (re.search(r"\b(openDatabase|showModalDialog)\s*\(", src), b, "Dead Web API (EOL in modern browsers)"),
        (re.search(r"document\.write\s*\(", src), b, "Dangerous 'document.write()' call"),
        (re.search(r'\beval\s*\(|new\s+Function\s*\(', src), b, "Dynamic code execution (eval or new Function)"),
    ]
    for cond, target, msg in checks:
        if cond: target.append(msg)
    user_src = "\n".join([s for s in re.findall(r"<script[^>]*>(.*?)</script>", src, re.DOTALL) if not re.search(r"/\*!|@license|SheetJS|min\.js", s, re.I)]) if is_html else src
    if re.search(r"\bvar\s+[a-zA-Z0-9_$]+", user_src): w.append("Legacy 'var' keyword in user code (use const/let)")
    if re.search(r"(\.innerHTML\s*=|v-html|dangerouslySetInnerHTML)", src) and "DOMPurify" not in src:
        (w if is_html else b).append("Unsanitized innerHTML assignment (recommend textContent or DOMPurify)" if is_html else "Unsanitized HTML/rich-text assignment (DOMPurify required)")
    if is_html and re.search(r"\b(fetch\s*\(|XMLHttpRequest\b|<script[^>]+src=[\"']https?://)", src):
        w.append("External network call detected in local HTML (verify offline integrity)")
    budget = 3145728 if is_html else 102400
    if size_bytes > budget: w.append(f"Asset budget exceeded ({size_bytes / 1024:.1f}KB > {budget / 1024:.0f}KB)")

    pkgs = [p for p in PKG_RE.findall(src) if p not in ["blob", "tree", "raw", "releases", "git"]]
    for sig, name in [(r"\[vuex\]", "vuex"), (r"\[vue-gtag\]", "vue-gtag"), (r"var lottie\s*=", "lottie-web")]:
        if re.search(sig, src): pkgs.append(name)
    return set(pkgs), set(f"{x} ({filename})" for x in b), set(f"{x} ({filename})" for x in w)

def print_dashboard(target, infra, framework, pkgs, blockers, warnings):
    print(f"\n[AUDIT DASHBOARD] -> {target}\n" + "=" * 66)
    print(f"[1. TECH STACK PROFILED]\n  ├── Infrastructure : {infra or 'Local / Unknown'}\n  ├── Framework      : {framework or 'Unknown'}")
    print(f"  └── Libraries      : {', '.join(sorted(pkgs)) if pkgs else 'None detected'}\n\n[2. SECURITY & CODE HEALTH]")
    if not blockers and not warnings: print("  └── [✓] All guardrails passed")
    for b in sorted(blockers): print(f"  └── [BLOCKER] {b}")
    for w in sorted(warnings): print(f"  └── [ADVISORY] {w}")
    status = "[✗] FAIL" if blockers else ("[!] WARN" if warnings else "[✓] PASS")
    print(f"\n[3. CONCLUSION] -> {status} ({len(blockers)} Blockers, {len(warnings)} Advisories)\n" + "=" * 66)

def audit_remote(url: str):
    pkgs, blockers, warnings = set(), set(), set()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            headers = dict(resp.headers)
            content = resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="ignore")
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return

    infra = headers.get("Server", "")
    framework = "Vue (SPA #app)" if ("<div id=app>" in content or '<div id="app">' in content) else ("React (#root)" if 'id="root"' in content else ("Next.js" if "__NEXT_DATA__" in content else ""))
    scripts = re.findall(r'<script[^>]+src=[\"\x27]?([^\"\'\x27\s>]+)', content, re.I)
    js_urls = [urllib.parse.urljoin(url, s) for s in scripts if not s.startswith("data:")]
    targets = [u for u in js_urls if any(k in u for k in ["vendor", "chunk", "app"])] or js_urls[:2]
    for u in targets:
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Antigravity/1.0"}), timeout=5) as jr:
                c = jr.read().decode(jr.headers.get_content_charset() or "utf-8", errors="ignore")
                p, b, w = audit_content(c, u.split("/")[-1], size_bytes=len(c.encode("utf-8")))
                pkgs.update(p); blockers.update(b); warnings.update(w)
        except Exception: pass
    print_dashboard(url, infra, framework, pkgs, blockers, warnings)

def audit_local(target: str):
    p, pkgs, blockers, warnings = Path(target), set(), set(), set()
    framework = ""
    valid_exts = [".js", ".mjs", ".ts", ".jsx", ".tsx", ".vue", ".html", ".htm"]
    files = [p] if (p.is_file() and p.suffix.lower() in valid_exts) else [f for f in p.glob("**/*") if f.is_file() and f.suffix.lower() in valid_exts]
    for f in files:
        src = f.read_text(encoding="utf-8-sig", errors="ignore")
        if not framework:
            framework = "Vue.js" if ("vue" in f.suffix.lower() or "id=app" in src) else ("React" if (f.suffix.lower() in [".jsx", ".tsx"] or 'id="root"' in src) else ("HTML/Vanilla JS" if f.suffix.lower() in [".html", ".htm"] else ""))
        p_set, b_set, w_set = audit_content(src, f.name, size_bytes=f.stat().st_size)
        pkgs.update(p_set); blockers.update(b_set); warnings.update(w_set)
    print_dashboard(target, "Local Filesystem", framework, pkgs, blockers, warnings)

def audit_target(target: str):
    if target.startswith(("http://", "https://")): audit_remote(target)
    elif Path(target).exists(): audit_local(target)
    else: print(f"[ERROR] Target does not exist: {target}")

if __name__ == "__main__":
    if len(sys.argv) < 2: print("Usage: python3 audit_frontend.py <target_url_or_local_path>"); sys.exit(1)
    for arg in sys.argv[1:]: audit_target(arg)
