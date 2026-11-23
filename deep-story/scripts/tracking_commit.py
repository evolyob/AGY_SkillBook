#!/usr/bin/env python3
"""Maintain one structured story state and its deterministic Markdown views.

The language model supplies compact semantic JSON.  This tool validates and
merges that input in memory, renders every derived view, then atomically writes
``_tracking-state.json`` last as the single commit point. Per-project locking
serializes concurrent writers before revision and wordcount checks.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import stat
import sys
import tempfile
import time
import unicodedata
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any


_WORDCOUNT_CORE_PATH = Path(__file__).with_name("wordcount_core.py")
if not _WORDCOUNT_CORE_PATH.is_file():  # pragma: no cover - broken deployment
    raise RuntimeError("TOOL_UNAVAILABLE: wordcount_core.py")
_WORDCOUNT_CORE_SPEC = importlib.util.spec_from_file_location(
    "story_wordcount_core", _WORDCOUNT_CORE_PATH
)
if _WORDCOUNT_CORE_SPEC is None or _WORDCOUNT_CORE_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("unable to load wordcount core")
wordcount_core = importlib.util.module_from_spec(_WORDCOUNT_CORE_SPEC)
_WORDCOUNT_CORE_SPEC.loader.exec_module(wordcount_core)


_CONTRACTS_PATH = Path(__file__).resolve().parent.parent / "data" / "contracts.json"
_TRACKING_LIMITS = json.loads(_CONTRACTS_PATH.read_text(encoding="utf-8"))["tracking_limits"]

INPUT_SCHEMA_VERSION = int(_TRACKING_LIMITS["input_schema_version"])
TRACKING_SCHEMA_VERSION = int(_TRACKING_LIMITS["tracking_schema_version"])
DELTA_TARGET_BYTES = int(_TRACKING_LIMITS["delta_target_bytes"])
DELTA_MAX_BYTES = int(_TRACKING_LIMITS["delta_max_bytes"])
CONTEXT_TARGET_BYTES = int(_TRACKING_LIMITS["context_target_bytes"])
CONTEXT_MAX_BYTES = int(_TRACKING_LIMITS["context_max_bytes"])
# 角色快照屬按需讀取的冷視圖（不進 上下文.md 四列表）；單文件上限對齊各宿主單次無分頁 Read 的 25K token 邊界。
SNAPSHOT_TARGET_BYTES = int(_TRACKING_LIMITS["snapshot_target_bytes"])
SNAPSHOT_MAX_BYTES = int(_TRACKING_LIMITS["snapshot_max_bytes"])
SNAPSHOT_ITEM_MAX_BYTES = int(_TRACKING_LIMITS["snapshot_item_max_bytes"])
DRAFT_INLINE_SNAPSHOTS_MAX_BYTES = int(_TRACKING_LIMITS["draft_inline_snapshots_max_bytes"])
# 下一章熱上下文里列出的活躍角色，不是核心角色總數；體積仍由 CONTEXT_MAX_BYTES 兜底。
ACTIVE_CHARACTER_MAX = int(_TRACKING_LIMITS["active_character_max"])

CONTEXT_HEADINGS = tuple(_TRACKING_LIMITS["context_headings"])
FORESHADOW_STATUSES = tuple(_TRACKING_LIMITS["foreshadow_statuses"])
FORESHADOW_IMPORTANCE = tuple(_TRACKING_LIMITS["foreshadow_importance"])
REVEAL_STATUSES = tuple(_TRACKING_LIMITS["reveal_statuses"])
# 伏筆與時間線條目里模型常用的同義寫法：含義明確的直接改成正式名，不讓一次提交為措辭失敗。
ACTION_ALIASES = _TRACKING_LIMITS["action_aliases"]
FORESHADOW_ACTION_STATUS = _TRACKING_LIMITS["foreshadow_action_status"]
FORESHADOW_KEY_ALIASES = _TRACKING_LIMITS["foreshadow_key_aliases"]
TIMELINE_KEY_ALIASES = _TRACKING_LIMITS["timeline_key_aliases"]
INVALID_FILE_CHARS = re.compile(r"[<>:\"/\\|?*\x00-\x1f]")
FORESHADOW_ID = re.compile(r"^F\d{3,}$")
SNAPSHOT_TEXT_FIELDS = tuple(_TRACKING_LIMITS["snapshot_text_fields"])
SNAPSHOT_LIST_FIELDS = tuple(_TRACKING_LIMITS["snapshot_list_fields"])
EVENT_ID = re.compile(r"^E\d{3,}$")
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
RETIRED_TRACKING_PATHS = tuple(_TRACKING_LIMITS["retired_tracking_paths"])
RETIRED_ARCHIVE_DIR = "_archive"


class TrackingError(ValueError):
    """Expected validation or tracking-state error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TrackingError(message)


def wordcount_value(function: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return function(*args, **kwargs)
    except wordcount_core.WordcountError as exc:
        raise TrackingError(str(exc)) from exc


def as_mapping(value: object, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def as_list(value: object, label: str) -> list[Any]:
    require(isinstance(value, list), f"{label} must be a JSON array")
    return value


def as_int(value: object, label: str, *, minimum: int = 0) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), f"{label} must be an integer")
    require(value >= minimum, f"{label} must be >= {minimum}")
    return value


def as_chapter(value: object, label: str, *, minimum: int = 1) -> int:
    """章號：模型常寫成 "22"。純數字字符串按整數收，語義不變；其余照舊報錯。"""
    if isinstance(value, str) and value.strip().isdecimal():
        value = int(value.strip())
    return as_int(value, label, minimum=minimum)


def with_aliases(row: dict[str, Any], aliases: dict[str, str]) -> dict[str, Any]:
    """把含義明確的同義字段名改成正式字段名；正式字段已在時不動，留給未知字段報錯。"""
    row = dict(row)
    for alias, canonical in aliases.items():
        if alias in row and canonical not in row:
            row[canonical] = row.pop(alias)
    return row


def normalize_action(value: object, label: str, *, allow_delete: bool) -> str:
    action = clean_text(value, label, max_bytes=24)
    action = ACTION_ALIASES.get(action.lower(), action.lower())
    allowed = ("upsert", "delete") if allow_delete else ("upsert",)
    require(action in allowed, f"{label} is invalid: use {' or '.join(allowed)}")
    return action


def require_known_keys(mapping: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = set(mapping) - allowed
    require(not unknown, f"{label} contains unsupported fields: {', '.join(sorted(unknown))}"
                         f"（只收 {', '.join(sorted(allowed))}）")


# 事務校驗期間收集全部超長字段，一次報完；None 表示逐條立即報錯（初始化、狀態讀取等路徑）。
_LENGTH_ISSUES: ContextVar[list[str] | None] = ContextVar("_LENGTH_ISSUES", default=None)


def length_hint(label: str, text: str, max_bytes: int) -> str:
    """把字節上限換算成字數：模型寫的是中文，只看得懂「要刪几個字」。"""
    size = len(text.encode("utf-8"))
    allowed = max(1, max_bytes * len(text) // size)
    return (f"{label} exceeds {max_bytes} bytes（現 {len(text)} 字，上限約 {allowed} 字，"
            f"至少刪 {len(text) - allowed} 字）")


def clean_text(value: object, label: str, *, allow_empty: bool = False, max_bytes: int = 768) -> str:
    require(isinstance(value, str), f"{label} must be a string")
    cleaned = " ".join(value.replace("|", "｜").split())
    require(allow_empty or bool(cleaned), f"{label} must not be empty")
    if len(cleaned.encode("utf-8")) > max_bytes:
        issues = _LENGTH_ISSUES.get()
        if issues is None:
            raise TrackingError(length_hint(label, cleaned, max_bytes))
        issues.append(length_hint(label, cleaned, max_bytes))
    return cleaned


def clean_string_list(
    value: object,
    label: str,
    *,
    maximum: int | None = None,
    item_max_bytes: int = 384,
) -> list[str]:
    values = as_list(value, label)
    if maximum is not None:
        require(len(values) <= maximum, f"{label} may contain at most {maximum} items")
    return [clean_text(item, f"{label}[{index}]", max_bytes=item_max_bytes) for index, item in enumerate(values)]


def safe_file_component(value: object, label: str) -> str:
    name = unicodedata.normalize("NFC", clean_text(value, label, max_bytes=180))
    require(not INVALID_FILE_CHARS.search(name), f"{label} contains an invalid filename character")
    require(name not in {".", ".."} and not name.endswith((".", " ")), f"{label} is not a safe filename")
    require(name.split(".", 1)[0].upper() not in WINDOWS_RESERVED_NAMES, f"{label} is reserved on Windows")
    return name


def portable_name_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def byte_size(text: str) -> int:
    return len(text.encode("utf-8"))


def emit(text: str, *, error: bool = False) -> None:
    """Write UTF-8 bytes directly.

    Windows 的文本 stdout 是 cp1252（含中文即 UnicodeEncodeError），stderr 默認
    backslashreplace（中文被轉義成反斜杠碼位，作者看不懂）。兩條路都要繞開。
    """
    stream = sys.stderr if error else sys.stdout
    stream.flush()
    stream.buffer.write((text + "\n").encode("utf-8"))
    stream.buffer.flush()


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrackingError(f"unable to read JSON {path}: {exc}") from exc


def json_payload(document: object) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_if_changed(path: Path, payload: str) -> None:
    try:
        if path.read_text(encoding="utf-8") == payload:
            return
    except FileNotFoundError:
        pass
    atomic_write_text(path, payload)


def tracking_root(project: Path) -> Path:
    return project.resolve() / "tracking"


def state_path(project: Path) -> Path:
    return tracking_root(project) / "_tracking-state.json"


@contextmanager
def project_write_lock(project: Path, *, timeout_seconds: float = 10.0):
    tracking = tracking_root(project)
    tracking.mkdir(parents=True, exist_ok=True)
    path = tracking / ".tracking-commit.lock"
    deadline = time.monotonic() + timeout_seconds
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TrackingError(
                    "tracking commit lock is busy or stale; retry, or remove tracking/.tracking-commit.lock after confirming no commit is running"
                )
            time.sleep(0.05)
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        os.fsync(descriptor)
        yield
    finally:
        os.close(descriptor)
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def delta_path(tracking: Path, chapter: int) -> Path:
    width = max(3, len(str(chapter)))
    return tracking / "logs" / f"ch_{chapter:0{width}d}.md"


def chapter_work_dir(project: Path, chapter: int) -> Path:
    width = max(3, len(str(chapter)))
    return project / ".story" / "work" / f"ch_{chapter:0{width}d}"


def find_retired_tracking_paths(tracking: Path) -> list[str]:
    found = [relative for relative in RETIRED_TRACKING_PATHS if (tracking / relative).exists()]
    found.extend(sorted(path.name for path in tracking.glob("基線_截至第*章.md")))
    return found


def require_no_retired_tracking_paths(tracking: Path) -> None:
    found = find_retired_tracking_paths(tracking)
    require(not found, f"retired tracking files are not supported: {', '.join(found)}")


def archive_retired_tracking_paths(tracking: Path) -> list[str]:
    """Move a pre-transaction 追蹤/ aside so init can build the current protocol in place.

    Nothing is parsed or converted: the old files are kept verbatim for the author to
    consult, and the new state is reconstructed from the init document alone.
    """
    retired = find_retired_tracking_paths(tracking)
    if not retired:
        return []
    archive = tracking / RETIRED_ARCHIVE_DIR
    for relative in retired:
        require(
            not (archive / relative).exists(),
            f"追蹤/{RETIRED_ARCHIVE_DIR}/{relative} already exists; move it away before initializing",
        )
    # 先全量校驗再搬運；中斷後重跑時已搬走的條目不再出現在待搬列表里，可直接續做。
    for relative in retired:
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tracking / relative, target)
    return retired


def _both_blank(position: dict[str, Any]) -> bool:
    return all(isinstance(position.get(key), str) and not position[key].strip() for key in ("story_time", "scene"))


def validate_position(value: object, label: str = "context.position") -> dict[str, Any]:
    position = as_mapping(value, label)
    require_known_keys(position, {"volume", "volume_start_chapter", "story_time", "scene"}, label)
    require(not _both_blank(position),
            f"{label}.story_time and {label}.scene must not be empty: fill where this chapter ends")
    return {
        "volume": safe_file_component(position.get("volume"), f"{label}.volume"),
        "volume_start_chapter": as_int(
            position.get("volume_start_chapter"), f"{label}.volume_start_chapter", minimum=1
        ),
        "story_time": clean_text(position.get("story_time"), f"{label}.story_time", max_bytes=240),
        "scene": clean_text(position.get("scene"), f"{label}.scene", max_bytes=240),
    }


def joined_text(value: object) -> object:
    """單句字段寫成了字符串列表時按「；」連成一句，內容不丟。"""
    if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
        return "；".join(value)
    return value


def as_text_list(value: object) -> object:
    """列表字段只寫了一句時當作一項。"""
    return [value] if isinstance(value, str) and value.strip() else value


def normalize_snapshot(value: object, label: str) -> dict[str, Any]:
    snapshot = as_mapping(value, label)
    snapshot = {key: joined_text(item) if key in SNAPSHOT_TEXT_FIELDS else as_text_list(item)
                if key in SNAPSHOT_LIST_FIELDS else item for key, item in snapshot.items()}
    require_known_keys(
        snapshot,
        {"identity", "location", "goal", "state", "abilities_resources", "relationships", "knowledge", "open_threads"},
        label,
    )
    return {
        "identity": clean_text(snapshot.get("identity"), f"{label}.identity", max_bytes=240),
        "location": clean_text(snapshot.get("location"), f"{label}.location", max_bytes=240),
        "goal": clean_text(snapshot.get("goal"), f"{label}.goal", max_bytes=300),
        "state": clean_text(snapshot.get("state"), f"{label}.state", max_bytes=300),
        "abilities_resources": clean_string_list(
            snapshot.get("abilities_resources", []),
            f"{label}.abilities_resources",
            item_max_bytes=SNAPSHOT_ITEM_MAX_BYTES,
        ),
        "relationships": clean_string_list(
            snapshot.get("relationships", []),
            f"{label}.relationships",
            item_max_bytes=SNAPSHOT_ITEM_MAX_BYTES,
        ),
        "knowledge": clean_string_list(
            snapshot.get("knowledge", []),
            f"{label}.knowledge",
            item_max_bytes=SNAPSHOT_ITEM_MAX_BYTES,
        ),
        "open_threads": clean_string_list(
            snapshot.get("open_threads", []),
            f"{label}.open_threads",
            item_max_bytes=SNAPSHOT_ITEM_MAX_BYTES,
        ),
    }


def normalize_snapshots(value: object, label: str = "character_snapshots") -> dict[str, dict[str, Any]]:
    snapshots = as_mapping(value, label)
    normalized: dict[str, dict[str, Any]] = {}
    portable_names: set[str] = set()
    for raw_name, raw_snapshot in snapshots.items():
        name = safe_file_component(raw_name, f"{label} character name")
        key = portable_name_key(name)
        require(key not in portable_names, f"{label} contains a cross-platform duplicate character {name}")
        portable_names.add(key)
        normalized[name] = normalize_snapshot(raw_snapshot, f"{label}.{name}")
    return normalized


def render_snapshot(name: str, snapshot: dict[str, Any], through_chapter: int, revision: int) -> str:
    def section(title: str, values: list[str]) -> list[str]:
        return [f"## {title}", *(f"- {item}" for item in values or ["無"]), ""]

    lines = [
        f"# {name}｜當前狀態",
        "",
        f"- 狀態修訂：{revision}",
        f"- 截至章節：第{through_chapter}章",
        f"- 身份：{snapshot['identity']}",
        f"- 位置：{snapshot['location']}",
        f"- 當前目標：{snapshot['goal']}",
        f"- 身心狀態：{snapshot['state']}",
        "",
    ]
    lines.extend(section("能力與資源", snapshot["abilities_resources"]))
    lines.extend(section("關鍵關係", snapshot["relationships"]))
    lines.extend(section("已知信息", snapshot["knowledge"]))
    lines.extend(section("未結事項", snapshot["open_threads"]))
    payload = "\n".join(lines).rstrip() + "\n"
    size = byte_size(payload)
    if size > SNAPSHOT_MAX_BYTES:
        allowed = max(1, SNAPSHOT_MAX_BYTES * len(payload) // size)
        counts = "、".join(
            f"{title} {len(values)} 項"
            for title, values in (
                ("能力與資源", snapshot["abilities_resources"]),
                ("關鍵關係", snapshot["relationships"]),
                ("已知信息", snapshot["knowledge"]),
                ("未結事項", snapshot["open_threads"]),
            )
        )
        raise TrackingError(
            f"character snapshot {name} ({size} bytes) exceeds hard cap of {SNAPSHOT_MAX_BYTES} bytes"
            f"（現 {len(payload)} 字，上限約 {allowed} 字，至少精簡 {len(payload) - allowed} 字；"
            f"當前：{counts}。逐章經過已留在 逐章記錄/，快照只保留截至當前章仍有效的狀態與條目）"
        )
    return payload


def normalize_foreshadow_change(
    value: object,
    label: str,
    *,
    allow_delete: bool,
    through_chapter: int,
) -> dict[str, Any]:
    row = with_aliases(as_mapping(value, label), FORESHADOW_KEY_ALIASES)
    require_known_keys(
        row,
        {"action", "id", "summary", "planted_chapter", "planned_resolution_chapter", "status", "importance"},
        label,
    )
    raw_action = row.get("action", "upsert")
    action = normalize_action(raw_action, f"{label}.action", allow_delete=allow_delete)
    identifier = clean_text(row.get("id"), f"{label}.id", max_bytes=24)
    require(FORESHADOW_ID.fullmatch(identifier) is not None, f"{label}.id must look like F001")
    if action == "delete":
        return {"action": action, "id": identifier}
    implied = FORESHADOW_ACTION_STATUS.get(" ".join(str(raw_action).split()).lower())
    if implied is not None:
        if row.get("status") in (None, ""):
            row["status"] = implied
        right = "回收了就寫 status=已回收" if implied == "已回收" else "只是推進、還沒回收就寫 status=已埋"
        require(
            row["status"] == implied,
            f"{label}.action={raw_action} 與 status={row['status']} 矛盾：{right}；"
            "不是這個意思就把 action 改成 upsert 並寫實際狀態",
        )
    planted_chapter = as_chapter(row.get("planted_chapter"), f"{label}.planted_chapter")
    require(planted_chapter <= through_chapter, f"{label}.planted_chapter cannot be in the future")
    planned_raw = row.get("planned_resolution_chapter")
    planned_chapter = (
        None if planned_raw in (None, "") else as_chapter(planned_raw, f"{label}.planned_resolution_chapter")
    )
    require(
        planned_chapter is None or planned_chapter >= planted_chapter,
        f"{label}.planned_resolution_chapter cannot precede planted_chapter",
    )
    status = clean_text(row.get("status"), f"{label}.status", max_bytes=24)
    importance = clean_text(row.get("importance"), f"{label}.importance", max_bytes=12)
    require(status in FORESHADOW_STATUSES, f"{label}.status must be one of {FORESHADOW_STATUSES}")
    require(importance in FORESHADOW_IMPORTANCE, f"{label}.importance must be one of {FORESHADOW_IMPORTANCE}")
    return {
        "action": action,
        "id": identifier,
        "summary": clean_text(row.get("summary"), f"{label}.summary", max_bytes=360),
        "planted_chapter": planted_chapter,
        "planned_resolution_chapter": planned_chapter,
        "status": status,
        "importance": importance,
    }


def normalize_foreshadow_state(value: object, last_chapter: int) -> dict[str, dict[str, Any]]:
    rows = as_mapping(value, "tracking state.foreshadow")
    normalized: dict[str, dict[str, Any]] = {}
    for raw_identifier, raw_row in rows.items():
        identifier = clean_text(raw_identifier, "tracking state.foreshadow ID", max_bytes=24)
        row = as_mapping(raw_row, f"tracking state.foreshadow.{identifier}")
        require_known_keys(
            row,
            {"id", "summary", "planted_chapter", "planned_resolution_chapter", "status", "importance", "updated_chapter"},
            f"tracking state.foreshadow.{identifier}",
        )
        require(row.get("id") == identifier, f"tracking state.foreshadow.{identifier}.id does not match its key")
        change = normalize_foreshadow_change(
            {
                "action": "upsert",
                **{key: value for key, value in row.items() if key != "updated_chapter"},
            },
            f"tracking state.foreshadow.{identifier}",
            allow_delete=False,
            through_chapter=last_chapter,
        )
        change.pop("action")
        updated = as_int(row.get("updated_chapter"), f"tracking state.foreshadow.{identifier}.updated_chapter", minimum=1)
        require(updated <= last_chapter, f"foreshadow {identifier} updates after current chapter")
        change["updated_chapter"] = updated
        normalized[identifier] = change
    return normalized


def render_foreshadow(rows: dict[str, dict[str, Any]], revision: int) -> str:
    lines = [
        "# 伏筆當前狀態",
        "",
        f"> 狀態修訂：{revision}。每個 ID 只保留一行當前狀態；歷史變化見 `逐章記錄/`。",
        "",
        "| ID | 內容 | 埋設章 | 計划回收章 | 狀態 | 重要度 | 最近變更章 |",
        "|---|---|---:|---:|---|---|---:|",
    ]
    for identifier in sorted(rows):
        row = rows[identifier]
        planned = f"第{row['planned_resolution_chapter']}章" if row["planned_resolution_chapter"] else "—"
        lines.append(
            f"| {identifier} | {row['summary']} | 第{row['planted_chapter']}章 | {planned} | "
            f"{row['status']} | {row['importance']} | 第{row['updated_chapter']}章 |"
        )
    return "\n".join(lines) + "\n"


def normalize_timeline_change(
    value: object,
    label: str,
    *,
    allow_delete: bool,
    through_chapter: int,
) -> dict[str, Any]:
    event = with_aliases(as_mapping(value, label), TIMELINE_KEY_ALIASES)
    require_known_keys(
        event,
        {"action", "id", "story_time", "objective_fact", "reader_knowledge", "reveal_status", "reveal_chapter", "characters"},
        label,
    )
    action = normalize_action(event.get("action", "upsert"), f"{label}.action", allow_delete=allow_delete)
    identifier = clean_text(event.get("id"), f"{label}.id", max_bytes=24)
    require(EVENT_ID.fullmatch(identifier) is not None, f"{label}.id must look like E001")
    if action == "delete":
        return {"action": action, "id": identifier}
    reveal_status = clean_text(event.get("reveal_status"), f"{label}.reveal_status", max_bytes=24)
    require(reveal_status in REVEAL_STATUSES, f"{label}.reveal_status must be one of {REVEAL_STATUSES}")
    reveal_raw = event.get("reveal_chapter")
    reveal_chapter = None if reveal_raw in (None, "") else as_chapter(reveal_raw, f"{label}.reveal_chapter")
    if reveal_status == "未揭示":
        require(reveal_chapter is None, f"{label} must not put a future reveal chapter in established timeline facts")
    else:
        require(reveal_chapter is not None, f"{label}.reveal_chapter is required once revealed")
        require(reveal_chapter <= through_chapter, f"{label}.reveal_chapter cannot be in the future")
    return {
        "action": action,
        "id": identifier,
        "story_time": clean_text(event.get("story_time"), f"{label}.story_time", max_bytes=240),
        "objective_fact": clean_text(event.get("objective_fact"), f"{label}.objective_fact", max_bytes=480),
        "reader_knowledge": clean_text(event.get("reader_knowledge"), f"{label}.reader_knowledge", max_bytes=480),
        "reveal_status": reveal_status,
        "reveal_chapter": reveal_chapter,
        "characters": clean_string_list(event.get("characters", []), f"{label}.characters", maximum=12, item_max_bytes=120),
    }


def normalize_timeline_state(value: object, last_chapter: int) -> dict[str, dict[str, Any]]:
    events = as_mapping(value, "tracking state.timeline")
    normalized: dict[str, dict[str, Any]] = {}
    for raw_identifier, raw_event in events.items():
        identifier = clean_text(raw_identifier, "tracking state.timeline ID", max_bytes=24)
        event = as_mapping(raw_event, f"tracking state.timeline.{identifier}")
        require_known_keys(
            event,
            {
                "id", "story_time", "objective_fact", "reader_knowledge", "reveal_status", "reveal_chapter",
                "characters", "first_recorded_chapter", "updated_chapter",
            },
            f"tracking state.timeline.{identifier}",
        )
        require(event.get("id") == identifier, f"tracking state.timeline.{identifier}.id does not match its key")
        change = normalize_timeline_change(
            {
                "action": "upsert",
                **{
                    key: value
                    for key, value in event.items()
                    if key not in {"first_recorded_chapter", "updated_chapter"}
                },
            },
            f"tracking state.timeline.{identifier}",
            allow_delete=False,
            through_chapter=last_chapter,
        )
        change.pop("action")
        first = as_int(event.get("first_recorded_chapter"), f"tracking state.timeline.{identifier}.first_recorded_chapter", minimum=1)
        updated = as_int(event.get("updated_chapter"), f"tracking state.timeline.{identifier}.updated_chapter", minimum=1)
        require(first <= last_chapter, f"timeline event {identifier} starts after current chapter")
        require(updated <= last_chapter, f"timeline event {identifier} updates after current chapter")
        change["first_recorded_chapter"] = first
        change["updated_chapter"] = updated
        normalized[identifier] = change
    return normalized


def render_timeline_views(events: dict[str, dict[str, Any]], revision: int) -> tuple[str, str]:
    author_lines = [
        "# 作者真相時間線",
        "",
        f"> 狀態修訂：{revision}。客觀事實與讀者認知的權威對照；未來揭示計划仍留在大綱。",
        "",
        "| ID | 首次登記章 | 故事時間 | 客觀事實 | 讀者當前認知 | 揭示狀態 | 實際揭示章 |",
        "|---|---:|---|---|---|---|---:|",
    ]
    reader_lines = [
        "# 讀者已知時間線",
        "",
        f"> 狀態修訂：{revision}。只呈現讀者截至當前章節已經知道或相信的內容，不泄露作者側客觀真相。",
        "",
        "| ID | 讀者當前認知 | 認知截至章 |",
        "|---|---|---:|",
    ]
    for identifier in sorted(events):
        event = events[identifier]
        reveal = f"第{event['reveal_chapter']}章" if event.get("reveal_chapter") else "—"
        characters = "、".join(event.get("characters", []))
        objective = event["objective_fact"] + (f"（涉及：{characters}）" if characters else "")
        author_lines.append(
            f"| {identifier} | 第{event['first_recorded_chapter']}章 | {event['story_time']} | {objective} | "
            f"{event['reader_knowledge']} | {event['reveal_status']} | {reveal} |"
        )
        reader_lines.append(f"| {identifier} | {event['reader_knowledge']} | 第{event['updated_chapter']}章 |")
    return "\n".join(author_lines) + "\n", "\n".join(reader_lines) + "\n"


def validate_context_input(value: object, *, include_initial_fields: bool) -> dict[str, Any]:
    context = as_mapping(value, "context")
    allowed = {"position", "long_term_constraints", "active_character_names", "continuity_risks"}
    if include_initial_fields:
        allowed.update({"recent_chapters", "next_chapter_commitments"})
    require_known_keys(context, allowed, "context")
    normalized: dict[str, Any] = {
        "position": validate_position(context.get("position")),
        "long_term_constraints": clean_string_list(
            context.get("long_term_constraints", []), "context.long_term_constraints", maximum=6
        ),
        "active_character_names": [
            safe_file_component(name, f"context.active_character_names[{index}]")
            for index, name in enumerate(as_list(context.get("active_character_names", []), "context.active_character_names"))
        ],
        "continuity_risks": clean_string_list(
            context.get("continuity_risks", []), "context.continuity_risks", maximum=5
        ),
    }
    require(
        len(normalized["active_character_names"]) <= ACTIVE_CHARACTER_MAX,
        f"context.active_character_names may contain at most {ACTIVE_CHARACTER_MAX} names",
    )
    require(
        len({portable_name_key(name) for name in normalized["active_character_names"]})
        == len(normalized["active_character_names"]),
        "context.active_character_names contains cross-platform duplicates",
    )
    if include_initial_fields:
        recent: list[dict[str, Any]] = []
        for index, raw_item in enumerate(as_list(context.get("recent_chapters", []), "context.recent_chapters")):
            item = as_mapping(raw_item, f"context.recent_chapters[{index}]")
            require_known_keys(item, {"chapter", "summary"}, f"context.recent_chapters[{index}]")
            recent.append(
                {
                    "chapter": as_int(item.get("chapter"), f"context.recent_chapters[{index}].chapter", minimum=1),
                    "summary": clean_text(item.get("summary"), f"context.recent_chapters[{index}].summary", max_bytes=360),
                }
            )
        require(len(recent) <= 3, "context.recent_chapters may contain at most 3 items")
        normalized["recent_chapters"] = recent
        normalized["next_chapter_commitments"] = clean_string_list(
            context.get("next_chapter_commitments", []), "context.next_chapter_commitments", maximum=5
        )
    return normalized


def active_foreshadow_lines(rows: dict[str, dict[str, Any]]) -> list[str]:
    importance = {value: index for index, value in enumerate(FORESHADOW_IMPORTANCE)}
    candidates = [row for row in rows.values() if row["status"] == "已埋"]
    candidates.sort(
        key=lambda row: (importance[row["importance"]], row["planned_resolution_chapter"] or 10**12, row["id"])
    )
    result = []
    for row in candidates[:8]:
        planned = f"第{row['planned_resolution_chapter']}章" if row["planned_resolution_chapter"] else "回收章未定"
        result.append(f"{row['id']}｜{row['summary']}｜埋第{row['planted_chapter']}章｜{planned}｜{row['importance']}")
    return result


def render_context(state: dict[str, Any]) -> str:
    context = state["context"]
    position = context["position"]
    current_chapter = (
        "尚未開篇" if state["last_committed_chapter"] == 0 else f"第{state['last_committed_chapter']}章"
    )
    character_lines = [
        f"{name}｜{state['characters'][name]['identity']}｜{state['characters'][name]['state']}｜"
        f"目標：{state['characters'][name]['goal']}"
        for name in context["active_character_names"]
    ]
    sections: list[tuple[str, list[str]]] = [
        (
            "## 當前位置",
            [
                f"當前章：{current_chapter}",
                f"卷：{position['volume']}（始於第{position['volume_start_chapter']}章）",
                f"故事時間：{position['story_time']}",
                f"場景：{position['scene']}",
            ],
        ),
        ("## 長期約束", context["long_term_constraints"]),
        ("## 核心角色狀態", character_lines),
        ("## 活躍伏筆", active_foreshadow_lines(state["foreshadow"])),
        ("## 近三章速記", [f"第{item['chapter']}章｜{item['summary']}" for item in context["recent_chapters"]]),
        ("## 下一章承諾", context["next_chapter_commitments"]),
        ("## 連貫性風險", context["continuity_risks"]),
    ]
    lines = [
        f"# 寫作連續性上下文 — {state['book_title']}",
        "",
        f"> 狀態修訂：{state['state_revision']}。截至當前章的續寫狀態卡，只放下一章真正需要的連續性狀態。",
        "",
    ]
    for heading, values in sections:
        lines.append(heading)
        lines.extend(f"- {value}" for value in values or ["無"])
        lines.append("")
    payload = "\n".join(lines).rstrip() + "\n"
    headings = tuple(line for line in payload.splitlines() if line.startswith("## "))
    require(headings == CONTEXT_HEADINGS, "generated context headings do not match the seven-section schema")
    require(byte_size(payload) <= CONTEXT_MAX_BYTES, f"hot context exceeds {CONTEXT_MAX_BYTES} bytes")
    return payload


def normalize_delta(
    value: object,
    *,
    through_chapter: int,
    snapshots: dict[str, dict[str, Any]],
    existing_core_names: dict[str, str],
) -> dict[str, Any]:
    delta = as_mapping(value, "delta")
    require_known_keys(
        delta,
        {
            "result", "character_changes", "foreshadow_changes", "timeline_events", "constraints",
            "next_chapter_commitments", "retired_context_items", "retired_characters",
        },
        "delta",
    )
    retired_characters = [
        safe_file_component(name, f"delta.retired_characters[{index}]")
        for index, name in enumerate(as_list(delta.get("retired_characters", []), "delta.retired_characters"))
    ]
    retired_keys = [portable_name_key(name) for name in retired_characters]
    require(len(retired_keys) == len(set(retired_keys)), "delta.retired_characters contains duplicate characters")
    retiring = set(retired_keys)
    character_changes: list[dict[str, Any]] = []
    for index, raw_change in enumerate(as_list(delta.get("character_changes", []), "delta.character_changes")):
        change = as_mapping(raw_change, f"delta.character_changes[{index}]")
        require_known_keys(change, {"name", "change"}, f"delta.character_changes[{index}]")
        name = safe_file_component(change.get("name"), f"delta.character_changes[{index}].name")
        existing = existing_core_names.get(portable_name_key(name))
        is_core = name in snapshots or existing is not None
        # 本章退役的角色記錄最後一次變化即可，不必再交一份馬上要刪的快照。
        require(
            not is_core or name in snapshots or portable_name_key(name) in retiring,
            f"core character {name} changed but has no current snapshot: 把 draft 輸出 current_snapshots"
            f"（或 snapshot_files 里的 {name}.json）中「{name}」的快照整份改成本章結束時的狀態，放進 character_snapshots",
        )
        character_changes.append(
            {"name": name, "change": clean_text(change.get("change"), f"delta.character_changes[{index}].change", max_bytes=360)}
        )
    character_keys = [portable_name_key(item["name"]) for item in character_changes]
    require(len(character_keys) == len(set(character_keys)), "delta.character_changes contains duplicate characters")
    foreshadow_changes = [
        normalize_foreshadow_change(
            raw, f"delta.foreshadow_changes[{index}]", allow_delete=True, through_chapter=through_chapter
        )
        for index, raw in enumerate(as_list(delta.get("foreshadow_changes", []), "delta.foreshadow_changes"))
    ]
    timeline_events = [
        normalize_timeline_change(
            raw, f"delta.timeline_events[{index}]", allow_delete=True, through_chapter=through_chapter
        )
        for index, raw in enumerate(as_list(delta.get("timeline_events", []), "delta.timeline_events"))
    ]
    require(
        len({item["id"] for item in foreshadow_changes}) == len(foreshadow_changes),
        "delta.foreshadow_changes contains duplicate IDs",
    )
    require(
        len({item["id"] for item in timeline_events}) == len(timeline_events),
        "delta.timeline_events contains duplicate IDs",
    )
    require(
        set(snapshots).issubset({item["name"] for item in character_changes}),
        "character_snapshots must contain exactly the core characters changed by this transaction",
    )
    return {
        "result": clean_text(delta.get("result"), "delta.result", max_bytes=480),
        "character_changes": character_changes,
        "foreshadow_changes": foreshadow_changes,
        "timeline_events": timeline_events,
        "constraints": clean_string_list(delta.get("constraints", []), "delta.constraints", maximum=6),
        "next_chapter_commitments": clean_string_list(
            delta.get("next_chapter_commitments", []), "delta.next_chapter_commitments", maximum=5
        ),
        "retired_context_items": clean_string_list(
            delta.get("retired_context_items", []), "delta.retired_context_items", maximum=11
        ),
        "retired_characters": retired_characters,
    }


def render_commitments(commitments: list[str]) -> list[str]:
    # 常見情形一行用「；」連寫；有承諾原文自帶「；」時連寫就拆不回來，改成逐條縮進子項。
    if any("；" in item for item in commitments):
        return ["- 下一章承諾："] + [f"  - {item}" for item in commitments]
    return ["- 下一章承諾：" + ("；".join(commitments) or "無")]


def render_delta(chapter: int, title: str, delta: dict[str, Any], core_names: set[str]) -> str:
    lines = [
        f"# 第{chapter:03d}章 · {title}",
        f"- 結果：{delta['result']}",
        *render_commitments(delta["next_chapter_commitments"]),
        "",
        "## 角色變化",
    ]
    lines.extend(
        f"- {item['name']}｜{'核心' if item['name'] in core_names else '臨時'}｜{item['change']}"
        for item in delta["character_changes"]
    )
    if not delta["character_changes"]:
        lines.append("- 無")
    lines.extend(["", "## 伏筆變化"])
    for item in delta["foreshadow_changes"]:
        if item["action"] == "delete":
            lines.append(f"- {item['id']}｜刪除當前登記")
        else:
            planned = f"第{item['planned_resolution_chapter']}章" if item["planned_resolution_chapter"] else "未定"
            lines.append(f"- {item['id']}｜{item['status']}｜{item['summary']}｜回收{planned}")
    if not delta["foreshadow_changes"]:
        lines.append("- 無")
    lines.extend(["", "## 時間與揭示"])
    for item in delta["timeline_events"]:
        if item["action"] == "delete":
            lines.append(f"- {item['id']}｜刪除當前登記")
        else:
            lines.append(
                f"- {item['id']}｜{item['story_time']}｜事實：{item['objective_fact']}｜"
                f"讀者：{item['reader_knowledge']}｜{item['reveal_status']}"
            )
    if not delta["timeline_events"]:
        lines.append("- 無")
    lines.extend(["", "## 連貫性約束"])
    lines.extend(f"- {item}" for item in delta["constraints"])
    if not delta["constraints"]:
        lines.append("- 無")
    retired = delta.get("retired_context_items", []) + [
        f"角色狀態：{name}" for name in delta.get("retired_characters", [])
    ]
    if retired:
        # 退役條目在此留檔，續寫狀態卡收縮後仍可回查當初撤下了什麼。
        lines.extend(["", "## 本章退役登記"])
        lines.extend(f"- {item}" for item in retired)
    payload = "\n".join(lines) + "\n"
    size = byte_size(payload)
    if size > DELTA_MAX_BYTES:
        longest = sorted((line for line in lines if line.startswith("- ")), key=len, reverse=True)[:3]
        allowed = DELTA_MAX_BYTES * len(payload) // size
        raise TrackingError(
            f"chapter delta is {size} bytes; hard cap is {DELTA_MAX_BYTES}（逐章記錄現 {len(payload)} 字，"
            f"上限約 {allowed} 字，至少壓縮 {len(payload) - allowed} 字；最長几項："
            + "；".join(f"{line[2:18]}…（{len(line) - 2} 字）" for line in longest) + "）")
    return payload


def normalize_wordcount_records(value: object, last_chapter: int) -> dict[str, dict[str, Any]]:
    records = as_mapping(value, "tracking state.wordcount_records")
    normalized: dict[str, dict[str, Any]] = {}
    for raw_chapter, raw_record in records.items():
        require(isinstance(raw_chapter, str) and re.fullmatch(r"[1-9]\d*", raw_chapter) is not None,
                "wordcount record chapter key is invalid")
        chapter = int(raw_chapter)
        require(chapter <= last_chapter, "wordcount record exceeds last committed chapter")
        normalized[raw_chapter] = wordcount_value(wordcount_core.normalize_wordcount_record, raw_record)
    return normalized


def normalize_state(document: object) -> dict[str, Any]:
    root = as_mapping(document, "tracking state")
    require_known_keys(
        root,
        {
            "schema_version", "book_title", "last_committed_chapter", "imported_through_chapter",
            "state_revision", "context", "characters", "foreshadow", "timeline",
            "wordcount_records",
        },
        "tracking state",
    )
    require(root.get("schema_version") == TRACKING_SCHEMA_VERSION, "tracking state schema is unsupported")
    last_chapter = as_int(root.get("last_committed_chapter"), "tracking state.last_committed_chapter")
    imported_through = as_int(root.get("imported_through_chapter"), "tracking state.imported_through_chapter")
    require(imported_through <= last_chapter, "imported chapter cutoff exceeds current chapter")
    context = validate_context_input(root.get("context"), include_initial_fields=True)
    require(
        context["position"]["volume_start_chapter"] <= max(1, last_chapter),
        "context.position.volume_start_chapter is after the current writing position",
    )
    recent_numbers = [item["chapter"] for item in context["recent_chapters"]]
    require(recent_numbers == sorted(recent_numbers), "context.recent_chapters must be ordered")
    require(len(recent_numbers) == len(set(recent_numbers)), "context.recent_chapters contains duplicates")
    require(all(chapter <= last_chapter for chapter in recent_numbers), "context.recent_chapters cannot include future chapters")
    characters = normalize_snapshots(root.get("characters", {}), "tracking state.characters")
    for name in context["active_character_names"]:
        require(name in characters, f"active core character {name} has no current snapshot")
    foreshadow = normalize_foreshadow_state(root.get("foreshadow", {}), last_chapter)
    timeline = normalize_timeline_state(root.get("timeline", {}), last_chapter)
    if last_chapter == 0:
        require(not foreshadow, "a chapter-0 project cannot have planted foreshadow facts")
        require(not timeline, "a chapter-0 project cannot have established timeline facts")
    state_revision = as_int(root.get("state_revision"), "tracking state.state_revision")
    wordcount_records = normalize_wordcount_records(root.get("wordcount_records", {}), last_chapter)
    return {
        "schema_version": TRACKING_SCHEMA_VERSION,
        "book_title": clean_text(root.get("book_title"), "tracking state.book_title", max_bytes=240),
        "last_committed_chapter": last_chapter,
        "imported_through_chapter": imported_through,
        "state_revision": state_revision,
        "context": context,
        "characters": characters,
        "foreshadow": foreshadow,
        "timeline": timeline,
        "wordcount_records": wordcount_records,
    }


def load_state(project: Path) -> dict[str, Any]:
    path = state_path(project)
    require(path.exists(), "tracking state is missing; run init first")
    return normalize_state(read_json(path))


def normalize_initial_document(document: object) -> dict[str, Any]:
    issues: list[str] = []
    token = _LENGTH_ISSUES.set(issues)
    try:
        state_doc = _normalize_initial_document(document)
    finally:
        _LENGTH_ISSUES.reset(token)
    require(not issues, f"{len(issues)} 個字段超長，一次改完再提交：" + "；".join(issues))
    return normalize_state(state_doc)


def _normalize_initial_document(document: object) -> dict[str, Any]:
    root = as_mapping(document, "init input")
    require_known_keys(
        root,
        {
            "schema_version", "book_title", "last_chapter", "context", "character_snapshots",
            "foreshadow", "timeline_events",
        },
        "init input",
    )
    require(root.get("schema_version") == INPUT_SCHEMA_VERSION, "init input schema_version is unsupported")
    last_chapter = as_int(root.get("last_chapter"), "last_chapter")
    book_title = clean_text(root.get("book_title"), "book_title", max_bytes=240)
    context = validate_context_input(root.get("context"), include_initial_fields=True)
    snapshots = normalize_snapshots(root.get("character_snapshots", {}))
    foreshadow: dict[str, dict[str, Any]] = {}
    for index, raw_row in enumerate(as_list(root.get("foreshadow", []), "foreshadow")):
        row = normalize_foreshadow_change(
            raw_row, f"foreshadow[{index}]", allow_delete=False, through_chapter=last_chapter
        )
        require(row["id"] not in foreshadow, f"duplicate foreshadow ID {row['id']}")
        row.pop("action")
        row["updated_chapter"] = max(1, last_chapter)
        foreshadow[row["id"]] = row
    timeline: dict[str, dict[str, Any]] = {}
    for index, raw_event in enumerate(as_list(root.get("timeline_events", []), "timeline_events")):
        event = normalize_timeline_change(
            raw_event, f"timeline_events[{index}]", allow_delete=False, through_chapter=last_chapter
        )
        require(event["id"] not in timeline, f"duplicate timeline event ID {event['id']}")
        event.pop("action")
        event["first_recorded_chapter"] = max(1, last_chapter)
        event["updated_chapter"] = max(1, last_chapter)
        timeline[event["id"]] = event
    return {
        "schema_version": TRACKING_SCHEMA_VERSION,
        "book_title": book_title,
        "last_committed_chapter": last_chapter,
        "imported_through_chapter": last_chapter,
        "state_revision": 0,
        "context": context,
        "characters": snapshots,
        "foreshadow": foreshadow,
        "timeline": timeline,
        "wordcount_records": {},
    }


def normalize_transaction(project: Path, state: dict[str, Any], document: object) -> dict[str, Any]:
    issues: list[str] = []
    token = _LENGTH_ISSUES.set(issues)
    try:
        transaction = _normalize_transaction(project, state, document)
    finally:
        _LENGTH_ISSUES.reset(token)
    require(not issues, f"{len(issues)} 個字段超長，一次改完再提交：" + "；".join(issues))
    return transaction


# 本文件在 story-long-write / story-review / story-import 三份逐字相同；只有 story-long-write 帶 storyctl.py。
RECOUNT_HINT = ("修訂請用 story-long-write 的 storyctl.py chapter commit（帶外用 chapter accept-current-length）"
                "提交同一份事務，它會重新計數並清理本章工作目錄")


def _normalize_transaction(project: Path, state: dict[str, Any], document: object) -> dict[str, Any]:
    root = as_mapping(document, "transaction")
    require_known_keys(
        root,
        {
            "schema_version", "mode", "chapter", "chapter_title", "expected_state_revision",
            "delta", "context", "character_snapshots", "wordcount",
        },
        "transaction",
    )
    require(root.get("schema_version") == INPUT_SCHEMA_VERSION, "transaction schema_version is unsupported")
    mode = clean_text(root.get("mode"), "mode", max_bytes=24)
    require(mode in {"append", "revision"}, "mode must be append or revision")
    chapter = as_int(root.get("chapter"), "chapter", minimum=1)
    expected_revision = as_int(root.get("expected_state_revision"), "expected_state_revision")
    wordcount_input = root.get("wordcount")
    require(expected_revision == state["state_revision"], "tracking state changed since this transaction was prepared")
    last = state["last_committed_chapter"]
    if mode == "append":
        require(chapter == last + 1, f"append chapter must be {last + 1}, got {chapter}")
    else:
        require(chapter <= last, f"cannot revise unwritten chapter {chapter}; last committed chapter is {last}")
    context = validate_context_input(root.get("context"), include_initial_fields=False)
    snapshots = normalize_snapshots(root.get("character_snapshots", {}))
    existing_names = {portable_name_key(name): name for name in state["characters"]}
    for name in snapshots:
        existing = existing_names.get(portable_name_key(name))
        require(existing is None or existing == name, f"character {name} conflicts with existing character {existing}")
    through_chapter = chapter if mode == "append" else last
    delta = normalize_delta(
        root.get("delta"),
        through_chapter=through_chapter,
        snapshots=snapshots,
        existing_core_names=existing_names,
    )
    wordcount = None
    if wordcount_input is not None:
        wordcount = wordcount_value(
            wordcount_core.validate_current_wordcount_record, project, chapter, wordcount_input
        )
    elif mode == "revision" and str(chapter) in state["wordcount_records"]:
        # 已提交字數記錄的章節：去味、審稿改過正文或目標後的修訂，按現文件重新計數，記錄不留舊值。
        # 只核對記錄釘住的正文與目標；細綱事後補的「字數范圍」不算過期。
        previous = state["wordcount_records"][str(chapter)]
        try:
            drift = wordcount_core.wordcount_record_drift(project, chapter, previous)
        except wordcount_core.WordcountError as exc:
            raise TrackingError(f"第{chapter}章的字數記錄無法核對（{exc}）；{RECOUNT_HINT}") from exc
        if drift:
            wordcount = recount_revised_chapter(project, chapter, previous, drift)
    return {
        "mode": mode,
        "chapter": chapter,
        "title": clean_text(root.get("chapter_title"), "chapter_title", max_bytes=240),
        "delta": delta,
        "context": context,
        "snapshots": snapshots,
        "wordcount": wordcount,
    }


def recount_revised_chapter(project: Path, chapter: int, previous: dict[str, Any], drift: list[str]) -> dict[str, Any]:
    """改後仍在作者范圍內，或作者原先就接受了帶外長度且仍在帶外：直接按現文件記帳。
    原本在范圍內、改後出了范圍，才要作者拍板，交給 storyctl 的 accept-current-length。"""
    resolutions = ["within_user_band"]
    if previous["resolution"] == "accepted_current_length":
        resolutions.append("accepted_current_length")
    for resolution in resolutions:
        try:
            return wordcount_core.build_project_wordcount_record(
                project, chapter, resolution=resolution, author_range=previous.get("author_range"),
            )
        except wordcount_core.WordcountError:
            continue
    raise TrackingError(f"第{chapter}章{'和'.join(drift)}已改，字數出了作者范圍；{RECOUNT_HINT}")


def checkpoint_record(
    change: dict[str, Any], chapter: int, previous: dict[str, Any] | None, *, keep_first_chapter: bool = False
) -> dict[str, Any]:
    current = {key: value for key, value in change.items() if key != "action"}
    current["updated_chapter"] = max(previous["updated_chapter"] if previous else chapter, chapter)
    if keep_first_chapter:
        current["first_recorded_chapter"] = previous["first_recorded_chapter"] if previous else chapter
    return current


def merge_transaction(state: dict[str, Any], transaction: dict[str, Any]) -> dict[str, Any]:
    next_state = copy.deepcopy(state)
    chapter = transaction["chapter"]
    if transaction["mode"] == "append":
        next_state["last_committed_chapter"] = chapter
    next_state["state_revision"] += 1
    next_state["characters"].update(transaction["snapshots"])
    if transaction["wordcount"] is not None:
        next_state["wordcount_records"][str(chapter)] = transaction["wordcount"]

    next_context = transaction["context"]
    # 退役說的是「從此刻起離開當前狀態」，只有 append 的逐章記錄代表此刻；
    # 修訂記錄屬於被改寫的舊章，落在那里會謊報退役發生的章節。
    is_revision = transaction["mode"] == "revision"
    require(
        not (is_revision and transaction["delta"]["retired_characters"]),
        "retired_characters must be committed in an append transaction, not a revision",
    )
    for name in transaction["delta"]["retired_characters"]:
        require(name in next_state["characters"], f"retired character {name} has no current snapshot")
        require(
            name not in transaction["snapshots"],
            f"character {name} cannot be retired and updated in the same transaction",
        )
        require(
            name not in next_context["active_character_names"],
            f"retired character {name} is still listed in context.active_character_names",
        )
        next_state["characters"].pop(name)

    # 上下文條目是整份提交的；漏寫會靜默丟歷史裁定，因此掉落必須顯式聲明。
    previous_items = set(state["context"]["long_term_constraints"]) | set(state["context"]["continuity_risks"])
    dropped = previous_items - (set(next_context["long_term_constraints"]) | set(next_context["continuity_risks"]))
    require(
        not (is_revision and dropped),
        "a revision must resubmit every current context item; retire them in an append transaction instead: "
        + "；".join(sorted(dropped)),
    )
    kept = set(next_context["long_term_constraints"]) | set(next_context["continuity_risks"])
    still_listed = sorted(set(transaction["delta"]["retired_context_items"]) & kept)
    require(
        not still_listed,
        "delta.retired_context_items lists items that are still in context; remove them from context: "
        + "；".join(still_listed),
    )
    undeclared = sorted(dropped - set(transaction["delta"]["retired_context_items"]))
    require(
        not undeclared,
        "context items were dropped without being declared in delta.retired_context_items: "
        + "；".join(undeclared),
    )
    transaction["delta"]["retired_context_items"] = sorted(dropped)

    for change in transaction["delta"]["foreshadow_changes"]:
        if change["action"] == "delete":
            next_state["foreshadow"].pop(change["id"], None)
        else:
            next_state["foreshadow"][change["id"]] = checkpoint_record(
                change, chapter, next_state["foreshadow"].get(change["id"])
            )
    for change in transaction["delta"]["timeline_events"]:
        if change["action"] == "delete":
            next_state["timeline"].pop(change["id"], None)
        else:
            next_state["timeline"][change["id"]] = checkpoint_record(
                change, chapter, next_state["timeline"].get(change["id"]), keep_first_chapter=True
            )

    recent_by_chapter = {item["chapter"]: item for item in state["context"]["recent_chapters"]}
    if chapter in recent_by_chapter or transaction["mode"] == "append":
        recent_by_chapter[chapter] = {"chapter": chapter, "summary": transaction["delta"]["result"]}
    recent = sorted(recent_by_chapter.values(), key=lambda item: item["chapter"])[-3:]
    current_last = next_state["last_committed_chapter"]
    next_commitments = (
        transaction["delta"]["next_chapter_commitments"]
        if transaction["mode"] == "append" or chapter == current_last
        else state["context"]["next_chapter_commitments"]
    )
    next_state["context"] = {
        **next_context,
        "recent_chapters": recent,
        "next_chapter_commitments": next_commitments,
    }
    return normalize_state(next_state)


def render_views(state: dict[str, Any]) -> dict[str, str]:
    revision = state["state_revision"]
    views = {
        "context.md": render_context(state),
        "foreshadowing.md": render_foreshadow(state["foreshadow"], revision),
    }
    author, reader = render_timeline_views(state["timeline"], revision)
    views["timeline/author_truth.md"] = author
    views["timeline/reader_known.md"] = reader
    for name, snapshot in state["characters"].items():
        views[f"characters/{name}.md"] = render_snapshot(
            name, snapshot, state["last_committed_chapter"], revision
        )
    return views


def write_views(tracking: Path, views: dict[str, str]) -> None:
    # context.md carries next revision; write it first so any subsequent failure is caught by check.
    write_if_changed(tracking / "context.md", views["context.md"])
    for relative in sorted(path for path in views if path != "context.md"):
        write_if_changed(tracking / relative, views[relative])
    expected_character_files = {
        Path(relative).name for relative in views if relative.startswith("characters/")
    }
    character_dir = tracking / "characters"
    character_dir.mkdir(parents=True, exist_ok=True)
    for path in character_dir.glob("*.md"):
        if path.name not in expected_character_files:
            path.unlink()


def warn_sizes(views: dict[str, str], delta_payload: str | None = None) -> None:
    if delta_payload is not None and byte_size(delta_payload) > DELTA_TARGET_BYTES:
        emit(
            f"WARNING: chapter delta is {byte_size(delta_payload)} bytes; target is <= {DELTA_TARGET_BYTES}",
            error=True,
        )
    context_size = byte_size(views["context.md"])
    if context_size > CONTEXT_TARGET_BYTES:
        emit(f"WARNING: hot context is {context_size} bytes; target is <= {CONTEXT_TARGET_BYTES}", error=True)
    for relative, payload in views.items():
        if not relative.startswith("characters/"):
            continue
        size = byte_size(payload)
        if size > SNAPSHOT_TARGET_BYTES:
            target_chars = max(1, SNAPSHOT_TARGET_BYTES * len(payload) // size)
            emit(
                f"WARNING: character snapshot {Path(relative).stem} is {size} bytes; target is <= {SNAPSHOT_TARGET_BYTES}"
                f"（現 {len(payload)} 字，建議目標約 {target_chars} 字；不影響本次提交，"
                "後續更新時可將已了結事項或已被新狀態取代的舊階段歸並為當前值）",
                error=True,
            )


def _initialize_locked(project: Path, document: object) -> dict[str, Any]:
    tracking = tracking_root(project)
    require(not state_path(project).exists(), "tracking state already exists; init never overwrites project state")
    state = normalize_initial_document(document)
    views = render_views(state)
    state_payload = json_payload(state)

    # 輸入全部校驗通過後才動用戶文件，失敗的 init 不會挪走任何東西。
    archived = archive_retired_tracking_paths(tracking)
    for directory in (tracking / "logs", tracking / "characters", tracking / "timeline"):
        directory.mkdir(parents=True, exist_ok=True)
    write_views(tracking, views)
    atomic_write_text(state_path(project), state_payload)
    warn_sizes(views)
    if archived:
        emit(
            f"NOTE: 舊追蹤結構已原樣移入 tracking/{RETIRED_ARCHIVE_DIR}/：{', '.join(archived)}；"
            "當前狀態以本次 init 輸入為準，舊文件不參與解析。",
            error=True,
        )
    return state


def initialize(project: Path, document: object) -> dict[str, Any]:
    with project_write_lock(project):
        return _initialize_locked(project, document)


def _apply_transaction_locked(project: Path, document: object) -> dict[str, Any]:
    tracking = tracking_root(project)
    require_no_retired_tracking_paths(tracking)
    state = load_state(project)
    transaction = normalize_transaction(project, state, document)
    next_state = merge_transaction(state, transaction)
    path = delta_path(tracking, transaction["chapter"])
    previous_record = parse_chapter_record(path) if transaction["mode"] == "revision" else None
    if previous_record is not None:
        # 退役只在 append 發生；修訂重寫舊章記錄時把當初的退役登記原樣帶過來，不讓它隨修訂消失。
        transaction["delta"]["retired_context_items"] = previous_record["retired"]

    delta_payload = render_delta(
        transaction["chapter"],
        transaction["title"],
        transaction["delta"],
        # 本章退役的角色在 next_state 里已被刪除，但本章記錄里仍應標為核心。
        set(next_state["characters"]) | set(transaction["delta"]["retired_characters"]),
    )
    views = render_views(next_state)
    next_state_payload = json_payload(next_state)
    if transaction["mode"] == "append" and path.exists():
        require(
            path.read_text(encoding="utf-8") == delta_payload,
            f"chapter delta {transaction['chapter']} already exists with different content",
        )

    write_if_changed(path, delta_payload)
    write_views(tracking, views)
    # 唯一權威文件最後落盤；在此之前失敗可用同一事務直接重跑。
    atomic_write_text(state_path(project), next_state_payload)
    warn_sizes(views, delta_payload)
    warn_emptied_snapshots(state["characters"], transaction["snapshots"])
    if previous_record is not None:
        warn_emptied_record(transaction["chapter"], previous_record, transaction["delta"])
    return next_state


def warn_emptied_snapshots(
    previous_characters: dict[str, dict[str, Any]],
    updated_snapshots: dict[str, dict[str, Any]],
) -> None:
    labels = {
        "abilities_resources": "能力與資源",
        "relationships": "關鍵關係",
        "knowledge": "已知信息",
    }
    for name, updated in updated_snapshots.items():
        previous = previous_characters.get(name)
        if previous is None:
            continue
        emptied = [
            f"{label}（原有 {len(previous[key])} 項）"
            for key, label in labels.items()
            if previous.get(key) and not updated.get(key)
        ]
        if emptied:
            emit(
                f"WARNING: 角色快照「{name}」把 " + "、".join(emptied)
                + " 清空成了空列表；character_snapshots 提交的是角色完整當前狀態，不是只寫本章新增。"
                "若非有意清空，請從 draft 的 snapshot_files 讀回完整快照修改後重提。",
                error=True,
            )


def warn_emptied_record(chapter: int, previous: dict[str, Any], delta: dict[str, Any]) -> None:
    labels = {"character_changes": "角色變化", "foreshadow_changes": "伏筆變化", "timeline_events": "時間與揭示",
              "constraints": "連貫性約束", "next_chapter_commitments": "下一章承諾"}
    emptied = [f"{label}（原有 {len(previous[key])} 項）" for key, label in labels.items()
               if previous[key] and not delta[key]]
    if emptied:
        emit(f"WARNING: 第{chapter}章修訂把逐章記錄的 " + "、".join(emptied)
             + " 清空了；修訂的 delta 是本章完整記錄，不是只寫改動。不是有意刪除就用 draft 重新預填後再提交。", error=True)


def apply_transaction(project: Path, document: object) -> dict[str, Any]:
    with project_write_lock(project):
        return _apply_transaction_locked(project, document)


def check_project(project: Path) -> dict[str, Any]:
    tracking = tracking_root(project)
    require_no_retired_tracking_paths(tracking)
    state = load_state(project)
    last_chapter = state["last_committed_chapter"]
    required_delta_start = state["imported_through_chapter"] + 1
    for chapter in range(required_delta_start, last_chapter + 1):
        require(delta_path(tracking, chapter).exists(), f"chapter delta {chapter} is missing")
    for path in (tracking / "logs").glob("ch_*.md"):
        match = re.fullmatch(r"ch_(\d+)\.md", path.name)
        require(match is not None, f"chapter delta has an invalid filename: {path.name}")
        chapter = as_int(int(match.group(1)), f"chapter delta {path.name}", minimum=1)
        require(path == delta_path(tracking, chapter), f"chapter delta {chapter} filename is not canonical")
        require(chapter <= last_chapter, f"chapter delta {chapter} exceeds last_committed_chapter")
        require(path.stat().st_size <= DELTA_MAX_BYTES, f"chapter delta {chapter} exceeds {DELTA_MAX_BYTES} bytes")

    expected_views = render_views(state)
    for relative, expected in expected_views.items():
        path = tracking / relative
        require(path.exists(), f"derived view is missing: {relative}")
        require(
            path.read_text(encoding="utf-8") == expected,
            f"derived view differs from _tracking-state.json: {relative}",
        )
    expected_character_files = {
        Path(relative).name for relative in expected_views if relative.startswith("characters/")
    }
    actual_character_files = {path.name for path in (tracking / "characters").glob("*.md")}
    require(actual_character_files == expected_character_files, "character snapshot files differ from tracking state")
    return state


# 事務草稿里各文本字段的字數上限（按全中文估：UTF-8 每字 3 字節），寫進提示，免得模型反複試錯。
DRAFT_LIMITS = {
    "delta.result": 160, "character_changes[].change": 120, "foreshadow_changes[].summary": 120,
    "timeline_events[].objective_fact / reader_knowledge": 160, "context.position.story_time / scene": 80,
    "character_snapshots.*.identity / location": 80, "character_snapshots.*.goal / state": 100,
    "character_snapshots.*.四個列表單項": 200, "角色快照單文件": 21500, "逐章記錄總量": 1024,
}


RECORD_SECTIONS = {"角色變化": "character_changes", "伏筆變化": "foreshadow_changes",
                   "時間與揭示": "timeline_events", "連貫性約束": "constraints", "本章退役登記": "retired"}


def parse_chapter_record(path: Path) -> dict[str, Any] | None:
    """讀回本工具自己渲染的逐章記錄（render_delta 的固定格式），供修訂草稿預填與修訂提交核對。
    這是對自家確定性輸出的逆運算，不是解析手寫 Markdown；讀不到返回 None。"""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    record: dict[str, Any] = {"title": "", "result": "", "next_chapter_commitments": [],
                              **{key: [] for key in RECORD_SECTIONS.values()}}
    section = None
    in_commitments = False
    for line in text.splitlines():
        heading = re.match(r"^# 第\d+章 · (.+)$", line)
        if heading and not record["title"]:
            record["title"] = heading.group(1).strip()
            continue
        if line.startswith("## "):
            section = RECORD_SECTIONS.get(line[3:].strip())
            in_commitments = False
            continue
        if in_commitments and line.startswith("  - "):
            record["next_chapter_commitments"].append(line[4:])
            continue
        in_commitments = False
        if not line.startswith("- "):
            continue
        item = line[2:]
        if section is None:
            if item.startswith("結果："):
                record["result"] = item[len("結果："):]
            elif item.startswith("下一章承諾："):
                value = item[len("下一章承諾："):]
                # 空值 = 逐條子項格式（render_commitments），後面的縮進行逐條讀回。
                in_commitments = value == ""
                record["next_chapter_commitments"] = [] if value in ("無", "") else value.split("；")
            continue
        if item == "無" and section != "retired":
            continue
        record[section].append(item)
    return record


def record_prefill(state: dict[str, Any], record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """把已提交的逐章記錄還原成修訂 delta：結果、承諾、約束、角色變化按記錄原文；伏筆與時間線
    取受影響 ID 的當前值（修訂提交的就是截至最新章的當前值）。另返回記錄里核心角色的當前快照。"""
    notes: list[str] = []
    changes = []
    for line in record["character_changes"]:
        parts = line.split("｜", 2)
        if len(parts) == 3:
            changes.append({"name": parts[0], "change": parts[2]})
    snapshots = {item["name"]: copy.deepcopy(state["characters"][item["name"]])
                 for item in changes if item["name"] in state["characters"]}

    def rows(lines: list[str], current: dict[str, Any], label: str) -> list[dict[str, Any]]:
        prefilled = []
        for line in lines:
            parts = line.split("｜")
            identifier = parts[0]
            if len(parts) > 1 and parts[1] == "刪除當前登記":
                if identifier in current:
                    notes.append(f"{label} {identifier} 本章刪過、後來又登記了，沒有預填刪除，確需刪除自行加回")
                else:
                    prefilled.append({"action": "delete", "id": identifier})
            elif identifier in current:
                prefilled.append({"action": "upsert", **{key: copy.deepcopy(value) for key, value in current[identifier].items()
                                                         if key not in ("updated_chapter", "first_recorded_chapter")}})
            else:
                notes.append(f"{label} {identifier} 已在後續章節刪除，沒有預填")
        return prefilled

    delta = {
        "result": record["result"],
        "character_changes": changes,
        "foreshadow_changes": rows(record["foreshadow_changes"], state["foreshadow"], "伏筆"),
        "timeline_events": rows(record["timeline_events"], state["timeline"], "時間線事件"),
        "constraints": list(record["constraints"]),
        "next_chapter_commitments": list(record["next_chapter_commitments"]),
    }
    return delta, snapshots, notes


def entry_shapes(chapter: int) -> dict[str, Any]:
    """draft 當場給出每類條目的形狀：模型填 delta 時手裡只有空數組，字段名、整數、枚舉都靠猜，
    首次提交几乎都因此被退回。取值從校驗用的同一組常量生成，不另立一套。"""
    return {
        "delta.character_changes[]": {"name": "角色名", "change": "一句話：本章起了什麼變化"},
        "delta.foreshadow_changes[]": {
            "action": "upsert（撤掉整條寫 delete，只帶 id）", "id": "F007", "summary": "伏筆一句話",
            "planted_chapter": chapter, "planned_resolution_chapter": "計划回收章的整數，未定寫 null",
            "status": "|".join(FORESHADOW_STATUSES), "importance": "|".join(FORESHADOW_IMPORTANCE),
        },
        "delta.timeline_events[]": {
            "action": "upsert（撤掉整條寫 delete，只帶 id）", "id": "E012", "story_time": "故事內時間",
            "objective_fact": "客觀發生了什麼", "reader_knowledge": "讀者此刻知道/以為什麼",
            "reveal_status": "|".join(REVEAL_STATUSES),
            "reveal_chapter": f"已揭示或部分揭示時寫揭示章的整數（不晚於 {chapter}），未揭示寫 null",
            "characters": ["角色名"],
        },
        "character_snapshots.{角色名}": {
            **{key: "一句話" for key in SNAPSHOT_TEXT_FIELDS},
            **{key: ["一條一句"] for key in SNAPSHOT_LIST_FIELDS},
        },
    }


def draft_transaction(
    project: Path, chapter: int, *, state: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """按當前 state 預填一份逐章事務：修訂號、模式、章名和整份提交的上下文當前值都填好。
    新章（append）調用方只寫本章變化；另返回在場核心角色的當前快照，供有變化時整份改寫後放進事務。
    新章的故事時間與場景留空：它們必須是本章結束時的位置，沿用上一章的值能靜默提交，
    所以不預填，上一章的值另行返回作參考。
    修訂（revision）的 delta 是修訂後本章的完整記錄，所以按已提交的逐章記錄預填，調用方在上面改；
    第三項返回 {"notes": [...], "prefilled": bool}：沒能預填的條目，以及逐章記錄是否讀到。"""
    if state is None:
        state = load_state(project)
    last = state["last_committed_chapter"]
    require(1 <= chapter <= last + 1, f"draft chapter must be between 1 and {last + 1}")
    mode = "append" if chapter == last + 1 else "revision"
    title = ""
    outline_candidates = [
        *sorted((project / "outlines").glob(f"ch_{chapter:03d}*.md")),
        *sorted((project / "大綱").glob(f"細綱_第{chapter:03d}章*.md")),
    ]
    for outline in outline_candidates:
        match = re.search(
            rf"^#{{1,4}}\s*(?:Chapter\s*0*{chapter}|第\s*0*{chapter}\s*章)(?:\s+Outline|\s*細綱)?\s*(?:[：:—\-]\s*(.+?))?\s*$",
            outline.read_text(encoding="utf-8"),
            re.M | re.I,
        )
        if match and match.group(1):
            title = match.group(1).strip()
            break
    context = json.loads(json.dumps(state["context"], ensure_ascii=False))
    previous_position = {key: context["position"][key] for key in ("story_time", "scene")}
    delta: dict[str, Any] = {
        "result": "", "character_changes": [], "foreshadow_changes": [], "timeline_events": [],
        "constraints": [], "next_chapter_commitments": [],
    }
    snapshots_prefill: dict[str, Any] = {}
    notes: list[str] = []
    prefilled = False
    if mode == "append":
        delta.update({"retired_context_items": [], "retired_characters": []})
        context["position"].update({"story_time": "", "scene": ""})
    else:
        record = parse_chapter_record(delta_path(tracking_root(project), chapter))
        if record is not None:
            prefilled = True
            delta, snapshots_prefill, notes = record_prefill(state, record)
            title = title or record["title"]
            if chapter == last:
                # 最新章的承諾原樣在 state 里，比從記錄行按「；」拆回更準。
                delta["next_chapter_commitments"] = list(state["context"]["next_chapter_commitments"])
    document = {
        "schema_version": INPUT_SCHEMA_VERSION,
        "mode": mode,
        "chapter": chapter,
        "chapter_title": title,
        "expected_state_revision": state["state_revision"],
        "delta": delta,
        "context": {key: context[key] for key in
                    ("position", "long_term_constraints", "active_character_names", "continuity_risks")},
        "character_snapshots": snapshots_prefill,
    }
    snapshots = {name: state["characters"][name] for name in context["active_character_names"]
                 if name in state["characters"]}
    if mode == "revision":
        return document, snapshots, {"notes": notes, "prefilled": prefilled}
    return document, snapshots, previous_position


def rebuild_stale_draft(document: dict[str, Any], existing: dict[str, Any], append: bool,
                        current_characters: Any = ()) -> str:
    """修訂號變了：中間提交過別的事務。以當前狀態為底，只自動合並確定安全的部分，其余列給調用方核對。

    新章草稿之間只可能插進修訂事務，修訂不能刪約束與風險條目，所以當前約束與風險覆蓋舊底稿：
    舊草稿多出來的就是本章新增，delta 里聲明退役的就是本章刪除，可以精確合並。
    修訂草稿之間可能插進新章（新章能退役條目），在場角色名修訂也能刪，都無法判斷誰新：
    取當前狀態，差異列出來；只有本章帶了快照的新角色名自動加回。"""
    def items(value: object) -> list[str]:
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []

    def norm(item: str) -> str:
        return " ".join(item.replace("|", "｜").split())

    notes = ["修訂號已變：context 按當前狀態重建，本章已填的 delta" + ("、新增與退役的約束、結尾位置" if append else "")
             + "已合並"]
    for key in ("delta", "character_snapshots"):
        if isinstance(existing.get(key), dict):
            document[key] = existing[key]
    if existing.get("chapter_title"):
        document["chapter_title"] = existing["chapter_title"]
    old_context = existing.get("context") if isinstance(existing.get("context"), dict) else {}
    delta = document["delta"] if isinstance(document["delta"], dict) else {}
    context = document["context"]
    retired = {norm(item) for item in items(delta.get("retired_context_items"))}
    left_out: list[str] = []
    for key in ("long_term_constraints", "continuity_risks"):
        current = {norm(item) for item in context[key]}
        extra = []
        for item in items(old_context.get(key)):
            if norm(item) not in current:
                current.add(norm(item))
                extra.append(item)
        if append:
            context[key] = [item for item in context[key] if norm(item) not in retired] + extra
        else:
            left_out += extra
    snapshots = document["character_snapshots"] if isinstance(document["character_snapshots"], dict) else {}
    names = context["active_character_names"]
    for name in items(old_context.get("active_character_names")):
        if name in names:
            continue
        if append and name in snapshots:
            names.append(name)
        else:
            left_out.append(f"在場角色 {name}")
    names[:] = [name for name in names if name not in set(items(delta.get("retired_characters")))]
    known = set(current_characters)
    for name in list(snapshots):
        if name not in known and name not in names:
            snapshots.pop(name)
            left_out.append(f"角色快照 {name}")
    if left_out:
        notes.append("草稿里有、當前狀態沒有的條目沒有自動帶回（可能已被別的提交退役），本章確實需要就加回："
                     + "；".join(left_out))
    old_position = old_context.get("position") if isinstance(old_context.get("position"), dict) else {}
    position = context["position"]
    if append:
        for key in ("story_time", "scene"):
            if isinstance(old_position.get(key), str) and old_position[key].strip():
                position[key] = old_position[key]
    differs = [f"{key}：草稿寫的是「{old_position[key]}」，當前狀態是「{position[key]}」"
               for key in ("volume", "volume_start_chapter")
               if key in old_position and old_position[key] != position[key]]
    if differs:
        notes.append("卷信息與當前狀態不同，已取當前狀態，本章確實換卷就改回（" + "；".join(differs) + "）")
    if snapshots:
        notes.append("帶過來的角色快照（" + "、".join(snapshots) + "）可能被中間的提交改過，逐個對照 current_snapshots 或 snapshot_files 重核")
    return "；".join(notes)


def prepare_draft_snapshots(
    project: Path,
    chapter: int,
    all_characters: dict[str, dict[str, Any]],
    active_names: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, str], list[str]]:
    """把全部核心角色的當前快照落到本章工作目錄，並把 stdout 內聯體積控制在預算內。

    久別回歸的非在場核心角色不在 active_character_names 里，但本章一旦變化也必須交完整新快照；
    單角色快照放大到 64 KiB 後，20 名在場角色全塞進單行 stdout 又會撐大上下文或被宿主截斷。
    因此所有核心角色一律寫 `.story/work/第NNN章/snapshots/{名}.json`（隨 chapter commit 自動清理），
    stdout 的 `current_snapshots` 只內聯預算內的在場角色，其余指路 `snapshot_files`。
    """
    snapshots_dir = chapter_work_dir(project, chapter) / "snapshots"
    expected_files = {f"{name}.json" for name in all_characters}
    if snapshots_dir.is_dir():
        for existing_file in snapshots_dir.glob("*.json"):
            if existing_file.name not in expected_files:
                existing_file.unlink()
        if not all_characters:
            try:
                snapshots_dir.rmdir()
            except OSError:
                pass
    snapshot_files: dict[str, str] = {}
    for name, snap in all_characters.items():
        target = snapshots_dir / f"{name}.json"
        write_if_changed(target, json_payload(snap))
        snapshot_files[name] = str(target)

    inline: dict[str, dict[str, Any]] = {}
    omitted: list[str] = []
    used_bytes = 2
    for name in dict.fromkeys(active_names):
        if name not in all_characters:
            continue
        entry_bytes = byte_size(json.dumps({name: all_characters[name]}, ensure_ascii=False))
        if used_bytes + entry_bytes <= DRAFT_INLINE_SNAPSHOTS_MAX_BYTES:
            inline[name] = all_characters[name]
            used_bytes += entry_bytes
        else:
            omitted.append(name)
    return inline, snapshot_files, omitted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "commit"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--project", type=Path, required=True, help="book project root containing tracking/")
        subparser.add_argument("--input", type=Path, required=True, help="UTF-8 JSON input document")
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--project", type=Path, required=True, help="book project root containing tracking/")
    draft_parser = subparsers.add_parser("draft", help="write a pre-filled chapter transaction to fill in")
    draft_parser.add_argument("--project", type=Path, required=True, help="book project root containing tracking/")
    draft_parser.add_argument("--chapter", type=int, required=True)
    draft_parser.add_argument("--out", type=Path, help="default: <project>/.story/work/ch_<NNN>/tracking.json")
    draft_parser.add_argument("--force", action="store_true",
                              help="discard an existing draft instead of only refreshing its revision")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        try:
            args.project = wordcount_core.resolve_book_dir(args.project)
        except wordcount_core.WordcountError as exc:
            raise TrackingError(str(exc)) from exc
        if args.command == "draft":
            state = load_state(args.project)
            document, _, extra = draft_transaction(args.project, args.chapter, state=state)
            all_characters = state["characters"]
            previous_position = extra if document["mode"] == "append" else {}
            prefill_notes = extra.get("notes", []) if document["mode"] == "revision" else []
            record_prefilled = bool(extra.get("prefilled")) if document["mode"] == "revision" else False
            out = args.out or chapter_work_dir(args.project, args.chapter) / "tracking.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            refreshed = ""
            if out.exists() and not args.force:
                # 重跑 draft 不衝掉已經填好的變化。修訂號變了說明中間提交過別的事務：context 按當前
                # 狀態重建（沿用舊 context 會把那次變更整份覆蓋回去），只帶過本章自己填的部分。
                existing = read_json(out)
                require(isinstance(existing, dict) and existing.get("chapter") == document["chapter"]
                        and existing.get("mode") == document["mode"],
                        f"{out} already holds a draft for a different chapter or mode; pass --force to replace it")
                if existing.get("expected_state_revision") == document["expected_state_revision"]:
                    document, refreshed = existing, "已有草稿且修訂號未變，原樣保留"
                else:
                    refreshed = rebuild_stale_draft(document, existing, bool(previous_position), all_characters)
            out.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            raw_active = (document.get("context") or {}).get("active_character_names") if isinstance(document.get("context"), dict) else []
            active_names = [name for name in raw_active if isinstance(name, str)] if isinstance(raw_active, list) else []
            snapshots, snapshot_files, omitted_snapshots = prepare_draft_snapshots(
                args.project, args.chapter, all_characters, active_names
            )
            if document["mode"] == "revision" and not record_prefilled:
                fill = (f"這是修訂，但本章逐章記錄缺失或讀不了（{delta_path(Path('tracking'), args.chapter).as_posix()}），delta 沒有預填："
                        "按修訂後正文把本章完整記錄整份寫上（結果、承諾、角色變化、伏筆、時間線、約束），沒寫的項不會進記錄。"
                        "角色快照、伏筆、時間線寫截至最新已寫章的當前值（已有核心角色的當前快照見 snapshot_files）；context 原樣保留全部當前條目（修訂不能退役）。"
                        "正文改過就用 story-long-write 的 storyctl.py chapter commit 提交（重新計數並清理本章工作目錄）。"
                        "不要從腳本源碼或 state 文件里另找格式。")
            elif document["mode"] == "revision":
                fill = ("這是修訂：delta 是修訂後本章的完整記錄，已按本章現有逐章記錄預填（伏筆與時間線取當前值，"
                        "記錄里的核心角色快照已放進 character_snapshots，其他核心角色當前快照見 snapshot_files）。對照修訂後正文逐項改：仍成立的原樣保留，"
                        "被推翻的刪掉或改寫，新增的補上；不要清空後只寫改動，沒寫的項會從本章記錄里消失。"
                        "角色快照、伏筆、時間線改成截至最新已寫章的當前值；context 原樣保留全部當前條目（修訂不能退役）。"
                        "正文改過就用 story-long-write 的 storyctl.py chapter commit 提交（重新計數並清理本章工作目錄）。"
                        "不要從腳本源碼或 state 文件里另找格式。")
                if prefill_notes:
                    fill += "沒能預填：" + "；".join(prefill_notes) + "。"
            else:
                fill = ("只填 delta 里本章的變化；context 其余字段已是當前值，要撤下的長期約束或連貫性風險從 context 刪掉並把原文放進 "
                        "delta.retired_context_items（僅 append）；本章有變化的核心角色從 current_snapshots（未內聯的大快照或久別回歸角色讀 snapshot_files 對應 JSON）"
                        "取當前快照整份改好放進 character_snapshots，並在 character_changes 寫一句變化。每類條目照 shapes 的形狀寫，不要從腳本源碼或 state 文件里另找格式。")
            if omitted_snapshots:
                fill = (f"在場角色（{'、'.join(omitted_snapshots)}）快照較大未內聯到 stdout，本章若有變化先讀取 snapshot_files 對應 JSON 在其基礎上修改，勿憑空重寫以免丟失既有條目。") + fill
            blank = not (document["context"]["position"].get("story_time") or document["context"]["position"].get("scene"))
            if previous_position and blank:
                fill = ("context.position 的 story_time 與 scene 留空，填本章結束時的故事時間與場景（上一章結束時見 "
                        "previous_position；換卷時連同 volume 與 volume_start_chapter 一起改）。") + fill
            payload = {
                "draft": str(out),
                "mode": document["mode"],
                "expected_state_revision": document["expected_state_revision"],
                "fill": (f"{refreshed}；要從頭生成加 --force。" if refreshed else "") + fill,
                "limits_chars": DRAFT_LIMITS,
                "shapes": entry_shapes(args.chapter),
                "current_snapshots": snapshots,
                "snapshot_files": snapshot_files,
            }
            if omitted_snapshots:
                payload["omitted_active_snapshots"] = omitted_snapshots
            if previous_position:
                payload["previous_position"] = previous_position
            emit(json.dumps(payload, ensure_ascii=False))
            return 0
        if args.command == "init":
            result = initialize(args.project, read_json(args.input))
        elif args.command == "commit":
            result = apply_transaction(args.project, read_json(args.input))
        else:
            result = check_project(args.project)
    except (TrackingError, OSError, UnicodeError) as exc:
        emit(f"ERROR: {exc}", error=True)
        return 2
    emit(
        json.dumps(
            {
                "last_committed_chapter": result["last_committed_chapter"],
                "state_revision": result["state_revision"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
