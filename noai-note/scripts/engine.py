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

TECHNICAL_WHITELISTS = {
    "佈局": [r"(?:CSS|css|網格|版面|介面|UI|畫布|晶片|電路|PCB|layout|Layout)\s*佈局", r"佈局\s*(?:元件|模組|設計|規劃)"],
    "維度": [r"(?:資料庫|數據|多維度|特徵|向量|空間|分析|報表|指標|維度表)\s*維度", r"維度\s*(?:模型|分析|表|削減)"],
    "打造": [r"打造\s*(?:CI/CD|pipeline|系統|環境|工具|架構|模組|平台|測試鏈)"],
}


def is_whitelisted(term: str, text: str) -> bool:
    if term not in TECHNICAL_WHITELISTS:
        return False
    for pattern in TECHNICAL_WHITELISTS[term]:
        if re.search(pattern, text, re.I):
            return True
    return False


def run_gate1(title_or_assertion: str) -> Dict[str, Any]:
    text = title_or_assertion.strip()
    circuit_broken, reasons = False, []

    # 1. PR Formula Pattern checks
    pr_patterns = [
        (r"以.+搭配.+落實", "對稱式公關口號（以...搭配...落實...）"),
        (r"透過.+旨在.+進而", "公關遞進套話（透過...旨在...進而...）"),
        (r"全面(提升|打造|推動|深化|落實|賦能)", "空洞公關動詞（全面...）"),
        (r"[？?]|這意味著什麼", "自問自答反問句"),
    ]
    for pattern, desc in pr_patterns:
        if re.search(pattern, text):
            reasons.append(f"發現{desc}")
            circuit_broken = True

    # 破折號動態預算：單一破折號可作為合法副標題或附註，僅阻斷 2 組以上過度使用
    dashes = len(re.findall(r"—{1,2}|――", text))
    if dashes >= 2:
        reasons.append("發現過度使用破折號（≥2 組，易流於公關套路炫技）")
        circuit_broken = True

    # 2. Strict Buzzwords (Always unacceptable in executive/engineering notes)
    strict_banned = ["賦能", "閉環", "打法", "抓手", "賦能體系", "守住底線", "深耕細作"]
    found_strict = [b for b in strict_banned if b in text]
    if found_strict:
        reasons.append(f"包含空洞公關詞彙 [{', '.join(found_strict)}]")
        circuit_broken = True

    # 3. Contextual Buzzwords (Checked against technical whitelist)
    contextual_banned = ["痛點", "心智", "壁壘", "佈局", "維度", "打造"]
    found_contextual = []
    for term in contextual_banned:
        if term in text and not is_whitelisted(term, text):
            found_contextual.append(term)
    if found_contextual:
        reasons.append(f"包含易流於空泛的詞彙（若屬技術專有名詞請明確標示上下文）[{', '.join(found_contextual)}]")
        circuit_broken = True

    # 4. Metric Check (Discriminate performance/operational metrics from calendar timestamps)
    metric_regex = (
        r"(?:\d+(?:\.\d+)?\s*(?:%|倍|ms|毫秒|秒|QPS|TPS|GB|TB|MB|KB|筆|次|件|元|萬|億)"
        r"|(?<!\b19\d\d)(?<!\b20\d\d)(?:縮短|耗時|節省|提升|降低)\s*\d+\s*(?:天|日|小時|分|週|個月)"
        r"|SLA|KPI|P99|P95|P50|ROI|MTTR|MTBF)"
    )
    has_metric = bool(re.search(metric_regex, text, re.I))

    # 5. Action Check (Broadened across Engineering, Architecture, DevOps, Governance, and Operations)
    action_regex = (
        r"修復|遷移|重構|隔離|部署|替換|上線|降低|減少|縮短|提升|限制|攔截|阻斷|消除|清理|收斂|整併|監控|"
        r"核准|裁決|簽署|驗收|採購|預算|撥款|調配|發布|定案|修訂|終止|展延|合規|審查|盤點|交付|"
        r"取消|廢止|改由|導入|轉移|重寫|剔除|升級|解耦|重組|實作|整合|對齊|抽換|切換|啟用|停用|優化|快取|調校|歸檔|備份"
    )
    has_action = bool(re.search(action_regex, text))

    if not has_metric and not has_action and not circuit_broken:
        reasons.append("缺乏明確決策/工程動作或量化驗證數據，建議補充具體成果。")

    passed = not circuit_broken and (has_metric or has_action)
    return {
        "text": text,
        "passed": passed,
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
