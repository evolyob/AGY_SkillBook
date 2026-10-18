#!/usr/bin/env python3
"""Raw Document Flattener & Chapter Chunker for deep-base."""

import argparse
from collections import Counter
import html
import importlib
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def load_flatten_config() -> tuple[dict, dict]:
    cfg_path = Path(__file__).resolve().parent / "config.json"
    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        return raw.get("flatten", {}), raw.get("hygiene", {}).get("redact_patterns", {})
    except Exception:
        return {}, {}


CFG, HYGIENE_PATS = load_flatten_config()
MAX_CHAPTER_BYTES = CFG.get("max_chapter_bytes", 40000)
MIN_CHAPTER_CHARS = CFG.get("min_chapter_chars", 80)
MIN_CHARS_PER_PAGE_OCR = CFG.get("min_chars_per_page_ocr", 50)
SINGLE_AGENT_MAX_BYTES = CFG.get("single_agent_max_bytes", 81920)
SINGLE_AGENT_MAX_CHAPTERS = CFG.get("single_agent_max_chapters", 6)
BATCH_TARGET_BYTES = CFG.get("batch_target_bytes", 65536)

PATS = CFG.get("patterns", {})
TOC_DOT_LEADER_RX = re.compile(PATS.get("toc_dot", r"(?:\.{3,}|(?:\.\s*){3,}|·{3,}|…{2,})\s*\d+\s*$"))
PAGE_NUM_RX = re.compile(PATS.get("page_num", r"^(?:[-－—–]\s*\d+\s*[-－—–]|Page\s+\d+)$"), re.I)
HEADING_RX = re.compile(PATS.get("heading", r"^#{1,2}\s+.+$"), re.M)
SUB_HEADING_RX = re.compile(PATS.get("sub_heading", r"^#{2,4}\s+.+$"), re.M)
SECRET_TOKEN_RX = re.compile(HYGIENE_PATS.get("secret_token", r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})\b"))
PRIVATE_KEY_RX = re.compile(HYGIENE_PATS.get("private_key", r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----"))
TW_MOBILE_RX = re.compile(HYGIENE_PATS.get("tw_phone", r"(?<!\d)09\d{2}[-\s]?\d{3}[-\s]?\d{3}(?!\d)"))


def sanitize_sensitive_text(text: str) -> str:
    """Scrub host user-home absolute paths, private keys, API tokens, personal mobile numbers, and markdown syntax at Gate 1."""
    home_str = str(Path.home())
    if home_str and home_str != "/":
        text = text.replace(home_str, "~")
    text = PRIVATE_KEY_RX.sub("[REDACTED_PRIVATE_KEY]", text)
    text = SECRET_TOKEN_RX.sub("[REDACTED_SECRET]", text)
    text = TW_MOBILE_RX.sub("[REDACTED_PHONE]", text)
    try:
        from sanitize import sanitize_markdown_text
        text, _ = sanitize_markdown_text(text)
    except Exception:
        pass
    return text


def normalize_cjk_spacing(text: str) -> str:
    """Repair artificial intra-line CJK and numbering spaces from PDF extraction."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"(\b[A-Za-z]+)-\n([A-Za-z]+\b)", r"\1\2", text)
    text = re.sub(r"(?m)^(\d{1,2})\s+\.\s+", r"\1. ", text)
    text = re.sub(
        r"(?m)^(\d{1,2})\.\s+(\d{1,2})(?:\.\s*(\d{1,2}))?\s+",
        lambda m: f"{m.group(1)}.{m.group(2)}" + (f".{m.group(3)} " if m.group(3) else " "),
        text,
    )
    for _ in range(2):
        text = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", text)
    text = re.sub(r"([\u4e00-\u9fff])\s+([，。、；：！？）》」』])", r"\1\2", text)
    return re.sub(r"([（《「『])\s+([\u4e00-\u9fff])", r"\1\2", text)


def is_valid_heading(line: str) -> bool:
    """Check if a line is a structural chapter/section heading rather than a sentence."""
    s = line.strip()
    if not s or len(s) > 65 or s.endswith(("。", "，", ",", ";", "；", "、", "：", ":")):
        return False
    return not TOC_DOT_LEADER_RX.search(s) and bool(HEADING_RX.match(s))


def clean_single_page(lines: list[str], repeated_edges: set[str]) -> str:
    """Filter TOC pages, dot leaders, page numbers, and repeated headers/footers."""
    if not lines:
        return ""
    dot_lines = sum(1 for ln in lines if TOC_DOT_LEADER_RX.search(ln))
    if len(lines) >= 5 and (dot_lines / len(lines)) >= 0.35:
        return ""
    kept = [
        ln for idx, ln in enumerate(lines)
        if not TOC_DOT_LEADER_RX.search(ln)
        and not PAGE_NUM_RX.match(ln)
        and not ((idx < 3 or idx >= len(lines) - 3) and ln in repeated_edges)
    ]
    return "\n".join(kept)


def strip_running_headers_and_toc(pages: list[str]) -> list[str]:
    """Remove repeated running headers/footers and TOC dot-leader pages across PDF pages."""
    norm_pages = [[ln.strip() for ln in normalize_cjk_spacing(p).splitlines() if ln.strip()] for p in pages]
    edge_counts = Counter(ln for lines in norm_pages for ln in (lines[:3] + lines[-3:]) if len(ln) <= 45)
    threshold = max(3, len(norm_pages) // 5)
    repeated_edges = {ln for ln, cnt in edge_counts.items() if cnt >= threshold}
    cleaned = [clean_single_page(lines, repeated_edges) for lines in norm_pages]
    return [c for c in cleaned if c]


STRUCT_SOLO_RX = re.compile(r"^(?:Module|Lesson|Chapter|Section|Domain|Unit)\s+[0-9A-Z]+$", re.I)


def unwrap_broken_lines(text: str) -> str:
    """Rejoin mid-sentence PDF line wraps while preserving headings, lists, and tables."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: list[str] = []
    for ln in lines:
        if out and STRUCT_SOLO_RX.match(out[-1]) and not is_valid_heading(ln) and len(ln) <= 75:
            out[-1] = f"{out[-1]}: {ln}"
            continue
        is_struct = any(ln.startswith(p) for p in ("#", ">", "|", "```", "---")) or bool(re.match(r"^(?:[-*+]|\(\d+\)|\([a-zA-Z]\)|\d+[\.\)])\s*", ln)) or is_valid_heading(ln)
        prev = out[-1] if out else ""
        prev_struct = any(prev.startswith(p) for p in ("#", ">", "|", "```", "---")) or is_valid_heading(prev)
        can_join = bool(out) and not is_struct and not prev_struct and not prev.endswith((".", ":", "!", "?", ";", "。", "！", "？", "；", "：")) and (ln[0].islower() or prev.endswith("-") or (len(prev) >= 28 and "\u4e00" <= ln[0] <= "\u9fff"))
        if can_join:
            sep = "" if ("\u4e00" <= prev[-1] <= "\u9fff" and "\u4e00" <= ln[0] <= "\u9fff") else " "
            out[-1] += sep + ln
        else:
            out.append(ln)
    return "\n".join(out)


def extract_pdf(path: Path) -> tuple[str, dict]:
    """Extract and clean PDF pages with OCR character density guard."""
    pypdf = importlib.import_module("pypdf")
    reader = pypdf.PdfReader(str(path))
    total_pages = len(reader.pages)
    raw_pages = [page.extract_text() or "" for page in reader.pages]
    avg_chars = sum(len(p.strip()) for p in raw_pages) // max(1, total_pages)
    if total_pages > 0 and avg_chars < MIN_CHARS_PER_PAGE_OCR:
        return "", {
            "error": "OCR_REQUIRED",
            "message": f"Average character density ({avg_chars} chars/page < {MIN_CHARS_PER_PAGE_OCR}) indicates a scanned PDF.",
            "total_pages": total_pages,
            "avg_chars_per_page": avg_chars,
        }
    full_text = unwrap_broken_lines("\n".join(strip_running_headers_and_toc(raw_pages)))
    full_text = re.sub(r"(?m)^#\s+", "// ", full_text)
    return full_text, {"total_pages": total_pages, "avg_chars_per_page": avg_chars}


def extract_document(path: Path) -> tuple[str, dict]:
    """Dispatch document extraction by file extension."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    if ext == ".docx":
        with zipfile.ZipFile(path) as z:
            tree = ET.fromstring(z.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paras = ["".join(t.text for t in n.findall(".//w:t", ns) if t.text) for n in tree.findall(".//w:p", ns)]
        txt = unwrap_broken_lines(normalize_cjk_spacing("\n".join(paras)))
        return txt, {"total_pages": 1, "avg_chars_per_page": len(txt)}
    if ext == ".xlsx":
        openpyxl = importlib.import_module("openpyxl")
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        sheets = [f"# Sheet: {s}\n" + "\n".join(" | ".join(str(v).strip() for v in r if v is not None and str(v).strip()) for r in wb[s].iter_rows(values_only=True) if any(r)) for s in wb.sheetnames]
        txt = "\n\n".join(sheets)
        return txt, {"total_pages": len(wb.sheetnames), "avg_chars_per_page": len(txt) // max(1, len(wb.sheetnames))}
    if ext in (".md", ".txt", ".html"):
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        if ext == ".html":
            t = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", "", raw, flags=re.DOTALL | re.I)
            t = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n# \1\n", t, flags=re.DOTALL | re.I)
            raw = html.unescape(re.sub(r"<[^>]+>", " ", t))
        return raw.strip(), {"total_pages": 1, "avg_chars_per_page": len(raw)}
    raise ValueError(f"Unsupported file extension: {ext}")


def pack_segments_by_budget(title: str, segments: list[str]) -> list[tuple[str, str]]:
    """Pack text segments into <= MAX_CHAPTER_BYTES parts."""
    parts: list[tuple[str, str]] = []
    buf: list[str] = []
    for seg in segments:
        if not seg:
            continue
        cand = ("\n".join(buf) + "\n" + seg).strip() if buf else seg
        if len(cand.encode("utf-8")) > MAX_CHAPTER_BYTES and buf:
            parts.append((f"{title} (Part {len(parts) + 1})", "\n".join(buf).strip()))
            buf = [seg]
        else:
            buf.append(seg)
    if buf:
        label = f"{title} (Part {len(parts) + 1})" if parts else title
        parts.append((label, "\n".join(buf).strip()))
    return parts


FENCE_LINE_RX = re.compile(r"^\s*(```|~~~)")


def non_fenced_indices(lines: list[str], predicate) -> list[int]:
    """Return line indices matching predicate outside fenced code blocks."""
    indices: list[int] = []
    in_fence = False
    for i, ln in enumerate(lines):
        if FENCE_LINE_RX.match(ln):
            in_fence = not in_fence
            continue
        if not in_fence and predicate(ln):
            indices.append(i)
    return indices


def split_oversized_section(title: str, body: str) -> list[tuple[str, str]]:
    """Split a section exceeding MAX_CHAPTER_BYTES along sub-headings or lines."""
    if len(body.encode("utf-8")) <= MAX_CHAPTER_BYTES:
        return [(title, body)]
    lines = body.splitlines()
    sub_idx = non_fenced_indices(lines, lambda ln: bool(SUB_HEADING_RX.match(ln.strip())) and len(ln.strip()) <= 70)
    if len(sub_idx) >= 2:
        bounds = [0] + sub_idx + [len(lines)]
        segs = ["\n".join(lines[bounds[i]:bounds[i + 1]]).strip() for i in range(len(bounds) - 1)]
        return pack_segments_by_budget(title, segs)
    return pack_segments_by_budget(title, lines)


def merge_and_split_headings(lines: list[str], heading_indices: list[int]) -> list[tuple[str, str]]:
    """Slice lines by heading indices while merging tiny sections into subsequent sections."""
    raw_sections: list[tuple[str, str]] = []
    preamble = "\n".join(lines[:heading_indices[0]]).strip() if heading_indices[0] > 0 else ""
    carry_title = ""
    carry_body = ""
    if len(preamble) >= MIN_CHAPTER_CHARS:
        raw_sections.extend(split_oversized_section("00_Preamble", preamble))
    elif preamble:
        carry_body = preamble

    for idx, h_idx in enumerate(heading_indices):
        end_idx = heading_indices[idx + 1] if idx + 1 < len(heading_indices) else len(lines)
        title = lines[h_idx].strip("# ").strip()
        body = "\n".join(lines[h_idx + 1:end_idx]).strip()
        if carry_body:
            title = f"{carry_title} & {title}" if carry_title else title
            body = f"{carry_body}\n\n## {lines[h_idx].strip('# ').strip()}\n{body}".strip()
            carry_title, carry_body = "", ""
        if len(body) < MIN_CHAPTER_CHARS and idx + 1 < len(heading_indices):
            carry_title, carry_body = title, f"## {title}\n{body}".strip()
            continue
        raw_sections.extend(split_oversized_section(title, body))

    if carry_body:
        raw_sections.extend(split_oversized_section(carry_title or "Appendix", carry_body))
    return raw_sections


def segment_chapters(text: str) -> list[dict]:
    """Segment cleaned document text into chapter dicts without dropping short sections."""
    text = sanitize_sensitive_text(text)
    lines = text.splitlines()
    heading_indices = non_fenced_indices(lines, is_valid_heading)
    raw_sections = split_oversized_section("Full Document", text.strip()) if not heading_indices else merge_and_split_headings(lines, heading_indices)
    chapters = []
    for i, (title, body) in enumerate(raw_sections, 1):
        safe_slug = re.sub(r'[\\/*?:"<>|#\s]+', "_", title).strip("_")[:45].strip("_") or f"section_{i:02d}"
        full_md = f"# {title}\n\n{body}\n"
        chapters.append({
            "index": i,
            "title": title,
            "file": f"{i:02d}_{safe_slug}.md",
            "chars": len(full_md),
            "bytes": len(full_md.encode("utf-8")),
            "est_tokens": len(full_md) // 3,
            "content": full_md,
        })
    return chapters


def plan_batches(chapters: list[dict]) -> tuple[str, list[dict]]:
    """Determine single_agent vs subagent_parallel mode and group chapters into batches."""
    total_bytes = sum(c["bytes"] for c in chapters)
    if total_bytes <= SINGLE_AGENT_MAX_BYTES and len(chapters) <= SINGLE_AGENT_MAX_CHAPTERS:
        return "single_agent", [{"batch_id": 1, "chapter_files": [c["file"] for c in chapters], "titles": [c["title"] for c in chapters], "total_bytes": total_bytes, "est_tokens": sum(c["est_tokens"] for c in chapters)}]

    batches: list[dict] = []
    cur_f, cur_t, cur_b, cur_tok = [], [], 0, 0
    for c in chapters:
        if cur_f and (cur_b + c["bytes"] > BATCH_TARGET_BYTES or len(cur_f) >= 5):
            batches.append({"batch_id": len(batches) + 1, "chapter_files": cur_f, "titles": cur_t, "total_bytes": cur_b, "est_tokens": cur_tok})
            cur_f, cur_t, cur_b, cur_tok = [], [], 0, 0
        cur_f.append(c["file"])
        cur_t.append(c["title"])
        cur_b += c["bytes"]
        cur_tok += c["est_tokens"]
    if cur_f:
        batches.append({"batch_id": len(batches) + 1, "chapter_files": cur_f, "titles": cur_t, "total_bytes": cur_b, "est_tokens": cur_tok})
    return "subagent_parallel", batches


def main():
    parser = argparse.ArgumentParser(description="Flatten and chunk raw documents into <=40KB Markdown chapters.")
    parser.add_argument("input", help="Source document path (PDF, DOCX, XLSX, HTML, MD, TXT)")
    parser.add_argument("--list-only", action="store_true", help="Output reconnaissance JSON without writing files")
    parser.add_argument("--split-dir", help="Target directory to write flattened chapter .md files")
    parser.add_argument("--json", action="store_true", help="Output JSON result summary")
    args = parser.parse_args()

    src_path = Path(args.input).expanduser().resolve()
    if not src_path.is_file():
        sys.exit(f"Error: Input file not found: {src_path}")

    try:
        full_text, meta = extract_document(src_path)
    except Exception as exc:
        sys.exit(f"Error extracting {src_path.name}: {exc}")

    if meta.get("error") == "OCR_REQUIRED":
        if args.json or args.list_only:
            print(json.dumps(meta, ensure_ascii=False, indent=2))
        else:
            sys.stderr.write(f"[!] OCR_REQUIRED: {meta['message']}\n")
        sys.exit(3)

    chapters = segment_chapters(full_text)
    dispatch_mode, batches = plan_batches(chapters)
    catalog = [{k: v for k, v in c.items() if k != "content"} for c in chapters]
    report = {
        "source_file": src_path.name,
        "total_pages": meta.get("total_pages", 1),
        "avg_chars_per_page": meta.get("avg_chars_per_page", 0),
        "total_chapters": len(catalog),
        "total_bytes": sum(c["bytes"] for c in catalog),
        "total_est_tokens": sum(c["est_tokens"] for c in catalog),
        "dispatch_mode": dispatch_mode,
        "recommended_batches": batches,
        "chapters": catalog,
    }

    if args.list_only or not args.split_dir:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    out_dir = Path(args.split_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    for c in chapters:
        (out_dir / c["file"]).write_text(c["content"], encoding="utf-8")
    (out_dir / "index.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    home_str = str(Path.home())
    out_str = str(out_dir).replace(home_str, "~", 1) if str(out_dir).startswith(home_str) else str(out_dir)
    report["output_dir"] = out_str
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"Flattened {src_path.name} -> {len(chapters)} chapters in {out_str} (mode: {dispatch_mode})")


if __name__ == "__main__":
    main()
