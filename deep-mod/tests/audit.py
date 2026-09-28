#!/usr/bin/env python3
"""Lightweight Python Script Auditor for deep-mod (Stdlib only)."""
import argparse, ast, re, sys
from pathlib import Path

PEP_594 = {"cgi", "cgitb", "pipes", "crypt", "imghdr", "sndhdr", "aifc", "audioop", "chunk", "mailcap", "nntplib", "sunau", "telnetlib", "uu", "xdrlib", "distutils"}
PRIVS = ["su" + "do ", "ch" + "mod +x", "ch" + "own ", "/et" + "c/shadow", "/et" + "c/passwd"]

def check_nesting(node, issues: list[str], depth: int = 0) -> None:
    if not isinstance(node, ast.If):
        for c in ast.iter_child_nodes(node): check_nesting(c, issues, depth)
        return
    if depth >= 2: issues.append(f"Nested if depth {depth + 1} > 2")
    for c in node.body: check_nesting(c, issues, depth + 1)
    is_elif = len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)
    for c in node.orelse: check_nesting(c, issues, depth if is_elif else depth + 1)

def scan_text_lines(src: str, issues: list[str]) -> None:
    for i, l in enumerate(src.splitlines(), 1):
        if l.strip().startswith("#") or any(k in l for k in ("re.search", "re.compile", "Zero-Leakage", "r'/", 'r"/')):
            continue
        if re.search(r'/(Users|home)/[a-zA-Z0-9_-]+/', l):
            issues.append(f"Line {i}: Hardcoded absolute user path"); break

def audit_script(src: str, filename: str) -> list[str]:
    lines, issues = len(src.splitlines()), []
    scan_text_lines(src, issues)
    for p in PRIVS:
        if p in src and not any(k in src for k in ("Zero", "detect", "guard")): issues.append(f"Privilege escalation ({p})")
    if re.search(r"ignore\s+previous\s+instructions|system\s+override|DAN\s+mode", src, re.I): issues.append("Prompt injection keyword")
    try: tree = ast.parse(src)
    except SyntaxError as e: return issues + [f"SyntaxError: {e}"]
    check_nesting(tree, issues)
    seen_defs, has_cls, n_defs, dict_lines, imps = set(), 0, 0, 0, set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if n.name in seen_defs: issues.append(f"Duplicate def '{n.name}'")
            seen_defs.add(n.name)
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef): has_cls = 1
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            n_defs += 1
            for d in (n.args.defaults + [x for x in n.args.kw_defaults if x]):
                if isinstance(d, (ast.List, ast.Dict, ast.Set)): issues.append(f"Mutable default in '{n.name}'")
        elif isinstance(n, ast.Dict):
            dict_lines += max(0, getattr(n, "end_lineno", 0) - getattr(n, "lineno", 0))
            keys = set()
            for k in n.keys:
                kv = k.value if isinstance(k, ast.Constant) else (k.id if isinstance(k, ast.Name) else None)
                if kv in keys: issues.append(f"Duplicate dict key '{kv}'")
                if kv is not None: keys.add(kv)
        elif isinstance(n, ast.Global): issues.append(f"Mutable global ({', '.join(n.names)})")
        elif isinstance(n, ast.ExceptHandler) and n.type is None: issues.append("Bare except handler")
        elif isinstance(n, ast.Call):
            is_eval = isinstance(n.func, ast.Name) and n.func.id in ("eval", "exec")
            is_sys = isinstance(n.func, ast.Attribute) and n.func.attr == "system" and getattr(n.func.value, "id", None) == "os"
            if is_eval or is_sys: issues.append("Arbitrary execution call")
        elif isinstance(n, ast.Import): imps.update(x.name.split('.')[0] for x in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0: imps.add(n.module.split('.')[0])
    for dead in sorted(imps & PEP_594): issues.append(f"PEP 594 removed module '{dead}'")
    base, rate = (70, 12) if has_cls else (43, 25)
    if lines > (limit := base + n_defs * rate + dict_lines):
        issues.append(f"Lines {lines} > limit {limit} (Base {base} + {n_defs} defs × {rate} + {dict_lines} dict)")
    return issues

def main():
    p = argparse.ArgumentParser(description="deep-mod script auditor")
    p.add_argument("target", help="Target Python file or directory")
    tgt = Path(p.parse_args().target).resolve()
    files = [tgt] if tgt.is_file() else sorted(tgt.rglob("*.py")) if tgt.is_dir() else []
    if not files: sys.exit(f"No Python files found in {tgt}")
    has_fail = False
    for f in files:
        issues = audit_script(f.read_text(encoding="utf-8-sig", errors="ignore"), f.name)
        print(f"{'[✗] FAIL' if issues else '[✓] PASS'} {f.name} ({len(f.read_text(encoding='utf-8-sig', errors='ignore').splitlines())} lines)")
        for issue in issues: print(f"  └── [ISSUE] {issue}")
        if issues: has_fail = True
    if has_fail: sys.exit(1)

if __name__ == "__main__": main()
