#!/usr/bin/env python3
"""
NoAI-Note Dedicated First-Mile Detox & Standup Test Engine.
Standard library only. Robust, stateless, zero-bloat.
Enhanced with cross-domain support, contextual whitelists, and date/metric discrimination.
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CJK_PATTERN = r"[\u4e00-\u9fff]"


def load_rules(lang: str = "zhtw") -> Dict[str, Any]:
    rule_file = DATA_DIR / ("rules_zhtw.json" if lang == "zhtw" else "rules_en.json")
    if not rule_file.exists():
        return {}
    with open(rule_file, "r", encoding="utf-8") as f:
        return json.load(f)


def count_cjk(text: str) -> int:
    return len(re.findall(CJK_PATTERN, text))


def detect_language(text: str) -> str:
    cjk = count_cjk(text)
    return "zhtw" if (cjk >= 15 or (text.strip() and cjk / len(text.strip()) > 0.15)) else "en"


def extract_context(text: str, pattern: str, limit: int = 2) -> List[str]:
    matches: List[str] = []
    for seg in re.split(r"(?<=[。！？\n])\s*", text):
        s = seg.strip()
        if re.search(pattern, s):
            matches.append(s if len(s) <= 90 else f"{s[:87]}…")
        if len(matches) >= limit:
            break
    return matches


# --- 1. Detox Engine ---

def run_detox(text: str, lang: str = "auto") -> Dict[str, Any]:
    lang = detect_language(text) if lang == "auto" else lang
    rules = load_rules(lang)
    findings: Dict[str, Any] = {
        "lang": lang, "chars": len(text), "cjk_chars": count_cjk(text),
        "simplified": [], "mainland_terms": [], "formulaic_patterns": [], "buzzwords": []
    }
    if lang == "zhtw":
        sim_set = set(rules.get("simplified_chars", []))
        sim = Counter(ch for ch in text if ch in sim_set)
        if sim:
            findings["simplified"] = [{"char": ch, "count": c} for ch, c in sim.most_common(15)]
        for cat, lbl in [("cn_high", "高信心（強烈建議替換）"), ("cn_mid", "職場套話"), ("cn_ctx", "需看語境")]:
            for term, suggestion in rules.get(cat, {}).items():
                if term == suggestion:
                    continue
                pat = r"(?<!演)算法" if term == "算法" else re.escape(term)
                m_list = re.findall(pat, text)
                c = len(m_list)
                if c > 0:
                    findings["mainland_terms"].append({
                        "term": term, "count": c, "suggest": suggestion, "category": lbl,
                        "example": (extract_context(text, pat, limit=1) or [""])[0]
                    })
        for p in rules.get("patterns", []):
            m = len(re.findall(p["regex"], text))
            # 破折號預算動態化：若僅出現 1 次且篇幅大於 80 字（如正常副標題或附註），不視為套路警告
            if p.get("label", "").startswith("破折號") and m <= 1 and len(text) > 80:
                continue
            if m > 0:
                findings["formulaic_patterns"].append({"label": p["label"], "count": m, "advice": p["advice"], "examples": extract_context(text, p["regex"], limit=2)})
        for b in rules.get("buzz", []):
            m = len(re.findall(b["regex"], text))
            if m > 0:
                findings["buzzwords"].append({"label": b["label"], "count": m, "advice": b["advice"], "examples": extract_context(text, b["regex"], limit=2)})
    else:
        for p in rules.get("generic_patterns", []):
            m = len(re.findall(p["regex"], text, re.I))
            if m > 0:
                findings["formulaic_patterns"].append({"label": p["label"], "count": m, "advice": p.get("advice", ""), "examples": extract_context(text, p["regex"], limit=2)})
    return findings


def report_detox(res: Dict[str, Any]) -> str:
    lines = [f"# NoAI-Note 排毒檢驗報告 ({'繁中台灣' if res['lang'] == 'zhtw' else 'English'})\n分析字數：{res['chars']} 字（中文字元：{res['cjk_chars']}）\n"]
    has_issue = False
    if res["simplified"]:
        has_issue = True
        s = "、".join(f"{x['char']}({x['count']})" for x in res["simplified"])
        lines.append(f"### [警告] 發現簡體字殘留：\n- {s}\n")
    if res["mainland_terms"]:
        has_issue = True
        lines.extend(["### [攔截] 發現非在地術語／常用陸詞：", "| 原詞 | 次數 | 台灣在地化建議 | 分類 |", "|---|---|---|---|"])
        for m in sorted(res["mainland_terms"], key=lambda x: -x["count"]):
            lines.append(f"| **{m['term']}** | {m['count']} | `{m['suggest']}` | {m['category']} |")
        lines.append("")
    if res["formulaic_patterns"]:
        has_issue = True
        lines.append("### [警告] AI 套路句式：")
        for p in res["formulaic_patterns"]:
            lines.append(f"- **{p['label']}** ({p['count']} 次)：{p['advice']}")
            for ex in p["examples"]:
                lines.append(f"  > 原文：{ex}")
        lines.append("")
    if res["buzzwords"]:
        has_issue = True
        lines.append("### [警告] 空洞 Buzzwords：")
        for b in res["buzzwords"]:
            lines.append(f"- **{b['label']}** ({b['count']} 次)：{b['advice']}")
        lines.append("")
    if not has_issue:
        lines.append("[PASS] **未發現顯著 AI 味、外來用語或套路句式，內文品質良好。**\n")
    return "\n".join(lines)


# --- 2. Gate 1 Standup Test Engine ---

def is_whitelisted(term: str, text: str, whitelists: Dict[str, List[str]] = None) -> bool:
    if whitelists is None:
        whitelists = load_rules("zhtw").get("technical_whitelists", {})
    return any(re.search(pat, text, re.I) for pat in whitelists.get(term, []))


def run_gate1(title_or_assertion: str, rules: Dict[str, Any] = None) -> Dict[str, Any]:
    text = title_or_assertion.strip()
    circuit_broken, reasons = False, []
    rules = rules or load_rules("zhtw")
    g1 = rules.get("gate1_rules", {})
    whitelists = rules.get("technical_whitelists", {})

    # 1. PR Formula Pattern checks
    for item in g1.get("pr_patterns", []):
        if re.search(item["regex"], text):
            reasons.append(f"發現{item['desc']}")
            circuit_broken = True

    # 破折號動態預算：單一破折號可作為合法副標題或附註，僅阻斷超過門檻之使用
    dash_limit = g1.get("dash_threshold", 2)
    if len(re.findall(r"—{1,2}|――", text)) >= dash_limit:
        reasons.append(f"發現過度使用破折號（≥{dash_limit} 組，易流於公關套路炫技）")
        circuit_broken = True

    # 2. Strict Buzzwords
    found_strict = [b for b in g1.get("strict_banned", []) if b in text]
    if found_strict:
        reasons.append(f"包含空洞公關詞彙 [{', '.join(found_strict)}]")
        circuit_broken = True

    # 3. Contextual Buzzwords (Checked against technical whitelist from SSOT JSON)
    found_ctx = [
        term for term in g1.get("contextual_banned", [])
        if term in text and not is_whitelisted(term, text, whitelists)
    ]
    if found_ctx:
        reasons.append(f"包含易流於空泛的詞彙（若屬技術專有名詞請明確標示上下文）[{', '.join(found_ctx)}]")
        circuit_broken = True

    # 4. Metric & Action Checks
    has_metric = bool(re.search(g1.get("metric_regex", ""), text, re.I)) if g1.get("metric_regex") else False
    has_action = bool(re.search(g1.get("action_regex", ""), text)) if g1.get("action_regex") else False

    if not has_metric and not has_action and not circuit_broken:
        reasons.append("缺乏明確決策/工程動作或量化驗證數據，建議補充具體成果。")

    return {
        "text": text,
        "passed": not circuit_broken and (has_metric or has_action),
        "circuit_broken": circuit_broken,
        "has_metric": has_metric,
        "has_action": has_action,
        "reasons": reasons
    }


def report_gate1(res: Dict[str, Any], advisory: bool = False) -> str:
    status_str = "[PASS] **GATE 1 通過**" if res["passed"] else ("[ADVISORY WARNING]" if advisory else "[FAIL] **GATE 1 門禁未通過**")
    lines = [f"# Gate 1: First-Mile 晨會直白與資訊量測試\n檢驗標題／斷言：『**{res['text']}**』\n", status_str]
    if res["passed"]:
        lines.append("- 符合高階晨會標準：具備明確行動決策或量化數據，無公關套話。\n")
    else:
        for r in res["reasons"]:
            lines.append(f"- [!] {r}")
        lines.append("\n**改寫建議**：請直述「做了什麼動作/決策」、「解決什麼實質阻礙」或「達到什麼具體驗收數據」。\n")
    return "\n".join(lines)
