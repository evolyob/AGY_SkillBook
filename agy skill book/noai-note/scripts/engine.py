#!/usr/bin/env python3
"""
NoAI-Note Dedicated First-Mile Detox & Standup Test Engine.
Standard library only. Robust, stateless, zero-bloat.
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
                c = text.count(term)
                if c > 0:
                    findings["mainland_terms"].append({
                        "term": term, "count": c, "suggest": suggestion, "category": lbl,
                        "example": (extract_context(text, re.escape(term), limit=1) or [""])[0]
                    })
        for p in rules.get("patterns", []):
            m = len(re.findall(p["regex"], text))
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
    lines = [f"# NoAI-Note 筆記排毒報告 ({'繁中台灣' if res['lang'] == 'zhtw' else 'English'})\n分析字數：{res['chars']} 字（中文字元：{res['cjk_chars']}）\n"]
    has_issue = False
    if res["simplified"]:
        has_issue = True
        s = "、".join(f"{x['char']}({x['count']})" for x in res["simplified"])
        lines.append(f"### [警告] 發現簡體字殘留：\n- {s}\n")
    if res["mainland_terms"]:
        has_issue = True
        lines.extend(["### [攔截] 發現陸味用詞與非在地術語：", "| 陸味原詞 | 次數 | 台灣在地化建議 | 分類 |", "|---|---|---|---|"])
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
        lines.append("[PASS] **恭喜！未發現顯著 AI 味、陸味用語或套路句式，內文健康度良好。**\n")
    return "\n".join(lines)


# --- 2. Gate 1 Standup Test Engine ---

TECHNICAL_WHITELISTS = (
    r"(?:CSS(?:\s*網格)?|網格|PCB|硬體|管線|版面)\s*佈局",
    r"(?:特徵|向量|資料庫)\s*維度",
    r"打造\s*[\w\-/]*\s*(?:CI/CD|流水線|系統|平台|架構)",
)


def run_gate1(title_or_assertion: str) -> Dict[str, Any]:
    text = title_or_assertion.strip()
    reasons = []
    circuit_broken = False
    dashes = len(re.findall(r"—{1,2}|――", text))
    if dashes >= 2:
        reasons.append("發現過度使用破折號（≥2 組，易流於公關套路炫技）")
        circuit_broken = True

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

    # 1. 術語白名單過濾（避免誤殺正常工程詞）
    cleaned = text
    for wl in TECHNICAL_WHITELISTS:
        cleaned = re.sub(wl, "", cleaned, flags=re.I)

    banned = ["賦能", "閉環", "打法", "抓手", "痛點", "打造", "心智", "壁壘", "佈局", "維度", "守住底線", "深耕細作", "底層邏輯", "組合拳"]
    found_buzz = [b for b in banned if b in cleaned]
    if found_buzz:
        reasons.append(f"包含空洞字眼或陸味詞 [{', '.join(found_buzz)}]")
        circuit_broken = True

    # 2. 指標檢驗：排除 2026年 等日曆年份假指標
    has_metric = bool(re.search(
        r"(?<!\d)(?!(?:19|20)\d{2}\s*年(?:度)?)\d+(?:\.\d+)?\s*(?:%|倍|ms|秒|分|小時|日|天|月|年|萬|億)|SLA|KPI|P99|P95|QPS|ROI",
        text, re.I
    ))

    # 3. 動作檢驗：擴充研發、主管決策與架構動詞
    has_action = bool(re.search(
        r"修復|遷移|重構|隔離|部署|替換|上線|降低|減少|縮短|提升|限制|攔截|阻斷|消除|清理|收斂|整併|監控|"
        r"核准|裁決|簽署|驗收|採購|預算|合規|交付|盤點|審查|定案|修訂|終止|展延|撥款|調配|發布|"
        r"取消|改由|導入|轉移|重寫|剔除|升級|解耦|重組|實作|整合|對齊|抽換|切換|啟用|停用|優化|快取|調校|歸檔|備份",
        text
    ))

    if not has_metric and not has_action and not circuit_broken:
        reasons.append("缺乏工程動作（修復/遷移/重構/降低）或量化指標（數據/時間/%），缺乏晨會直白度。")
    passed = not circuit_broken and (has_metric or has_action)
    return {"text": text, "passed": passed, "circuit_broken": circuit_broken, "has_metric": has_metric, "has_action": has_action, "reasons": reasons}


def report_gate1(res: Dict[str, Any]) -> str:
    lines = [f"# Gate 1: First-Mile 晨會直白測試結果\n檢驗標題／斷言：『**{res['text']}**』\n"]
    if res["passed"]:
        lines.extend(["[PASS] **GATE 1 通過**", "- 符合 9:30 AM 站立晨會標準：具備具體動作或量化驗證資訊，零公關套話。\n"])
    else:
        lines.append("[FAIL] **GATE 1 熔斷不通過 (REJECT & REWRITE)**")
        for r in res["reasons"]:
            lines.append(f"- [!] {r}")
        lines.append("\n**改寫建議**：請捨棄宣傳式形容詞，直述「做了什麼動作」、「解決什麼阻礙」或「達到什麼具體數據指標」。\n")
    return "\n".join(lines)



