#!/usr/bin/env python3
"""Cross-Skill Semantic Mapping & Registry Engine (`cross-map`)."""

import argparse, ast, json, re, sys
from importlib.util import find_spec
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "groups.json"
SCENARIOS_CUSTOM = Path(__file__).resolve().parent.parent / "data" / "scenarios.json"
SCENARIOS_EXAMPLE = Path(__file__).resolve().parent.parent / "data" / "scenarios.example.json"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
MAX_SCENARIO_DEPTH = 3
SCENARIO_ROUTE_KEYS = (
    "next_scenario",
    "next_scenarios",
    "sub_scenarios",
    "depends_on",
    "next",
    "target_scenario",
    "call_scenario",
)
STEP_ROUTE_KEYS = (
    "sub_scenario",
    "next_scenario",
    "scenario",
    "scenario_id",
    "target_scenario",
    "call_scenario",
)


def load_config(scenarios_path: str | Path | None = None) -> dict:
    cfg = json.loads(DATA_FILE.read_text(encoding="utf-8-sig")) if DATA_FILE.exists() else {}
    if scenarios_path:
        s_file = Path(scenarios_path).expanduser().resolve()
    else:
        s_file = SCENARIOS_CUSTOM if SCENARIOS_CUSTOM.exists() else SCENARIOS_EXAMPLE
    if s_file.exists():
        try:
            sc_cfg = json.loads(s_file.read_text(encoding="utf-8-sig"))
            cfg["scenarios"] = sc_cfg.get("scenarios", [])
            cfg["_scenarios_file"] = str(s_file)
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
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument":
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


def get_scenario_targets(sc: dict, valid_ids: set[str]) -> tuple[list[str], list[str]]:
    raw_targets, unresolved = [], []
    for k in SCENARIO_ROUTE_KEYS:
        val = sc.get(k)
        if isinstance(val, str):
            (raw_targets if val in valid_ids else unresolved).append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    (raw_targets if item in valid_ids else unresolved).append(item)

    for step in sc.get("pipeline", []):
        if not isinstance(step, dict):
            continue
        for k in STEP_ROUTE_KEYS:
            val = step.get(k)
            if isinstance(val, str):
                (raw_targets if val in valid_ids else unresolved).append(val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        (raw_targets if item in valid_ids else unresolved).append(item)
        for k in ("suggested_scenarios", "suggested_skills"):
            val = step.get(k)
            if isinstance(val, list):
                raw_targets.extend(item for item in val if isinstance(item, str) and item in valid_ids)
        skill_val = step.get("skill")
        if isinstance(skill_val, str) and skill_val in valid_ids:
            raw_targets.append(skill_val)

    targets, seen = [], set()
    for t in raw_targets:
        if t not in seen:
            seen.add(t)
            targets.append(t)
    return targets, sorted(set(unresolved))


def _normalize_cycle(cycle: list[str]) -> tuple[str, ...]:
    nodes = cycle[:-1]
    if not nodes:
        return tuple(cycle)
    min_idx = nodes.index(min(nodes))
    rotated = nodes[min_idx:] + nodes[:min_idx] + [nodes[min_idx]]
    return tuple(rotated)


def validate_scenario_dag(scenarios: list[dict], max_depth: int = MAX_SCENARIO_DEPTH) -> dict:
    valid_ids = {s.get("id") for s in scenarios if isinstance(s, dict) and s.get("id")}
    graph, unresolved_map = {}, {}
    for s in scenarios:
        if not isinstance(s, dict) or not s.get("id"):
            continue
        sid = s["id"]
        targets, unres = get_scenario_targets(s, valid_ids)
        graph[sid] = targets
        if unres:
            unresolved_map[sid] = unres

    cycles, depth_violations = [], []
    seen_cycles, seen_violations = set(), set()
    scenario_max_depth = {sid: 0 for sid in valid_ids}
    scenario_issues = {sid: [] for sid in valid_ids}

    def dfs(current: str, path: list[str], current_depth: int):
        root_id = path[0]
        if current_depth > scenario_max_depth[root_id]:
            scenario_max_depth[root_id] = current_depth

        for nxt in graph.get(current, []):
            if nxt in path:
                cycle_slice = path[path.index(nxt):] + [nxt]
                norm_cycle = _normalize_cycle(cycle_slice)
                if norm_cycle in seen_cycles:
                    continue
                seen_cycles.add(norm_cycle)
                cycles.append(cycle_slice)
                warn = f"Cycle detected: {' -> '.join(cycle_slice)}"
                for node in set(cycle_slice):
                    scenario_issues[node].append(warn)
                continue

            next_depth = current_depth + 1
            if next_depth > max_depth:
                violation_path = path + [nxt]
                v_key = tuple(violation_path)
                if v_key in seen_violations:
                    continue
                seen_violations.add(v_key)
                depth_violations.append({"path": violation_path, "depth": next_depth})
                warn = f"Max depth exceeded ({next_depth} > {max_depth}): {' -> '.join(violation_path)}"
                scenario_issues[root_id].append(warn)
                continue

            dfs(nxt, path + [nxt], next_depth)

    for sid in sorted(valid_ids):
        dfs(sid, [sid], 0)

    warnings = []
    for c in cycles:
        warnings.append(f"Cycle detected: {' -> '.join(c)}")
    for v in depth_violations:
        warnings.append(f"Max depth exceeded ({v['depth']} > {max_depth}): {' -> '.join(v['path'])}")
    for sid, unres in unresolved_map.items():
        warnings.append(f"Scenario '{sid}' has unresolved route targets: {', '.join(unres)}")

    scenario_reports = {}
    for sid in sorted(valid_ids):
        issues = scenario_issues.get(sid, [])
        status = "DAG Valid"
        if any("Cycle" in iss for iss in issues):
            status = "Cycle Detected"
        elif any("Max depth" in iss for iss in issues):
            status = "Max Depth Exceeded"
        scenario_reports[sid] = {
            "status": status,
            "max_depth": scenario_max_depth.get(sid, 0),
            "targets": graph.get(sid, []),
            "issues": issues,
        }

    return {
        "is_valid": len(cycles) == 0 and len(depth_violations) == 0,
        "cycles": cycles,
        "depth_violations": depth_violations,
        "warnings": warnings,
        "scenarios": scenario_reports,
        "graph": graph,
        "max_depth_limit": max_depth,
        "max_depth_observed": max(scenario_max_depth.values(), default=0),
    }


def render_scenario_dag_table(dag_res: dict) -> str:
    headers = ["Scenario Pipeline", "DAG Status", "Max Depth", "Route Targets", "Notes"]
    rows = []
    for sid, rep in dag_res.get("scenarios", {}).items():
        targets_str = ", ".join(f"`{t}`" for t in rep["targets"]) if rep["targets"] else "*(Leaf / None)*"
        issues_str = "<br>".join(rep["issues"]) if rep["issues"] else "Cycle-free, Depth <= 3"
        badge = f"`{rep['status']}`" if rep["status"] == "DAG Valid" else f"⚠️ `{rep['status']}`"
        rows.append([f"`{sid}`", badge, str(rep["max_depth"]), targets_str, issues_str])
    return render_table(headers, rows)


def generate_skills_doc(profs: list[dict], cfg: dict) -> str:
    h = cfg.get("headers", {})
    installed = {p["skill"] for p in profs}
    dag_res = validate_scenario_dag(cfg.get("scenarios", []))
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
        sid = g.get("id", "")
        rep = dag_res.get("scenarios", {}).get(sid, {})
        label_prefix = f"⚠️ `[{rep['status']}]` " if rep.get("status") and rep["status"] != "DAG Valid" else ""
        g_rows.append([f"**{label_prefix}{g['label']}**<br>*({sid})*", w_mode, utts, p_skills, pipe_details])

    table_3 = render_table(h.get('groups', []), g_rows) if g_rows else "*(No composite scenario pipelines available for currently installed skills)*"
    return f"# Global Skills Registry & Intent Index (`SKILLS.md`)\n\n> Authoritative capability registry, 4-facet intent matrix, and scenario pipelines for all active skills under this directory.\n> Automatically generated and synchronized via `cross-map`.\n\n---\n\n## 1. Skill Registry & Security Contracts\n\n{render_table(h.get('registry', []), r_rows)}\n\n---\n\n## 2. 4-Facet Intent & Semantic Routing Matrix\n\n{render_table(h.get('matrix', []), m_rows)}\n\n---\n\n## 3. Multi-Skill Scenario Pipelines\n\n{table_3}\n"


def main():
    p = argparse.ArgumentParser(description="Cross-Skill Semantic Mapping & Registry Engine")
    p.add_argument("target", nargs="?", default=str(DEFAULT_ROOT))
    p.add_argument("--sync", action="store_true", help="Sync SKILLS.md in target directory")
    p.add_argument("--json", action="store_true", help="Output raw JSON")
    p.add_argument("--check", action="store_true", help="Output dependency readiness and scenario DAG report")
    p.add_argument("--check-dag", action="store_true", help="Output scenario routing DAG cycle and depth verification")
    p.add_argument("--scenarios", type=str, default=None, help="Path to custom scenarios JSON file")
    p.add_argument("--max-depth", type=int, default=MAX_SCENARIO_DEPTH, help="Maximum allowed scenario invocation depth (default: 3)")
    args = p.parse_args()

    tpath = Path(args.target).expanduser().resolve()
    if not tpath.exists():
        sys.exit(f"Error: Target path does not exist: {tpath}")

    dirs = [tpath] if (tpath / "SKILL.md").exists() else [d for d in sorted(tpath.iterdir()) if d.is_dir() and (d / "SKILL.md").exists()]
    profs = [scan_skill(d) for d in dirs]
    cfg = load_config(args.scenarios)
    dag_res = validate_scenario_dag(cfg.get("scenarios", []), max_depth=args.max_depth)

    if args.json:
        if args.check or args.check_dag:
            print(json.dumps({"skills": profs, "scenario_dag": dag_res}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(profs, ensure_ascii=False, indent=2))
        return

    if args.check_dag:
        print(render_scenario_dag_table(dag_res))
        if dag_res["warnings"]:
            print("\n**Warnings / Violations:**")
            for w in dag_res["warnings"]:
                print(f"- ⚠️ {w}")
        else:
            print(f"\n[OK] All scenario pipelines are DAG valid (Cycle-free, Max Depth <= {args.max_depth}).")
        return

    if args.check:
        headers = ["Skill", "Readiness", "Path"]
        rows = [[f"`{p['skill']}`", p["readiness"], p["path"]] for p in profs]
        print(render_table(headers, rows))
        print("\n---\n")
        print(f"### Scenario Routing DAG Verification (Max Depth <= {args.max_depth})\n")
        print(render_scenario_dag_table(dag_res))
        if dag_res["warnings"]:
            print("\n**Warnings / Violations:**")
            for w in dag_res["warnings"]:
                print(f"- ⚠️ {w}")
        else:
            print(f"\n[OK] All scenario pipelines are DAG valid (Cycle-free, Max Depth <= {args.max_depth}).")
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
