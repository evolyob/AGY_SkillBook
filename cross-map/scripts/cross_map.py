#!/usr/bin/env python3
"""Cross-Skill Semantic Mapping & Registry Engine (`cross-map`)."""

import argparse, ast, json, re, sys
from importlib.util import find_spec
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "groups.json"
SCENARIOS_FILE = Path(__file__).resolve().parent.parent / "data" / "scenarios.example.json"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def load_config() -> dict:
    cfg = json.loads(DATA_FILE.read_text(encoding="utf-8-sig")) if DATA_FILE.exists() else {}
    if SCENARIOS_FILE.exists():
        try:
            sc_cfg = json.loads(SCENARIOS_FILE.read_text(encoding="utf-8-sig"))
            cfg["scenarios"] = sc_cfg.get("scenarios", [])
        except Exception:
            pass
    return cfg


def _extract_imported_pkgs(tree: ast.AST) -> list[str]:
    pkgs = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            pkgs.extend(a.name.split('.')[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            pkgs.append(n.module.split('.')[0])
    return pkgs


def check_readiness(p: Path) -> str:
    sdir = p / "scripts"
    if not sdir.exists():
        return "`Ready`"
    stdlib = sys.stdlib_module_names
    local_modules = {f.stem for f in sdir.glob("*.py")} | {d.name for d in sdir.iterdir() if d.is_dir()}
    missing = []
    for f in sdir.glob("*.py"):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8-sig", errors="replace"))
        except SyntaxError:
            continue
        for pkg in _extract_imported_pkgs(tree):
            if pkg not in stdlib and pkg not in sys.builtin_module_names and pkg not in local_modules and not find_spec(pkg):
                missing.append(pkg)
    return f"`Missing: {', '.join(sorted(set(missing))[:2])}`" if missing else "`Ready`"


def parse_skill_meta(p: Path) -> dict:
    f = p / "SKILL.md"
    if not f.exists():
        return {"name": p.name, "description": "", "intents": [], "utterances": []}
    txt = f.read_text(encoding="utf-8-sig", errors="replace")
    desc = re.search(r"^description:\s*(.+)$", txt, re.M)
    name = re.search(r"^name:\s*(.+)$", txt, re.M)
    intents = re.findall(r"^###?\s+(?:Step\s+\d+:|Phase\s+\d+:|Branch\s+[A-Z]:?)\s*(.+)$", txt, re.M)
    if not intents:
        intents = [x.strip() for x in re.findall(r"^##\s+Objective\s*\n+([^#\n]+)", txt, re.M)]
    body = re.sub(r"^---.*?---\s*", "", txt, flags=re.DOTALL)
    matches = re.findall(r"「([^」]+)」|'([^']+)'|\"([^\"]+)\"", body)
    utts = [next(i for i in t if i).strip("•- \t'\"") for t in matches if any(t)]
    return {
        "name": name.group(1).strip() if name else p.name,
        "description": desc.group(1).strip() if desc else "",
        "intents": [re.sub(r"[\(\)\[\]]", "", i).strip() for i in intents if i.strip()],
        "utterances": [u for u in utts if len(u) > 3 and not u.startswith("--") and "/" not in u][:4]
    }


def parse_sec(p: Path) -> dict:
    f = p / "SECURITY.md"
    if not f.exists():
        return {"channel": "Direct CLI", "flags": [], "slots": []}
    txt = f.read_text(encoding="utf-8-sig", errors="replace")
    ch = re.search(r"##\s+Execution\s*\n+([^#\n]+)", txt)
    return {
        "channel": ch.group(1).strip() if ch else "Single-shot CLI (< 50ms)",
        "flags": sorted(set(re.findall(r"(--[a-zA-Z0-9_-]+)", txt))),
        "slots": sorted(set(re.findall(r"(\[[a-zA-Z0-9_\s/-]+\])", txt)))
    }


def parse_scripts(p: Path) -> dict:
    sdir = p / "scripts"
    if not sdir.exists():
        return {}
    sflags = {}
    for f in sdir.glob("*.py"):
        src = f.read_text(encoding="utf-8-sig", errors="replace")
        flags = set(re.findall(r'["\'](--[a-zA-Z0-9_-]+)["\']', src))
        try:
            tree = ast.parse(src)
        except SyntaxError:
            tree = None
        if tree:
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "add_argument":
                    flags.update(a.value for a in n.args if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value.startswith("--"))
        sflags[f.name] = sorted(flags - {"--help"})
    return sflags


def scan_skill(p: Path) -> dict:
    m, s, scr = parse_skill_meta(p), parse_sec(p), parse_scripts(p)
    return {
        "skill": m["name"], "path": str(p), "description": m["description"], "intents": m["intents"],
        "flags": sorted(set(s["flags"]) | {x for fl in scr.values() for x in fl}),
        "slots": s["slots"], "scripts": scr, "channel": s["channel"], "utterances": m["utterances"],
        "has_sec": (p / "SECURITY.md").exists(),
        "readiness": check_readiness(p)
    }



def render_table(headers: list[str], rows: list[list[str]]) -> str:
    sep = " | ".join([":---"] * len(headers))
    return "\n".join([f"| {' | '.join(headers)} |", f"| {sep} |"] + [f"| {' | '.join(r)} |" for r in rows])


def generate_skills_doc(profs: list[dict], cfg: dict) -> str:
    h = cfg.get("headers", {})
    installed = {p["skill"] for p in profs}
    r_rows = [
        [
            f"**`{p['skill']}`**",
            p["description"].split(".")[0] if p["description"] else p["skill"],
            p["readiness"],
            p["channel"].split(".")[0],
            ", ".join(f"`{f}`" for f in p["flags"][:3]) or "*(Module / API)*",
            f"[`SECURITY.md`](./{p['skill']}/SECURITY.md)" if p.get("has_sec") else "*(Standard)*"
        ]
        for p in profs
    ]
    m_rows = []
    for p in profs:
        sf = " ".join([f"`{f}`" for f in p["flags"][:2]] + [f"`{s}`" for s in p["slots"][:2]]) or "`[path]`"
        utts = "<br>".join(f"• \"{u}\"" for u in p["utterances"][:2]) or "• \"Analyze / Execute\""
        for idx, it in enumerate(p["intents"][:3] or ["default_action"]):
            m_rows.append([f"**`{p['skill']}`**" if idx == 0 else "", f"`{it}`", sf, utts if idx == 0 else ""])
    g_rows = []
    for g in cfg.get("scenarios", []):
        pipe_steps = g.get("pipeline", [])
        matched_pipeline = []
        is_satisfiable = True
        for s in pipe_steps:
            candidates = s.get("suggested_skills", [s["skill"]] if "skill" in s else [])
            matched = next((c for c in candidates if c in installed), None)
            if not matched:
                is_satisfiable = False
                break
            matched_pipeline.append((s, matched))
        if not is_satisfiable or not matched_pipeline:
            continue
        w_mode = f"`{g.get('work_mode', 'phased')}`"
        utts = "<br>".join(f"• \"{t}\"" for t in g.get("utterance_triggers", [])[:2])
        p_skills = "<br>".join(f"**Step {s['step']}**: `{matched}`" for s, matched in matched_pipeline)
        pipe_details = "<br>".join(
            f"**Step {s['step']}**: `{(', '.join(s['flags']) if 'flags' in s else s.get('flag', ''))}` `{s.get('slot', '')}`<br>*(Gate: `{s.get('exit_gate', 'done')}`)*"
            for s, _ in matched_pipeline
        )
        g_rows.append([f"**{g['label']}**<br>*({g['id']})*", w_mode, utts, p_skills, pipe_details])
    
    table_3 = render_table(h.get('groups', []), g_rows) if g_rows else "*(No composite scenario pipelines available for currently installed skills)*"
    return f"# Global Skills Registry & Intent Index (`SKILLS.md`)\n\n> Authoritative capability registry, 4-facet intent matrix, and scenario pipelines for all active skills under this directory.\n> Automatically generated and synchronized via `cross-map`.\n\n---\n\n## 1. Skill Registry & Security Contracts\n\n{render_table(h.get('registry', []), r_rows)}\n\n---\n\n## 2. 4-Facet Intent & Semantic Routing Matrix\n\n{render_table(h.get('matrix', []), m_rows)}\n\n---\n\n## 3. Multi-Skill Scenario Pipelines\n\n{table_3}\n"




def main():
    p = argparse.ArgumentParser(description="Cross-Skill Semantic Mapping & Registry Engine")
    p.add_argument("target", nargs="?", default=str(DEFAULT_ROOT))
    p.add_argument("--sync", action="store_true", help="Sync SKILLS.md in target directory")
    p.add_argument("--json", action="store_true", help="Output raw JSON")
    p.add_argument("--check", action="store_true", help="Output dependency readiness status report")
    args = p.parse_args()

    tpath = Path(args.target).expanduser().resolve()
    if not tpath.exists():
        sys.exit(f"Error: Target path does not exist: {tpath}")

    dirs = [tpath] if (tpath / "SKILL.md").exists() else [d for d in sorted(tpath.iterdir()) if d.is_dir() and (d / "SKILL.md").exists()]
    profs = [scan_skill(d) for d in dirs]
    cfg = load_config()

    if args.json:
        print(json.dumps(profs, ensure_ascii=False, indent=2))
        return

    if args.check:
        headers = ["Skill", "Readiness", "Path"]
        rows = [[f"`{p['skill']}`", p["readiness"], p["path"]] for p in profs]
        print(render_table(headers, rows))
        return

    doc = generate_skills_doc(profs, cfg)
    if not args.sync:
        print(doc)
        return

    target_file = tpath / "SKILLS.md" if tpath.is_dir() and not (tpath / "SKILL.md").exists() else tpath.parent / "SKILLS.md"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(doc, encoding="utf-8-sig")
    print(f"[OK] Successfully synchronized registry to: {target_file}")


if __name__ == "__main__":
    main()
