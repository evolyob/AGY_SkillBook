#!/usr/bin/env python3
"""Faithful Python 3 port of normalize-punctuation.js.

Normalizes Chinese prose punctuation deterministically:
- Preserves standard ellipses (……) and unifies non-standard ellipses.
- Preserves em dashes (——) inside dialogue quotes and unifies variants.
- Replaces unquoted em dashes and double hyphens in narration with Chinese punctuation.
- Removes markdown divider lines (---) outside front matter, fences, and HTML comments.
- Respects book-local .deslop-whitelist literals.
- Optionally converts quote styles (keep|curly|ascii|yan).
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any

USAGE = """Usage: python3 normalize_punctuation.py [--check] [--quote-mode keep|curly|ascii|yan] <file...>

Normalize正文 punctuation deterministically:
  - keep standard ellipses (……) in dialogue, 【…】 panels, and narration; unify non-standard ellipses (..., single …, ………+, 。。。+, .……..) to ……
  - keep em dashes inside dialogue quotes (“”「」『』 and paired ASCII "), unified as ——
  - replace unquoted em dashes and double hyphens in narration with Chinese punctuation
  - remove markdown divider lines (---) from正文
  - preserve pause punctuation covered by book-local .deslop-whitelist literals
  - keep quote style by default; convert quotes only when explicitly requested (curly|ascii|yan)
"""

DASH_UNIT = r'(?:—+[-—]*|-+—+[-—]*|--+)'
ELLIPSIS_UNIT = r'(?:\.+…+[.…]*|…+\.+[.…]*|…+|\.{3,}|。{3,})'
PAUSE_PATTERN = re.compile(
    f'{DASH_UNIT}{ELLIPSIS_UNIT}|{ELLIPSIS_UNIT}{DASH_UNIT}|{ELLIPSIS_UNIT}|{DASH_UNIT}'
)
HAS_ELLIPSIS_RE = re.compile(r'[…。]|\.{3,}')
HAS_DASH_RE = re.compile(r'[—-]')
OPENING_FENCE_RE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
YAML_FIELD_RE = re.compile(r'^[A-Za-z0-9_-]+:\s*')
COLON_AFTER_RE = re.compile(
    r'^(因為|原來|這是|那是|也就是|換句話|說白了|所謂|答案|原因|結果|真相|問題在於)'
)
COLON_BEFORE_RE = re.compile(r'(原因|答案|真相|結果|結論|問題|選擇|意思)$')
SENTENCE_PUNCT_RE = re.compile(r'[，,。.!！?？;；:：…]$')
PUNCT_RE = re.compile(r'[，,。.!！?？;；:：、…"“”\'‘’」』）)]')
CLOSING_QUOTE_RE = re.compile(r'["”」』]')
OPENING_DELIM_RE = re.compile(r'[「『（(“‘]')
ASCII_WORD_RE = re.compile(r'^[A-Za-z0-9_]$')
ASCII_QUOTE_TARGET_RE = re.compile(r'[「」『』“”]')


def die(message: str) -> None:
    """Print an error message and usage text to stderr, then exit with code 2."""
    sys.stderr.write(f'{message}\n')
    sys.stderr.write(f'{USAGE.rstrip()}\n')
    sys.exit(2)


def load_style_whitelist(file_path: str) -> list[str]:
    """Load book-local .deslop-whitelist literals sorted longest-first."""
    parent = os.path.dirname(os.path.abspath(file_path))
    book = os.path.dirname(parent) if os.path.basename(parent) == '正文' else parent
    whitelist_path = os.path.join(book, '.deslop-whitelist')
    try:
        with open(whitelist_path, 'r', encoding='utf-8', newline='') as fh:
            raw = fh.read()
    except FileNotFoundError:
        return []
    lines = [line.strip() for line in re.split(r'\r?\n', raw)]
    filtered = [line for line in lines if line and not line.startswith('#')]
    filtered.sort(key=len, reverse=True)
    return filtered


def style_spans(text: str, whitelist: list[str]) -> list[tuple[int, int]]:
    """Return character spans in text matching any literal in whitelist."""
    spans: list[tuple[int, int]] = []
    for literal in whitelist:
        at = text.find(literal)
        while at != -1:
            spans.append((at, at + len(literal)))
            at = text.find(literal, at + 1)
    return spans


def split_lines_keeping_endings(text: str) -> tuple[list[str], list[str]]:
    """Split text into parallel lists of line bodies and original line endings."""
    lines: list[str] = []
    endings: list[str] = []
    cursor = 0
    length = len(text)
    while cursor < length:
        nl = text.find('\n', cursor)
        if nl == -1:
            lines.append(text[cursor:])
            endings.append('')
            break
        crlf = nl > cursor and text[nl - 1] == '\r'
        lines.append(text[cursor : nl - 1 if crlf else nl])
        endings.append('\r\n' if crlf else '\n')
        cursor = nl + 1
    return lines, endings


def has_yaml_front_matter(lines: list[str]) -> bool:
    """Return True if lines begin with a valid YAML front-matter block."""
    if not lines or lines[0].strip() != '---':
        return False
    saw_yaml_field = False
    for line in lines[1 : min(len(lines), 40)]:
        trimmed = line.strip()
        if trimmed == '---':
            return saw_yaml_field
        if YAML_FIELD_RE.match(trimmed):
            saw_yaml_field = True
    return False


def parse_opening_fence(line: str) -> dict[str, Any] | None:
    """Parse a markdown code fence opening line, or return None."""
    match = OPENING_FENCE_RE.match(line)
    if not match:
        return None
    marker, rest = match.group(1), match.group(2)
    if marker[0] == '`' and '`' in rest:
        return None
    return {'marker': marker[0], 'minimum_length': len(marker)}


def is_closing_fence(line: str, fence: dict[str, Any]) -> bool:
    """Return True if line closes the active markdown code fence."""
    marker = '`' if fence['marker'] == '`' else '~'
    pattern = re.compile(rf'^ {{0,3}}({re.escape(marker)}{{3,}})[\t ]*$')
    match = pattern.match(line)
    return bool(match and len(match.group(1)) >= fence['minimum_length'])


def html_comment_spans(line: str, open_before: bool) -> tuple[list[tuple[int, int]], bool]:
    """Find inline HTML comment spans and return whether a comment remains open."""
    spans: list[tuple[int, int]] = []
    is_open = open_before
    cursor = 0
    while cursor < len(line):
        if is_open:
            close = line.find('-->', cursor)
            if close == -1:
                spans.append((cursor, len(line)))
                return spans, True
            spans.append((cursor, close + 3))
            cursor = close + 3
            is_open = False
            continue
        start = line.find('<!--', cursor)
        if start == -1:
            break
        cursor = start
        is_open = True
    return spans, is_open


def quote_spans(line: str) -> list[tuple[int, int]]:
    """Return spans inside dialogue quotes on a single line (excluding delimiters)."""
    spans: list[tuple[int, int]] = []
    stack: list[tuple[str, int]] = []
    for i, ch in enumerate(line):
        if ch == '"' and stack and stack[-1][0] == '"':
            _, at = stack.pop()
            if not stack:
                spans.append((at + 1, i))
        elif ch in ('"', '“', '「', '『'):
            stack.append((ch, i))
        elif ch in ('”', '」', '』') and stack:
            _, at = stack.pop()
            if not stack:
                spans.append((at + 1, i))
    if stack:
        spans.append((stack[0][1] + 1, len(line)))
    return spans


def inside_spans(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    """Return True if [start, end) overlaps any span in spans."""
    return any(start < s_end and end > s_start for s_start, s_end in spans)


def get_pause_type(token: str) -> str:
    """Classify a pause punctuation token into double-hyphen, em-dash, or ellipsis."""
    if token.startswith('-'):
        return 'double-hyphen'
    if '—' in token:
        return 'em-dash'
    return 'ellipsis'


def previous_non_space(text: str, index: int) -> str:
    """Return the nearest non-whitespace character at or before index, or ''."""
    for i in range(index, -1, -1):
        if not text[i].isspace():
            return text[i]
    return ''


def next_non_space(text: str, index: int) -> str:
    """Return the nearest non-whitespace character at or after index, or ''."""
    for i in range(index, len(text)):
        if not text[i].isspace():
            return text[i]
    return ''


def is_sentence_punctuation(ch: str) -> bool:
    """Return True if ch is sentence-level punctuation."""
    return bool(SENTENCE_PUNCT_RE.search(ch or ''))


def is_punctuation(ch: str) -> bool:
    """Return True if ch is any Chinese or ASCII punctuation character."""
    return bool(PUNCT_RE.search(ch or ''))


def is_closing_quote(ch: str) -> bool:
    """Return True if ch is a closing dialogue quote."""
    return bool(CLOSING_QUOTE_RE.search(ch or ''))


def is_opening_delimiter(ch: str) -> bool:
    """Return True if ch is an opening quote or parenthesis."""
    return bool(OPENING_DELIM_RE.search(ch or ''))


def choose_pause_replacement(text: str, start: int, length: int) -> str:
    """Choose the Chinese punctuation replacement for an unquoted pause token."""
    before = previous_non_space(text, start - 1)
    after = next_non_space(text, start + length)
    rest = text[start + length :].lstrip()

    if before == '':
        return ''
    if is_opening_delimiter(before):
        return ''
    if before.isdigit() and after.isdigit() and before.isascii() and after.isascii():
        return '到'
    if is_closing_quote(after):
        return '' if is_sentence_punctuation(before) else '。'
    if not after:
        return '' if is_sentence_punctuation(before) else '。'
    if is_sentence_punctuation(before) or is_punctuation(after):
        return ''
    if COLON_AFTER_RE.match(rest):
        return '：'
    if COLON_BEFORE_RE.search(text[:start].strip()):
        return '：'
    return '，'


def _replace_pause_match(
    original: str,
    match: re.Match[str],
    line_no: int,
    last_index: int,
    output: str,
    quotes: list[tuple[int, int]],
) -> tuple[str, int, dict[str, Any] | None]:
    """Process a single pause-punctuation regex match and return updated state."""
    start, end = match.start(), match.end()
    token = match.group(0)
    in_quote = inside_spans(start, end, quotes)
    has_ellipsis = bool(HAS_ELLIPSIS_RE.search(token))
    has_dash = bool(HAS_DASH_RE.search(token))

    if has_ellipsis and has_dash:
        merged = last_index == start and output.endswith('……')
        rep = '' if merged else '……'
        finding = {
            'line': line_no,
            'column': start + 1,
            'type': 'double-hyphen' if token.startswith('-') else 'em-dash',
            'message': '粘連的破折號與省略號統一為「……」。',
        }
        return output + original[last_index:start] + rep, end, finding

    if has_ellipsis:
        merged = last_index == start and output.endswith('……')
        rep = '' if merged else '……'
        finding = None
        if rep != token:
            finding = {
                'line': line_no,
                'column': start + 1,
                'type': 'ellipsis',
                'message': '省略號統一為「……」。',
            }
        return output + original[last_index:start] + rep, end, finding

    if in_quote and has_dash:
        merged = last_index == start and output.endswith('——')
        rep = '' if merged else '——'
        finding = None
        if rep != token:
            finding = {
                'line': line_no,
                'column': start + 1,
                'type': get_pause_type(token),
                'message': '引號內的破折號統一為「——」。',
            }
        return output + original[last_index:start] + rep, end, finding

    rep = choose_pause_replacement(original, start, len(token))
    msg = f'替換為「{rep}」。' if rep else '移除重複標點。'
    finding = {
        'line': line_no,
        'column': start + 1,
        'type': get_pause_type(token),
        'message': msg,
    }
    return output + original[last_index:start] + rep, end, finding


def normalize_pause_punctuation_pass(
    line: str, line_no: int, protected_spans: list[tuple[int, int]]
) -> tuple[str, list[dict[str, Any]]]:
    """Run one pass of pause punctuation normalization over a single line."""
    findings: list[dict[str, Any]] = []
    quotes = quote_spans(line)
    output = ''
    last_index = 0

    for match in PAUSE_PATTERN.finditer(line):
        if inside_spans(match.start(), match.end(), protected_spans):
            continue
        output, last_index, finding = _replace_pause_match(
            line, match, line_no, last_index, output, quotes
        )
        if finding is not None:
            findings.append(finding)

    output += line[last_index:]
    return output, findings


def normalize_pause_punctuation(
    line: str, line_no: int, comment_open: bool, whitelist: list[str]
) -> tuple[str, list[dict[str, Any]], bool]:
    """Normalize pause punctuation to a fixed point, keeping first-pass findings."""
    current = line
    findings: list[dict[str, Any]] | None = None
    comment_open_after = comment_open

    while True:
        c_spans, comment_open_after = html_comment_spans(current, comment_open)
        protected = c_spans + style_spans(current, whitelist)
        next_line, pass_findings = normalize_pause_punctuation_pass(
            current, line_no, protected
        )
        if findings is None:
            findings = pass_findings
        if next_line == current:
            break
        current = next_line

    return current, findings or [], comment_open_after


def _is_ascii_word(ch: str) -> bool:
    """Return True if ch is an ASCII word character."""
    return bool(ch and ASCII_WORD_RE.match(ch))


def _normalize_curly_char(
    ch: str, prev_ch: str, next_ch: str, stack: list[str]
) -> str:
    """Convert a single character in curly quote mode, updating stack in place."""
    if ch in ('“', '「', '『'):
        level = 'outer' if not stack else 'inner'
        stack.append(level)
        return '“' if level == 'outer' else '‘'
    if ch == '‘':
        stack.append('inner')
        return '‘'
    if ch in ('”', '」', '』'):
        level = stack.pop() if stack else 'outer'
        return '’' if level == 'inner' else '”'
    if ch == '’':
        if (not _is_ascii_word(prev_ch) or not _is_ascii_word(next_ch)) and stack and stack[-1] == 'inner':
            stack.pop()
        return '’'
    if ch == '"':
        if stack and stack[-1] == 'outer':
            stack.pop()
            return '”'
        stack.append('outer')
        return '“'
    if ch == "'" and not (_is_ascii_word(prev_ch) and _is_ascii_word(next_ch)):
        if stack and stack[-1] == 'inner':
            stack.pop()
            return '’'
        stack.append('inner')
        return '‘'
    return ch


def _normalize_quotes_curly(
    line: str, line_no: int
) -> tuple[str, list[dict[str, Any]], bool]:
    """Convert quotes on a line to Chinese curly quotes while preserving apostrophes."""
    findings: list[dict[str, Any]] = []
    stack: list[str] = []
    out_chars: list[str] = []
    length = len(line)

    for i, ch in enumerate(line):
        prev_ch = line[i - 1] if i > 0 else ''
        next_ch = line[i + 1] if i + 1 < length else ''
        rep = _normalize_curly_char(ch, prev_ch, next_ch, stack)
        out_chars.append(rep)
        if rep != ch:
            findings.append(
                {
                    'line': line_no,
                    'column': i + 1,
                    'type': 'quote-style',
                    'message': '按顯式 quote-mode 轉為中文彎引號。',
                }
            )

    return ''.join(out_chars), findings, len(stack) > 0


def normalize_quotes(
    line: str, quote_mode: str, quote_open: bool, line_no: int
) -> tuple[str, list[dict[str, Any]], bool]:
    """Normalize quotes on a single line according to quote_mode."""
    if quote_mode == 'keep':
        return line, [], quote_open
    if quote_mode == 'curly':
        return _normalize_quotes_curly(line, line_no)

    findings: list[dict[str, Any]] = []
    out_chars: list[str] = []
    for i, ch in enumerate(line):
        if quote_mode == 'ascii' and ASCII_QUOTE_TARGET_RE.match(ch):
            out_chars.append('"')
            findings.append(
                {
                    'line': line_no,
                    'column': i + 1,
                    'type': 'quote-style',
                    'message': '按顯式 quote-mode 轉為半角雙引號。',
                }
            )
            continue
        if quote_mode == 'yan' and ch in ('"', '“', '”'):
            rep = '」' if (quote_open or ch == '”') else '「'
            out_chars.append(rep)
            quote_open = rep == '「'
            findings.append(
                {
                    'line': line_no,
                    'column': i + 1,
                    'type': 'quote-style',
                    'message': '按顯式 quote-mode 轉為鹽言引號。',
                }
            )
            continue
        out_chars.append(ch)

    return ''.join(out_chars), findings, quote_open


def normalize_document(
    input_text: str, quote_mode: str, whitelist: list[str]
) -> dict[str, Any]:
    """Normalize an entire document and return output text and findings."""
    lines, endings = split_lines_keeping_endings(input_text)
    findings: list[dict[str, Any]] = []
    output_lines: list[str] = []
    fence: dict[str, Any] | None = None
    in_front_matter = has_yaml_front_matter(lines)
    quote_open = False
    comment_open = False
    comment_start: dict[str, int] | None = None

    comment_close_ahead = [False] * (len(lines) + 1)
    for idx in range(len(lines) - 1, -1, -1):
        comment_close_ahead[idx] = ('-->' in lines[idx]) or comment_close_ahead[idx + 1]

    for idx, (line, ending) in enumerate(zip(lines, endings)):
        line_no = idx + 1
        trimmed = line.strip()

        if comment_open and not comment_close_ahead[idx]:
            findings.append(
                {
                    'line': comment_start['line'] if comment_start else line_no,
                    'column': comment_start['column'] if comment_start else 1,
                    'type': 'html-comment-unclosed',
                    'message': 'HTML 注釋未閉合；後續內容仍按正文檢查。',
                }
            )
            comment_open = False
            comment_start = None

        if in_front_matter:
            output_lines.append(line + ending)
            if idx > 0 and trimmed == '---':
                in_front_matter = False
            continue

        if fence is not None:
            output_lines.append(line + ending)
            if is_closing_fence(line, fence):
                fence = None
            continue

        opening_fence = parse_opening_fence(line)
        if opening_fence is not None:
            fence = opening_fence
            output_lines.append(line + ending)
            continue

        if trimmed == '---' and not comment_open:
            findings.append(
                {
                    'line': line_no,
                    'column': line.index('-') + 1,
                    'type': 'markdown-divider',
                    'message': '正文中不要使用 markdown 分隔線；建議移除該行。',
                }
            )
            continue

        comment_open_before = comment_open
        line, punct_findings, comment_open = normalize_pause_punctuation(
            line, line_no, comment_open, whitelist
        )
        findings.extend(punct_findings)
        if not comment_open_before and comment_open:
            comment_start = {'line': line_no, 'column': max(1, line.rfind('<!--') + 1)}
        elif not comment_open:
            comment_start = None

        line, quote_findings, quote_open = normalize_quotes(
            line, quote_mode, quote_open, line_no
        )
        findings.extend(quote_findings)
        output_lines.append(line + ending)

    if comment_open:
        findings.append(
            {
                'line': comment_start['line'] if comment_start else len(lines),
                'column': comment_start['column'] if comment_start else 1,
                'type': 'html-comment-unclosed',
                'message': 'HTML 注釋未閉合；後續內容仍按正文檢查。',
            }
        )

    return {'output': ''.join(output_lines), 'findings': findings}


def parse_args(argv: list[str]) -> tuple[bool, str, list[str]]:
    """Parse CLI arguments and return (check, quote_mode, files)."""
    check = False
    quote_mode = 'keep'
    files: list[str] = []
    i = 0

    while i < len(argv):
        arg = argv[i]
        if arg == '--check':
            check = True
        elif arg == '--quote-mode':
            if i + 1 >= len(argv) or not argv[i + 1]:
                die('--quote-mode requires keep, curly, ascii, or yan')
            quote_mode = argv[i + 1]
            i += 1
        elif arg.startswith('--quote-mode='):
            quote_mode = arg[len('--quote-mode=') :]
        elif arg in ('-h', '--help'):
            sys.stdout.write(USAGE)
            sys.exit(0)
        elif arg.startswith('-'):
            die(f'Unknown option: {arg}')
        else:
            files.append(arg)
        i += 1

    if quote_mode not in ('keep', 'curly', 'ascii', 'yan'):
        die(f'Invalid --quote-mode: {quote_mode}')
    if not files:
        die('No files provided')

    return check, quote_mode, files


def process_file(
    file_path: str, check: bool, quote_mode: str
) -> tuple[int, bool, bool]:
    """Read, normalize, and check or write a single file."""
    full_path = os.path.abspath(file_path)
    try:
        with open(full_path, 'r', encoding='utf-8', newline='') as fh:
            input_text = fh.read()
    except OSError as exc:
        msg = exc.strerror or str(exc)
        sys.stderr.write(f'{file_path}: unable to read ({msg})\n')
        return 0, False, True

    try:
        whitelist = load_style_whitelist(full_path)
    except OSError as exc:
        msg = exc.strerror or str(exc)
        die(f'{file_path}: unable to read .deslop-whitelist ({msg})')

    result = normalize_document(input_text, quote_mode, whitelist)
    findings = result['findings']

    if check:
        for finding in findings:
            sys.stdout.write(
                f"{file_path}:{finding['line']}:{finding['column']}: "
                f"{finding['type']}: {finding['message']}\n"
            )
        return len(findings), False, False

    if result['output'] != input_text:
        with open(full_path, 'w', encoding='utf-8', newline='') as fh:
            fh.write(result['output'])
        suffix = '' if len(findings) == 1 else 's'
        sys.stdout.write(
            f'{file_path}: normalized ({len(findings)} issue{suffix})\n'
        )
        return len(findings), True, False

    return len(findings), False, False


def main() -> int:
    """CLI entry point for normalize_punctuation."""
    check, quote_mode, files = parse_args(sys.argv[1:])
    total_findings = 0
    changed_files = 0
    failed = False

    for file_path in files:
        count, changed, err = process_file(file_path, check, quote_mode)
        total_findings += count
        if changed:
            changed_files += 1
        if err:
            failed = True

    if failed:
        return 2
    if check and total_findings > 0:
        return 1
    if not check:
        sys.stdout.write(f'Done. Changed files: {changed_files}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
