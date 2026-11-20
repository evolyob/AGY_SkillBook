#!/usr/bin/env python3
"""Measure, checkpoint, check, and commit long-form story chapters.

`chapter check --plain` 把同一份檢查結果說成作者能懂的話（單章檢查一條命令出白話結論），
並报本章碎度两個數：短段占比與敘述句長中位數，附真人参照；碎度只提示、不拦。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


def _load_local_module(name: str, filename: str) -> Any:
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"TOOL_UNAVAILABLE: {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = _load_local_module("story_wordcount_core", "wordcount_core.py")
for _name in dir(core):
    if not _name.startswith("_"):
        globals()[_name] = getattr(core, _name)

CHAPTER_CHECK_SCHEMA = "story-chapter-check/v1"
CHAPTER_ERROR_SCHEMA = "story-chapter-error/v1"
# 書內工作目錄：分組 segment、writer prompt 留檔、逐章事务 JSON 的唯一落點。
# 提交成功後整目錄刪除，失敗時原樣保留供重跑。
WORK_ROOT = (".story", "work")


# ---- 碎度（只提示，不拦）----
# 先去掉 # 開頭的行；短段＝非空行里去空白後不到 20 字的占比（對話段也算）；
# 敘述句＝逐段去掉“…”「…」『…』"..."里的對話後按 。！？!?… 切句，取每句去空白後的字數求中位數。
# 真人参照：番茄、七猫、纵横 970 本長篇抽樣 5458 章標定，短段中位數约 38%（P10–P90 16%–62%），
# 敘述句長中位數约 23 字（P10–P90 15–35 字）。
SHORT_PARAGRAPH_CHARS = 20
HUMAN_SHORT_PARAGRAPH_RATIO = 0.38
HUMAN_NARRATIVE_SENTENCE_MEDIAN = 23
HUMAN_SHORT_PARAGRAPH_RANGE = (0.16, 0.62)
HUMAN_NARRATIVE_SENTENCE_RANGE = (15, 35)
# ---- 動作與心理平衡（只提示，不拦）----
# 七猫 132 本完結長篇抽樣 5246 章去引語敘述句標定：
# 帶肢體/手眼動作詞的敘述句平均约 12%（P10–P90 3%–23%，P95 29%），帶盘算/因果詞的敘述句平均约 15%（P10–P90 4%–28%）。
HUMAN_BODY_ACTION_SENTENCE_RATIO = 0.12
HUMAN_BODY_ACTION_SENTENCE_RANGE = (0.03, 0.23)
HUMAN_THOUGHT_CAUSAL_SENTENCE_RATIO = 0.15
HUMAN_THOUGHT_CAUSAL_SENTENCE_RANGE = (0.04, 0.28)
_QUOTED = re.compile(r'“[^”]*”|「[^」]*」|『[^』]*』|"[^"]*"')
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_BODY_ACTION_SENTENCE_RE = re.compile(
    r"指尖|指腹|手指|指節|手背|掌心|拳頭|手腕|袖口|衣角|喉結|眼眶|眼底|眸光|目光|視線|眼神|眉頭|嘴角|唇角|肩膀|呼吸|"
    r"伸手|抬手|探手|拿起|拿過|取出|取過|掏出|摸出|抓起|攥住|攥紧|握住|握紧|捏住|按住|压住|扣住|拢住|摩挲|"
    r"推開|拉開|打開|關上|放下|遞給|挑開|掀開|扯開|轉身|回頭|抬頭|低頭|彎腰|俯身|走到|走向|坐下|站起|盯着|掃過|看向|望向"
)
_THOUGHT_CAUSAL_SENTENCE_RE = re.compile(
    r"因為|所以|既然|省得|免得|要不然|否則|怪不得|難怪|偏偏|明明|反正|横竖|索性|乾脆|好在|幸亏|毕竟|本來|原本|其實|說白了|說到底|"
    r"知道|明白|清楚|覺得|以為|盘算|寻思|估摸|琢磨|怀疑|擔心|害怕|後悔|心想|暗想|暗道|暗罵|腹诽|犯不着|舍不得|懒得|巴不得"
)


def _narrative_sentences(text: str) -> tuple[list[str], list[str]]:
    lines = [line.strip() for line in _HTML_COMMENT.sub("", text.lstrip("\ufeff")).splitlines()]
    paragraphs = [line for line in lines if line and not line.startswith("#")]
    sentences = [
        compact
        for line in paragraphs
        for s in re.split(r"[。！？!?…]+", _QUOTED.sub("", line))
        if (compact := re.sub(r"\s", "", s))
    ]
    return paragraphs, sentences


def fragmentation(text: str) -> dict[str, Any]:
    paragraphs, sentences = _narrative_sentences(text)
    short = sum(1 for line in paragraphs if len(re.sub(r"\s", "", line)) < SHORT_PARAGRAPH_CHARS)
    lengths = [len(sentence) for sentence in sentences]
    return {
        "paragraphs": len(paragraphs),
        "short_paragraphs": short,
        "short_paragraph_ratio": round(short / len(paragraphs), 3) if paragraphs else None,
        "narrative_sentences": len(lengths),
        "narrative_sentence_median": statistics.median(lengths) if lengths else None,
        "human_reference": {"short_paragraph_ratio": HUMAN_SHORT_PARAGRAPH_RATIO,
                            "narrative_sentence_median": HUMAN_NARRATIVE_SENTENCE_MEDIAN,
                            "short_paragraph_range": list(HUMAN_SHORT_PARAGRAPH_RANGE),
                            "narrative_sentence_range": list(HUMAN_NARRATIVE_SENTENCE_RANGE)},
    }


def prose_balance(text: str) -> dict[str, Any]:
    _, sentences = _narrative_sentences(text)
    total = len(sentences)
    act_hits = sum(1 for s in sentences if _BODY_ACTION_SENTENCE_RE.search(s))
    thought_hits = sum(1 for s in sentences if _THOUGHT_CAUSAL_SENTENCE_RE.search(s))
    return {
        "narrative_sentences": total,
        "body_action_sentences": act_hits,
        "body_action_sentence_ratio": round(act_hits / total, 3) if total else None,
        "thought_causal_sentences": thought_hits,
        "thought_causal_sentence_ratio": round(thought_hits / total, 3) if total else None,
        "human_reference": {
            "body_action_sentence_ratio": HUMAN_BODY_ACTION_SENTENCE_RATIO,
            "body_action_sentence_range": list(HUMAN_BODY_ACTION_SENTENCE_RANGE),
            "thought_causal_sentence_ratio": HUMAN_THOUGHT_CAUSAL_SENTENCE_RATIO,
            "thought_causal_sentence_range": list(HUMAN_THOUGHT_CAUSAL_SENTENCE_RANGE),
        },
    }


class CliArgumentError(ValueError):
    pass


class StructuredArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliArgumentError(message)


def _tracking_module() -> Any:
    return _load_local_module("story_tracking_for_storyctl", "tracking_commit.py")


def _tracking_call(function: Any, *args: Any) -> Any:
    try:
        return function(*args)
    except Exception as exc:
        if exc.__class__.__name__ == "TrackingError":
            raise WordcountError(str(exc)) from exc
        raise


def _json_line(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    # Windows runners may expose a cp1252 console even when callers explicitly
    # consume UTF-8.  Write protocol output as bytes so JSON never depends on
    # the host console code page.
    sys.stdout.buffer.write(rendered.encode("utf-8"))
    sys.stdout.buffer.flush()


def _text_lines(lines: list[str]) -> None:
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WordcountError(f"unable to read {label}: {exc}") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def chapter_work_dir(project: Path, chapter: int) -> Path:
    width = max(3, len(str(chapter)))
    return project.resolve().joinpath(*WORK_ROOT, f"第{chapter:0{width}d}章")


def _remove_chapter_work_dir(project: Path, chapter: int) -> str | None:
    """Delete this chapter's scratch directory after a successful commit.

    Only the per-chapter directory is removed; `.story/work` and `.story` are
    pruned only when empty, so book-level author memory under `.story/` stays.
    """
    path = chapter_work_dir(project, chapter)
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        return None
    for parent in (path.parent, path.parent.parent):
        try:
            parent.rmdir()
        except OSError:
            break
    return "/".join((*WORK_ROOT, path.name))


def _project_files(
    project: Path, chapter: int, author_range: Any = None,
) -> tuple[Path, Path, int, dict[str, int] | None]:
    return read_project_chapter(project, chapter, author_range)


def _json_findings(output: str) -> list[dict[str, Any]] | None:
    """檢測器 --json 輸出里的 findings；輸出不是預期 JSON 時返回 None（按工具故障處理，不當作無問題）。"""
    try:
        value = json.loads(output)
    except json.JSONDecodeError:
        return None
    findings = value.get("findings") if isinstance(value, dict) else None
    if not isinstance(findings, list) or not all(isinstance(row, dict) for row in findings):
        return None
    return findings


NODE_REQUIRED = (
    "質量檢查（AI 句式、退化、標點、細綱照搬）要用 Node.js 運行，本機找不到 node。"
    "安裝 Node.js 18 或更高版本並確認 `node --version` 可用後重跑本命令；裝好之前本章不能提交。"
)


def _semantic_advisories(advisories: list[dict[str, Any]]) -> int:
    # check-ai-patterns 給每條 finding 標 review=semantic|mechanical，退化檢測器的在入口統一標 mechanical；
    # 其余來源沒標的按語義類算，宁多勿漏。
    return sum(1 for row in advisories if row.get("review") != "mechanical")


# 與 hooks（JS core DESLOP_SKIP_MARKER / codex py / bash guard）同一語法：注釋內只認 ASCII 空格/Tab，
# 冒號全角半角都認；裸寫不在注釋里的不算。
DESLOP_SKIP = re.compile(r"<!--[ \t]*去味[ \t]*(：|:)[ \t]*跳過[ \t]*-->")


def deslop_skipped(body: Path) -> bool:
    """作者顯式說本章不去味時，標題行下的 <!-- 去味:跳過 --> 豁免 AI 句式；與 hooks 同一個首 6 行窗口。"""
    head = re.split(r"\r?\n", body.read_text(encoding="utf-8-sig"))[:6]
    return bool(DESLOP_SKIP.search("\n".join(head)))


def check_blocking_quality(outline: Path, body: Path) -> dict[str, Any]:
    """Run the deterministic prose checks.

    status: pass（無 blocking）/ fail（有 blocking 正文問題）/ unavailable（檢測工具缺失或崩溃，
    不是正文問題，見 tool_errors）。
    """
    py_exe = sys.executable
    root = Path(__file__).parent
    exempt = deslop_skipped(body)
    blocking: list[dict[str, Any]] = []
    advisories: list[dict[str, Any]] = []
    tool_errors: list[dict[str, Any]] = []
    for name, script in (
        ("ai-pattern", "check_ai_patterns.py"),
        ("degeneration", "check_degeneration.py"),
    ):
        path = root / script
        if not path.is_file():
            tool_errors.append({"type": "TOOL_UNAVAILABLE", "tool": script, "message": f"missing {script}"})
            continue
        completed = subprocess.run(
            [py_exe, str(path), "--check", "--json", "--fail-on=blocking", str(body)],
            text=True, encoding="utf-8", capture_output=True, check=False,
        )
        findings = _json_findings(completed.stdout)
        if findings is None or completed.returncode not in {0, 1}:
            tool_errors.append({"type": "TOOL_ERROR", "tool": script, "source": name,
                                "message": completed.stderr.strip() or f"{script} exited {completed.returncode} without JSON findings"})
            continue
        for finding in findings:
            row = {"source": name, **finding}
            if name == "degeneration":
                # 退化類（複讀、截斷、拒絕語、工程詞）不是 AI 味，不計入触發去 AI 味审查的語義條數。
                row.setdefault("review", "mechanical")
            if exempt and name == "ai-pattern" and finding.get("severity") == "blocking":
                # 豁免只管 AI 句式；退化類（複讀、截斷、拒絕語、工程詞）照常必須修。
                advisories.append({**row, "severity": "advisory", "exempted": "去味:跳過"})
                continue
            (blocking if finding.get("severity") == "blocking" else advisories).append(row)

    punctuation = root / "normalize_punctuation.py"
    if not punctuation.is_file():
        tool_errors.append({"type": "TOOL_UNAVAILABLE", "tool": punctuation.name,
                            "message": "missing normalize_punctuation.py"})
    else:
        completed = subprocess.run(
            [py_exe, str(punctuation), "--check", str(body)],
            text=True, encoding="utf-8", capture_output=True, check=False,
        )
        if completed.returncode == 1:
            blocking.append(
                {"type": "PUNCTUATION_NOT_NORMALIZED", "message": (completed.stdout or completed.stderr).strip()}
            )
        elif completed.returncode != 0:
            tool_errors.append({"type": "TOOL_ERROR", "tool": punctuation.name,
                                "message": completed.stderr.strip() or f"exited {completed.returncode}"})

    outline_copy = root / "check_outline_copy.py"
    if not outline_copy.is_file():
        tool_errors.append({"type": "TOOL_UNAVAILABLE", "tool": outline_copy.name,
                            "message": "missing check_outline_copy.py"})
    else:
        completed = subprocess.run(
            [py_exe, str(outline_copy), "--outline", str(outline), str(body)],
            text=True, encoding="utf-8", capture_output=True, check=False,
        )
        if completed.returncode != 0:
            advisories.append(
                {"source": "outline-copy", "type": "OUTLINE_COPY_REVIEW", "review": "semantic",
                 "message": completed.stdout.strip()}
            )
    return {
        "status": "unavailable" if tool_errors else ("fail" if blocking else "pass"),
        "blocking_findings": blocking,
        "advisories": advisories,
        "semantic_advisories": _semantic_advisories(advisories),
        "tool_errors": tool_errors,
    }


# chapter check 頂層 status 與退出碼：一眼分清「能提交」「要作者定」「正文要改」「工具壞了」。
CHECK_EXIT_CODES = {"ready": 0, "needs_decision": 0, "blocked": 1, "invalid": 1, "tool_unavailable": 3}
ERROR_EXIT_CODES = {"TOOL_UNAVAILABLE": 3}
ACCEPT_FLOOR_RATIO = 0.5
BASELINE_FILE = "over_length_baseline.json"


class ChapterRefused(WordcountError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _check_status(length: dict[str, Any], quality: dict[str, Any]) -> str:
    if quality["status"] == "unavailable":
        return "tool_unavailable"
    if quality["status"] != "pass":
        return "blocked"
    if length["status"] == "invalid":
        return "invalid"
    return "ready" if length["status"] in {"internal_pass", "borderline"} else "needs_decision"


def _body_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record_over_baseline(project: Path, chapter: int, body_path: Path, actual: int) -> None:
    """第一次看到 over 時記下原稿指纹：接受超長前要证明那一次淨刪压縮真的做過。"""
    path = chapter_work_dir(project, chapter) / BASELINE_FILE
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        previous = None
    # 已有基線且這次更短：是压縮後的複檢，保留基線；更長則是重寫出的新稿，重新記。
    if isinstance(previous, dict) and isinstance(previous.get("actual"), int) and actual <= previous["actual"]:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"body_sha256": _body_digest(body_path), "actual": actual}), encoding="utf-8")


def chapter_check(project: Path, chapter: int, author_range: Any = None) -> dict[str, Any]:
    outline, body_path, target, effective_range = _project_files(project, chapter, author_range)
    try:
        body = body_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise WordcountError(f"unable to read body: {exc}") from exc
    length = evaluate_wordcount(body, target, chapter=chapter, author_range=effective_range)
    quality = check_blocking_quality(outline, body_path)
    status = _check_status(length, quality)
    if status == "ready":
        actions = ["commit"]
    elif status != "needs_decision":
        actions: list[str] = []
    elif length["status"] == "over":
        actions = ["compress-once", "accept-current-length", "revise-outline-or-target", "discard"]
    else:
        actions = ["accept-current-length", "revise-outline-or-target", "discard"]
    tracking = _tracking_module()
    state = _tracking_call(tracking.load_state, project)
    compression = None
    if length["status"] == "over" and quality["status"] == "pass":
        actual = length["actual"]
        compression = {
            "mode": "single_pass_remove_only",
            "remove_to_internal_band": {
                "min": actual - length["internal_band"]["max"],
                "max": actual - length["internal_band"]["min"],
            },
            "remove_to_user_band": {
                "min": actual - length["user_band"]["max"],
                "max": actual - length["user_band"]["min"],
            },
        }
        _record_over_baseline(project, chapter, body_path, actual)
    return {
        "schema": CHAPTER_CHECK_SCHEMA,
        "status": status,
        "chapter": chapter,
        "length": length,
        "quality": quality,
        "fragmentation": fragmentation(body),
        "prose_balance": prose_balance(body),
        "compression": compression,
        "state_revision": state["state_revision"],
        "tracking_committed": state["last_committed_chapter"] >= chapter,
        "next_chapter_started": state["last_committed_chapter"] > chapter,
        "available_actions": actions,
    }


def fix_punctuation(project: Path, chapter: int, author_range: Any = None) -> bool:
    """Run the deterministic punctuation normalizer on the chapter body in place.

    Folding it into `chapter check --fix-punctuation` lets the parent flow close a
    chapter with one call instead of running each cleanup script separately.
    """
    _, body, _, _ = _project_files(project, chapter, author_range)
    script = Path(__file__).with_name("normalize_punctuation.py")
    if not script.is_file():
        return False  # chapter check reports the missing tool in quality.tool_errors
    before = body.read_bytes()
    subprocess.run([sys.executable, str(script), str(body)], text=True, encoding="utf-8",
                   capture_output=True, check=False)
    return body.read_bytes() != before


def _require_acceptable_length(
    project: Path, chapter: int, checked: dict[str, Any], *, force: bool, author_range: Any = None,
) -> None:
    """接受當前長度的两道底線：欠長不低於目標一半；超長先做過一次淨刪压縮（刪掉原稿到作者范围上限
    差額的至少一半）。作者明確拍板用 --force 越過。"""
    if force:
        return
    length = checked["length"]
    if length["status"] == "under" and length["actual"] < length["target"] * ACCEPT_FLOOR_RATIO:
        raise ChapterRefused(
            "BELOW_ACCEPT_FLOOR",
            f"本章 {length['actual']} 字，不到字數目標 {length['target']} 的一半，不能直接按當前長度接受；"
            "先補細綱或改字數目標，作者明確要這個長度時加 --force",
        )
    if length["status"] == "over":
        path = chapter_work_dir(project, chapter) / BASELINE_FILE
        try:
            baseline = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            baseline = None
        _, body_path, _, _ = _project_files(project, chapter, author_range)
        valid = isinstance(baseline, dict) and isinstance(baseline.get("actual"), int)
        # 压縮要真刪：至少刪掉原稿到作者字數范围上限差額的一半（至少 1 字），刪一两個字不算做過。
        ceiling = None
        if valid:
            gap = baseline["actual"] - length["user_band"]["max"]
            ceiling = baseline["actual"] - max(1, (gap + 1) // 2)
        compressed = (
            valid
            and baseline.get("body_sha256") != _body_digest(body_path)
            and length["actual"] <= ceiling
        )
        if not compressed:
            detail = (f"（原稿 {baseline['actual']} 字，压縮後要不超過 {ceiling} 字，現在 {length['actual']} 字）"
                      if valid else "")
            raise ChapterRefused(
                "COMPRESSION_REQUIRED",
                f"超長章節先按 compress-once 做一次淨刪压縮並重跑 chapter check{detail}，仍超長再接受當前長度；"
                "作者明確不压縮時加 --force",
            )


def chapter_commit(
    project: Path, chapter: int, input_path: Path, *, accept_current_length: bool,
    author_range: Any = None, force: bool = False,
) -> dict[str, Any]:
    checked = chapter_check(project, chapter, author_range)
    if checked["status"] == "tool_unavailable":
        raise ChapterRefused(
            "TOOL_UNAVAILABLE",
            "；".join(item["message"] for item in checked["quality"]["tool_errors"]) or NODE_REQUIRED,
        )
    if checked["quality"]["status"] != "pass":
        raise ChapterRefused("QUALITY_BLOCKED", "blocking quality findings must be fixed before commit")
    length_status = checked["length"]["status"]
    in_user_band = length_status in {"internal_pass", "borderline"}
    if accept_current_length:
        require(length_status in {"under", "over"}, "accept-current-length requires a valid out-of-band chapter")
        _require_acceptable_length(project, chapter, checked, force=force, author_range=author_range)
        resolution = "accepted_current_length"
    else:
        if not in_user_band:
            raise ChapterRefused(
                "LENGTH_OUT_OF_BAND",
                "chapter length is outside the user band; use accept-current-length or revise it",
            )
        resolution = "within_user_band"
    document = _read_json_object(input_path, "tracking transaction")
    require(document.get("chapter") == chapter, "tracking transaction chapter does not match command")
    require("wordcount" not in document, "tracking transaction must not provide wordcount")
    document["wordcount"] = build_project_wordcount_record(
        project, chapter, resolution=resolution, author_range=author_range,
    )
    tracking = _tracking_module()
    state = _tracking_call(tracking.apply_transaction, project, document)
    checked["tracking_committed"] = state["last_committed_chapter"] >= chapter
    checked["next_chapter_started"] = state["last_committed_chapter"] > chapter
    checked["wordcount"] = state["wordcount_records"].get(str(chapter))
    checked["mode"] = document.get("mode")
    # The commit is already durable; a cleanup failure is reported, never turned into a failed commit.
    try:
        checked["work_dir_removed"] = _remove_chapter_work_dir(project, chapter)
    except OSError as exc:
        checked["work_dir_removed"] = None
        checked["work_dir_cleanup_error"] = str(exc)
    return checked


PLAIN_SHOWN = 8  # 建議看的提示最多列几條，其余报個數


def _finding_line(row: dict[str, Any]) -> str:
    where = f"第 {row['line']} 行" if row.get("line") else "全章"
    excerpt = str(row.get("excerpt") or "").strip()
    message = str(row.get("message") or row.get("type") or "").strip()
    return f"- {where}" + (f"「{excerpt[:40]}」" if excerpt else "") + f"：{message}"


def plain_report(result: dict[str, Any]) -> list[str]:
    """把 chapter check 的結果說成白話：先結論，再字數、必須改的、建議看的、碎度。"""
    chapter = result["chapter"]
    status = result["status"]
    length = result["length"]
    quality = result["quality"]
    lines: list[str] = []
    verdict = {
        "ready": f"第 {chapter} 章檢查完了，可以提交。",
        "needs_decision": f"第 {chapter} 章沒有必須改的，但字數不在范围里，要請作者定。",
        "blocked": f"第 {chapter} 章有必須改的地方，改完再查一次。",
        "invalid": f"第 {chapter} 章正文是空的或讀不出字數，先把正文寫進去再查。",
        "tool_unavailable": f"第 {chapter} 章這次沒查完：檢查工具沒跑起來，不能提交。",
    }[status]
    if result.get("punctuation_fixed"):
        verdict += "標點已順手整理過。"
    lines.append(verdict)
    actual = length.get("actual")
    band = length.get("user_band") or {}
    if actual is not None and band:
        span = f"{band.get('min')} 到 {band.get('max')} 字"
        if length.get("status") == "under":
            lines.append(f"字數：约 {actual} 字，比范围（{span}）少了约 {band['min'] - actual} 字。欠的不補寫，請作者選：收下現在的長度、改細綱或目標後重寫、或不要這章。")
        elif length.get("status") == "over":
            lines.append(f"字數：约 {actual} 字，比范围（{span}）多了约 {actual - band['max']} 字。")
            compression = result.get("compression")
            if compression:
                remove = compression["remove_to_internal_band"]
                lines.append(f"先做一次只刪不加的压縮：刪掉 {max(remove['min'], 0)} 到 {remove['max']} 字（刪重複解釋、裝飾排比、沒用的小動作，情節點和钩子都留着），刪完再查；還超就請作者選。")
        else:
            lines.append(f"字數：约 {actual} 字，在范围里（{span}）。")
    for error in quality.get("tool_errors") or []:
        lines.append(f"- 沒跑起來：{error.get('message') or error.get('tool')}")
    blocking = quality.get("blocking_findings") or []
    if blocking:
        lines.append(f"必須改的 {len(blocking)} 處：")
        lines.extend(_finding_line(row) for row in blocking)
    advisories = quality.get("advisories") or []
    if advisories:
        semantic = quality.get("semantic_advisories", 0)
        lines.append(f"建議看看的 {len(advisories)} 處（其中像 AI 腔、要讀原文判斷的 {semantic} 處；確屬問題才改）：")
        lines.extend(_finding_line(row) for row in advisories[:PLAIN_SHOWN])
        if len(advisories) > PLAIN_SHOWN:
            lines.append(f"- 另有 {len(advisories) - PLAIN_SHOWN} 處，見 chapter check 的完整結果")
    if not blocking and not advisories and status in {"ready", "needs_decision"}:
        lines.append("沒發現 AI 腔或寫壞的地方。")
    frag = result.get("fragmentation") or {}
    ratio, median = frag.get("short_paragraph_ratio"), frag.get("narrative_sentence_median")
    if ratio is not None or median is not None:
        parts = []
        low, high = HUMAN_SHORT_PARAGRAPH_RANGE
        if ratio is not None:
            parts.append(f"不到 {SHORT_PARAGRAPH_CHARS} 字的短段占 {round(ratio * 100)}%"
                         f"（真人平均约 {round(HUMAN_SHORT_PARAGRAPH_RATIO * 100)}%，多數章在 {round(low * 100)}%–{round(high * 100)}%）")
        shortest, longest = HUMAN_NARRATIVE_SENTENCE_RANGE
        if median is not None:
            parts.append(f"敘述句長中位數 {median:g} 字（真人平均约 {HUMAN_NARRATIVE_SENTENCE_MEDIAN} 字，多數章在 {shortest}–{longest} 字）")
        choppy = (ratio is not None and ratio > high) or (median is not None and median < shortest)
        tail = "。偏碎：同一個動作或同一層意思的几句可以接成一句、並成一段。" if choppy else "。"
        lines.append("這章碎不碎（只作参考，不拦）：" + "，".join(parts) + tail)
    balance = result.get("prose_balance") or {}
    act_ratio = balance.get("body_action_sentence_ratio")
    thought_ratio = balance.get("thought_causal_sentence_ratio")
    total_sentences = balance.get("narrative_sentences") or 0
    if act_ratio is not None and thought_ratio is not None:
        act_low, act_high = HUMAN_BODY_ACTION_SENTENCE_RANGE
        th_low, th_high = HUMAN_THOUGHT_CAUSAL_SENTENCE_RANGE
        b_parts = [
            f"帶肢體或手眼動作的敘述句占 {round(act_ratio * 100)}%"
            f"（真人平均约 {round(HUMAN_BODY_ACTION_SENTENCE_RATIO * 100)}%，多數章在 {round(act_low * 100)}%–{round(act_high * 100)}%）",
            f"帶盘算或因果的敘述句占 {round(thought_ratio * 100)}%"
            f"（真人平均约 {round(HUMAN_THOUGHT_CAUSAL_SENTENCE_RATIO * 100)}%，多數章在 {round(th_low * 100)}%–{round(th_high * 100)}%）",
        ]
        action_heavy = total_sentences >= 8 and (
            act_ratio > 0.29 or (act_ratio > act_high and thought_ratio < 0.08)
        )
        b_tail = (
            "。動作偏密、心裡帳偏少：刪掉不改局面的手眼或道具小動作，把角色為什麼這麼選、圖什麼直接寫出來。"
            if action_heavy else "。"
        )
        lines.append("動作和心裡話（只作参考，不拦）：" + "，".join(b_parts) + b_tail)
    return lines


_PLAIN_ERRORS = (
    (re.compile(r"chapter (\d+) must have exactly one outline file"), "第 {0} 章沒有細綱，或者細綱不止一份"),
    (re.compile(r"chapter (\d+) must have exactly one body file"), "第 {0} 章沒有正文，或者正文不止一份"),
    (re.compile(r"chapter directory is missing: .*/(\S+)$"), "書里沒有「{0}」這個目錄"),
    (re.compile(r"字數目標"), "細綱的字數目標沒寫或寫法不對（寫成「字數目標：2500 字」）"),
    (re.compile(r"字數范围"), "細綱的字數范围寫法不對（寫成「字數范围：2000-2600」）"),
)


def _plain_error(message: str) -> list[str]:
    for pattern, text in _PLAIN_ERRORS:
        match = pattern.search(message)
        if match:
            return [f"這次沒查成：{text.format(*match.groups())}。"]
    return [f"這次沒查成：{message}"]


def _build_parser() -> StructuredArgumentParser:
    parser = StructuredArgumentParser(prog="storyctl.py")
    commands = parser.add_subparsers(dest="command", required=True)
    wordcount = commands.add_parser("wordcount")
    wordcount_commands = wordcount.add_subparsers(dest="wordcount_command", required=True)
    for command in ("measure", "check", "checkpoint"):
        subparser = wordcount_commands.add_parser(command)
        subparser.add_argument("--file", required=True)
        subparser.add_argument("--chapter")
        subparser.add_argument("--case-id")
        if command != "measure":
            subparser.add_argument("--target", required=command == "check")
            _add_range_arguments(subparser)
        if command == "checkpoint":
            subparser.add_argument("--project", type=Path,
                                   help="書目錄：與 --chapter 一起從細綱讀字數目標（未給 --target 時）和「字數范围」")
    chapter = commands.add_parser("chapter")
    chapter_commands = chapter.add_subparsers(dest="chapter_command", required=True)
    for command in ("check", "commit", "accept-current-length"):
        subparser = chapter_commands.add_parser(command)
        subparser.add_argument("--project", type=Path, required=True)
        subparser.add_argument("--chapter", type=int, required=True)
        _add_range_arguments(subparser)
        if command != "check":
            subparser.add_argument("--input", type=Path, required=True)
        else:
            subparser.add_argument("--fix-punctuation", action="store_true",
                                   help="先就地整理正文標點，再做檢查")
            subparser.add_argument("--plain", action="store_true",
                                   help="用白話輸出結論（給作者和主會話看），不輸出 JSON；退出碼不變")
        if command == "accept-current-length":
            subparser.add_argument("--force", action="store_true",
                                   help="作者明確拍板：越過欠長一半下限與超長先压縮一次的要求")
    return parser


def _add_range_arguments(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--min-chars", type=int, help="作者本輪給定的字數下限（須與 --max-chars 同給），優先於細綱字數范围與默認 ±15%%")
    subparser.add_argument("--max-chars", type=int, help="作者本輪給定的字數上限")


def _cli_author_range(args: argparse.Namespace) -> dict[str, int] | None:
    low, high = getattr(args, "min_chars", None), getattr(args, "max_chars", None)
    if low is None and high is None:
        return None
    if low is None or high is None:
        raise CliArgumentError("--min-chars and --max-chars must be given together")
    try:
        return normalize_author_range({"min": low, "max": high})
    except WordcountError as exc:
        raise CliArgumentError(str(exc)) from exc


def _wordcount_command(args: argparse.Namespace, author_range: dict[str, int] | None) -> int:
    try:
        body = Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        result = (
            {"schema": MEASUREMENT_SCHEMA, "metric": METRIC, "chapter": args.chapter, "case_id": args.case_id,
             "actual": None, "status": "invalid", "invalid_reason": "INVALID_FILE"}
            if args.wordcount_command == "measure"
            else invalid_wordcount_result("INVALID_FILE", chapter=args.chapter, case_id=args.case_id)
        )
        _json_line(result)
        return 2
    if args.wordcount_command == "measure":
        result = measure_wordcount(body, chapter=args.chapter, case_id=args.case_id)
    elif args.wordcount_command == "checkpoint":
        target = args.target
        if args.project is not None:
            # 與 chapter check 同一優先級：命令行上下限 > 細綱「字數范围」 > 默認帶。
            try:
                chapter = int(args.chapter or "")
                _, outline = read_chapter_outline(core.resolve_book_dir(args.project), chapter)
                if target is None:
                    target = target_from_outline(outline)
                author_range = effective_author_range(outline, author_range)
            except (ValueError, WordcountError):
                _json_line(invalid_wordcount_result("INVALID_OUTLINE", chapter=args.chapter, case_id=args.case_id))
                return 2
        if target is None:
            _json_line(invalid_wordcount_result("INVALID_ARGUMENT", chapter=args.chapter, case_id="--target or --project is required"))
            return 2
        try:
            result = checkpoint_wordcount(
                body, target, chapter=args.chapter, case_id=args.case_id, author_range=author_range,
            )
        except WordcountError:
            result = invalid_wordcount_result("INVALID_TARGET", chapter=args.chapter, case_id=args.case_id)
    else:
        result = evaluate_wordcount(
            body, args.target, chapter=args.chapter, case_id=args.case_id, author_range=author_range,
        )
    _json_line(result)
    return 2 if result.get("status") == "invalid" else 0


def main(argv: Sequence[str] | None = None) -> int:
    raw = list(argv) if argv is not None else sys.argv[1:]
    try:
        args = _build_parser().parse_args(raw)
        author_range = _cli_author_range(args)
    except CliArgumentError as exc:
        payload = (
            {"schema": CHAPTER_ERROR_SCHEMA, "status": "error", "error_code": "INVALID_ARGUMENT", "message": str(exc)}
            if raw[:1] == ["chapter"] else invalid_wordcount_result("INVALID_ARGUMENT", case_id=str(exc))
        )
        _json_line(payload)
        return 2
    if args.command == "wordcount":
        return _wordcount_command(args, author_range)
    try:
        args.project = core.resolve_book_dir(args.project)
        if args.chapter_command == "check":
            fixed = fix_punctuation(args.project, args.chapter, author_range) if args.fix_punctuation else None
            result = chapter_check(args.project, args.chapter, author_range)
            if fixed is not None:
                result["punctuation_fixed"] = fixed
        else:
            result = chapter_commit(
                args.project, args.chapter, args.input,
                accept_current_length=args.chapter_command == "accept-current-length",
                author_range=author_range, force=getattr(args, "force", False),
            )
    except (WordcountError, OSError, UnicodeError) as exc:
        code = exc.code if isinstance(exc, ChapterRefused) else "CHECK_FAILED"
        if getattr(args, "plain", False):
            _text_lines(_plain_error(str(exc)))
        else:
            _json_line({"schema": CHAPTER_ERROR_SCHEMA, "status": "error", "error_code": code, "message": str(exc)})
        return ERROR_EXIT_CODES.get(code, 2)
    if getattr(args, "plain", False):
        _text_lines(plain_report(result))
    else:
        _json_line(result)
    if args.chapter_command != "check":
        return 0
    return CHECK_EXIT_CODES[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
