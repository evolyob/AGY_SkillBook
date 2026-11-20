#!/usr/bin/env python3
"""卷綱取段器 —— 讓「不整讀卷綱」成立。

按聲明作用域選取卷級、單元級和批次材料；未聲明的舊段保守納入並告警。

兩種寫法都認（新卷綱只寫第一種）：

1. 標題尾部注釋（0.10 起）：
       ## 本卷故事線 <!-- 全卷 -->
       ### 第一段劇情：退婚風波 <!-- L1-01 -->
       #### 老底稿 <!-- 批次底稿 L1-01｜已退役 -->
   新寫法里沒寫注釋的子標題跟隨上級劇情段（上級是全卷段的不跟隨，仍算未聲明）。
2. 舊寫法：標題**下一行非空行**寫
       > 作用域：卷級常任
       > 作用域：單元級 D1-03
       > 作用域：批次底稿 D1-03｜狀態：在用

退役行（行內覆蓋）：以 `⊘` 起頭的列表行 / 表格行，默認過濾。

卷綱、細綱按名讀取的字段在這里集中給出新舊名（UNIT_FIELD_NAMES、CHAPTER_UNIT_FIELDS），
其他腳本從這里取，不各自寫死一種叫法。

細綱屬於哪段劇情：新細綱只寫段名（「第一段劇情：退婚風波」），按本章章號落在卷綱哪張劇情段卡的
「章節范圍」里定位（unit_for_chapter / --chapter）；舊細綱行末的編號注釋、舊「單元ID/位置」字段照樣認。

用法：
    outline_view.py --toc   卷綱.md
    outline_view.py --unit D1-03 卷綱.md
    outline_view.py --chapter 12 卷綱.md      # 第 12 章落在哪段劇情，就取哪段（同 --unit）
    outline_view.py --contract 卷綱.md
    outline_view.py --check 卷綱.md
    任意子命令加 --history 連退役行一起輸出
"""
import argparse
import io
import re
import sys

_OUTLINE_CFG = json.loads(
    (Path(__file__).resolve().parent.parent / "data" / "contracts.json").read_text(encoding="utf-8")
)["outline_contract"]

HEADING = re.compile(r"^(#{2,4})\s+(.*\S)\s*$")
SCOPE = re.compile(r"^>\s*作用域[：:]\s*(.+?)\s*$")
# 標題尾部注釋：## 本卷故事線 <!-- 全卷 -->
TRAILING = re.compile(r"^(.*?)\s*<!--\s*(.*?)\s*-->\s*$")
RETIRED_LINE = re.compile(r"^\s*(?:[-*]\s*)?⊘|^\s*\|\s*⊘")
# 單元塊內不該出現的全卷字樣：出現即說明這條常任規則放錯了地方
LEAK = re.compile(_OUTLINE_CFG["view_leak_regex"])
# 指向卷級的指針行不算泄漏：單元塊可以引用常任規則，不可以複述它
POINTER = re.compile(_OUTLINE_CFG["view_pointer_regex"])
UNIT_IN_TITLE = re.compile(r"(?<![\w-])([LD]\d+-\d+|U\d+)(?![\w-])")
# 批次底稿裡出現跨章祈使＝這條約束在寫作期還有效，而寫作檔不給底稿 -> 必須下沉
IMPERATIVE = re.compile(_OUTLINE_CFG["view_imperative_regex"])
CH_RANGE = re.compile(r"章節範圍[：:]\s*第\s*(\d+)\s*[-–—~至]\s*(\d+)\s*章")
# 情緒弧線逐章行：首列寫「12」或範本裡的「第12章」都認
ARC_ROW = re.compile(r"^\|\s*第?\s*(\d+)\s*章?\s*\|")
UNIT_ID = re.compile(r"(?<![\w-])([A-Za-z]\d+-\d+|U\d+)(?![\w-])")

# 按名讀取的欄位由 contracts.json 統一管理
UNIT_FIELD_NAMES = {k: tuple(v) for k, v in _OUTLINE_CFG["unit_field_names"].items()}
CHAPTER_UNIT_FIELDS = tuple(_OUTLINE_CFG["chapter_unit_fields"])


def classify(section):
    """作用域串 → kind / unit / status。新舊叫法都認：全卷＝卷級常任，單寫編號＝單元級。"""
    parts = [part.strip() for part in re.split(r"[｜|]", section.scope)]
    head = parts[0]
    if head in ("卷級常任", "全卷"):
        section.kind = "卷級常任"
    elif re.fullmatch(r"單元級(?:\s+[A-Za-z][\w-]*)?", head):
        section.kind = "單元級"
    elif re.fullmatch(r"批次底稿(?:\s+[A-Za-z][\w-]*)?", head):
        section.kind = "批次底稿"
    elif section.inline and re.fullmatch(r"[A-Za-z][\w-]*", head) and UNIT_ID.fullmatch(head):
        section.kind = "單元級"
        section.unit = head
    found = re.search(r"^(?:單元級|批次底稿)\s+([A-Za-z][\w-]*)$", head)
    if found:
        section.unit = found.group(1)
    if any("已退役" in part for part in parts):
        section.status = "已退役"


def is_unit_card(section):
    """劇情段的卡頭：舊寫法標題含「劇情單元」，新寫法標題是「第N段劇情」，或這一段自己寫著章節范圍。"""
    if section.kind != "單元級" or section.inherited:
        return False
    return ("劇情單元" in section.title or "段劇情" in section.title
            or any(CH_RANGE.search(line) for line in section.lines))


def field_value(text, names):
    """按名取列表字段的值（第一種叫法有就用它，否則試舊名）；沒有返回 None。"""
    for name in names:
        pattern = re.compile(rf"^[ \t>]*[-*+][ \t]*\*{{0,2}}{re.escape(name)}\*{{0,2}}[ \t]*[：:][ \t]*(.*)$", re.M)
        match = pattern.search(text or "")
        if match:
            return match.group(1).strip()
    return None


def unit_id_of(value):
    """從「屬於哪段劇情：第一段劇情，第二步 <!-- L1-01 -->」或舊「單元ID/位置：L1-01；第2拍」取單元編號。"""
    if not value:
        return None
    found = UNIT_ID.search(value)
    return found.group(1) if found else None


def chapter_unit(outline_text):
    """細綱里寫明的劇情段編號（舊寫法：行末注釋或「單元ID/位置」）；新細綱不寫編號，返回 None，
    由調用方按章號走 unit_for_chapter。"""
    return unit_id_of(field_value(outline_text, CHAPTER_UNIT_FIELDS))


def unit_for_chapter(sections, chapter):
    """本章章號落在哪張劇情段卡的「章節范圍」里（跳過已退役的卡）；沒有返回 None。"""
    for section in sections:
        if section.status == "已退役" or not section.unit or not is_unit_card(section):
            continue
        for line in section.lines:
            found = CH_RANGE.search(line)
            if found:
                if int(found.group(1)) <= chapter <= int(found.group(2)):
                    return section.unit
                break
    return None


def chapter_unit_in_volume(volume_text, chapter):
    """卷綱全文 + 章號 → 劇情段編號；卷綱讀不出或沒有覆蓋本章的段返回 None。"""
    try:
        _, sections = parse(volume_text or "")
    except Exception:  # noqa: BLE001 —— 卷綱寫壞時按「找不到」處理，由調用方報告
        return None
    return unit_for_chapter(sections, chapter)


def read(path):
    with io.open(path, encoding="utf-8-sig") as handle:
        return handle.read()


class Section:
    __slots__ = ("level", "title", "start", "end", "scope", "kind",
                 "unit", "status", "lines", "inline", "inherited")

    def __init__(self, level, title, start):
        self.level = level
        self.title = title
        self.start = start          # 標題行號（0 基）
        self.end = None
        self.scope = None           # 原始作用域串，None ＝ 未聲明
        self.kind = None            # 卷級常任 / 單元級 / 批次底稿
        self.unit = None
        self.status = "在用"
        self.lines = []
        self.inline = False         # 作用域寫在標題尾部注釋里（新寫法）
        self.inherited = False      # 新寫法里沒寫注釋、跟隨上級劇情段


def parse(text):
    lines = text.split("\n")
    sections = []
    fence = None
    for index, line in enumerate(lines):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        match = HEADING.match(line)
        if match:
            if sections:
                sections[-1].end = index
            sections.append(Section(len(match.group(1)), match.group(2), index))
    if sections:
        sections[-1].end = len(lines)
    for section in sections:
        section.lines = lines[section.start:section.end]
        trailing = TRAILING.match(section.title)
        if trailing and trailing.group(2):
            section.title = trailing.group(1).strip() or section.title
            section.scope = trailing.group(2)
            section.inline = True
        else:
            for candidate in section.lines[1:]:
                if not candidate.strip():
                    continue
                scope_match = SCOPE.match(candidate)
                if scope_match:
                    section.scope = scope_match.group(1)
                break
        if section.scope:
            classify(section)
        if section.unit is None:
            found = re.search(r"劇情單元\s+([A-Za-z][\w-]*)", section.title) or UNIT_IN_TITLE.search(section.title)
            if found:
                section.unit = found.group(1)
        if section.unit is None and section.scope is None:
            for line in section.lines[1:]:
                field = re.match(r"^\s*[-*+]\s*單元ID\s*[：:]\s*([A-Za-z][\w-]*)\s*$", line.replace("**", ""))
                if field:
                    section.unit = field.group(1)
                    break
    # 新寫法：沒寫注釋的子標題跟隨最近的上級劇情段（單元級或批次底稿），上級是全卷段的不跟隨。
    stack = []
    for section in sections:
        while stack and stack[-1].level >= section.level:
            stack.pop()
        parent = stack[-1] if stack else None
        if (section.scope is None and parent is not None and parent.inline
                and parent.kind in ("單元級", "批次底稿") and parent.unit):
            section.scope = parent.scope
            section.kind = parent.kind
            section.unit = parent.unit
            section.status = parent.status
            section.inline = True
            section.inherited = True
        stack.append(section)
    # 新寫法里全卷小節可以不寫注釋：文件里只要有劇情段用了標題尾注釋，其余沒標的段一律算全卷。
    if any(section.inline for section in sections):
        for section in sections:
            if section.scope is None and section.unit is None:
                section.scope = "全卷"
                section.inline = True
                classify(section)
    return lines, sections


def strip_retired(block_lines, keep_history):
    if keep_history:
        return block_lines
    return [line for line in block_lines if not RETIRED_LINE.match(line)]


def unit_chapter_range(sections, unit):
    for section in sections:
        if section.unit == unit and is_unit_card(section):
            for line in section.lines:
                found = CH_RANGE.search(line)
                if found:
                    return int(found.group(1)), int(found.group(2))
    return None


def slice_arc(section, span):
    """情緒弧線這類逐章表：只留本單元章區間的行，表頭與說明照留。"""
    if span is None:
        return section.lines
    low, high = span
    kept = []
    for line in section.lines:
        row = ARC_ROW.match(line)
        if row and not (low <= int(row.group(1)) <= high):
            continue
        kept.append(line)
    return kept


def emit(sections, chosen, span, keep_history, note, preamble):
    out = ["\n".join(strip_retired(preamble, keep_history)).rstrip()] if preamble else []
    for section in sections:
        if section not in chosen:
            continue
        body = section.lines
        if "情緒弧線" in section.title or "排班" in section.title:
            body = slice_arc(section, span)
        body = strip_retired(body, keep_history)
        out.append("\n".join(body).rstrip())
    text = "\n\n".join(out)
    sys.stdout.write(text + "\n")
    if note:
        sys.stderr.write(note + "\n")


def cmd_toc(sections):
    print("%-3s %-6s %-9s %-8s %-46s %s" %
          ("#", "行", "作用域", "單元", "段", "字符"))
    for number, section in enumerate(sections, 1):
        size = sum(len(line) + 1 for line in section.lines)
        print("%-3d %-6d %-9s %-8s %-46s %d" %
              (number, section.start + 1, section.kind or "**未聲明**",
               (section.unit or "-") + ("(退)" if section.status == "已退役" else ""),
               section.title[:44], size))


def cmd_check(sections, strict=False):
    problems = []
    warnings = []
    for section in sections:
        if section.kind == "批次底稿":
            for offset, line in enumerate(section.lines):
                if IMPERATIVE.search(line):
                    warnings.append(
                        ("W1", "第%d行" % (section.start + offset + 1),
                         "批次底稿里有跨章祈使，寫作檔不給底稿——確認已下沉到單元級段或細綱：%s"
                         % line.strip()[:52]))
    for section in sections:
        where = "第%d行「%s」" % (section.start + 1, section.title[:36])
        if section.scope is None:
            (problems if strict else warnings).append(
                ("E1" if strict else "W2", where,
                 "標題沒標是全卷還是哪段劇情：標題末尾加 <!-- 全卷 --> 或 <!-- 單元編號 -->；舊段保守納入"))
            continue
        if section.kind is None:
            problems.append(("E2", where, "標題注釋不認識：%s（只認 全卷 / 單元編號 / 批次底稿 單元編號）" % section.scope))
        if section.kind in ("單元級", "批次底稿") and section.unit is None:
            problems.append(("E3", where, "劇情段/批次底稿段沒寫單元編號"))
        if section.kind in ("單元級", "批次底稿"):
            for offset, line in enumerate(section.lines):
                if LEAK.search(line) and not POINTER.search(line):
                    problems.append(
                        ("E4", "第%d行" % (section.start + offset + 1),
                         "劇情段里寫了全卷都要守的規矩，挪到「全卷規矩」：%s"
                         % line.strip()[:56]))
    for code, where, message in problems + warnings:
        print("%s %s %s" % (code, where, message))
    print("---")
    print("段 %d ／ 問題 %d ／ 告警 %d（告警不阻斷，逐條人工判斷）"
          % (len(sections), len(problems), len(warnings)))
    return 1 if problems else 0


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("path")
    parser.add_argument("--toc", action="store_true")
    parser.add_argument("--unit")
    parser.add_argument("--chapter", type=int, help="按章號找本章落在哪段劇情的章節范圍里，取那一段（同 --unit）")
    parser.add_argument("--contract", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--strict", action="store_true", help="新建卷綱校驗：標題沒標全卷或單元編號也視為錯誤")
    # 排綱筆記放在卷綱外的 .story/排綱筆記/{單元ID}.md（老書在 大綱/排綱筆記_ 或 排綱底稿_），默認輸出就是寫作要的閉包。
    # --stage outline 只為老卷綱保留：它們的供給自查等底稿還寫在卷綱里（作用域：批次底稿）。
    parser.add_argument("--stage", choices=["outline", "write"], default="write",
                        help="write（默認）＝卷級常任＋單元級；"
                             "outline＝另帶老卷綱里仍在用的批次底稿段")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        lines, sections = parse(read(args.path))
    except (OSError, UnicodeError) as error:
        sys.stderr.write(f"無法讀取卷綱：{error}\n")
        return 2
    if not sections:
        sys.stderr.write("卷綱里沒有 ## 段，路徑對不對？\n")
        return 2

    if args.toc:
        cmd_toc(sections)
        return 0
    if args.check:
        return cmd_check(sections, args.strict)

    invalid = [s for s in sections if s.scope and
               (s.kind is None or (s.kind != "卷級常任" and s.unit is None))]
    if invalid:
        sys.stderr.write("標題注釋（或舊的作用域行）寫得不對，先運行 --check 修正\n")
        return 1
    active = [s for s in sections if args.history or s.status != "已退役"]
    permanent = [s for s in active if s.kind == "卷級常任"]
    undeclared = [s for s in active if s.scope is None]
    note = ("%d 段沒標全卷或單元編號，已保守納入；用 --check 查看" % len(undeclared)) if undeclared else None
    preamble = lines[:sections[0].start]
    if args.contract:
        emit(sections, set(permanent + undeclared), None, args.history, note, preamble)
        return 0

    if args.chapter is not None and not args.unit:
        args.unit = unit_for_chapter(active, args.chapter)
        if not args.unit:
            sys.stderr.write(
                "卷綱里沒有哪段劇情的章節范圍覆蓋第 %d 章 —— 不靜默降級。核對劇情段的「章節范圍」，或先補卷綱。\n"
                % args.chapter)
            return 1
        sys.stderr.write("第 %d 章屬於劇情段 %s\n" % (args.chapter, args.unit))

    if args.unit:
        unit = args.unit
        owned = [s for s in active if s.unit == unit]
        if not owned:
            sys.stderr.write(
                "找不到單元 %s —— 不靜默降級。核對單元編號，或先補卷綱。\n" % unit)
            return 1
        if args.stage == "write":
            # 寫作檔不給批次底稿：它是排綱期的工作底稿，其中有寫作期約束力的條目
            # 必須已經下沉到單元級段或細綱（見 artifact-protocols.md「排綱筆記不進卷綱」）
            live = [s for s in owned if s.kind == "單元級"]
        else:
            live = [s for s in owned
                    if s.kind == "單元級"
                    or s.kind == "批次底稿"]
        chosen = set(permanent + live + undeclared)
        span = unit_chapter_range(active, unit)
        emit(sections, chosen, span, args.history, note, preamble)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
