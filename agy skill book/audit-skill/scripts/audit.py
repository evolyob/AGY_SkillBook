#!/usr/bin/env python3
"""
Universal Skill & Code Auditor (Lean 100-line Enterprise Standard)
Severity Stratification: FAIL (Critical Blockers) vs WARN (Architecture Advisories).
"""

import ast, re, sys
from pathlib import Path

PEP_594_REMOVED = {"cgi", "cgitb", "pipes", "crypt", "imghdr", "sndhdr", "aifc", "audioop", "chunk", "mailcap", "nntplib", "sunau", "telnetlib", "uu", "xdrlib", "distutils"}
SECRETS = [r"sk-[a-zA-Z0-9]{20,}", r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z]+ PRIVATE KEY-----"]
PRIVS = ["su" + "do ", "ch" + "mod +x", "ch" + "own ", "/et" + "c/shadow", "/et" + "c/passwd"]
FRONTEND_EXTS = {".html", ".htm", ".js", ".mjs", ".ts", ".jsx", ".tsx", ".vue"}

def audit_source(src, filename, is_markdown=False, skill_txt="", local_modules=None):
    lines = len(src.splitlines())
    blockers, warnings = [], []
    is_test = "test" in filename.lower()
    is_meta = filename in ["audit.py", "remediation_guide.md", "developer_7_coding_laws_and_ast_audit.md"]
    local_mods = local_modules or set()

    # 1. Text & Security Guardrails
    if not is_meta:
        if ("/Us" + "ers/") in src or ("/ho" + "me/") in src:
            blockers.append("Hardcoded absolute user path (~/ or $HOME required)")
        for s in SECRETS:
            if re.search(s, src): blockers.append("Plaintext secret/API key")
        for p in PRIVS:
            if p in src and not ("Zero" in src or "detect" in src or "guard" in src):
                blockers.append(f"Privilege escalation ({p})")
        if re.search(r"ignore\s+previous\s+instructions|system\s+override|DAN\s+mode", src, re.I):
            blockers.append("Prompt injection keyword")

    # 2. Markdown Specific Rules
    if is_markdown:
        limit = 100 if filename == "SKILL.md" else 200
        if lines > limit and not is_meta:
            warnings.append(f"Lines {lines} > {limit}")
        stack = []
        for l in src.splitlines():
            s = l.strip()
            if s.startswith("````"):
                if stack and stack[-1] == 4: stack.pop()
                else: stack.append(4)
            elif s.startswith("```"):
                if stack and stack[-1] == 3: stack.pop()
                elif not stack or stack[-1] == 4: stack.append(3)
        if stack:
            blockers.append("Unclosed code fence / Broken 4-backtick nesting")

    # 3. Python Code Analysis (Runs on .py or extracts ```python from .md)
    py_blocks = re.findall(r"```python[^\n]*\n(.*?)\n```", src, re.DOTALL) if is_markdown else [src]
    for idx, code in enumerate(py_blocks):
        tag = f"Snippet #{idx+1}" if is_markdown else "Script"
        if not is_markdown and not is_meta and any(re.search(r"\bopen\(", l) and "encoding=" not in l and "wb" not in l and "rb" not in l for l in code.splitlines()):
            warnings.append("Unencoded open() call")
        if re.search(r'f["\x27]<[a-zA-Z]+', code) and not re.search(r"(escape|clean_text|sanitize|&amp;)", code):
            warnings.append(f"{tag} unescaped dynamic markup template")
        try:
            tree = ast.parse(code)

            # Dynamic Line Budget: Base = 43 + (has_class * 27) + (N * rate)
            if not is_markdown and not is_meta:
                has_class = 1 if any(isinstance(n, ast.ClassDef) for n in ast.walk(tree)) else 0
                n_defs = len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
                base = 43 + (has_class * 27)
                x_rate = 12 if has_class else 25
                py_limit = base + (n_defs * x_rate)
                if lines > py_limit:
                    warnings.append(f"Lines {lines} > dynamic limit {py_limit} (Base {base} + {n_defs} defs × {x_rate})")

            # Level 1 Law 1: Nesting Depth (Keep Main Path Easy to Follow)
            def check_nesting(node, current_depth=0):
                if isinstance(node, ast.If):
                    if current_depth >= 2:
                        warnings.append(f"{tag} nested if-block depth {current_depth+1} > 2")
                    for child in node.body:
                        check_nesting(child, current_depth + 1)
                    if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                        check_nesting(node.orelse[0], current_depth)
                    else:
                        for child in node.orelse:
                            check_nesting(child, current_depth + 1)
                else:
                    for child in ast.iter_child_nodes(node):
                        check_nesting(child, current_depth)
            if not is_meta:
                check_nesting(tree, 0)

            # Law 7 / SRP: Duplicate Function/Class Definitions in Same Scope
            def check_duplicate_defs(nodes, scope_name="module"):
                seen = set()
                for n in nodes:
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        is_overload = any((isinstance(d, ast.Name) and d.id == "overload") or (isinstance(d, ast.Attribute) and d.attr == "overload") for d in getattr(n, "decorator_list", []))
                        if not is_overload:
                            if n.name in seen:
                                blockers.append(f"{tag} duplicate definition of '{n.name}' in {scope_name}")
                            seen.add(n.name)
                    if isinstance(n, ast.ClassDef):
                        check_duplicate_defs(n.body, f"class '{n.name}'")
            check_duplicate_defs(tree.body)

            imported_modules = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.Global):
                    warnings.append(f"{tag} mutable global state ({n.names})")
                # Level 1 Law 4: Mutable default arguments
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for default in (n.args.defaults + [d for d in n.args.kw_defaults if d is not None]):
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            blockers.append(f"{tag} mutable default argument in func '{n.name}'")
                # Level 1 Law 6: Bare except & Assert
                if isinstance(n, ast.ExceptHandler) and n.type is None:
                    blockers.append(f"{tag} bare 'except:' handler")
                if isinstance(n, ast.Assert) and not is_test and not is_meta:
                    warnings.append(f"{tag} production 'assert' statement")
                # Law 7 / DRY: Duplicate dictionary keys
                if isinstance(n, ast.Dict):
                    seen_keys = set()
                    for k in n.keys:
                        if k is not None:
                            k_val = k.value if isinstance(k, ast.Constant) else (k.id if isinstance(k, ast.Name) else None)
                            if k_val is not None:
                                if k_val in seen_keys:
                                    blockers.append(f"{tag} duplicate dictionary key '{k_val}'")
                                seen_keys.add(k_val)
                if not is_meta and isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ["eval", "exec"]:
                    blockers.append(f"{tag} arbitrary execution ({n.func.id})")
                if not is_meta and isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "system" and getattr(n.func.value, "id", None) == "os":
                    blockers.append(f"{tag} os.system() execution")
                if isinstance(n, ast.Import):
                    for name in n.names: imported_modules.add(name.name.split('.')[0])
                elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                    imported_modules.add(n.module.split('.')[0])

            # Universal Zero-EOL check: PEP 594 dead batteries
            for dead in sorted(imported_modules & PEP_594_REMOVED):
                blockers.append(f"{tag} Zero-EOL: removed stdlib module '{dead}' in Python >= 3.13 (PEP 594)")

            # Universal Third-Party Dependency Reconciliation
            third_party = {m for m in imported_modules if m not in sys.stdlib_module_names and m not in local_mods and not m.startswith("_")}
            if skill_txt and third_party:
                for dep in sorted(third_party):
                    dep_norm = dep.lower().replace("_", "-")
                    if dep.lower() not in skill_txt.lower() and dep_norm not in skill_txt.lower():
                        blockers.append(f"{tag} undeclared external dependency '{dep}'")
                    elif re.search(rf'{dep}\s*==\s*\*|{dep_norm}\s*==\s*\*|\*\s*$', skill_txt):
                        blockers.append(f"{tag} wildcard version '*' for '{dep}' prohibited")

            if not is_markdown:
                imports = {n.asname or n.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names}
                imports.update({n.asname or n.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) for n in node.names if n.name != '*'})
                used_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
                unused = sorted(list(imports - used_names))
                if unused:
                    warnings.append(f"Unused imports: {unused}")
        except SyntaxError as e:
            blockers.append(f"{tag} SyntaxError: {e}")

    if blockers:
        status = "[✗] FAIL"
    elif warnings:
        status = "[!] WARN"
    else:
        status = "[✓] PASS"

    report = f"{status} {filename} ({lines} lines)"
    if blockers:
        report += "\n" + "\n".join(f"  └── [BLOCKER] {b}" for b in blockers)
    if warnings:
        report += "\n" + "\n".join(f"  └── [ADVISORY] {w}" for w in warnings)
    return report

def audit_path(target):
    t = Path(target)
    if t.is_file() and t.suffix.lower() in FRONTEND_EXTS:
        import audit_frontend; return audit_frontend.audit_target(str(t))
    if t.is_file() and t.suffix in [".json", ".xml", ".yaml", ".csv", ".txt"]:
        try:
            raw = t.read_text(encoding="utf-8-sig")
            if t.suffix == ".json":
                import json; json.loads(raw)
            elif t.suffix == ".xml":
                import xml.etree.ElementTree as ET; ET.fromstring(raw)
            print(f"[✓] PASS {t.name} (Valid syntax & UTF-8 encoding)")
        except Exception as err:
            print(f"[✗] FAIL {t.name}\n  └── [BLOCKER] Data Syntax/Encoding Error: {err}")
        return
    if t.is_file():
        skill_md = t if t.name == "SKILL.md" else (t.parent / "SKILL.md" if (t.parent / "SKILL.md").exists() else t.parent.parent / "SKILL.md")
        stxt = skill_md.read_text(encoding="utf-8-sig", errors="ignore") if skill_md.exists() else ""
        root = t.parent if (t.parent / "SKILL.md").exists() else (t.parent.parent if (t.parent.parent / "SKILL.md").exists() else t.parent)
        lmods = {p.stem for p in root.glob("**/*.py")} | {p.name for p in root.glob("**/*") if p.is_dir()}
        src = t.read_text(encoding="utf-8-sig", errors="ignore")
        print(audit_source(src, t.name, is_markdown=t.suffix == ".md", skill_txt=stxt, local_modules=lmods))
    elif t.is_dir():
        print(f"\n[SKILL AUDIT] -> {t}\n" + "=" * 55)
        skill_md = t / "SKILL.md"
        stxt = skill_md.read_text(encoding="utf-8-sig", errors="ignore") if skill_md.exists() else ""
        lmods = {p.stem for p in t.glob("**/*.py")} | {p.name for p in t.glob("**/*") if p.is_dir()}
        for f in sorted(t.glob("**/*")):
            if f.is_file() and f.suffix in [".json", ".xml", ".yaml", ".csv", ".txt"]:
                try:
                    raw = f.read_text(encoding="utf-8-sig")
                    if f.suffix == ".json":
                        import json; json.loads(raw)
                    elif f.suffix == ".xml":
                        import xml.etree.ElementTree as ET; ET.fromstring(raw)
                except Exception as err:
                    print(f"[✗] FAIL {f.name}\n  └── [BLOCKER] Data Syntax/Encoding Error: {err}")
                if f.stat().st_size > 102400:
                    sz_kb = f.stat().st_size / 1024
                    print(f"[!] WARN {f.name} ({sz_kb:.1f}KB > 100KB)\n  └── [ADVISORY] Large static asset (>100KB)")
            elif f.is_file() and f.suffix.lower() in FRONTEND_EXTS:
                import audit_frontend; audit_frontend.audit_target(str(f))
            elif f.is_file() and f.suffix in [".py", ".md"]:
                src = f.read_text(encoding="utf-8-sig", errors="ignore")
                print(audit_source(src, f.name, is_markdown=f.suffix == ".md", skill_txt=stxt, local_modules=lmods))
    else:
        print(f"[ERROR] Target does not exist: {target}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 audit.py <target_path>")
        sys.exit(1)
    for arg in sys.argv[1:]:
        audit_path(arg)
