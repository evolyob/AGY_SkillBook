#!/usr/bin/env python3
"""Faithful Python 3 port of check-outline-copy.js.

Detects contiguous Han-character overlap (> 15 chars, i.e. >= 16) between
prose files and their corresponding chapter outlines or section outlines,
exempting registered verbatim anchor sentences.
"""

from __future__ import annotations

import errno
import os
import re
import stat
import sys
from typing import Any

MIN_RUN = 16
REPORT_TOP = 8

NON_HAN_RE = re.compile(r'[^\u4e00-\u9fff]')
HEADING_RE = re.compile(r'^ {0,3}(#{1,6})[\t ]+(.*)$')
FIELD_ITEM_RE = re.compile(r'^[-*+][\t ]+')
COMPLETION_FIELD_RE = re.compile(
    r'^[-*+][\t ]+(?:\*\*|__)?实际完成情况[^：:]*[：:]'
)
ANCHOR_BLOCK_RE = re.compile(
    r'(?:原样出现的原话|复沓锚句)[^：:\n]*[：:]([\s\S]*?)(?=\n[-*+]\s|\n#{1,6}\s|$)'
)
ANCHOR_PREFIX_RE = re.compile(
    r'^\s*[-*+]?\s*(?:\d+[.、)]\s*)?(?:点\s*\d+\s*[：:])?'
)
CHAPTER_PREFIX_RE = re.compile(r'^第\s*0*(\d+)\s*章')
OUTLINE_FILE_RE = re.compile(r'^细纲_第0*(\d+)章.*\.md$')
MARKDOWN_HEADING_RE = re.compile(r'^#.*$', re.MULTILINE)


def read_text_file(path_str: str) -> dict[str, Any]:
    """Read a UTF-8 regular file, stripping a single leading BOM if present."""
    try:
        st = os.stat(path_str)
        if not stat.S_ISREG(st.st_mode):
            return {'ok': False, 'reason': '不是普通文件'}
        with open(path_str, 'r', encoding='utf-8') as fh:
            text = fh.read()
        if text.startswith('\ufeff'):
            text = text[1:]
        return {'ok': True, 'text': text}
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            return {'ok': False, 'reason': '不存在'}
        code_name = errno.errorcode.get(exc.errno or 0) or str(exc.errno)
        return {'ok': False, 'reason': f'无法读取（{code_name}）'}


def report_input_error(kind: str, file_path: str, reason: str) -> None:
    """Write a localized input read error to stderr."""
    sys.stderr.write(f'错误: 无法读取{kind} "{file_path}"：{reason}。\n')


def report_usage_error(message: str) -> int:
    """Write a localized CLI usage error to stderr and return exit code 2."""
    sys.stderr.write(f'错误: {message}。\n')
    sys.stderr.write(
        '用法: node check-outline-copy.js [--outline <细纲路径>] <正文路径...>\n'
    )
    return 2


def han_only(text: str) -> str:
    """Strip everything except CJK Unified Ideographs (U+4E00..U+9FFF)."""
    return NON_HAN_RE.sub('', text)


def strip_completion_record(outline: str) -> str:
    """Remove post-write completion record sections and fields from an outline."""
    heading_level = 0
    in_field = False
    kept: list[str] = []

    for line in outline.split('\n'):
        heading = HEADING_RE.match(line)
        if heading_level:
            if not heading or len(heading.group(1)) > heading_level:
                continue
            heading_level = 0
        if in_field:
            if not heading and not FIELD_ITEM_RE.match(line):
                continue
            in_field = False
        if heading and '实际完成情况' in heading.group(2):
            heading_level = len(heading.group(1))
            continue
        if COMPLETION_FIELD_RE.match(line):
            in_field = True
            continue
        kept.append(line)

    return '\n'.join(kept)


def extract_anchors(outline: str) -> list[str]:
    """Extract registered verbatim anchor sentences as Han-only strings."""
    match = ANCHOR_BLOCK_RE.search(outline)
    if not match:
        return []
    anchors: list[str] = []
    for raw_line in match.group(1).split('\n'):
        cleaned = ANCHOR_PREFIX_RE.sub('', raw_line)
        han = han_only(cleaned)
        if len(han) >= 2:
            anchors.append(han)
    return anchors


def _collect_anchor_spans(frag: str, anchors: list[str]) -> list[list[int]]:
    """Find all [start, end] occurrence intervals of anchors inside frag."""
    spans: list[list[int]] = []
    for anchor in anchors:
        from_idx = 0
        while from_idx + len(anchor) <= len(frag):
            at = frag.find(anchor, from_idx)
            if at < 0:
                break
            spans.append([at, at + len(anchor)])
            from_idx = at + 1
    return spans


def split_by_anchors(frag: str, anchors: list[str]) -> tuple[list[str], int]:
    """Excise exact anchor spans from frag and return (remaining_segments, anchored_len)."""
    if any(frag in anchor for anchor in anchors):
        return [], len(frag)

    spans = _collect_anchor_spans(frag, anchors)
    if not spans:
        return [frag], 0

    spans.sort(key=lambda item: item[0])
    merged: list[list[int]] = [spans[0]]
    for start, end in spans[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    rest: list[str] = []
    cursor = 0
    anchored_len = 0
    for start, end in merged:
        if start > cursor:
            rest.append(frag[cursor:start])
        anchored_len += end - start
        cursor = end
    if cursor < len(frag):
        rest.append(frag[cursor:])
    return rest, anchored_len


def find_outline(prose_file: str) -> str | None:
    """Auto-discover the matching outline file for a prose file."""
    base = os.path.basename(prose_file)
    if base == '正文.md':
        sibling = os.path.join(os.path.dirname(prose_file), '小节大纲.md')
        return sibling if os.path.exists(sibling) else None

    match = CHAPTER_PREFIX_RE.match(base)
    if not match:
        return None
    chapter = match.group(1)
    outline_dir = os.path.join(os.path.dirname(os.path.dirname(prose_file)), '大纲')
    try:
        entries = os.listdir(outline_dir)
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            return None
        raise

    for filename in entries:
        fm = OUTLINE_FILE_RE.match(filename)
        if fm and fm.group(1) == chapter:
            return os.path.join(outline_dir, filename)
    return None


def _longest_match_from(prose_han: str, outline_han: str, index: int) -> int:
    """Binary search the longest substring starting at index present in outline_han."""
    if index + MIN_RUN > len(prose_han):
        return 0
    if prose_han[index : index + MIN_RUN] not in outline_han:
        return 0

    best = MIN_RUN
    lo = MIN_RUN
    hi = min(len(prose_han) - index, 200)
    while lo <= hi:
        mid = (lo + hi) >> 1
        if prose_han[index : index + mid] in outline_han:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def _scan_overlaps(
    prose_han: str, outline_han: str, anchors: list[str]
) -> tuple[list[dict[str, Any]], int, int, int]:
    """Greedily scan prose_han for non-overlapping runs matching outline_han."""
    hits: list[dict[str, Any]] = []
    copied = 0
    anchored = 0
    anchored_count = 0
    i = 0

    while i < len(prose_han):
        best = _longest_match_from(prose_han, outline_han, i)
        if not best:
            i += 1
            continue
        frag = prose_han[i : i + best]
        rest, anchored_len = split_by_anchors(frag, anchors)
        if anchored_len:
            anchored += anchored_len
            anchored_count += 1
        for seg in rest:
            if len(seg) >= MIN_RUN:
                hits.append({'frag': seg, 'len': len(seg)})
                copied += len(seg)
        i += best

    return hits, copied, anchored, anchored_count


def _format_report(
    prose_file: str,
    outline_file: str,
    prose_len: int,
    hits: list[dict[str, Any]],
    copied: int,
    anchored: int,
    anchored_count: int,
) -> str:
    """Format the overlap detection report for stdout."""
    rate = f'{(copied * 100) / prose_len:.1f}'
    is_short = os.path.basename(outline_file) == '小节大纲.md'
    if is_short:
        guidance = (
            '逐条对照原文判断：确属把小节大纲叙述搬进正文就重写——大纲只锁功能与结果，'
            '句子在正文现场写；誓词、关键原话、固定专名等功能性重合可保留。每条都要有结论，'
            '不为归零机械改写。保留项由主会话登记进小节大纲.md 表格下方「原样出现的原话：」行下'
            '（每行一条原话，缩进写；旧书叫「复沓锚句」，照认）再复检——子代理只重写正文或标 '
            '`[需复核]` 交回，不改小节大纲。'
        )
    else:
        guidance = (
            '逐条对照原文判断：确属把细纲叙述搬进正文就重写——细纲只锁功能与结果，'
            '句子在正文现场写；系统面板、誓词、案卷原话、固定专名等功能性重合可保留。'
            '每条都要有结论，不为归零机械改写。保留项由主会话补进细纲「原样出现的原话」——'
            '子代理只重写正文或标 `[需复核]` 交回，不改大纲细纲。'
        )

    title_kind = '小节大纲' if is_short else '细纲'
    prose_base = os.path.basename(prose_file)
    outline_base = os.path.basename(outline_file)
    out = [
        f'=== {title_kind}照搬检测（{prose_base}）===',
        f'正文 {prose_len} 字，与 {outline_base} 连续重合 >{MIN_RUN - 1} 字的片段 '
        f'{len(hits)} 处，共 {copied} 字（{rate}%）。',
        guidance,
    ]
    top_hits = sorted(hits, key=lambda h: h['len'], reverse=True)[:REPORT_TOP]
    for hit in top_hits:
        out.append(f"  · {hit['len']} 字「{hit['frag']}」")
    if len(hits) > REPORT_TOP:
        out.append(f'  · …另有 {len(hits) - REPORT_TOP} 处')
    if anchored_count:
        out.append(
            f'（另有 {anchored_count} 处 {anchored} 字为登记原话的逐字落地，不计入誊抄）'
        )
    return '\n'.join(out) + '\n'


def check_one(prose_file: str, explicit_outline: str | None) -> int:
    """Check a single prose file against its explicit or auto-discovered outline."""
    prose_res = read_text_file(prose_file)
    if not prose_res['ok']:
        report_input_error('正文', prose_file, prose_res['reason'])
        return 2
    prose = prose_res['text']

    outline_file = explicit_outline or find_outline(prose_file)
    if not outline_file:
        sys.stdout.write(
            f'细纲照搬检测：跳过 "{prose_file}"（未自动发现细纲）。\n'
        )
        return 0

    outline_res = read_text_file(outline_file)
    if not outline_res['ok']:
        kind = '显式细纲' if explicit_outline else '自动发现的细纲'
        report_input_error(kind, outline_file, outline_res['reason'])
        return 2
    outline = outline_res['text']

    prose_han = han_only(MARKDOWN_HEADING_RE.sub('', prose))
    outline_han = han_only(strip_completion_record(outline))
    if len(prose_han) < MIN_RUN or len(outline_han) < MIN_RUN:
        return 0

    anchors = extract_anchors(outline)
    hits, copied, anchored, anchored_count = _scan_overlaps(
        prose_han, outline_han, anchors
    )
    if not hits:
        if anchored_count:
            base = os.path.basename(prose_file)
            sys.stdout.write(
                f'细纲照搬检测（{base}）：无未授权誊抄；'
                f'另有 {anchored_count} 处 {anchored} 字为登记原话的逐字落地。\n'
            )
        return 0

    report = _format_report(
        prose_file, outline_file, len(prose_han), hits, copied, anchored, anchored_count
    )
    sys.stdout.write(report)
    return 1


def parse_args(argv: list[str]) -> tuple[str | None, list[str]] | int:
    """Parse CLI arguments or return usage error code 2."""
    prose_files: list[str] = []
    explicit_outline: str | None = None
    positional_only = False
    k = 0

    while k < len(argv):
        arg = argv[k]
        if not positional_only and arg == '--':
            positional_only = True
        elif not positional_only and arg == '--outline':
            if explicit_outline is not None:
                return report_usage_error('--outline 不能重复指定')
            val = argv[k + 1] if k + 1 < len(argv) else ''
            if not val or val.startswith('--'):
                return report_usage_error('--outline 缺少路径')
            explicit_outline = val
            k += 1
        elif not positional_only and arg.startswith('--'):
            return report_usage_error(f'未知选项: {arg}')
        else:
            prose_files.append(arg)
        k += 1

    if not prose_files:
        return report_usage_error('缺少正文路径')
    return explicit_outline, prose_files


def main() -> int:
    """CLI entry point for check_outline_copy."""
    parsed = parse_args(sys.argv[1:])
    if isinstance(parsed, int):
        return parsed
    explicit_outline, prose_files = parsed

    status = 0
    for prose_file in prose_files:
        status = max(status, check_one(prose_file, explicit_outline))
    return status


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        sys.stderr.write(f'错误: 细纲照搬检测异常：{exc}。\n')
        sys.exit(2)
