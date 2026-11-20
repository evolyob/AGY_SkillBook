#!/usr/bin/env python3
"""Detect high-risk AI-flavor prose patterns in Chinese fiction manuscripts.

Pure Python 3 (>= 3.10) standard-library port of ``check-ai-patterns.js``.
Reports findings only (never rewrites text) with mechanical vs. semantic
review classification and blocking vs. advisory severity gates.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    from style_whitelist import load_style_whitelist, mask_style_text
except ImportError:  # pragma: no cover - fallback if snake_case is absent
    from style_whitelist import (  # type: ignore[no-redef]
        loadStyleWhitelist as load_style_whitelist,
        maskStyleText as mask_style_text,
    )

USAGE = """Usage: python3 check_ai_patterns.py [--check] [--json] [--fail-on=blocking|all] <file...>
       python3 check_ai_patterns.py --list-review-classes

Detect high-risk AI-flavor prose patterns that need human rewrite:
  - negative setup followed by positive flip in the same sentence
  - comma/semicolon/colon + positive flip
  - sentence break + positive flip
  - repeated negative setup followed by positive flip
  - em-dash (按功能改寫), 碎句號 (連續短敘述句), 長段落 (按鏡頭斷段)
  - 微動作複讀 (「了下/了一下」式輕量補語高密度，電报體指纹)
  - 套式反應細節 (指尖/指節/目光等無功能微動作與「平靜得像在念」式語氣比喻成片)
  - 抽象總結複讀 (命運/棋局/這一刻終於明白/才刚刚開始，AI 結尾腔)
  - 套詞密度過高 (仿佛/一丝/深吸一口氣/平靜無波等禁用詞聚集)
  - 比喻密度過高 (像/好像/仿佛/如同等比喻標記成片複現)
  - 解釋链密度過高 (知道/明白/這意味着/必須/需要等判斷链聚集)
  - 系統公告公文腔過密 (方括號系統/規則行里硬規則詞聚集)
  - 過度精炼短段 (長文本里短敘述段過密且自然連接偏少)
  - 低連接密度 (引號外敘述功能詞/白話連接偏少且中長句不足，像提綱/電报體)
  - 监控摄像頭式動作清單 (同段連續擺放動作動詞，缺少視角溫度/情绪缓冲)
  - 音量反差腔 (聲音不高/不大…卻…, 實戰漏網句式)
  - 否定排比 (沒有X，沒有Y…連排 / 沒X…只是Y 先否定後肯定, 實戰漏網句式)
  - 工整並列 (至於X不X，怎麼X / 同動詞「不V A，不V B」，含台詞，advisory)
  - 反序對比 (是A，不是B — not-is 的反序變種, 實戰漏網句式)
  - 預告式總結收尾 (文末窗口 沒人知道/才刚刚開始/正朝着…压了過去, 實戰漏網句式)
  - 章尾狀態總結體 (文末窗口 這一夜注定/這一切都結束了/新的人生才刚刚開始/命運的齒輪)
  - 引號強調滥用 (敘述里 1-4 字短詞加引號強調，密度型)
  - 敘述省略號過密 (引號與面板外 …… 高密度刷屏，advisory)

Book-local .deslop-whitelist literal spans are excluded from style scanning (no regex or ancestor inheritance).
Each finding carries severity: blocking by default for generation/deslop cleanup (not-is-comparison / em-dash / voice-contrast / negation-parade / reverse-not-is / trailer-ending / trailer-summary), where single/low-count hits of rhetorical patterns downgrade to semantic advisory and high-density clusters block. This is a local style/readability gate, not an AIGC detector score; functional human text can be marked for review instead of hard-edited for a detector.
或 advisory (period-stutter / long-paragraph / micro-action-tic / negation-pair-tic / stock-reaction-tic / action-list-tic / abstract-summary-tic / cliche-density-tic / metaphor-density-tic / reasoning-chain-tic / system-notice-formality-tic / overcompressed-prose-tic / low-connective-density-tic / quote-emphasis-tic / formulaic-parallelism / ellipsis-density-tic，是提示，justified 的長推理/氛围段可保留)。
--fail-on=blocking 只在出現 blocking finding 時退出 1；默認 --fail-on=all 有任何 finding 即退出 1。
Each finding also carries review: mechanical（表面形態確定、就地改寫即可）或 semantic（可能承擔敘事功能，需讀上下文判斷是否保留）；blocking 一律 mechanical。--list-review-classes 輸出完整分類表（JSON）。
HTML comments (<!-- ... -->, e.g. the 去味:跳過 exemption marker) are metadata, not prose, and are never scanned.

The script reports findings only. It never rewrites text, because the safe fix is
contextual: usually delete the negative setup, write the positive term directly,
or show it via action/detail."""

STOP_CHARS = frozenset({'。', '！', '？', '!', '?', '\n'})
SOFT_SEPARATORS = frozenset({'，', ',', '、', '；', ';', '：', ':'})
HARD_SEPARATORS = frozenset({'。', '.', '！', '!', '？', '?'})
MAX_NEGATIVE_SPAN = 80
MAX_POSITIVE_SPAN = 80

_DESLOP_RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "deslop_rules.json"
_AI_CFG = json.loads(_DESLOP_RULES_PATH.read_text(encoding="utf-8"))["ai_pattern_rules"]

STUTTER_MIN_RUN = int(_AI_CFG["stutter_min_run"])
STUTTER_MAX_SENTENCE = int(_AI_CFG["stutter_max_sentence"])
LONG_PARAGRAPH_CHARS = int(_AI_CFG["long_paragraph_chars"])

MICRO_TIC_PATTERN = re.compile(_AI_CFG["micro_tic"]["regex"])
MICRO_TIC_MIN_HITS = int(_AI_CFG["micro_tic"]["min_hits"])
NEGATION_PAIR_PATTERN = re.compile(_AI_CFG["negation_pair"]["regex"])
NEGATION_PAIR_MIN_HITS = int(_AI_CFG["negation_pair"]["min_hits"])
MICRO_TIC_PER_KILO = float(_AI_CFG["micro_tic"]["per_kilo"])

STOCK_REACTION_PATTERNS = [re.compile(p) for p in _AI_CFG["stock_reactions"]["patterns"]]
STOCK_REACTION_MIN_HITS = int(_AI_CFG["stock_reactions"]["min_hits"])
STOCK_REACTION_PER_KILO = float(_AI_CFG["stock_reactions"]["per_kilo"])

ACTION_LIST_VERB_PATTERN = re.compile(_AI_CFG["action_list"]["regex"])
ACTION_LIST_MIN_HITS = int(_AI_CFG["action_list"]["min_hits"])
ACTION_LIST_MIN_SEPARATORS = int(_AI_CFG["action_list"]["min_separators"])

ABSTRACT_SUMMARY_PATTERNS = [re.compile(p) for p in _AI_CFG["abstract_summary"]["patterns"]]
ABSTRACT_SUMMARY_MIN_HITS = int(_AI_CFG["abstract_summary"]["min_hits"])
ABSTRACT_SUMMARY_PER_KILO = float(_AI_CFG["abstract_summary"]["per_kilo"])

CLICHE_PATTERNS = [re.compile(p) for p in _AI_CFG["cliche_density"]["patterns"]]
CLICHE_DENSITY_MIN_HITS = int(_AI_CFG["cliche_density"]["min_hits"])
CLICHE_DENSITY_PER_KILO = float(_AI_CFG["cliche_density"]["per_kilo"])

METAPHOR_MARKER_PATTERN = re.compile(_AI_CFG["metaphor_density"]["marker_regex"])
METAPHOR_LIKE_PHRASE_PATTERN = re.compile(_AI_CFG["metaphor_density"]["like_phrase_regex"])
METAPHOR_DENSITY_MIN_HITS = int(_AI_CFG["metaphor_density"]["min_hits"])
METAPHOR_DENSITY_PER_KILO = float(_AI_CFG["metaphor_density"]["per_kilo"])

REASONING_CHAIN_PATTERNS = [
    {"key": item["key"], "core": bool(item["core"]), "pattern": re.compile(item["regex"])}
    for item in _AI_CFG["reasoning_chain"]["patterns"]
]
REASONING_CHAIN_MIN_HITS = int(_AI_CFG["reasoning_chain"]["min_hits"])
REASONING_CHAIN_CORE_MIN_HITS = int(_AI_CFG["reasoning_chain"]["core_min_hits"])
REASONING_CHAIN_MIN_LINKS = int(_AI_CFG["reasoning_chain"]["min_links"])
REASONING_CHAIN_MIN_BUCKETS = int(_AI_CFG["reasoning_chain"]["min_buckets"])
REASONING_CHAIN_PER_KILO = float(_AI_CFG["reasoning_chain"]["per_kilo"])

NOTICE_FORMAL_PATTERNS = [re.compile(p) for p in _AI_CFG["notice_formal"]["patterns"]]
NOTICE_FORMAL_CORE_PATTERN = re.compile(_AI_CFG["notice_formal"]["core_regex"])
NOTICE_FORMAL_MIN_LINES = 4
NOTICE_FORMAL_MIN_HITS = 12
NOTICE_FORMAL_CORE_MIN_HITS = 5
NOTICE_FORMAL_PER_KILO = 60

OVERCOMPRESSED_PROSE_PARTICLE_PATTERN = re.compile(r'[的了就着過呢吧啊呀嘛]')
OVERCOMPRESSED_PROSE_MIN_CHARS = 1200
OVERCOMPRESSED_PROSE_MIN_PARAS = 45
OVERCOMPRESSED_PROSE_SHORT_MAX_CHARS = 15
OVERCOMPRESSED_PROSE_SHORT_RATIO = 0.58
OVERCOMPRESSED_PROSE_PARTICLE_PER_KILO = 85

LOW_CONNECTIVE_FUNCTION_TERMS = list(_AI_CFG["low_connective_function_terms"])
LOW_CONNECTIVE_PLAIN_TERMS = list(_AI_CFG["low_connective_plain_terms"])
LOW_CONNECTIVE_MIN_CHARS = int(_AI_CFG["low_connective_min_chars"])
LOW_CONNECTIVE_FUNCTION_PER_KILO = float(_AI_CFG["low_connective_function_per_kilo"])
LOW_CONNECTIVE_PLAIN_PER_KILO = float(_AI_CFG["low_connective_plain_per_kilo"])
LOW_CONNECTIVE_LONG_SENTENCE_CHARS = int(_AI_CFG["low_connective_long_sentence_chars"])
LOW_CONNECTIVE_LONG_SENTENCE_RATIO = float(_AI_CFG["low_connective_long_sentence_ratio"])

COMPACT_EITHER_OR_PREV = frozenset({'不', '就', '也'})
TAG_PARTICLES = frozenset({'吗', '吧', '嘛'})
AFFIRMATION_TAG_PARTICLES = frozenset({'的', '啊', '呀', '呢'})
AFFIRMATION_TAG_BOUNDARY = frozenset({'', '，', ',', '。', '.', '！', '!', '？', '?', '、', '；', ';', '：', ':', '\n', '\r', '\t', ' '})


def escape_regexp_char_class(text: str) -> str:
    """Escape characters that have special meaning inside a regex character class."""
    return re.sub(r'([\\\]^-])', r'\\\1', text)


QUOTE_PAIRS = [('「', '」'), ('『', '』'), ('【', '】'), ('“', '”'), ('‘', '’'), ('"', '"'), ("'", "'")]
QUOTE_PATTERNS = [
    re.compile(f"{re.escape(open_q)}[^{escape_regexp_char_class(close_q)}\\n]*{re.escape(close_q)}")
    for open_q, close_q in QUOTE_PAIRS
]

VOICE_CONTRAST_PATTERN = re.compile(_AI_CFG["voice_contrast_regex"])
NEGATION_PARADE_PATTERNS = [re.compile(p) for p in _AI_CFG["negation_parade_patterns"]]
CROSS_NEGATION_START = re.compile(_AI_CFG["cross_negation_start_regex"])
CROSS_NEGATION_MIDDLE = re.compile(_AI_CFG["cross_negation_middle_regex"])
CROSS_NEGATION_END = re.compile(_AI_CFG["cross_negation_end_regex"])

DECISION_FRAME_PATTERN = re.compile(_AI_CFG["decision_frame_regex"])
REPEATED_NEGATIVE_VERB_PATTERN = re.compile(_AI_CFG["repeated_negative_verb_regex"])

REVERSE_NOT_IS_PATTERN = re.compile(_AI_CFG["reverse_not_is_regex"])
REVERSE_NOT_IS_PREV_EXCLUDE = frozenset(_AI_CFG["reverse_not_is_prev_exclude"])

TRAILER_ENDING_PATTERN = re.compile(_AI_CFG["trailer_ending_regex"])
TRAILER_ENDING_WINDOW_CHARS = int(_AI_CFG["trailer_ending_window_chars"])
TRAILER_SUMMARY_PATTERN = re.compile(_AI_CFG["trailer_summary_regex"])

QUOTE_EMPHASIS_MIN_HITS = int(_AI_CFG["quote_emphasis_min_hits"])
QUOTE_EMPHASIS_MAX_VISIBLE = int(_AI_CFG["quote_emphasis_max_visible"])
QUOTE_EMPHASIS_SPEECH_VERB_PATTERN = re.compile(_AI_CFG["quote_emphasis_speech_verb_regex"])

ELLIPSIS_DENSITY_PATTERN = re.compile(_AI_CFG["ellipsis_density_regex"])
ELLIPSIS_DENSITY_MIN_HITS = int(_AI_CFG["ellipsis_density_min_hits"])
ELLIPSIS_DENSITY_PER_KILO = float(_AI_CFG["ellipsis_density_per_kilo"])

DENSITY_SCALE_UNIT_CHARS = int(_AI_CFG["density_scale_unit_chars"])
NOT_IS_BLOCKING_MIN_HITS = int(_AI_CFG["not_is_blocking_min_hits"])
VOICE_CONTRAST_BLOCKING_MIN_HITS = int(_AI_CFG["voice_contrast_blocking_min_hits"])
NEGATION_PARADE_BLOCKING_MIN_HITS = int(_AI_CFG["negation_parade_blocking_min_hits"])
TRAILER_ENDING_BLOCKING_MIN_HITS = int(_AI_CFG["trailer_ending_blocking_min_hits"])

REVIEW_CLASSES: dict[str, str] = dict(_AI_CFG["review_classes"])

DASH_PATTERN = re.compile(r'——|—|--+')
UNCLOSED_QUOTE_OPEN_PATTERN = re.compile(r'[“「『"]')
QUOTE_EMPHASIS_PUNCT_PATTERN = re.compile(r'[。！？!?…，,；;：:—]|\.{2,}')
ONOMA_AFTER_PATTERN = re.compile(r'^(?:的|地)?一?[聲下响]')
ELLIPSIS_UNCLOSED_TAIL_PATTERN = re.compile(r'[“「『"][^”」』"]*$')
NOTICE_LINE_PATTERN = re.compile(r'^【[^】]+】$')
DIVIDER_HYPHEN_PATTERN = re.compile(r'^-{3,}$')
DIVIDER_OTHER_PATTERN = re.compile(r'^[*_]{3,}$')
STRUCTURAL_MD_PATTERN = re.compile(r'^(?:#{1,6}(?:\s|\d)|>\s?|[-*+]\s|\d+[.)]\s|\|)')
STRUCTURAL_CHAPTER_PATTERN = re.compile(r'^第[零〇一二三四五六七八九十百千万两\d]+[章節回](?:$|[\s_：:——\-]+[^\n。；;]{0,28}$)')
SENTENCE_SPLIT_PATTERN = re.compile(r'[。！？!?]')
VISIBLE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff\uff21-\uff5aA-Za-z0-9]')
FENCE_PATTERN = re.compile(r'^(?:`{3,}|~{3,})')
YAML_FIELD_PATTERN = re.compile(r'^[A-Za-z0-9_-]+:\s*')
TRAILING_NOISE_PATTERN = re.compile(r'[\s|）)】\]]+$')
SEPARATORS_COUNT_PATTERN = re.compile(r'[，、；;]')
METAPHOR_PREFIX_PATTERN = re.compile(r'好像|像是|像|仿佛|宛如|如同|犹如')


def review_class(finding_type: str) -> str:
    """Return the review class ('mechanical' or 'semantic') for a finding type."""
    review = REVIEW_CLASSES.get(finding_type)
    if not review:
        print(
            f"internal error: finding type '{finding_type}' has no review class (add it to REVIEW_CLASSES)",
            file=sys.stderr,
        )
        sys.exit(2)
    return review


def die(message: str) -> None:
    """Print an error message and usage to stderr, then exit with code 2."""
    print(message, file=sys.stderr)
    print(USAGE.rstrip(), file=sys.stderr)
    sys.exit(2)


def is_divider(trimmed: str) -> bool:
    """Return True if the trimmed line is a Markdown horizontal rule."""
    return bool(DIVIDER_HYPHEN_PATTERN.match(trimmed) or DIVIDER_OTHER_PATTERN.match(trimmed))


def is_structural(trimmed: str) -> bool:
    """Return True if the trimmed line is a Markdown heading/list/quote/table or chapter header."""
    return bool(STRUCTURAL_MD_PATTERN.match(trimmed) or STRUCTURAL_CHAPTER_PATTERN.match(trimmed))


def strip_quoted(text: str) -> str:
    """Remove paired quote/bracket spans from text, leaving only narrative prose."""
    out = text
    for pattern in QUOTE_PATTERNS:
        out = pattern.sub('', out)
    return out


def mask_quoted(text: str) -> str:
    """Replace paired quote/bracket spans with equal-length '？' placeholders."""
    out = text
    for pattern in QUOTE_PATTERNS:
        out = pattern.sub(lambda m: '？' * len(m.group(0)), out)
    return out


def mask_quoted_with_unclosed(text: str) -> str:
    """Mask paired quotes and any unclosed trailing quote from its opening mark to EOL."""
    out = mask_quoted(text)
    unclosed = UNCLOSED_QUOTE_OPEN_PATTERN.search(out)
    if not unclosed:
        return out
    idx = unclosed.start()
    return out[:idx] + '？' * (len(out) - idx)


def quoted_ranges(text: str) -> list[tuple[int, int]]:
    """Return [start, end) character index ranges for all paired quote/bracket spans."""
    ranges: list[tuple[int, int]] = []
    for pattern in QUOTE_PATTERNS:
        for match in pattern.finditer(text):
            ranges.append((match.start(), match.end()))
    return ranges


def inside_ranges(pos: int, ranges: list[tuple[int, int]]) -> bool:
    """Return True if character offset pos falls inside any [start, end) range."""
    return any(start <= pos < end for start, end in ranges)


def split_sentences(trimmed: str) -> list[str]:
    """Split text into non-empty trimmed sentences on Chinese/ASCII sentence-ending punctuation."""
    return [s.strip() for s in SENTENCE_SPLIT_PATTERN.split(trimmed) if s.strip()]


def compact(text: str) -> str:
    """Collapse whitespace and truncate excerpts longer than 80 characters."""
    normalized = re.sub(r'\s+', ' ', text).strip()
    return f"{normalized[:77]}..." if len(normalized) > 80 else normalized


def sentence_around(text: str, index: int) -> str:
    """Extract and compact the sentence surrounding character index."""
    start = index
    while start > 0 and text[start - 1] not in STOP_CHARS:
        start -= 1
    end = index
    while end < len(text) and text[end] not in STOP_CHARS:
        end += 1
    return compact(text[start:end].strip())


def visible_length(sentence: str) -> int:
    """Count visible CJK, fullwidth Latin, ASCII letter, and digit characters."""
    return len(VISIBLE_CHAR_PATTERN.findall(sentence))


def count_terms(text: str, terms: list[str]) -> int:
    """Count non-overlapping occurrences of each term in text."""
    return sum(text.count(term) for term in terms)


def mask_html_comments(
    line: str,
    open_before: bool,
    line_index: int = 0,
    unclosed_openings: set[str] | None = None,
) -> tuple[str, bool, str | None]:
    """Replace HTML comment spans with equal-length spaces, tracking multi-line state."""
    if unclosed_openings is None:
        unclosed_openings = set()
    out_parts: list[str] = []
    is_open = open_before
    cursor = 0
    opened_at: str | None = None

    while cursor < len(line):
        if is_open:
            close = line.find('-->', cursor)
            end = len(line) if close == -1 else close + 3
            out_parts.append(' ' * (end - cursor))
            cursor = end
            if close != -1:
                is_open = False
            continue
        start = line.find('<!--', cursor)
        if start == -1:
            out_parts.append(line[cursor:])
            break
        out_parts.append(line[cursor:start])
        out_parts.append('    ')
        cursor = start + 4
        key = f"{line_index}:{start}"
        if key in unclosed_openings:
            continue
        is_open = True
        opened_at = key

    return ''.join(out_parts), is_open, opened_at


def parse_fence_marker(trimmed_line: str) -> tuple[str, int] | None:
    """Parse a Markdown code fence marker (``` or ~~~) if present at line start."""
    match = FENCE_PATTERN.match(trimmed_line)
    if not match:
        return None
    marker = match.group(0)
    return marker[0], len(marker)


def has_yaml_front_matter(lines: list[str]) -> bool:
    """Return True if the document starts with a valid YAML front-matter block."""
    if not lines or lines[0].strip() != '---':
        return False
    saw_yaml_field = False
    for i in range(1, min(len(lines), 40)):
        trimmed = lines[i].strip()
        if trimmed == '---':
            return saw_yaml_field
        if YAML_FIELD_PATTERN.match(trimmed):
            saw_yaml_field = True
    return False


def is_inline_space(char: str) -> bool:
    """Return True for space, tab, or carriage return."""
    return char in (' ', '\t', '\r')


def skip_gap(text: str, index: int) -> int:
    """Advance past inline spaces and newlines to the next non-whitespace character."""
    while index < len(text) and (is_inline_space(text[index]) or text[index] == '\n'):
        index += 1
    return index


def starts_with_at(text: str, index: int, needle: str) -> bool:
    """Return True if text[index:] starts with needle."""
    return text[index:index + len(needle)] == needle


def is_affirmation_tag_at(text: str, index: int) -> bool:
    """Return True if '是' at index is part of a confirmation tag like '是的/是啊'."""
    if index >= len(text) or text[index] != '是':
        return False
    particle = text[index + 1] if index + 1 < len(text) else ''
    if particle not in AFFIRMATION_TAG_PARTICLES:
        return False
    boundary = text[index + 2] if index + 2 < len(text) else ''
    return boundary in AFFIRMATION_TAG_BOUNDARY


def trim_trailing_noise(text: str) -> str:
    """Strip trailing whitespace and closing brackets from an excerpt."""
    return TRAILING_NOISE_PATTERN.sub('', text)


def position_for_offset(line_starts: list[tuple[int, int]], offset: int) -> tuple[int, int]:
    """Binary-search line_starts to map a block character offset to (line_no, column)."""
    low = 0
    high = len(line_starts) - 1

    while low <= high:
        mid = (low + high) // 2
        current_offset, current_line = line_starts[mid]
        next_offset = line_starts[mid + 1][0] if mid + 1 < len(line_starts) else None

        if offset < current_offset:
            high = mid - 1
        elif next_offset is not None and offset >= next_offset:
            low = mid + 1
        else:
            return current_line, offset - current_offset + 1

    return line_starts[0][1], 1


def find_positive_flip_end(candidate: str) -> int:
    """Find the end offset of a positive flip ('而是'/'是') after '不是', or -1."""
    index = 2
    scanned = 0
    crossed_separator = False

    while index < len(candidate) and scanned <= MAX_NEGATIVE_SPAN:
        char = candidate[index]

        if starts_with_at(candidate, index, '而是'):
            return index + 2

        if char in SOFT_SEPARATORS:
            nxt = skip_gap(candidate, index + 1)
            if starts_with_at(candidate, nxt, '而是'):
                return nxt + 2
            nxt_char = candidate[nxt] if nxt < len(candidate) else ''
            nxt_after = candidate[nxt + 1] if nxt + 1 < len(candidate) else ''
            if nxt_char == '是' and nxt_after not in TAG_PARTICLES and not is_affirmation_tag_at(candidate, nxt):
                return nxt + 1
            crossed_separator = True

        if char in HARD_SEPARATORS:
            nxt = skip_gap(candidate, index + 1)
            nxt_char = candidate[nxt] if nxt < len(candidate) else ''
            nxt_after = candidate[nxt + 1] if nxt + 1 < len(candidate) else ''
            if nxt_char == '是' and nxt_after not in TAG_PARTICLES and not is_affirmation_tag_at(candidate, nxt):
                return nxt + 1
            if char != '.':
                break
            crossed_separator = True

        if char in STOP_CHARS:
            break

        if char == '是' and candidate[index - 1] not in COMPACT_EITHER_OR_PREV and not crossed_separator:
            return index + 1

        index += 1
        scanned += 1

    return -1


def extract_finding(candidate: str, marker_end: int) -> str:
    """Extract up to MAX_POSITIVE_SPAN characters after marker_end, stopping at STOP_CHARS."""
    end = marker_end
    limit = min(len(candidate), marker_end + MAX_POSITIVE_SPAN)
    while end < limit:
        if candidate[end] in STOP_CHARS:
            break
        end += 1
    return candidate[:end]


def find_not_is_comparisons(text: str, line_starts: list[tuple[int, int]]) -> list[dict[str, Any]]:
    """Scan a prose block for '不是A，而是B' / '不是A，是B' comparison patterns."""
    findings: list[dict[str, Any]] = []
    quoted = quoted_ranges(text)
    offset = 0

    while offset < len(text):
        start = text.find('不是', offset)
        if start == -1:
            break

        if inside_ranges(start, quoted):
            offset = start + 2
            continue

        if start > 0 and text[start - 1] == '是':
            offset = start + 2
            continue

        candidate = text[start:]
        marker_end = find_positive_flip_end(candidate)
        if marker_end == -1:
            offset = start + 2
            continue

        raw = trim_trailing_noise(extract_finding(candidate, marker_end))
        if len(raw) >= 4:
            line_no, col_no = position_for_offset(line_starts, start)
            findings.append({
                'line': line_no,
                'column': col_no,
                'type': 'not-is-comparison',
                'severity': 'blocking',
                'message': '高頻 AI 對比句式；刪掉否定铺垫，直接寫後項（直白情绪、判斷、對話或具體細節皆可）。',
                'excerpt': compact(raw),
            })

        offset = start + max(len(raw), 2)

    return findings


def scan_block(block: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Join a contiguous prose block and scan for cross-line not-is comparisons."""
    text = '\n'.join(entry_text for entry_text, _ in block)
    line_starts: list[tuple[int, int]] = []
    cursor = 0
    for entry_text, line_no in block:
        line_starts.append((cursor, line_no))
        cursor += len(entry_text) + 1
    return find_not_is_comparisons(text, line_starts)


def find_voice_contrast(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect '聲音不大/不高…卻/但…' contrast clichés outside quotes."""
    findings: list[dict[str, Any]] = []
    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        masked = mask_quoted(text)
        for match in VOICE_CONTRAST_PATTERN.finditer(masked):
            findings.append({
                'line': line_no,
                'column': match.start() + 1,
                'type': 'voice-contrast',
                'severity': 'blocking',
                'message': '音量反差腔：「聲音不大/不高…卻/但…」是 AI 高頻反差模板；刪掉音量铺垫，直接寫台詞分量、利害後果或在场者的立场反應。',
                'excerpt': compact(text[match.start():match.end()]),
            })
    return findings


def find_negation_parade(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect negation parades ('沒有X，沒有Y…') outside quotes with span deduplication."""
    findings: list[dict[str, Any]] = []
    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        masked = mask_quoted(text)

        spans: list[tuple[int, int]] = []
        for pattern in NEGATION_PARADE_PATTERNS:
            for match in pattern.finditer(masked):
                spans.append((match.start(), match.end()))
        spans.sort(key=lambda span: span[0])

        last_end = -1
        for start, end in spans:
            if start < last_end:
                last_end = max(last_end, end)
                continue
            last_end = end
            findings.append({
                'line': line_no,
                'column': start + 1,
                'type': 'negation-parade',
                'severity': 'blocking',
                'message': '否定排比：「沒有X，沒有Y…」/「沒X，沒有Y，只是Z」是 AI 高頻排比模板；刪掉否定清單，直接寫現场實際有什麼，最多留一個最有信息量的否定。',
                'excerpt': compact(text[start:end]),
            })
    return findings


def find_formulaic_parallelism(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect symmetric decision/negation frames and cross-paragraph '不是/也不是/只是' triads."""
    findings: list[dict[str, Any]] = []

    frame_specs = [
        (DECISION_FRAME_PATTERN, '「至於X不X，怎麼X」把同一决定拆成工整欄目；若只是複述細綱，压成角色當下的一次判斷或直接動作。'),
        (REPEATED_NEGATIVE_VERB_PATTERN, '同動詞「不V A，不V B」容易寫成否定清單；含台詞也要按語境複核，保留真正有功能的一項即可。'),
    ]

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        for pattern, message in frame_specs:
            for match in pattern.finditer(text):
                findings.append({
                    'line': line_no,
                    'column': match.start() + 1,
                    'type': 'formulaic-parallelism',
                    'severity': 'advisory',
                    'message': message,
                    'excerpt': compact(match.group(0)),
                })

    window: list[tuple[str, str, int]] = []
    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed:
            continue
        if is_divider(trimmed) or is_structural(trimmed):
            window.clear()
            continue
        if window and line_no - window[-1][2] > 2:
            window.clear()
        window.append((mask_quoted(trimmed), trimmed, line_no))
        if len(window) > 3:
            window.pop(0)
        if len(window) != 3:
            continue
        if (
            not CROSS_NEGATION_START.match(window[0][0])
            or not CROSS_NEGATION_MIDDLE.match(window[1][0])
            or not CROSS_NEGATION_END.match(window[2][0])
        ):
            continue
        findings.append({
            'line': window[0][2],
            'column': 1,
            'type': 'formulaic-parallelism',
            'severity': 'advisory',
            'message': '跨段「不是… / 也不是… / 只是…」可能是工整否定铺排，也可能承擔辯解或悬念排除；通讀語境，只在重複細綱或拖慢畫面時改寫。',
            'excerpt': compact(' / '.join(entry[1] for entry in window)),
        })

    return findings


def find_reverse_not_is(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect reverse comparison '是A，不是B' outside quotes."""
    findings: list[dict[str, Any]] = []
    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        masked = mask_quoted(text)
        for match in REVERSE_NOT_IS_PATTERN.finditer(masked):
            start = match.start()
            if start > 0 and masked[start - 1] in REVERSE_NOT_IS_PREV_EXCLUDE:
                continue
            if start + 1 < len(masked) and masked[start + 1] == '不':
                continue
            if is_affirmation_tag_at(masked, start):
                continue
            if match.group(2) and match.group(2)[0] in ('吗', '麼', '吧'):
                continue
            findings.append({
                'line': line_no,
                'column': start + 1,
                'type': 'reverse-not-is',
                'severity': 'blocking',
                'message': '反序對比腔：「是A，不是B」與「不是A，是B」同族；刪掉後置否定，直接寫 A 的具體表現，或用細節讓讀者自己對比。',
                'excerpt': compact(text[start:match.end()]),
            })
    return findings


def find_trailer_ending(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Scan the trailing window of narrative prose for trailer-ending and trailer-summary clichés."""
    window_lines: list[tuple[str, int]] = []
    accumulated = 0

    for i in range(len(prose_lines) - 1, -1, -1):
        if accumulated >= TRAILER_ENDING_WINDOW_CHARS:
            break
        text, line_no = prose_lines[i]
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        window_lines.append((text, line_no))
        accumulated += visible_length(strip_quoted(trimmed))

    window_lines.reverse()

    findings: list[dict[str, Any]] = []
    for text, line_no in window_lines:
        masked = mask_quoted(text)
        for match in TRAILER_ENDING_PATTERN.finditer(masked):
            findings.append({
                'line': line_no,
                'column': match.start() + 1,
                'type': 'trailer-ending',
                'severity': 'blocking',
                'message': '預告式總結收尾：「沒人知道/才刚刚開始/正朝着…压了過去」是 AI 章尾預告腔；結尾停在具體决定、動作、畫面或一句台詞上，悬念讓事件自己掛住，別替讀者預告下一章。',
                'excerpt': compact(text[match.start():match.end()]),
            })
        for match in TRAILER_SUMMARY_PATTERN.finditer(masked):
            findings.append({
                'line': line_no,
                'column': match.start() + 1,
                'type': 'trailer-summary',
                'severity': 'blocking',
                'message': '章尾狀態總結體：「這一夜注定…/這一切都結束了/新的人生才刚刚開始/命運的齒輪」是把細綱的結尾設定原樣寫成了總結句；結尾設定要落成最後一個具體决定、動作、畫面或台詞，別替讀者盖章。',
                'excerpt': compact(text[match.start():match.end()]),
            })

    return findings


def find_quote_emphasis_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect overuse of 1-4 character quoted emphasis spans in narrative prose."""
    hits = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        if visible_length(strip_quoted(trimmed)) == 0:
            continue
        ranges = quoted_ranges(text)

        for start, end in ranges:
            if text[start] == '【':
                continue
            if any(s2 <= start and end <= e2 and (s2 != start or e2 != end) for s2, e2 in ranges):
                continue
            inner = text[start + 1:end - 1]
            visible = visible_length(inner)
            if visible < 1 or visible > QUOTE_EMPHASIS_MAX_VISIBLE:
                continue
            if QUOTE_EMPHASIS_PUNCT_PATTERN.search(inner):
                continue
            before = text[max(0, start - 8):start]
            after = text[end:end + 6]
            if QUOTE_EMPHASIS_SPEECH_VERB_PATTERN.search(before) or QUOTE_EMPHASIS_SPEECH_VERB_PATTERN.search(after):
                continue
            if ONOMA_AFTER_PATTERN.match(after):
                continue
            hits += 1
            if first_line is None:
                first_line = line_no
            if len(samples) < 6 and inner not in samples:
                samples.append(inner)

    if hits < QUOTE_EMPHASIS_MIN_HITS:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'quote-emphasis-tic',
        'severity': 'advisory',
        'message': f'引號強調滥用：敘述里 1-4 字短詞加引號強調 {hits} 處；只留真正反讽/轉述必要的一两處，其余去掉引號直寫原意，或把話里的反讽直接點明。',
        'excerpt': compact(' '.join(samples)),
    }]


def find_negation_pair_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect high frequency of '沒A，也沒B' / '不A，也不B' negation pairs in narrative prose."""
    hits = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = strip_quoted(trimmed)
        for match in NEGATION_PAIR_PATTERN.finditer(narrative):
            hits += 1
            if first_line is None:
                first_line = line_no
            if len(samples) < 4:
                samples.append(match.group(0))

    if hits < NEGATION_PAIR_MIN_HITS:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'negation-pair-tic',
        'severity': 'advisory',
        'message': f'否定對偶偏多：「沒A，也沒B」式敘述 {hits} 處；寫人物沒做什麼是英文式節奏，改成他做了什麼（留一两處真正要強調的）。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_ellipsis_density_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect excessive ellipsis density outside quotes and system panels."""
    hits = 0
    narrative_chars = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = ELLIPSIS_UNCLOSED_TAIL_PATTERN.sub('', strip_quoted(trimmed))
        narrative_chars += visible_length(narrative)
        for match in ELLIPSIS_DENSITY_PATTERN.finditer(narrative):
            hits += 1
            if first_line is None:
                first_line = line_no
            sample = sentence_around(narrative, match.start())
            if len(samples) < 5 and sample and sample not in samples:
                samples.append(sample)

    if narrative_chars == 0 or hits < ELLIPSIS_DENSITY_MIN_HITS:
        return []
    per_kilo = (hits / narrative_chars) * 1000
    if per_kilo < ELLIPSIS_DENSITY_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'ellipsis-density-tic',
        'severity': 'advisory',
        'message': f'敘述省略號過密：引號與面板外省略號 {hits} 處（{per_kilo:.1f}/千字）；保留關鍵思绪留白，其余改成逗號承接、直白判斷或具體動作，別几句一刷。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_micro_action_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect high density of lightweight verbal complements ('了下/了一下') in narrative prose."""
    hits = 0
    narrative_chars = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = strip_quoted(trimmed)
        narrative_chars += visible_length(narrative)
        for match in MICRO_TIC_PATTERN.finditer(narrative):
            hits += 1
            if first_line is None:
                first_line = line_no
            matched = match.group(0)
            if len(samples) < 6 and matched not in samples:
                samples.append(matched)

    if narrative_chars == 0 or hits < MICRO_TIC_MIN_HITS:
        return []
    per_kilo = (hits / narrative_chars) * 1000
    if per_kilo < MICRO_TIC_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'micro-action-tic',
        'severity': 'advisory',
        'message': f'微動作複讀：「了下/了一下」式輕量補語 {hits} 處（{per_kilo:.1f}/千字）；同一反應模板高密度複現是機械指纹，合並動作 beat、換具體細節，別每個動作都補一個輕反應尾巴。',
        'excerpt': compact(' '.join(samples)),
    }]


def find_stock_reaction_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect clusters of stock body-part reactions and tone similes in narrative prose."""
    hits = 0
    narrative_chars = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = strip_quoted(trimmed)
        narrative_chars += visible_length(narrative)

        for pattern in STOCK_REACTION_PATTERNS:
            for match in pattern.finditer(narrative):
                hits += 1
                if first_line is None:
                    first_line = line_no
                sample = sentence_around(narrative, match.start())
                if len(samples) < 6 and sample and sample not in samples:
                    samples.append(sample)

    if narrative_chars == 0 or hits < STOCK_REACTION_MIN_HITS:
        return []
    per_kilo = (hits / narrative_chars) * 1000
    if per_kilo < STOCK_REACTION_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'stock-reaction-tic',
        'severity': 'advisory',
        'message': f'套式反應細節：指尖/指腹/喉結/眼圈/拢住按住/視線停頓等套式微動作或“平靜得像在念”式語氣比喻 {hits} 處（{per_kilo:.1f}/千字）；逐處做刪除測試，只標注情绪、不改變選择、關系或物理結果的直接刪掉，或改成直白情绪與利害判斷，不要換部位或換道具继續演。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_action_list_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect CCTV-style sequential action verb lists within a single paragraph."""
    findings: list[dict[str, Any]] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = strip_quoted(trimmed).strip()
        if not narrative:
            continue

        verbs = ACTION_LIST_VERB_PATTERN.findall(narrative)
        if len(verbs) < ACTION_LIST_MIN_HITS:
            continue
        separators = len(SEPARATORS_COUNT_PATTERN.findall(narrative))
        if separators < ACTION_LIST_MIN_SEPARATORS:
            continue

        findings.append({
            'line': line_no,
            'column': 1,
            'type': 'action-list-tic',
            'severity': 'advisory',
            'message': f'监控摄像頭式動作清單：同段連續動作動詞 {len(verbs)} 個、分隔符 {separators} 個；合並琐碎步驟，只保留有情绪/情節功能的動作，必要時用角色犹豫、誤判或环境反馈做缓冲。',
            'excerpt': compact(' '.join(verbs[:8])),
        })

    return findings


def find_cliche_density_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect high density of banned AI cliché words in narrative prose."""
    hits = 0
    narrative_chars = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = strip_quoted(trimmed)
        narrative_chars += visible_length(narrative)

        for pattern in CLICHE_PATTERNS:
            for match in pattern.finditer(narrative):
                hits += 1
                if first_line is None:
                    first_line = line_no
                matched = match.group(0)
                if len(samples) < 8 and matched not in samples:
                    samples.append(matched)

    if narrative_chars == 0 or hits < CLICHE_DENSITY_MIN_HITS:
        return []
    per_kilo = (hits / narrative_chars) * 1000
    if per_kilo < CLICHE_DENSITY_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'cliche-density-tic',
        'severity': 'advisory',
        'message': f'套詞密度過高：高危 AI 套詞 {hits} 處（{per_kilo:.1f}/千字）；不要同義詞輪換，直接刪或改成直白情绪、角色利害判斷、對話或具體後果，別硬塞手眼小動作。',
        'excerpt': compact(' '.join(samples)),
    }]


def find_metaphor_density_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect excessive density of simile/metaphor markers in narrative prose."""
    hits = 0
    narrative_chars = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = strip_quoted(trimmed)
        narrative_chars += visible_length(narrative)

        for match in METAPHOR_MARKER_PATTERN.finditer(narrative):
            hits += 1
            if first_line is None:
                first_line = line_no
            sample = sentence_around(narrative, match.start())
            if len(samples) < 6 and sample and sample not in samples:
                samples.append(sample)

        for match in METAPHOR_LIKE_PHRASE_PATTERN.finditer(narrative):
            prefix = narrative[max(0, match.start() - 8):match.start()]
            if METAPHOR_PREFIX_PATTERN.search(prefix):
                continue
            hits += 1
            if first_line is None:
                first_line = line_no
            sample = sentence_around(narrative, match.start())
            if len(samples) < 6 and sample and sample not in samples:
                samples.append(sample)

    if narrative_chars == 0 or hits < METAPHOR_DENSITY_MIN_HITS:
        return []
    per_kilo = (hits / narrative_chars) * 1000
    if per_kilo < METAPHOR_DENSITY_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'metaphor-density-tic',
        'severity': 'advisory',
        'message': f'比喻密度過高：像/好像/仿佛/如同等比喻標記 {hits} 處（{per_kilo:.1f}/千字）；保留最有敘事功能的少數比喻，其余回到直白情绪、角色判斷、對話或具體後果，不要換成新比喻或小動作。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_reasoning_chain_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect dense essay-style reasoning chains ('這意味着/必須/知道') in narrative prose."""
    hits = 0
    core_hits = 0
    link_hits = 0
    narrative_chars = 0
    first_line: int | None = None
    samples: list[str] = []
    buckets: set[str] = set()

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = strip_quoted(trimmed)
        narrative_chars += visible_length(narrative)
        accepted_spans: list[tuple[int, int]] = []

        for spec in REASONING_CHAIN_PATTERNS:
            pattern = spec['pattern']
            key = spec['key']
            core = spec['core']
            for match in pattern.finditer(narrative):
                start, end = match.start(), match.end()
                if any(start < b and end > a for a, b in accepted_spans):
                    continue
                accepted_spans.append((start, end))
                hits += 1
                if core:
                    core_hits += 1
                if key in ('connector', 'modal'):
                    link_hits += 1
                buckets.add(key)
                if first_line is None:
                    first_line = line_no
                sample = compact(match.group(0))
                if len(samples) < 8 and sample not in samples:
                    samples.append(sample)

    if narrative_chars == 0 or hits < REASONING_CHAIN_MIN_HITS:
        return []
    if core_hits < REASONING_CHAIN_CORE_MIN_HITS or len(buckets) < REASONING_CHAIN_MIN_BUCKETS:
        return []
    if link_hits < REASONING_CHAIN_MIN_LINKS:
        return []
    per_kilo = (hits / narrative_chars) * 1000
    if per_kilo < REASONING_CHAIN_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'reasoning-chain-tic',
        'severity': 'advisory',
        'message': f'解釋链密度過高：知道/明白/這意味着/必須/需要等論文式推導 {hits} 處（{per_kilo:.1f}/千字）；刪掉“這意味着/按照這個逻輯”式公文腔，保留角色自己的利害算帳與因果判斷，或落到對話與選择後果，別全改成手眼小動作。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_notice_formality_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect overly bureaucratic/officialese phrasing inside 【...】 system notice lines."""
    hits = 0
    notice_chars = 0
    notice_lines = 0
    core_hits = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not NOTICE_LINE_PATTERN.match(trimmed):
            continue
        notice_lines += 1
        notice_chars += visible_length(trimmed)

        core_hits += len(NOTICE_FORMAL_CORE_PATTERN.findall(trimmed))

        for pattern in NOTICE_FORMAL_PATTERNS:
            for match in pattern.finditer(trimmed):
                hits += 1
                if first_line is None:
                    first_line = line_no
                sample = compact(match.group(0))
                if len(samples) < 8 and sample not in samples:
                    samples.append(sample)

    if (
        notice_lines < NOTICE_FORMAL_MIN_LINES
        or notice_chars == 0
        or hits < NOTICE_FORMAL_MIN_HITS
        or core_hits < NOTICE_FORMAL_CORE_MIN_HITS
    ):
        return []
    per_kilo = (hits / notice_chars) * 1000
    if per_kilo < NOTICE_FORMAL_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'system-notice-formality-tic',
        'severity': 'advisory',
        'message': f'系統公告公文腔過密：方括號規則行中硬規則詞 {hits} 處（{per_kilo:.1f}/千字）；保留為角色看見的屏幕/公告/規則載體，只在載體內部白話化部分硬詞，或補角色當场看懂的具體後果，不改成敘述者解釋。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_overcompressed_prose_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect long texts dominated by ultra-short paragraphs with sparse natural particles."""
    narrative_chars = 0
    narrative_paras = 0
    short_paras = 0
    particles = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if (
            not trimmed
            or is_divider(trimmed)
            or is_structural(trimmed)
            or NOTICE_LINE_PATTERN.match(trimmed)
        ):
            continue
        narrative = strip_quoted(trimmed).strip()
        length = visible_length(narrative)
        if length == 0:
            continue

        if first_line is None:
            first_line = line_no
        narrative_paras += 1
        narrative_chars += length
        if length <= OVERCOMPRESSED_PROSE_SHORT_MAX_CHARS:
            short_paras += 1
            if len(samples) < 6:
                samples.append(narrative)

        particles += len(OVERCOMPRESSED_PROSE_PARTICLE_PATTERN.findall(narrative))

    if narrative_chars < OVERCOMPRESSED_PROSE_MIN_CHARS or narrative_paras < OVERCOMPRESSED_PROSE_MIN_PARAS:
        return []
    short_ratio = short_paras / narrative_paras
    if short_ratio < OVERCOMPRESSED_PROSE_SHORT_RATIO:
        return []
    particle_per_kilo = (particles / narrative_chars) * 1000
    if particle_per_kilo >= OVERCOMPRESSED_PROSE_PARTICLE_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'overcompressed-prose-tic',
        'severity': 'advisory',
        'message': f'過度精炼短段：敘述段 {narrative_paras} 個，其中 {short_paras} 個≤{OVERCOMPRESSED_PROSE_SHORT_MAX_CHARS}字（{short_ratio * 100:.0f}%），自然連接 {particle_per_kilo:.1f}/千字偏少；先通讀判斷，確有提綱感再補斷裂處和必要結構虛詞，有意短鏡頭可留，別機械注水。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_low_connective_density_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect telegraphic/outline-like prose with low connective density and few long sentences."""
    body_chars = 0
    function_hits = 0
    plain_hits = 0
    first_line: int | None = None
    sentences: list[int] = []
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue

        narrative = strip_quoted(trimmed).strip()
        narrative_len = visible_length(narrative)
        if narrative_len == 0:
            continue

        if first_line is None:
            first_line = line_no
        body_chars += narrative_len
        function_hits += count_terms(narrative, LOW_CONNECTIVE_FUNCTION_TERMS)
        plain_hits += count_terms(narrative, LOW_CONNECTIVE_PLAIN_TERMS)

        for sentence in split_sentences(narrative):
            length = visible_length(sentence)
            if length == 0:
                continue
            sentences.append(length)
            if length <= 12 and len(samples) < 6:
                samples.append(sentence)

    if body_chars < LOW_CONNECTIVE_MIN_CHARS or not sentences:
        return []
    function_per_kilo = (function_hits / body_chars) * 1000
    if function_per_kilo >= LOW_CONNECTIVE_FUNCTION_PER_KILO:
        return []
    plain_per_kilo = (plain_hits / body_chars) * 1000
    if plain_per_kilo >= LOW_CONNECTIVE_PLAIN_PER_KILO:
        return []
    long_sentence_ratio = sum(1 for length in sentences if length >= LOW_CONNECTIVE_LONG_SENTENCE_CHARS) / len(sentences)
    if long_sentence_ratio >= LOW_CONNECTIVE_LONG_SENTENCE_RATIO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'low-connective-density-tic',
        'severity': 'advisory',
        'message': f'低連接密度：引號外敘述功能詞 {function_per_kilo:.1f}/千字、白話連接 {plain_per_kilo:.1f}/千字，且≥{LOW_CONNECTIVE_LONG_SENTENCE_CHARS}字承接句僅 {long_sentence_ratio * 100:.0f}%；容易像提綱/電报體。通讀後補必要連接和中長句群，別機械注水。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_abstract_summary_tic(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect clusters of abstract authorial summary phrases in narrative prose."""
    hits = 0
    narrative_chars = 0
    first_line: int | None = None
    samples: list[str] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue
        narrative = strip_quoted(trimmed)
        narrative_chars += visible_length(narrative)

        for pattern in ABSTRACT_SUMMARY_PATTERNS:
            for match in pattern.finditer(narrative):
                hits += 1
                if first_line is None:
                    first_line = line_no
                sample = compact(match.group(0))
                if len(samples) < 6 and sample not in samples:
                    samples.append(sample)

    if narrative_chars == 0 or hits < ABSTRACT_SUMMARY_MIN_HITS:
        return []
    per_kilo = (hits / narrative_chars) * 1000
    if per_kilo < ABSTRACT_SUMMARY_PER_KILO:
        return []

    return [{
        'line': first_line,
        'column': 1,
        'type': 'abstract-summary-tic',
        'severity': 'advisory',
        'message': f'抽象總結複讀：命運/棋局/這一刻終於明白/才刚刚開始等作者總結 {hits} 處（{per_kilo:.1f}/千字）；刪掉作者盖章，回到角色當下的具體處境、利害盘算、對話或實際後果，別拿微動作頂替。',
        'excerpt': compact(' | '.join(samples)),
    }]


def find_period_stutter(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Detect runs of >= STUTTER_MIN_RUN consecutive short narrative sentences."""
    findings: list[dict[str, Any]] = []
    run_len = 0
    run_start_line: int | None = None
    run_sample: list[str] = []

    def flush() -> None:
        nonlocal run_len, run_start_line, run_sample
        if run_len >= STUTTER_MIN_RUN:
            findings.append({
                'line': run_start_line,
                'column': 1,
                'type': 'period-stutter',
                'severity': 'advisory',
                'message': f'碎句號：連續 {run_len} 個短句無呼吸；按目標句長把碎句合並成中長句、補回畫面與連接（見本 skill 句長/疏密節奏規則）。',
                'excerpt': compact(' '.join(run_sample)),
            })
        run_len = 0
        run_start_line = None
        run_sample = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed:
            continue
        if is_divider(trimmed) or is_structural(trimmed):
            flush()
            continue
        narrative = strip_quoted(trimmed)
        if visible_length(narrative) == 0:
            flush()
            continue
        for sentence in split_sentences(narrative):
            if visible_length(sentence) <= STUTTER_MAX_SENTENCE:
                if run_len == 0:
                    run_start_line = line_no
                run_len += 1
                if len(run_sample) < 6:
                    run_sample.append(sentence)
            else:
                flush()

    flush()
    return findings


_ZHTW_SUPP = json.loads(_DESLOP_RULES_PATH.read_text(encoding="utf-8")).get("zhtw_narrative_supplement", {})


def find_zhtw_supplement(prose_lines: list[tuple[str, int]], existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run Traditional Chinese narrative supplement rules from deslop_rules.json."""
    seen = {(f["line"], f["excerpt"]) for f in existing}
    findings: list[dict[str, Any]] = []
    for section in ("patterns", "buzz"):
        for rule in _ZHTW_SUPP.get(section, []):
            if rule["regex"] == "—{1,2}|――":
                continue
            compiled = re.compile(rule["regex"])
            is_blocking = section == "patterns" and float(rule.get("budget", 1.0)) == 0.0
            for text, line_no in prose_lines:
                trimmed = text.strip()
                if not trimmed or is_divider(trimmed) or is_structural(trimmed):
                    continue
                for m in compiled.finditer(mask_quoted_with_unclosed(text)):
                    excerpt = compact(text[max(0, m.start() - 4):m.end() + 4])
                    if (line_no, excerpt) in seen:
                        continue
                    seen.add((line_no, excerpt))
                    findings.append({
                        "line": line_no,
                        "column": m.start() + 1,
                        "type": "zhtw-pattern" if section == "patterns" else "zhtw-buzz",
                        "severity": "blocking" if is_blocking else "advisory",
                        "review": "mechanical" if is_blocking else "semantic",
                        "message": f"[{rule['label']}] {rule['advice']}",
                        "excerpt": excerpt,
                    })
    return findings


def scan_prose_patterns(prose_lines: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Run line-level and whole-document prose pattern scanners."""
    findings: list[dict[str, Any]] = []

    for text, line_no in prose_lines:
        trimmed = text.strip()
        if not trimmed or is_divider(trimmed) or is_structural(trimmed):
            continue

        dash_scan_text = mask_quoted_with_unclosed(text)
        for dash in DASH_PATTERN.finditer(dash_scan_text):
            findings.append({
                'line': line_no,
                'column': dash.start() + 1,
                'type': 'em-dash',
                'severity': 'blocking',
                'message': '敘述旁白不用破折號，按功能改寫：打斷→動作或抢白，停頓→逗號或省略，插入說明→逗號/冒號；勿一律改句號。',
                'excerpt': compact(text[max(0, dash.start() - 8):dash.end() + 8]),
            })

        if len(trimmed) > LONG_PARAGRAPH_CHARS:
            findings.append({
                'line': line_no,
                'column': 1,
                'type': 'long-paragraph',
                'severity': 'advisory',
                'message': f'段落過長（{len(trimmed)} 字）：按鏡頭/新動作/新線索/視線切換斷段，別一段到底。',
                'excerpt': compact(trimmed[:40]),
            })

    findings.extend(find_voice_contrast(prose_lines))
    findings.extend(find_negation_parade(prose_lines))
    findings.extend(find_formulaic_parallelism(prose_lines))
    findings.extend(find_reverse_not_is(prose_lines))
    findings.extend(find_trailer_ending(prose_lines))
    findings.extend(find_quote_emphasis_tic(prose_lines))
    findings.extend(find_period_stutter(prose_lines))
    findings.extend(find_micro_action_tic(prose_lines))
    findings.extend(find_negation_pair_tic(prose_lines))
    findings.extend(find_stock_reaction_tic(prose_lines))
    findings.extend(find_action_list_tic(prose_lines))
    findings.extend(find_abstract_summary_tic(prose_lines))
    findings.extend(find_cliche_density_tic(prose_lines))
    findings.extend(find_metaphor_density_tic(prose_lines))
    findings.extend(find_reasoning_chain_tic(prose_lines))
    findings.extend(find_notice_formality_tic(prose_lines))
    findings.extend(find_overcompressed_prose_tic(prose_lines))
    findings.extend(find_low_connective_density_tic(prose_lines))
    findings.extend(find_ellipsis_density_tic(prose_lines))
    findings.extend(find_zhtw_supplement(prose_lines, findings))
    return findings


def apply_density_severity_gates(findings: list[dict[str, Any]], prose_chars: int = 0) -> None:
    """Adjust severity and review class for rhetorical patterns based on chapter-scaled hit counts."""
    scale = max(1, (prose_chars + (DENSITY_SCALE_UNIT_CHARS // 2)) // DENSITY_SCALE_UNIT_CHARS)
    counts: dict[str, int] = {}
    for finding in findings:
        ftype = finding['type']
        counts[ftype] = counts.get(ftype, 0) + 1

    not_is_combined = counts.get('not-is-comparison', 0) + counts.get('reverse-not-is', 0)
    for finding in findings:
        ftype = finding['type']
        block: bool | None = None
        if ftype in ('not-is-comparison', 'reverse-not-is'):
            block = not_is_combined >= NOT_IS_BLOCKING_MIN_HITS * scale
        elif ftype == 'voice-contrast':
            block = counts.get('voice-contrast', 0) >= VOICE_CONTRAST_BLOCKING_MIN_HITS * scale
        elif ftype == 'negation-parade':
            block = counts.get('negation-parade', 0) >= NEGATION_PARADE_BLOCKING_MIN_HITS * scale
        elif ftype == 'trailer-ending':
            block = counts.get('trailer-ending', 0) >= TRAILER_ENDING_BLOCKING_MIN_HITS

        if block is True:
            finding['severity'] = 'blocking'
            finding['review'] = 'mechanical'
        elif block is False:
            finding['severity'] = 'advisory'
            finding['review'] = 'semantic'


def scan_document(input_text: str) -> list[dict[str, Any]]:
    """Scan an entire document string and return sorted findings."""
    lines = re.split(r'\r?\n', input_text)
    unclosed_openings: set[str] = set()

    while True:
        findings: list[dict[str, Any]] = []
        fence: tuple[str, int] | None = None
        in_front_matter = has_yaml_front_matter(lines)
        comment_open = False
        comment_start: str | None = None
        block: list[tuple[str, int]] = []
        prose_lines: list[tuple[str, int]] = []

        def flush_block() -> None:
            if not block:
                return
            findings.extend(scan_block(block))
            block.clear()

        for index, line in enumerate(lines):
            trimmed = line.strip()

            if in_front_matter:
                if index > 0 and trimmed == '---':
                    in_front_matter = False
                continue

            fence_marker = parse_fence_marker(trimmed)
            if fence is not None:
                if fence_marker is not None and fence_marker[0] == fence[0] and fence_marker[1] >= fence[1]:
                    fence = None
                continue

            if fence_marker is not None and not comment_open:
                flush_block()
                fence = fence_marker
                continue

            masked_text, comment_open, opened_at = mask_html_comments(
                line, comment_open, index, unclosed_openings
            )
            if opened_at is not None:
                comment_start = opened_at
            if masked_text != line and not masked_text.strip():
                continue

            block.append((masked_text, index + 1))
            prose_lines.append((masked_text, index + 1))

        if comment_open and comment_start is not None:
            unclosed_openings.add(comment_start)
            continue

        flush_block()
        findings.extend(scan_prose_patterns(prose_lines))
        prose_chars = 0
        for text, _ in prose_lines:
            trimmed = text.strip()
            if not trimmed or is_divider(trimmed) or is_structural(trimmed):
                continue
            prose_chars += len(re.sub(r'\s+', '', trimmed))

        apply_density_severity_gates(findings, prose_chars)
        findings.sort(key=lambda item: (item['line'], item['column']))
        return findings


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for check_ai_patterns.py."""
    args = sys.argv[1:] if argv is None else argv
    json_output = False
    files: list[str] = []
    fail_on = 'all'

    for arg in args:
        if arg == '--check':
            continue
        if arg == '--list-review-classes':
            sys.stdout.write(f"{json.dumps(REVIEW_CLASSES, indent=2, ensure_ascii=False)}\n")
            return 0
        if arg == '--json':
            json_output = True
        elif arg.startswith('--fail-on='):
            val = arg[len('--fail-on='):]
            if val not in ('blocking', 'all'):
                die("--fail-on must be 'blocking' or 'all'")
            fail_on = val
        elif arg in ('-h', '--help'):
            sys.stdout.write(f"{USAGE}\n")
            return 0
        elif arg.startswith('-'):
            die(f"Unknown option: {arg}")
        else:
            files.append(arg)

    if not files:
        die('No files provided')

    failed = False
    all_findings: list[dict[str, Any]] = []

    for file_arg in files:
        full_path = os.path.abspath(file_arg)
        try:
            text = Path(full_path).read_text(encoding='utf-8')
        except OSError as exc:
            failed = True
            if not json_output:
                print(f"{file_arg}: unable to read ({exc})", file=sys.stderr)
            continue

        try:
            whitelist = load_style_whitelist(full_path)
        except OSError as exc:
            die(f"{file_arg}: unable to read .deslop-whitelist ({exc})")

        masked_input = mask_style_text(text, whitelist)
        for finding in scan_document(masked_input):
            base_review = review_class(finding['type'])
            all_findings.append({
                'file': file_arg,
                **finding,
                'review': finding.get('review') or base_review,
            })

    if json_output:
        sys.stdout.write(f"{json.dumps({'findings': all_findings}, indent=2, ensure_ascii=False)}\n")
    else:
        for finding in all_findings:
            print(
                f"{finding['file']}:{finding['line']}:{finding['column']}: "
                f"[{finding['severity']}] {finding['type']}: {finding['message']} ({finding['excerpt']})"
            )

    if failed:
        return 2

    has_blocking = any(f['severity'] == 'blocking' for f in all_findings)
    if (has_blocking if fail_on == 'blocking' else len(all_findings) > 0):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
