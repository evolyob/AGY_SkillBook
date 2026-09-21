#!/usr/bin/env python3
"""
NoAI-Note Dedicated First-Mile Detox & Standup Test Engine.
Standard library only. Robust, stateless, zero-bloat.
Compliant with Senior Clean Code & Vibe Craft Guide (Negative Net Lines).
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
    cjk_count = count_cjk(text)
    total_length = len(text.strip())
    if not total_length:
        return "en"
    return "zhtw" if (cjk_count >= 15 or (cjk_count / total_length > 0.15)) else "en"


def extract_context(text: str, pattern: str, *, limit: int = 2) -> List[str]:
    matches: List[str] = []
    for segment in re.split(r"(?<=[。！？\n])\s*", text):
        clean_segment = segment.strip()
        if not clean_segment:
            continue
        if re.search(pattern, clean_segment):
            truncated = clean_segment if len(clean_segment) <= 90 else f"{clean_segment[:87]}…"
            matches.append(truncated)
        if len(matches) >= limit:
            break
    return matches


# --- Pure Functional Detox Engine (Two-Layer Unified Architecture) ---

def run_detox(text: str, lang: str = "auto") -> Dict[str, Any]:
    resolved_lang = detect_language(text) if lang == "auto" else lang
    rules = load_rules(resolved_lang)
    char_count = len(text)
    kb_density_factor = max(char_count / 1000.0, 0.1)

    simplified_findings: List[Dict[str, Any]] = []
    if resolved_lang == "zhtw" and "simplified_chars" in rules:
        sim_char_set = set(rules["simplified_chars"])
        sim_counter = Counter(ch for ch in text if ch in sim_char_set)
        if sim_counter:
            simplified_findings = [{"char": ch, "count": cnt} for ch, cnt in sim_counter.most_common(15)]

    # Layer 1: Vocabulary Lookups (Forbidden & Contextual)
    forbidden_findings: List[Dict[str, Any]] = []
    for term, suggestion in rules.get("forbidden", {}).items():
        count = text.count(term)
        if count > 0:
            forbidden_findings.append({
                "term": term,
                "count": count,
                "suggest": suggestion,
                "example": (extract_context(text, re.escape(term), limit=1) or [""])[0]
            })

    contextual_findings: List[Dict[str, Any]] = []
    for term, advice in rules.get("contextual", {}).items():
        count = text.count(term)
        if count > 0:
            contextual_findings.append({
                "term": term,
                "count": count,
                "advice": advice,
                "example": (extract_context(text, re.escape(term), limit=1) or [""])[0]
            })

    # Layer 2: Dynamic Density Budget Patterns
    pattern_findings: List[Dict[str, Any]] = []
    regex_flags = re.I if resolved_lang != "zhtw" else 0
    for pattern_rule in rules.get("patterns", []):
        regex = pattern_rule["regex"]
        matches = re.findall(regex, text, regex_flags)
        count = len(matches)
        if not count:
            continue

        rate = count / kb_density_factor
        budget = pattern_rule.get("budget", 0.0)
        min_count = pattern_rule.get("min_count", 1)

        # Allow single punctuation dash in long text
        if pattern_rule.get("label", "").startswith("破折號") and count <= 1 and char_count > 80:
            continue

        if count >= min_count and rate > budget:
            pattern_findings.append({
                "label": pattern_rule["label"],
                "count": count,
                "rate": round(rate, 2),
                "budget": budget,
                "advice": pattern_rule.get("advice", ""),
                "examples": extract_context(text, regex, limit=2)
            })

    return {
        "lang": resolved_lang,
        "chars": char_count,
        "cjk_chars": count_cjk(text),
        "simplified": simplified_findings,
        "forbidden": forbidden_findings,
        "contextual": contextual_findings,
        "patterns": pattern_findings,
        # Backward-compatibility aliases
        "mainland_terms": forbidden_findings,
        "formulaic_patterns": pattern_findings,
        "buzzwords": []
    }
