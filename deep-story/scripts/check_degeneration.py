#!/usr/bin/env python3
"""Detect model-degeneration fingerprints in generated prose.

Faithful port of `check-degeneration.js` using Python 3 standard library only.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

USAGE = """Usage: python3 check_degeneration.py [--check] [--json] [--fail-on=blocking|all] <file...>

Detect model-degeneration fingerprints that a degrading model cannot self-report:
  - verbatim repetition (複讀/打轉): a long sentence repeated, or back-to-back identical lines
  - mid-sentence truncation (截斷): file ends without terminal/closing punctuation
  - placeholder / refusal / meta leakage (元信息泄漏): 作為AI / 我無法继續 / 此處省略 / 亂碼
  - engineering-word leakage (工程詞泄漏): 細綱 / 情節點 / 本章 / 下一章 / 任务描述 漏進正文

Each finding carries severity: blocking (複讀/截斷/占位拒絕語/tier1 純工程詞，正文里永不合法，
命中即重寫) 或 advisory (tier2 章節/歧義詞、對話行里的工程詞，只提示、交人/LLM 判)。
--fail-on=blocking 只在出現 blocking finding 時退出 1；默認 --fail-on=all 有任何 finding 即退出 1。

Report-only. The script never rewrites — the safe response is to regenerate the
affected unit (chapter / 摘要) with the finding fed back as a constraint, cap retries,
then surface the evidence to the user. Conservative by design: 通俗網文 deliberately
uses 排比/複沓/弹幕刷屏/重複台詞 for rhythm, so short and dialogue repetition is exempt."""

_DESLOP_RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "deslop_rules.json"
_DEGEN_CFG = json.loads(_DESLOP_RULES_PATH.read_text(encoding="utf-8"))["degeneration_rules"]

REPEAT_MIN_LEN = int(_DEGEN_CFG["repeat_min_len"])
REPEAT_MIN_COUNT = int(_DEGEN_CFG["repeat_min_count"])
ADJACENT_MIN_LEN = int(_DEGEN_CFG["adjacent_min_len"])


@dataclass(frozen=True)
class PlaceholderPattern:
    """Compiled pattern for placeholder, refusal, or meta leakage."""

    re: re.Pattern[str]
    label: str
    hard: bool


@dataclass(frozen=True)
class ContentLine:
    """Body line outside YAML front-matter and fenced code blocks."""

    text: str
    trimmed: str
    line_no: int


PLACEHOLDER_PATTERNS: tuple[PlaceholderPattern, ...] = tuple(
    PlaceholderPattern(re=re.compile(item["regex"]), label=item["label"], hard=bool(item["hard"]))
    for item in _DEGEN_CFG["placeholder_patterns"]
)

QUOTED_SPAN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"「[^」]*」"),
    re.compile(r"『[^』]*』"),
    re.compile(r"【[^】]*】"),
    re.compile(r"“[^”]*”"),
    re.compile(
        r"(?<![A-Za-z0-9_])‘(?:[^’]|(?<=[A-Za-z0-9_])’(?=[A-Za-z0-9_]))*"
        r"(?!(?<=[A-Za-z0-9_])’[A-Za-z0-9_])’"
    ),
    re.compile(r'"[^"]*"'),
    re.compile(
        r"(?<![A-Za-z0-9_])'(?:[^']|(?<=[A-Za-z0-9_])'(?=[A-Za-z0-9_]))*"
        r"(?!(?<=[A-Za-z0-9_])'[A-Za-z0-9_])'"
    ),
)

META_TIER1_RE = re.compile(
    r"細綱|(?<!剧)情節點|卷綱|功能標签|目標情绪|字數目標|字數口徑|"
    r"章首钩子|章尾钩子|這章不能說破|本章禁止提前釋放|排綱筆記|排綱底稿|"
    r"節尾停在哪|結尾承接"
)
META_TIER2_RE = re.compile(
    r"第[一二三四五六七八九十百千万两0-9]+章|本章|這一章|上一章|下一章|"
    r"上章|下章|前一章|後一章|前文|後文|伏筆|讀者|任务描述"
)
CHAPTER_HEADING_RE = re.compile(
    r"^第[零〇一二三四五六七八九十百千万两0-9]+[章節回]"
    r"(?:$|[\s_：:——\-]+[^\n。；;]{0,28}$)"
)
END_SIGNOFF_RE = re.compile(
    r"^[-—~～＜<【\[（(《\s]*(?:全文完|正文完|全書完|本卷完|完結|完|END|The\s+End)"
    r"[-—~～＞>】\]）)》.。！!\s]*$",
    re.IGNORECASE,
)
YAML_FIELD_RE = re.compile(r"^[A-Za-z0-9_-]+:\s*")
FENCE_MARKER_RE = re.compile(r"^(?:`{3,}|~{3,})")
VISIBLE_CHAR_RE = re.compile(r"[一-鿿Ａ-ｚA-Za-z0-9]")
TERMINAL_PUNCT_RE = re.compile(r'(?:[。！？!?…~”"』」）)】]|\.{3,})$')


def die(message: str) -> None:
    """Print an error and usage message to stderr and exit with code 2."""
    print(message, file=sys.stderr)
    print(USAGE.rstrip(), file=sys.stderr)
    sys.exit(2)


def is_content(trimmed: str) -> bool:
    """Return True if `trimmed` is non-empty body prose (not heading or rule)."""
    return bool(
        trimmed
        and not trimmed.startswith("#")
        and not re.fullmatch(r"-{3,}", trimmed)
    )


def mask_quoted_spans(text: str) -> str:
    """Mask paired quoted spans with spaces of equal length to preserve columns."""
    masked = text
    for pattern in QUOTED_SPAN_PATTERNS:
        masked = pattern.sub(lambda m: " " * len(m.group(0)), masked)
    return masked


def strip_quoted(text: str) -> str:
    """Remove paired quoted spans, leaving only narration outside quotes."""
    stripped = text
    for pattern in QUOTED_SPAN_PATTERNS:
        stripped = pattern.sub("", stripped)
    return stripped


def visible_length(text: str) -> int:
    """Count visible CJK, full-width Latin, ASCII alphanumeric characters."""
    return len(VISIBLE_CHAR_RE.findall(text))


def compact(text: str) -> str:
    """Collapse whitespace and truncate excerpts to at most 80 characters."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) > 80:
        return f"{normalized[:77]}..."
    return normalized


def has_yaml_front_matter(lines: list[str]) -> bool:
    """Return True if `lines` starts with a valid YAML front-matter block."""
    if not lines or lines[0].strip() != "---":
        return False
    saw_yaml_field = False
    for i in range(1, min(len(lines), 40)):
        trimmed = lines[i].strip()
        if trimmed == "---":
            return saw_yaml_field
        if YAML_FIELD_RE.match(trimmed):
            saw_yaml_field = True
    return False


def _extract_body_sentences(body: list[ContentLine]) -> list[tuple[int, str]]:
    """Extract `(line_no, sentence)` pairs from narration outside quotes."""
    sentences: list[tuple[int, str]] = []
    for item in body:
        for part in re.split(r"[。！？!?]", strip_quoted(item.trimmed)):
            s = part.strip()
            if visible_length(s) >= REPEAT_MIN_LEN:
                sentences.append((item.line_no, s))
    return sentences


def find_repetition(content: list[ContentLine]) -> list[dict[str, Any]]:
    """Detect back-to-back line loops and repeated long narration sentences."""
    findings: list[dict[str, Any]] = []
    body = [c for c in content if is_content(c.trimmed)]

    for i in range(1, len(body)):
        if (
            body[i].trimmed == body[i - 1].trimmed
            and visible_length(strip_quoted(body[i].trimmed)) >= ADJACENT_MIN_LEN
        ):
            findings.append(
                {
                    "line": body[i].line_no,
                    "column": 1,
                    "type": "verbatim-repeat",
                    "severity": "blocking",
                    "message": "逐行複讀（紧鄰整行重複）：疑似模型打轉，重寫本段、刪掉重複。",
                    "excerpt": compact(body[i].trimmed),
                }
            )

    sentences = _extract_body_sentences(body)
    counts: dict[str, int] = {}
    for _, s in sentences:
        counts[s] = counts.get(s, 0) + 1

    flagged = {s for s, count in counts.items() if count >= REPEAT_MIN_COUNT}
    if not flagged:
        return findings

    for line_no, s in sentences:
        if s not in flagged:
            continue
        findings.append(
            {
                "line": line_no,
                "column": 1,
                "type": "verbatim-repeat",
                "severity": "blocking",
                "message": f"長句複讀（同句出現 {counts[s]} 次）：疑似模型打轉，重寫、保留一處。",
                "excerpt": compact(s),
            }
        )
        flagged.remove(s)

    return findings


def find_truncation(content: list[ContentLine]) -> list[dict[str, Any]]:
    """Detect mid-sentence truncation at the end of body content."""
    body = [
        c
        for c in content
        if is_content(c.trimmed) and not END_SIGNOFF_RE.match(c.trimmed)
    ]
    if not body:
        return []
    last = body[-1]
    if TERMINAL_PUNCT_RE.search(last.trimmed):
        return []
    return [
        {
            "line": last.line_no,
            "column": len(last.trimmed),
            "type": "truncated",
            "severity": "blocking",
            "message": "疑似截斷：正文末尾未以句末/收尾標點結束，可能被模型中途切斷；補完結尾或重寫收尾。",
            "excerpt": compact(last.trimmed[-24:]),
        }
    ]


def _match_placeholder_line(trimmed: str, line_no: int) -> dict[str, Any] | None:
    """Return the first placeholder/refusal finding on `trimmed`, or None."""
    outside_quotes = mask_quoted_spans(trimmed)
    for pattern in PLACEHOLDER_PATTERNS:
        target = trimmed if pattern.hard else outside_quotes
        match = pattern.re.search(target)
        if not match:
            continue
        index = match.start()
        return {
            "line": line_no,
            "column": index + 1,
            "type": "placeholder-leak",
            "severity": "blocking",
            "message": f"{pattern.label}：正文混入元信息/拒絕語/占位符，重寫本段乾淨落地。",
            "excerpt": compact(trimmed[max(0, index - 4) : index + 20]),
        }
    return None


def find_placeholders(content: list[ContentLine]) -> list[dict[str, Any]]:
    """Detect placeholder, refusal, and garbled-character leaks."""
    findings: list[dict[str, Any]] = []
    for item in content:
        if not is_content(item.trimmed):
            continue
        finding = _match_placeholder_line(item.trimmed, item.line_no)
        if finding is not None:
            findings.append(finding)
    return findings


def _match_meta_leak_line(trimmed: str, line_no: int) -> dict[str, Any] | None:
    """Return tier-1 or tier-2 engineering-word leakage finding on `trimmed`."""
    if CHAPTER_HEADING_RE.match(trimmed):
        return None
    outside_quotes = mask_quoted_spans(trimmed)
    match = META_TIER1_RE.search(outside_quotes)
    quoted_tier1 = False
    if not match:
        match = META_TIER1_RE.search(trimmed)
        quoted_tier1 = match is not None

    if match:
        suffix = (
            "例外：角色為作者/編剧、在故事內真實讨論創作時，台詞里可能合法。"
            if quoted_tier1
            else ""
        )
        idx = match.start()
        return {
            "line": line_no,
            "column": idx + 1,
            "type": "meta-leak",
            "severity": "advisory" if quoted_tier1 else "blocking",
            "message": (
                f"工程詞泄漏：「{match.group(0)}」是寫作流水線术語，正文里不該出現；"
                f"改成角色/场景內表達。{suffix}"
            ),
            "excerpt": compact(trimmed[max(0, idx - 6) : idx + 18]),
        }

    match = META_TIER2_RE.search(trimmed)
    if not match:
        return None
    idx = match.start()
    return {
        "line": line_no,
        "column": idx + 1,
        "type": "meta-leak",
        "severity": "advisory",
        "message": (
            f"元信息泄漏：「{match.group(0)}」疑似工程/章節結構詞混入正文；"
            "改成角色當下可感知的事件锚點或相對時間。"
            "例外：角色在故事內真實閱讀/讨論「第X章」、真身為作者/讀者、或故事內系統/界面用語。"
        ),
        "excerpt": compact(trimmed[max(0, idx - 6) : idx + 18]),
    }


def find_meta_leak(content: list[ContentLine]) -> list[dict[str, Any]]:
    """Detect tier-1 and tier-2 writing-pipeline meta leakage."""
    findings: list[dict[str, Any]] = []
    for item in content:
        if not is_content(item.trimmed):
            continue
        finding = _match_meta_leak_line(item.trimmed, item.line_no)
        if finding is not None:
            findings.append(finding)
    return findings


def scan_document(input_text: str) -> list[dict[str, Any]]:
    """Scan a document string and return sorted degeneration findings."""
    lines = re.split(r"\r?\n", input_text)
    content: list[ContentLine] = []
    fence: str | None = None
    in_front_matter = has_yaml_front_matter(lines)

    for index, line in enumerate(lines):
        trimmed = line.strip()
        if in_front_matter:
            if index > 0 and trimmed == "---":
                in_front_matter = False
            continue
        fence_marker = FENCE_MARKER_RE.match(trimmed)
        if fence is not None:
            if fence_marker and trimmed[0] == fence:
                fence = None
            continue
        if fence_marker:
            fence = trimmed[0]
            continue
        content.append(ContentLine(text=line, trimmed=trimmed, line_no=index + 1))

    findings: list[dict[str, Any]] = []
    findings.extend(find_repetition(content))
    findings.extend(find_truncation(content))
    findings.extend(find_placeholders(content))
    findings.extend(find_meta_leak(content))
    findings.sort(key=lambda f: (f["line"], f["column"]))
    return findings


def _parse_args(argv: list[str]) -> tuple[bool, str, list[str]]:
    """Parse CLI arguments and return `(json_mode, fail_on, files)`."""
    json_mode = False
    fail_on = "all"
    files: list[str] = []

    for arg in argv:
        if arg == "--check":
            continue
        if arg == "--json":
            json_mode = True
        elif arg.startswith("--fail-on="):
            value = arg[len("--fail-on=") :]
            if value not in ("blocking", "all"):
                die("--fail-on must be 'blocking' or 'all'")
            fail_on = value
        elif arg in ("-h", "--help"):
            print(USAGE)
            sys.exit(0)
        elif arg.startswith("-"):
            die(f"Unknown option: {arg}")
        else:
            files.append(arg)

    if not files:
        die("No files provided")
    return json_mode, fail_on, files


def main(argv: list[str] | None = None) -> int:
    """CLI entry point returning process exit code (0, 1, or 2)."""
    json_mode, fail_on, files = _parse_args(sys.argv[1:] if argv is None else argv)
    failed = False
    all_findings: list[dict[str, Any]] = []

    for file in files:
        full_path = Path(file).resolve()
        try:
            input_text = full_path.read_text(encoding="utf-8")
        except OSError as exc:
            failed = True
            if not json_mode:
                print(f"{file}: unable to read ({exc})", file=sys.stderr)
            continue
        for finding in scan_document(input_text):
            all_findings.append({"file": file, **finding})

    if json_mode:
        print(json.dumps({"findings": all_findings}, indent=2, ensure_ascii=False))
    else:
        for f in all_findings:
            print(
                f"{f['file']}:{f['line']}:{f['column']}: "
                f"[{f['severity']}] {f['type']}: {f['message']} ({f['excerpt']})"
            )

    if failed:
        return 2
    has_blocking = any(f["severity"] == "blocking" for f in all_findings)
    if has_blocking if fail_on == "blocking" else len(all_findings) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
