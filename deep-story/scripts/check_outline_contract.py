#!/usr/bin/env python3
"""Deterministic outline structural verifier for story-long-write.

Usage:
    python3 check_outline_contract.py --json <outline_path...>
    python3 check_outline_contract.py --json --project <book_dir> --chapter N
    python3 check_outline_contract.py --json --supply <volume_path> <unit_id>

Exit codes:
    0 = pass
    1 = blocking contract failures
    2 = invalid invocation
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_CONTRACTS_PATH = Path(__file__).resolve().parent.parent / "data" / "contracts.json"
_OUTLINE_CFG = json.loads(_CONTRACTS_PATH.read_text(encoding="utf-8"))["outline_contract"]

FIELD_NAMES: list[list[str]] = _OUTLINE_CFG["field_names"]
FIELDS: list[str] = [names[0] for names in FIELD_NAMES]
RELEASE_FIELDS: list[str] = _OUTLINE_CFG["release_fields"]
RELEASE_MAX_ITEMS = int(_OUTLINE_CFG["release_max_items"])

SUBSECTION_NAMES: list[list[str]] = _OUTLINE_CFG["subsection_names"]
SUBSECTIONS: list[str] = [names[0] for names in SUBSECTION_NAMES]
FIVE_ACT: list[list[str]] = [
    item if isinstance(item, list) else [item] for item in _OUTLINE_CFG["five_act"]
]
PLOT_HEADER_FIRST = re.compile(r"^(?:#|序号|序號|Beat)$", re.IGNORECASE)
INTENT_FIELDS: list[str] = ["目标情绪", "主角目标/关键选择"]
CALIBER = _OUTLINE_CFG["caliber"]

CONTRACT_RISK_LEVELS: list[str] = _OUTLINE_CFG["contract_risk_levels"]
LEGACY_RISK_LEVELS: dict[str, str] = _OUTLINE_CFG["legacy_risk_levels"]

NUMBER = r"([1-9][0-9]{0,2}(?:[,，][0-9]{3})+|[1-9][0-9]*)"
NOTE = r"(?:[（(][^（）()]*[）)])?"
TARGET_VALUE = re.compile(
    rf"^(?:约|大约)?[ \t]*{NUMBER}[ \t]*字?(?:左右)?[ \t]*{NOTE}$"
)
RANGE_VALUE = re.compile(
    rf"^{NUMBER}[ \t]*字?[ \t]*(?:-|~|～|—|–|－|至|到)[ \t]*{NUMBER}[ \t]*字?[ \t]*{NOTE}$"
)
METRIC_VALUE = re.compile(rf"^([A-Za-z0-9_-]+)[ \t]*{NOTE}$")
HAS_DIGIT = re.compile(r"[0-9０-９]")

REF_DIR_PREFIX = re.compile(r"^(?:设定|大纲|追踪|正文|读者笔记|对标)/")
SUPPLY_HEADING = re.compile(r"^(?:写纲前查缺|供给自查)(?:\s|[（(<]|$)")

_SCRIPT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_REFERENCES: list[str] = [
    rel
    for rel in (
        "references/08_novel_chapter_outline_template.md",
        "references/07_web_novel_outline_template.md",
    )
    if (_SCRIPT_ROOT / rel).exists()
]


def field_values(text: str, label: str) -> list[str]:
    """Extract all values for a given metadata field label from markdown text."""
    pattern = re.compile(
        rf"^[ \t>]*(?:[-*+][ \t]*)?(?:\*\*)?{re.escape(label)}(?:\*\*)?[ \t]*[:：][ \t]*(.*?)[ \t]*$",
        re.MULTILINE,
    )
    normalized = re.sub(r"\r\n?", "\n", text)
    if normalized.startswith("\ufeff"):
        normalized = normalized[1:]
    return [
        match.group(1).replace("**", "").strip()
        for match in pattern.finditer(normalized)
    ]


def numeric_field_values(text: str, label: str) -> list[str]:
    """Return field values for `label` that contain at least one ASCII or fullwidth digit."""
    return [v for v in field_values(text, label) if HAS_DIGIT.search(v)]


def to_number(raw: str) -> int:
    """Convert a comma-separated integer string (ASCII or fullwidth comma) to int."""
    return int(re.sub(r"[,，]", "", raw))


def parse_wordcount_target(text: str) -> dict[str, Any]:
    """Parse and validate the wordcount target field(s) in an outline."""
    raw: list[str] = []
    for label in ("字数目标", "字數目標", "Word Count Target"):
        raw.extend(numeric_field_values(text, label))
    if not raw:
        return {"status": "missing", "value": None, "raw": raw}
    matches = [TARGET_VALUE.match(value) for value in raw]
    if not all(matches):
        return {"status": "invalid", "value": None, "raw": raw}
    values = list(dict.fromkeys(to_number(m.group(1)) for m in matches if m))
    if len(values) != 1:
        return {"status": "conflict", "value": None, "raw": raw}
    return {"status": "ok", "value": values[0], "raw": raw}


def parse_wordcount_range(text: str) -> dict[str, Any]:
    """Parse and validate the optional wordcount range field(s) in an outline."""
    raw: list[str] = []
    for label in ("字数范围", "字數範圍", "Word Count Range"):
        raw.extend(numeric_field_values(text, label))
    if not raw:
        return {"status": "missing", "value": None, "raw": raw}
    matches = [RANGE_VALUE.match(value) for value in raw]
    if not all(matches):
        return {"status": "invalid", "value": None, "raw": raw}
    pairs = list(
        dict.fromkeys(
            (to_number(m.group(1)), to_number(m.group(2)))
            for m in matches
            if m
        )
    )
    if len(pairs) != 1:
        return {"status": "invalid", "value": None, "raw": raw}
    min_val, max_val = pairs[0]
    if min_val > max_val:
        return {"status": "invalid", "value": None, "raw": raw}
    return {"status": "ok", "value": {"min": min_val, "max": max_val}, "raw": raw}


def parse_wordcount_caliber(text: str) -> bool:
    """Validate the optional wordcount caliber field; absent means default caliber."""
    raw: list[str] = []
    for label in ("字数口径", "字數口徑", "Word Count Caliber"):
        raw.extend(field_values(text, label))
    if not raw:
        return True
    matches = [METRIC_VALUE.match(value) for value in raw]
    if not all(matches):
        return False
    calibers = {m.group(1) for m in matches if m}
    return len(calibers) == 1 and next(iter(calibers)) == CALIBER


def parse_contract_risk(text: str) -> dict[str, Any] | None:
    """Parse the optional contract risk field using current or legacy labels."""
    raw: list[str] = []
    for label in ("有没有硬伤", "契约风险", "风险等级"):
        raw = field_values(text, label)
        if raw:
            break
    if not raw:
        return None
    value = raw[-1].replace("`", "")
    if value == "[待补充]":
        return {"status": "unknown", "level": None, "detail": "", "raw": value}
    candidates = [*CONTRACT_RISK_LEVELS, *LEGACY_RISK_LEVELS.keys()]
    written = next((name for name in candidates if value.startswith(name)), None)
    if not written:
        return {"status": "invalid", "level": None, "detail": "", "raw": value}
    level = LEGACY_RISK_LEVELS.get(written, written)
    tail = value[len(written) :]
    detail = re.sub(r"[）)]$", "", re.sub(r"^[\s；;，,。：:—\-（(]+", "", tail)).strip()
    return {"status": "ok", "level": level, "detail": detail, "raw": value}


def field_pattern(name: str) -> re.Pattern[str]:
    """Build a line-start bullet/bold field regex for `name`."""
    escaped = re.escape(name)
    return re.compile(rf"^\s*[-*+]\s*\*{{0,2}}{escaped}\*{{0,2}}\s*[：:]", re.MULTILINE)


def read_utf8(file_path: str | Path) -> dict[str, Any]:
    """Read a UTF-8 file, stripping a leading BOM and checking non-empty content."""
    try:
        text = Path(file_path).read_text(encoding="utf-8")
        if text.startswith("\ufeff"):
            text = text[1:]
        return {"ok": len(text.strip()) > 0, "text": text}
    except (OSError, UnicodeDecodeError) as error:
        return {"ok": False, "text": "", "error": str(error)}


def make_check(
    check_id: str,
    ok: bool,
    file_name: str,
    evidence: str,
    expected: str,
    repair: str,
    severity: str = "blocking",
) -> dict[str, Any]:
    """Construct a structured contract check result object."""
    return {
        "id": check_id,
        "ok": ok,
        "severity": severity,
        "file": file_name,
        "evidence": evidence,
        "expected": expected,
        "references": TEMPLATE_REFERENCES,
        "repair": repair,
    }


def parse_table_row(line: str) -> list[str] | None:
    """Parse a markdown table row into stripped cells, or return None if not a row."""
    trimmed = line.strip()
    if not trimmed.startswith("|") or not trimmed.endswith("|"):
        return None
    return [
        cell.replace("**", "").replace("`", "").strip()
        for cell in trimmed[1:-1].split("|")
    ]


def resolve_book_root(file_path: str | Path, project_root: str | None) -> Path | None:
    """Resolve the book root directory from `--project` or an `大纲/` parent folder."""
    if project_root:
        return Path(project_root).resolve()
    parent = Path(file_path).resolve().parent
    if parent.name == "大纲":
        return parent.parent
    return None


def has_existing_chapter_prose(file_path: str | Path, project_root: str | None) -> bool:
    """Return True if a non-draft prose file already exists for the outline's chapter."""
    book_root = resolve_book_root(file_path, project_root)
    ch_match = re.match(r"^细纲_第0*(\d+)章.*\.md$", Path(file_path).name)
    if not book_root or not ch_match:
        return False
    wanted = int(ch_match.group(1))
    if wanted < 1:
        return False
    prose_dir = book_root / "正文"
    try:
        entries = list(prose_dir.iterdir())
    except OSError:
        return False
    for entry in entries:
        if "_原稿_" in entry.name:
            continue
        match = re.match(r"^第0*(\d+)章(?:[_\- 　].*)?\.md$", entry.name)
        if match and int(match.group(1)) == wanted and entry.is_file():
            return True
    return False


def check_setting_refs(
    text: str,
    name: str,
    file_path: str | Path,
    project_root: str | None,
) -> dict[str, Any]:
    """Verify that backticked project `.md` references resolve to existing files."""
    book_root = resolve_book_root(file_path, project_root)
    if not book_root:
        return make_check(
            "outline.setting-refs-exist",
            True,
            name,
            "未能定位书目录（细纲不在 大纲/ 下且未传 --project），跳过",
            "细纲引用的项目内文件真实存在",
            "无需修复。",
        )
    refs: dict[str, None] = {}
    for match in re.finditer(r"`([^`\n]+?\.md)[^`\n]*`", text):
        token = match.group(1).strip().replace("\\", "/")
        if "{" in token or "}" in token:
            continue
        if REF_DIR_PREFIX.match(token) or re.match(r"^\.{1,2}/", token):
            refs[token] = None
    file_dir = Path(file_path).resolve().parent
    missing: list[str] = []
    for token in refs:
        base = file_dir if re.match(r"^\.{1,2}/", token) else book_root
        if not (base / token).resolve().is_file():
            missing.append(token)
    evidence = (
        f"引用的路径不是可用文件：{'、'.join(missing)}"
        if missing
        else f"{len(refs)} 处项目内引用全部存在"
    )
    return make_check(
        "outline.setting-refs-exist",
        len(missing) == 0,
        name,
        evidence,
        "细纲引用的每个项目内 .md 文件都真实存在——不许把槽位指向查无实据的权威文件",
        "修正引用路径；或按新增物三级先把缺的设定落档（补上并记下的直接补并登记，要问作者的写进排纲笔记「写纲前查缺」的提案），再在细纲引用。",
    )


def _column_kind(cell: str) -> str | None:
    """Classify an optional plotpoint column header."""
    if "分辨率" in cell or "解析度" in cell or "Resolution" in cell:
        return "res"
    if re.search(r"执行边界|執行邊界|分寸|Bounds", cell, re.IGNORECASE):
        return "bound"
    return None


def _extra_columns_ok(extra: list[str]) -> bool:
    """Validate optional columns (4th+) in the plotpoint table header."""
    kinds = [_column_kind(cell) for cell in extra]
    if None in kinds or len(set(kinds)) != len(kinds):
        return False
    return "bound" not in kinds or kinds[-1] == "bound"


def _find_plotpoint_header(lines: list[str]) -> list[str] | None:
    """Return the first valid-shape plotpoint table header row, if present."""
    for line in lines:
        cells = parse_table_row(line)
        if cells and 3 <= len(cells) <= 5 and PLOT_HEADER_FIRST.match(cells[0]):
            return cells
    return None


def _is_released_cell(cell: str) -> bool:
    """Check whether a boundary cell contains a non-empty `放：` clause."""
    match = re.search(
        r"(?:^|[。；;\s])放\s*[：:]([\s\S]*?)(?=(?:禁|放)\s*[：:]|$)",
        cell,
    )
    if not match:
        return False
    value = re.sub(r"[\s。；;，,、\[\]【】]", "", match.group(1))
    return len(value) > 0 and not bool(
        re.match(r"^(?:无|暂无|待补充|待定|无缺口)$", value)
    )


def _check_plotpoint_release(
    lines: list[str],
    header: list[str],
    name: str,
) -> list[dict[str, Any]]:
    """Run legacy `执行边界` release-clause checks when applicable."""
    if "执行边界" not in header[-1]:
        return []
    if len(header) != 5 and "放" not in header[-1]:
        return []
    rows = [
        cells
        for line in lines
        if (cells := parse_table_row(line)) is not None
        and len(cells) == len(header)
        and re.match(r"^\d+$", cells[0])
    ]
    if not rows:
        return []
    released = [cells for cells in rows if _is_released_cell(cells[-1])]
    results = [
        make_check(
            "outline.plotpoint-release",
            len(released) > 0,
            name,
            f"{len(rows)} 个情节点里 {len(released)} 个写了「放」",
            "执行边界写成「禁＋放」两半，每章至少一个点写了「放」——放行是解除限制，不是义务",
            "给最该出彩的一两个点补「放」半边（谁可以出声、谁可以失态、允不允许当场标价），不改情节点本身。",
        )
    ]
    if len(released) > 0 and len(rows) >= 3 and len(released) * 3 < len(rows):
        results.append(
            make_check(
                "outline.plotpoint-release-ratio",
                False,
                name,
                f"{len(rows)} 个情节点里只有 {len(released)} 个写了「放」（不足三分之一）",
                "建议至少三分之一的情节点写「放」半边，避免整章只剩禁令",
                "按人工判断酌情补「放」；本项不阻断。",
                "advisory",
            )
        )
    return results


def _find_hollow_intent_fields(text: str) -> list[str]:
    """Return intent fields that are present but contain only `[待补充]` or punctuation."""
    hollow: list[str] = []
    for field in INTENT_FIELDS:
        pattern = re.compile(
            rf"^\s*[-*+]\s*\*{{0,2}}{re.escape(field)}\*{{0,2}}\s*[：:]\s*(.*)$",
            re.MULTILINE,
        )
        match = pattern.search(text)
        if not match:
            continue
        value = re.sub(r"[\s、，,。;；]", "", match.group(1).replace("[待补充]", ""))
        if not value:
            hollow.append(field)
    return hollow


def _check_release_brevity(text: str, name: str) -> dict[str, Any] | None:
    """Return an advisory check if the optional withheld-reveal line exceeds 3 items."""
    for label in RELEASE_FIELDS:
        pattern = re.compile(
            rf"^\s*[-*+]\s*\*{{0,2}}{re.escape(label)}\*{{0,2}}\s*[：:]\s*(.*)$",
            re.MULTILINE,
        )
        match = pattern.search(text)
        if not match:
            continue
        items = [s.strip() for s in re.split(r"[、；;，,/]", match.group(1)) if s.strip()]
        if len(items) > RELEASE_MAX_ITEMS:
            return make_check(
                "outline.release-brevity",
                False,
                name,
                f"这章不能说破列了 {len(items)} 条",
                f"只在这章确有一件具体的事要压住时写一行（至多 {RELEASE_MAX_ITEMS} 条）；全卷都压着的写在卷纲「这卷先不能揭开、不能用上的」，不逐章复读",
                "把和卷纲重复的条目删掉，只留这章确要压住的那件事；没有就整行删掉。本项不阻断。",
                "advisory",
            )
        return None
    return None


def _build_wordcount_check(
    file_path: str | Path,
    text: str,
    name: str,
    project_root: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate wordcount target, range, and caliber, returning the check and summary."""
    has_prose = has_existing_chapter_prose(file_path, project_root)
    min_target = 1 if has_prose else 500
    max_target = 500000 if has_prose else 20000
    target_parse = parse_wordcount_target(text)
    range_parse = parse_wordcount_range(text)
    target = target_parse["value"]
    caliber_ok = parse_wordcount_caliber(text)

    target_labels = {
        "ok": target,
        "missing": "未识别",
        "invalid": f"写法认不出（{'、'.join(target_parse['raw'])}）",
        "conflict": f"多个不同的值（{'、'.join(target_parse['raw'])}）",
    }
    target_label = target_labels[target_parse["status"]]
    range_label = ""
    if range_parse["status"] == "invalid":
        range_label = f"；字数范围写法不对（{'、'.join(range_parse['raw'])}）"
    elif range_parse["value"]:
        rval = range_parse["value"]
        range_label = f"；字数范围：{rval['min']}-{rval['max']}"

    ok = (
        target_parse["status"] == "ok"
        and min_target <= target <= max_target
        and caliber_ok
        and range_parse["status"] != "invalid"
    )
    caliber_str = "true" if caliber_ok else "false"
    check = make_check(
        "outline.wordcount-target",
        ok,
        name,
        f"字数目标：{target_label}；字数口径（可不写，写了须是 {CALIBER}）：{caliber_str}{range_label}",
        f"字数目标为 {min_target}-{max_target} 的正整数（可写「2300 字」「约 2300」「2,300」，可带括号备注）；字数口径不用写，写了只能是 {CALIBER}；作者给了上下限时另写一行「字数范围：2000-2600」",
        "只补字数目标、字数范围，或删掉写错的字数口径行，不调整情节安排。",
    )
    summary = {
        "target": target,
        "target_status": target_parse["status"],
        "range": range_parse["value"],
        "range_status": range_parse["status"],
    }
    return check, summary


def verify(file_path: str | Path, project_root: str | None = None) -> dict[str, Any]:
    """Run all structural contract checks on an outline markdown file."""
    name = Path(file_path).name
    read = read_utf8(file_path)
    checks: list[dict[str, Any]] = [
        make_check(
            "outline.readable",
            read["ok"],
            name,
            "文件存在且非空" if read["ok"] else read.get("error", "文件为空"),
            "细纲文件存在且非空",
            "只补建缺失的细纲文件，不改动同批其他章。",
        )
    ]
    if not read["ok"]:
        return report(file_path, checks)

    text: str = read["text"]

    missing_fields = [
        names[0]
        for names in FIELD_NAMES
        if not any(field_pattern(field).search(text) for field in names)
    ]
    checks.append(
        make_check(
            "outline.required-fields",
            len(missing_fields) == 0,
            name,
            f"缺字段：{'、'.join(missing_fields)}" if missing_fields else f"{len(FIELDS)} 个字段齐全",
            f"按权威模板列出全部字段：{'、'.join(FIELDS)}；值未知时写 [待补充]，不杜撰剧情",
            "只补报告里缺的字段行；确实还定不下来的写 [待补充]，不为补字段新增副线或人物关系。",
        )
    )

    hollow = _find_hollow_intent_fields(text)
    checks.append(
        make_check(
            "outline.intent-fields-substantive",
            len(hollow) == 0,
            name,
            f"只有占位符，没有实际内容：{'、'.join(hollow)}" if hollow else "目标情绪与主角目标/关键选择都写了实际内容",
            "目标情绪写清前状态→后状态；主角目标/关键选择写清本章要什么、必须做出的判断。这两项不接受 [待补充]",
            "只把这两个字段替换成本章的实际情绪变化与实际取舍；其余字段不动。",
        )
    )

    missing_subs = [
        names[0]
        for names in SUBSECTION_NAMES
        if not any(re.search(rf"^#{{3,4}}\s*{re.escape(sub)}", text, re.MULTILINE) for sub in names)
    ]
    checks.append(
        make_check(
            "outline.subsections",
            len(missing_subs) == 0,
            name,
            f"缺小节：{'、'.join(missing_subs)}" if missing_subs else "四个小节齐全",
            "包含 这章怎么走 / 情节安排 / 人物关系和出场顺序 / 情节细化 四个小节（旧名「内容概括」照认）",
            "只补缺失的小节标题及其条目，不重写已成立的内容。",
        )
    )

    missing_acts = [
        names[0] for names in FIVE_ACT
        if not any(field_pattern(act).search(text) for act in names)
    ]
    checks.append(
        make_check(
            "outline.five-act",
            len(missing_acts) == 0,
            name,
            f"「这章怎么走」缺：{'、'.join(missing_acts)}" if missing_acts else "「这章怎么走」五行齐全",
            "「这章怎么走」写全 起因 / 发展 / 转折 / 高潮 / 结尾",
            "只补缺的那一段，不改其余四段。",
        )
    )

    lines = re.split(r"\r?\n", text)
    header = _find_plotpoint_header(lines)
    header_ok = (
        bool(header)
        and bool(re.search(r"功能标签|功能標籤|作用|Function", header[2], re.IGNORECASE))
        and _extra_columns_ok(header[3:])
    )
    checks.append(
        make_check(
            "outline.plotpoint-table",
            header_ok,
            name,
            f"表头：{' | '.join(header)}" if header else "未找到 | # | 情节点 | 作用 | 表头",
            "情节细化使用表格：# / 情节点（谁做了什么） / 作用；需要时可加「分辨率」列，某个点确实要限定写到什么程度时在表末加「分寸」列",
            "只把情节点序列改成这张表，逐点补作用；不增删情节点本身。",
        )
    )

    if header_ok and header is not None:
        checks.extend(_check_plotpoint_release(lines, header, name))

    brevity_check = _check_release_brevity(text, name)
    if brevity_check:
        checks.append(brevity_check)

    checks.append(check_setting_refs(text, name, file_path, project_root))

    wc_check, wc_summary = _build_wordcount_check(file_path, text, name, project_root)
    checks.append(wc_check)

    risk = parse_contract_risk(text)
    if risk:
        checks.append(
            make_check(
                "outline.contract-risk",
                risk["status"] != "invalid",
                name,
                f"有没有硬伤写的是「{risk['raw']}」"
                if risk["status"] == "invalid"
                else f"有没有硬伤：{risk['level'] or '[待补充]'}",
                f"有没有硬伤只写 {' / '.join(CONTRACT_RISK_LEVELS)} 三档之一（要补时后面写怎么补），未定写 [待补充]",
                "只把这一行改成三档之一，不改其他字段。",
            )
        )

    return report(
        file_path,
        checks,
        {
            "wordcount": wc_summary,
            "contract_risk": (
                {"level": risk["level"], "detail": risk["detail"], "status": risk["status"]}
                if risk
                else None
            ),
        },
    )


def report(
    file_path: str | Path,
    checks: list[dict[str, Any]],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the final JSON report payload for an outline verification run."""
    failures = [c for c in checks if not c["ok"] and c["severity"] == "blocking"]
    advisories = [c for c in checks if not c["ok"] and c["severity"] == "advisory"]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "verifier": "story-long-write.outline-contract",
        "file": str(Path(file_path).resolve()),
        "ok": len(failures) == 0,
    }
    if extra:
        payload.update(extra)
    payload["checks"] = checks
    payload["failures"] = failures
    payload["advisories"] = advisories
    payload["repair_scope"] = [
        {
            "id": failure["id"],
            "file": failure["file"],
            "evidence": failure["evidence"],
            "expected": failure["expected"],
            "references": failure["references"],
            "repair": failure["repair"],
        }
        for failure in failures
    ]
    return payload


def resolve_chapter(project: str, chapter: str) -> dict[str, str]:
    """Locate the outline file for chapter N under `<project>/大纲/`."""
    outline_dir = Path(project) / "大纲"
    try:
        entries = os.listdir(outline_dir)
    except OSError as error:
        return {"error": f"无法读取 {outline_dir}：{error}"}
    wanted = int(chapter)
    for entry in entries:
        match = re.match(r"^细纲_第0*(\d+)章.*\.md$", entry)
        if match and int(match.group(1)) == wanted:
            return {"file": str(outline_dir / entry)}
    return {"error": f"{outline_dir} 下没有第 {wanted} 章细纲"}


def strip_trailing_comment(title: str) -> str:
    """Strip a trailing HTML comment from a markdown heading title."""
    return re.sub(r"\s*<!--[\s\S]*?-->\s*$", "", title).strip()


def has_supply_heading(text: str) -> bool:
    """Return True if any markdown heading in `text` is a supply-check heading."""
    for line in re.split(r"\r?\n", text):
        heading = re.match(r"^#{1,6}\s+(.+)$", line.replace("**", ""))
        if heading and SUPPLY_HEADING.match(strip_trailing_comment(heading.group(1))):
            return True
    return False


def notes_candidates(volume_file: str | Path, unit_id: str) -> list[tuple[Path, str]]:
    """Return candidate planning-note paths in priority order for `unit_id`."""
    outline_dir = Path(volume_file).resolve().parent
    book_root = outline_dir.parent
    return [
        (book_root / ".story" / "排纲笔记" / f"{unit_id}.md", "排纲笔记"),
        (outline_dir / f"排纲笔记_{unit_id}.md", "排纲笔记"),
        (outline_dir / f"排纲底稿_{unit_id}.md", "排纲底稿"),
    ]


def _update_fence(fence: str | None, tok: str) -> str | None:
    """Update the active code-fence delimiter when encountering a fence marker."""
    if fence is None:
        return tok
    if tok[0] == fence[0] and len(tok) >= len(fence):
        return None
    return fence


def _strip_fences(raw_lines: list[str]) -> list[str]:
    """Blank out fenced code blocks and strip bold markers from non-fence lines."""
    fence: str | None = None
    cleaned: list[str] = []
    for line in raw_lines:
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            fence = _update_fence(fence, marker.group(1))
            cleaned.append("")
            continue
        cleaned.append("" if fence is not None else line.replace("**", ""))
    return cleaned


def _extract_headings(lines: list[str]) -> list[dict[str, Any]]:
    """Extract markdown headings with line index, level, title, and trailing comment."""
    headings: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if not heading:
            continue
        comment = re.search(r"<!--\s*([\s\S]*?)\s*-->\s*$", heading.group(2))
        headings.append(
            {
                "index": index,
                "level": len(heading.group(1)),
                "title": strip_trailing_comment(heading.group(2)),
                "comment": comment.group(1) if comment else None,
            }
        )
    return headings


def _is_unit_card(
    heading: dict[str, Any],
    headings: list[dict[str, Any]],
    lines: list[str],
    unit_id: str,
) -> bool:
    """Return True if `heading` introduces the story unit `unit_id`."""
    if heading["comment"]:
        scope = re.sub(r"^单元级\s+", "", re.split(r"[｜|]", heading["comment"])[0].strip())
        if re.match(r"^[A-Za-z]\d*[\w-]*$", scope):
            return scope == unit_id
    id_match = re.search(r"剧情单元\s+([A-Za-z][\w-]*)", heading["title"])
    if id_match:
        return id_match.group(1) == unit_id
    end = next((h["index"] for h in headings if h["index"] > heading["index"]), len(lines))
    for line in lines[heading["index"] + 1 : end]:
        field = re.match(r"^\s*[-*+]\s*单元ID\s*[：:]\s*([A-Za-z][\w-]*)\s*$", line)
        if field and field.group(1) == unit_id:
            return True
    return False


def verify_supply(volume_file: str | Path, unit_id: str) -> dict[str, Any]:
    """Verify that pre-outline supply-check notes exist for `unit_id`."""
    for draft_file, label in notes_candidates(volume_file, unit_id):
        draft = read_utf8(draft_file)
        if not draft["ok"]:
            continue
        ok = has_supply_heading(draft["text"])
        return {
            "schema_version": 1,
            "verifier": "story-long-write.outline-supply",
            "file": str(draft_file.resolve()),
            "unit": unit_id,
            "ok": ok,
            "evidence": (
                f"{label}含「写纲前查缺」小节"
                if ok
                else f"{draft_file.name} 里没有「写纲前查缺」小节——每批出细纲前都要查一遍缺什么（没缺也写「无缺口」），见 workflow-outline.md「写纲前查缺」"
            ),
        }

    read = read_utf8(volume_file)
    resolved_vol = str(Path(volume_file).resolve())
    if not read["ok"]:
        return {
            "schema_version": 1,
            "verifier": "story-long-write.outline-supply",
            "file": resolved_vol,
            "unit": unit_id,
            "ok": False,
            "evidence": read.get("error", "卷纲文件为空"),
        }

    lines = _strip_fences(re.split(r"\r?\n", read["text"]))
    headings = _extract_headings(lines)
    card = next((h for h in headings if _is_unit_card(h, headings, lines, unit_id)), None)
    if not card:
        return {
            "schema_version": 1,
            "verifier": "story-long-write.outline-supply",
            "file": resolved_vol,
            "unit": unit_id,
            "ok": False,
            "evidence": f"卷纲中未找到剧情段 {unit_id}",
        }

    end = next(
        (h["index"] for h in headings if h["index"] > card["index"] and h["level"] <= card["level"]),
        len(lines),
    )
    ok = any(
        card["index"] < h["index"] < end and SUPPLY_HEADING.match(h["title"])
        for h in headings
    )
    return {
        "schema_version": 1,
        "verifier": "story-long-write.outline-supply",
        "file": resolved_vol,
        "unit": unit_id,
        "ok": ok,
        "evidence": (
            "剧情段内含「写纲前查缺」小节"
            if ok
            else f"没有 .story/排纲笔记/{unit_id}.md，剧情段 {unit_id} 里也没有「写纲前查缺」小节——每批出细纲前都要查一遍缺什么（没缺也写「无缺口」），见 workflow-outline.md「写纲前查缺」"
        ),
    }


def _consume_arg(
    argv: list[str],
    index: int,
    opts: dict[str, Any],
    files: list[str],
) -> int | None:
    """Consume one CLI token (flag or positional file); return next index or None."""
    arg = argv[index]
    if not arg.startswith("--"):
        files.append(arg)
        return index + 1
    if arg == "--json":
        return index + 1
    if arg == "--supply" and index + 2 < len(argv):
        opts["supply"] = {"volume_file": argv[index + 1], "unit_id": argv[index + 2]}
        return index + 3
    if arg in ("--project", "--chapter") and index + 1 < len(argv) and not argv[index + 1].startswith("--"):
        opts[arg[2:]] = argv[index + 1]
        return index + 2
    return None


def parse_args(argv: list[str]) -> dict[str, Any] | None:
    """Parse CLI arguments matching the original Node script contract."""
    files: list[str] = []
    opts: dict[str, Any] = {"project": None, "chapter": None, "supply": None}
    index: int | None = 0
    while index is not None and index < len(argv):
        index = _consume_arg(argv, index, opts, files)
    if index is None:
        return None
    if opts["supply"]:
        return None if (opts["project"] or opts["chapter"] or files) else {"supply": opts["supply"]}
    if opts["project"] or opts["chapter"]:
        valid = bool(opts["project"] and opts["chapter"] and not files and re.match(r"^\d+$", opts["chapter"]))
        return {"project": opts["project"], "chapter": opts["chapter"]} if valid else None
    return {"files": files} if files else None


def main(argv: list[str]) -> int:
    """CLI entrypoint returning 0 on pass, 1 on failure, 2 on invalid invocation."""
    parsed = parse_args(argv)
    if not parsed:
        sys.stderr.write(
            "用法: node scripts/check-outline-contract.js --json <细纲路径...> | --json --project <书目录> --chapter N | --json --supply <卷纲路径> <单元ID>\n"
        )
        return 2
    if "supply" in parsed:
        supply_report = verify_supply(
            parsed["supply"]["volume_file"],
            parsed["supply"]["unit_id"],
        )
        sys.stdout.write(f"{json.dumps(supply_report, ensure_ascii=False, indent=2)}\n")
        return 0 if supply_report["ok"] else 1

    targets: list[str] | None = parsed.get("files")
    if not targets:
        resolved = resolve_chapter(parsed["project"], parsed["chapter"])
        if "error" in resolved:
            sys.stderr.write(f"{resolved['error']}\n")
            return 2
        targets = [resolved["file"]]

    reports = [verify(file_path, parsed.get("project")) for file_path in targets]
    ok = all(entry["ok"] for entry in reports)
    output: Any = reports[0] if len(reports) == 1 else reports
    sys.stdout.write(f"{json.dumps(output, ensure_ascii=False, indent=2)}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
