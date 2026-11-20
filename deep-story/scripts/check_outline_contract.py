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
PLOT_HEADER_FIRST = re.compile(r"^(?:#|序號|序號|Beat)$", re.IGNORECASE)
INTENT_FIELDS: list[str] = ["目標情绪", "主角目標/關鍵選择"]
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

REF_DIR_PREFIX = re.compile(r"^(?:設定|大綱|追蹤|正文|讀者筆記|對標)/")
SUPPLY_HEADING = re.compile(r"^(?:寫綱前查缺|供給自查)(?:\s|[（(<]|$)")

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
    for label in ("字數目標", "字數目標", "Word Count Target"):
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
    for label in ("字數范围", "字數範圍", "Word Count Range"):
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
    for label in ("字數口徑", "字數口徑", "Word Count Caliber"):
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
    for label in ("有沒有硬傷", "契约風險", "風險等級"):
        raw = field_values(text, label)
        if raw:
            break
    if not raw:
        return None
    value = raw[-1].replace("`", "")
    if value == "[待補充]":
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
    """Resolve the book root directory from `--project` or an `大綱/` parent folder."""
    if project_root:
        return Path(project_root).resolve()
    parent = Path(file_path).resolve().parent
    if parent.name == "大綱":
        return parent.parent
    return None


def has_existing_chapter_prose(file_path: str | Path, project_root: str | None) -> bool:
    """Return True if a non-draft prose file already exists for the outline's chapter."""
    book_root = resolve_book_root(file_path, project_root)
    ch_match = re.match(r"^細綱_第0*(\d+)章.*\.md$", Path(file_path).name)
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
            "未能定位書目錄（細綱不在 大綱/ 下且未傳 --project），跳過",
            "細綱引用的項目內文件真實存在",
            "無需修複。",
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
        f"引用的路徑不是可用文件：{'、'.join(missing)}"
        if missing
        else f"{len(refs)} 處項目內引用全部存在"
    )
    return make_check(
        "outline.setting-refs-exist",
        len(missing) == 0,
        name,
        evidence,
        "細綱引用的每個項目內 .md 文件都真實存在——不許把槽位指向查無實據的權威文件",
        "修正引用路徑；或按新增物三級先把缺的設定落檔（補上並記下的直接補並登記，要問作者的寫進排綱筆記「寫綱前查缺」的提案），再在細綱引用。",
    )


def _column_kind(cell: str) -> str | None:
    """Classify an optional plotpoint column header."""
    if "分辨率" in cell or "解析度" in cell or "Resolution" in cell:
        return "res"
    if re.search(r"执行邊界|執行邊界|分寸|Bounds", cell, re.IGNORECASE):
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
        re.match(r"^(?:無|暂無|待補充|待定|無缺口)$", value)
    )


def _check_plotpoint_release(
    lines: list[str],
    header: list[str],
    name: str,
) -> list[dict[str, Any]]:
    """Run legacy `执行邊界` release-clause checks when applicable."""
    if "执行邊界" not in header[-1]:
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
            f"{len(rows)} 個情節點里 {len(released)} 個寫了「放」",
            "执行邊界寫成「禁＋放」两半，每章至少一個點寫了「放」——放行是解除限制，不是義务",
            "給最該出彩的一两個點補「放」半邊（誰可以出聲、誰可以失態、允不允許當场標价），不改情節點本身。",
        )
    ]
    if len(released) > 0 and len(rows) >= 3 and len(released) * 3 < len(rows):
        results.append(
            make_check(
                "outline.plotpoint-release-ratio",
                False,
                name,
                f"{len(rows)} 個情節點里只有 {len(released)} 個寫了「放」（不足三分之一）",
                "建議至少三分之一的情節點寫「放」半邊，避免整章只剩禁令",
                "按人工判斷酌情補「放」；本項不阻斷。",
                "advisory",
            )
        )
    return results


def _find_hollow_intent_fields(text: str) -> list[str]:
    """Return intent fields that are present but contain only `[待補充]` or punctuation."""
    hollow: list[str] = []
    for field in INTENT_FIELDS:
        pattern = re.compile(
            rf"^\s*[-*+]\s*\*{{0,2}}{re.escape(field)}\*{{0,2}}\s*[：:]\s*(.*)$",
            re.MULTILINE,
        )
        match = pattern.search(text)
        if not match:
            continue
        value = re.sub(r"[\s、，,。;；]", "", match.group(1).replace("[待補充]", ""))
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
                f"這章不能說破列了 {len(items)} 條",
                f"只在這章確有一件具體的事要压住時寫一行（至多 {RELEASE_MAX_ITEMS} 條）；全卷都压着的寫在卷綱「這卷先不能揭開、不能用上的」，不逐章複讀",
                "把和卷綱重複的條目刪掉，只留這章確要压住的那件事；沒有就整行刪掉。本項不阻斷。",
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
        "missing": "未识別",
        "invalid": f"寫法認不出（{'、'.join(target_parse['raw'])}）",
        "conflict": f"多個不同的值（{'、'.join(target_parse['raw'])}）",
    }
    target_label = target_labels[target_parse["status"]]
    range_label = ""
    if range_parse["status"] == "invalid":
        range_label = f"；字數范围寫法不對（{'、'.join(range_parse['raw'])}）"
    elif range_parse["value"]:
        rval = range_parse["value"]
        range_label = f"；字數范围：{rval['min']}-{rval['max']}"

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
        f"字數目標：{target_label}；字數口徑（可不寫，寫了須是 {CALIBER}）：{caliber_str}{range_label}",
        f"字數目標為 {min_target}-{max_target} 的正整數（可寫「2300 字」「约 2300」「2,300」，可帶括號備注）；字數口徑不用寫，寫了只能是 {CALIBER}；作者給了上下限時另寫一行「字數范围：2000-2600」",
        "只補字數目標、字數范围，或刪掉寫錯的字數口徑行，不調整情節安排。",
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
            "文件存在且非空" if read["ok"] else read.get("error", "文件為空"),
            "細綱文件存在且非空",
            "只補建缺失的細綱文件，不改動同批其他章。",
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
            f"缺字段：{'、'.join(missing_fields)}" if missing_fields else f"{len(FIELDS)} 個字段齊全",
            f"按權威模板列出全部字段：{'、'.join(FIELDS)}；值未知時寫 [待補充]，不杜撰剧情",
            "只補报告里缺的字段行；確實還定不下來的寫 [待補充]，不為補字段新增副線或人物關系。",
        )
    )

    hollow = _find_hollow_intent_fields(text)
    checks.append(
        make_check(
            "outline.intent-fields-substantive",
            len(hollow) == 0,
            name,
            f"只有占位符，沒有實際內容：{'、'.join(hollow)}" if hollow else "目標情绪與主角目標/關鍵選择都寫了實際內容",
            "目標情绪寫清前狀態→後狀態；主角目標/關鍵選择寫清本章要什麼、必須做出的判斷。這两項不接受 [待補充]",
            "只把這两個字段替換成本章的實際情绪變化與實際取舍；其余字段不動。",
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
            f"缺小節：{'、'.join(missing_subs)}" if missing_subs else "四個小節齊全",
            "包含 這章怎麼走 / 情節安排 / 人物關系和出场順序 / 情節細化 四個小節（舊名「內容概括」照認）",
            "只補缺失的小節標題及其條目，不重寫已成立的內容。",
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
            f"「這章怎麼走」缺：{'、'.join(missing_acts)}" if missing_acts else "「這章怎麼走」五行齊全",
            "「這章怎麼走」寫全 起因 / 發展 / 轉折 / 高潮 / 結尾",
            "只補缺的那一段，不改其余四段。",
        )
    )

    lines = re.split(r"\r?\n", text)
    header = _find_plotpoint_header(lines)
    header_ok = (
        bool(header)
        and bool(re.search(r"功能標签|功能標籤|作用|Function", header[2], re.IGNORECASE))
        and _extra_columns_ok(header[3:])
    )
    checks.append(
        make_check(
            "outline.plotpoint-table",
            header_ok,
            name,
            f"表頭：{' | '.join(header)}" if header else "未找到 | # | 情節點 | 作用 | 表頭",
            "情節細化使用表格：# / 情節點（誰做了什麼） / 作用；需要時可加「分辨率」列，某個點確實要限定寫到什麼程度時在表末加「分寸」列",
            "只把情節點序列改成這張表，逐點補作用；不增刪情節點本身。",
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
                f"有沒有硬傷寫的是「{risk['raw']}」"
                if risk["status"] == "invalid"
                else f"有沒有硬傷：{risk['level'] or '[待補充]'}",
                f"有沒有硬傷只寫 {' / '.join(CONTRACT_RISK_LEVELS)} 三檔之一（要補時後面寫怎麼補），未定寫 [待補充]",
                "只把這一行改成三檔之一，不改其他字段。",
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
    """Locate the outline file for chapter N under `<project>/大綱/`."""
    outline_dir = Path(project) / "大綱"
    try:
        entries = os.listdir(outline_dir)
    except OSError as error:
        return {"error": f"無法讀取 {outline_dir}：{error}"}
    wanted = int(chapter)
    for entry in entries:
        match = re.match(r"^細綱_第0*(\d+)章.*\.md$", entry)
        if match and int(match.group(1)) == wanted:
            return {"file": str(outline_dir / entry)}
    return {"error": f"{outline_dir} 下沒有第 {wanted} 章細綱"}


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
        (book_root / ".story" / "排綱筆記" / f"{unit_id}.md", "排綱筆記"),
        (outline_dir / f"排綱筆記_{unit_id}.md", "排綱筆記"),
        (outline_dir / f"排綱底稿_{unit_id}.md", "排綱底稿"),
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
        scope = re.sub(r"^單元級\s+", "", re.split(r"[｜|]", heading["comment"])[0].strip())
        if re.match(r"^[A-Za-z]\d*[\w-]*$", scope):
            return scope == unit_id
    id_match = re.search(r"剧情單元\s+([A-Za-z][\w-]*)", heading["title"])
    if id_match:
        return id_match.group(1) == unit_id
    end = next((h["index"] for h in headings if h["index"] > heading["index"]), len(lines))
    for line in lines[heading["index"] + 1 : end]:
        field = re.match(r"^\s*[-*+]\s*單元ID\s*[：:]\s*([A-Za-z][\w-]*)\s*$", line)
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
                f"{label}含「寫綱前查缺」小節"
                if ok
                else f"{draft_file.name} 里沒有「寫綱前查缺」小節——每批出細綱前都要查一遍缺什麼（沒缺也寫「無缺口」），見 workflow-outline.md「寫綱前查缺」"
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
            "evidence": read.get("error", "卷綱文件為空"),
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
            "evidence": f"卷綱中未找到剧情段 {unit_id}",
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
            "剧情段內含「寫綱前查缺」小節"
            if ok
            else f"沒有 .story/排綱筆記/{unit_id}.md，剧情段 {unit_id} 里也沒有「寫綱前查缺」小節——每批出細綱前都要查一遍缺什麼（沒缺也寫「無缺口」），見 workflow-outline.md「寫綱前查缺」"
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
            "用法: node scripts/check-outline-contract.js --json <細綱路徑...> | --json --project <書目錄> --chapter N | --json --supply <卷綱路徑> <單元ID>\n"
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
