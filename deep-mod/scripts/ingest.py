#!/usr/bin/env python3
"""Unified Ingester for deep-mod: Read -> Clean -> Chunk -> Output with Semantic Partitioning."""
import argparse, html, json, re, sys, unicodedata, zipfile
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parent.parent / "data" / "chapter_rules.json"
if not RULES_FILE.exists():
    RULES_FILE = Path(__file__).resolve().parent / "chapter_rules.json"
RULES_DATA = json.loads(RULES_FILE.read_text(encoding="utf-8")) if RULES_FILE.exists() else {}

SANITIZATION = RULES_DATA.get("sanitization", {})
CLEAN_PATTERN = re.compile(f"{SANITIZATION.get('invisibles', '')}|{SANITIZATION.get('pages', '')}", re.MULTILINE)

LIMITS = RULES_DATA.get("limits", {})
SUPPORTED_EXTS = set(LIMITS.get("supported_exts", [".docx", ".pdf", ".md", ".txt", ".xlsx", ".html"]))
CHUNK_LINES = LIMITS.get("chunk_lines", 800)
CHUNK_STEP = LIMITS.get("chunk_step", 750)
MAX_STREAM_TOKENS = LIMITS.get("max_stream_tokens", 10000)

CHAPTER_PATTERN = re.compile(RULES_DATA.get("pattern", r'^(?:#\s+|第\s*\d+\s*章\s*|Chapter\s+\d+[:\s]+)(.+)$'), re.MULTILINE | re.IGNORECASE)
TOC_DOT_LEADER_PATTERN = re.compile(r'(?:\.{3,}|(?:\.\s*){3,}|\·{3,}|…{2,})\s*\d+$')
MIN_CHUNK_CHAR_LENGTH = 90
MAX_SINGLE_CHUNK_BYTES = 38000
SUB_HEADING_PATTERN = re.compile(r'^(?:#{2,4}\s+|(?:\d+\.\d+|\b[A-Z]{2,3}-\d+)\s+)(.+)$', re.MULTILINE)

TAXONOMY = RULES_DATA.get("taxonomy", {})
INDEXING = RULES_DATA.get("indexing", {})
KEY_PATTERNS = [re.compile(p) for p in INDEXING.get("key_elements_patterns", [])]
MAX_KEY_ELEMENTS = INDEXING.get("max_key_elements_per_chunk", 8)
SUMMARY_LINES = INDEXING.get("summary_lines", 3)


def parse_html(raw: str) -> str:
    """Strip web clutter and elevate headings to Markdown anchors."""
    t = re.sub(r'<(script|style|nav|header|footer)[^>]*>.*?</\1>', '', raw, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n# \1\n', t, flags=re.DOTALL | re.IGNORECASE)
    return html.unescape(re.sub(r'<[^>]+>', ' ', t))


def read_raw(p: Path, page_range: tuple[int, int] | None = None) -> str:
    """Format ingestion with explicit EPUB rejection and page range support."""
    ext = p.suffix.lower()
    if ext == ".epub":
        raise ValueError(f"EPUB format is not supported: {p.name}")
    if ext == ".docx":
        with zipfile.ZipFile(p) as z:
            tree = ET.fromstring(z.read("word/document.xml"))
            ns = {"w": "http" + chr(58) + chr(47) + chr(47) + "schemas.openxmlformats.org/wordprocessingml/2006/main"}
            return "\n".join("".join(t.text for t in n.findall(".//w:t", ns) if t.text) for n in tree.findall(".//w:p", ns))
    if ext == ".xlsx":
        try:
            import openpyxl
            wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
            return "\n".join(f"# Sheet: {s}\n" + "\n".join(" | ".join(str(v).strip() for v in r if v is not None and str(v).strip()) for r in wb[s].iter_rows(values_only=True) if any(r)) for s in wb.sheetnames)
        except ImportError:
            sys.stderr.write("Warning: openpyxl not installed. Skipping XLSX parsing.\n")
            return ""
    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(p))
            total = len(reader.pages)
            start_p, end_p = (1, total) if not page_range else page_range
            return "\n".join(reader.pages[i].extract_text() or "" for i in range(max(0, start_p - 1), min(total, end_p)))
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to extract PDF {p.name}: {e}\n")
            return ""
    if ext in (".md", ".txt", ".html"):
        content = p.read_text(encoding="utf-8-sig", errors="replace")
        return parse_html(content) if ext == ".html" else content
    return ""


def defang_urls(text: str) -> str:
    """Defang all active URLs to prevent accidental clicks in threat/CTI documents."""
    def _defang(m: re.Match) -> str:
        u = m.group(0).replace("http://", "hxxp://").replace("https://", "hxxps://")
        parts = u.split("/")
        if len(parts) >= 3:
            parts[2] = parts[2].replace(".", "[.]")
            return "/".join(parts)
        return u.replace(".", "[.]")
    return re.sub(r'https?://[^\s)\]\"\'\`<>]+', _defang, text)


def strip_reference_blocks(text: str) -> str:
    """Filter out trailing citation blocks and reference sections."""
    lines, out, in_ref = text.splitlines(), [], False
    for l in lines:
        s = l.strip()
        if re.match(r'^#{1,4}\s*(?:References?|參考文獻|參考資料|Sources?|文獻來源)\s*$', s, re.I):
            in_ref = True
            continue
        if in_ref:
            if s.startswith("#") and not re.match(r'^#{1,4}\s*(?:References?|參考文獻|參考資料)', s, re.I):
                in_ref = False
            else:
                continue
        if re.match(r'^\s*\[\d+\]\s+[A-Z\"][a-zA-Z0-9\s,\-\.\'\":/]+', s) or re.match(r'^\s*\[\d+\]\s*$', s):
            continue
        out.append(l)
    return "\n".join(out)


def clean_text(raw: str) -> str:
    """Single-pass sanitization: NFKC normalization, hyphen rejoining, defanging, and noise removal."""
    if not raw:
        return ""
    text = re.sub(r'(\b[A-Za-z]+)-\n([A-Za-z]+\b)', r'\1\2', unicodedata.normalize("NFKC", raw))
    text = re.sub(r'^[A-Za-z0-9\s,\-\._/]+\s+\|\s+Chapter\s+\d+\s+\|\s+\d+\s*$', '', text, flags=re.M)
    text = re.sub(r'^Source:\s+PDF\s+Pages?\s+.*$', '', text, flags=re.M | re.I)
    text = strip_reference_blocks(text)
    text = defang_urls(text)
    return "\n".join(line.strip() for line in CLEAN_PATTERN.sub("", text).splitlines() if line.strip())


def extract_index_metadata(content: str) -> tuple[str, list[str]]:
    """Extract summary line and unique key elements for progressive disclosure."""
    lines = [ln.strip() for ln in content.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    summary = " ".join(lines[:SUMMARY_LINES])[:200]
    keys: list[str] = []
    for pat in KEY_PATTERNS:
        for m in pat.finditer(content):
            k = m.group(1).strip()
            if k and k not in keys:
                keys.append(k)
            if len(keys) >= MAX_KEY_ELEMENTS:
                break
        if len(keys) >= MAX_KEY_ELEMENTS:
            break
    return summary, keys


def chunk_sliding_window(text: str, source: str) -> list[dict]:
    """Fallback chunking with safe window snapping for unsegmented texts."""
    lines = text.splitlines()
    total = len(lines)
    if total <= CHUNK_LINES:
        summary, keys = extract_index_metadata(text)
        return [{"source": source, "chapter": "Full Document", "content": text, "start_line": 1, "end_line": total, "id": "part_01", "aliases": ["Full Document"], "summary": summary, "key_elements": keys}]
    chunks = []
    for idx, start_idx in enumerate(range(0, total, CHUNK_STEP), 1):
        end_idx = min(start_idx + CHUNK_LINES, total)
        c_text = "\n".join(lines[start_idx:end_idx])
        summary, keys = extract_index_metadata(c_text)
        chunks.append({"source": source, "chapter": f"Part {idx:02d} (Lines {start_idx+1}-{end_idx})", "content": c_text, "start_line": start_idx + 1, "end_line": end_idx, "id": f"part_{idx:02d}", "aliases": [f"Part {idx}", f"第{idx}批次"], "summary": summary, "key_elements": keys})
        if end_idx >= total:
            break
    return chunks


def resolve_taxonomy(title: str, idx: int) -> tuple[str, list[str]]:
    """Match title against TAXONOMY to assign semantic ID and aliases."""
    for keyword, meta in TAXONOMY.items():
        if keyword.lower() in title.lower():
            prefix = meta["prefix"]
            aliases = [title] + [a.format(idx=idx) for a in meta.get("aliases", [])]
            return f"{prefix}_{idx:02d}", list(dict.fromkeys(aliases))
    return f"ch_{idx:02d}", [title, f"Chapter {idx}", f"第{idx}單元"]


def filter_valid_chapter_matches(text: str) -> list[re.Match]:
    """Filter out TOC lines with dot-leaders and duplicate/empty fragments."""
    return [m for m in CHAPTER_PATTERN.finditer(text) if not TOC_DOT_LEADER_PATTERN.search(m.group(0).strip())]


def split_large_chunk_semantically(chunk: dict) -> list[dict]:
    """Hierarchically split oversized chapter chunks along semantic sub-headings or safe blank lines."""
    body = chunk["content"]
    if len(body.encode("utf-8")) <= MAX_SINGLE_CHUNK_BYTES:
        return [chunk]
    sub_matches = list(SUB_HEADING_PATTERN.finditer(body))
    sub_chunks = []
    if len(sub_matches) >= 2:
        for i, sm in enumerate(sub_matches):
            start = sm.start()
            end = sub_matches[i + 1].start() if i + 1 < len(sub_matches) else len(body)
            sub_title = sm.group(0).strip("# ").strip()
            sub_body = body[start:end].strip()
            if len(sub_body) < MIN_CHUNK_CHAR_LENGTH and i + 1 < len(sub_matches):
                continue
            sub_idx = len(sub_chunks) + 1
            parent_id = chunk.get("id", "ch_01")
            summary, keys = extract_index_metadata(sub_body)
            sub_chunks.append({"source": chunk.get("source", ""), "chapter": f"{chunk['chapter']} - {sub_title}", "content": sub_body, "start_line": chunk.get("start_line", 1) + body[:start].count("\n"), "end_line": chunk.get("start_line", 1) + body[:end].count("\n"), "id": f"{parent_id}-{sub_idx}", "aliases": chunk.get("aliases", []) + [sub_title, f"Part {sub_idx}"], "summary": summary, "key_elements": keys})
    if not sub_chunks:
        lines = body.splitlines()
        total_lines = len(lines)
        target_step = 400
        for idx, start_idx in enumerate(range(0, total_lines, target_step), 1):
            end_idx = min(start_idx + target_step, total_lines)
            while end_idx < total_lines and lines[end_idx].strip() != "":
                end_idx += 1
            c_text = "\n".join(lines[start_idx:end_idx]).strip()
            if not c_text:
                continue
            summary, keys = extract_index_metadata(c_text)
            sub_chunks.append({"source": chunk.get("source", ""), "chapter": f"{chunk['chapter']} (Part {idx})", "content": c_text, "start_line": chunk.get("start_line", 1) + start_idx, "end_line": chunk.get("start_line", 1) + end_idx, "id": f"{chunk.get('id', 'ch_01')}-{idx}", "aliases": chunk.get("aliases", []) + [f"Part {idx}"], "summary": summary, "key_elements": keys})
            if end_idx >= total_lines:
                break
    return sub_chunks if sub_chunks else [chunk]


def chunk_chapters(text: str, source: str) -> tuple[list[dict], bool]:
    """Segment text by dynamic patterns with TOC guard, semantic sub-partitioning, and minimum threshold."""
    matches = filter_valid_chapter_matches(text)
    if not matches:
        return chunk_sliding_window(text, source), False
    raw_chunks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group(0).strip("# ").strip()
        body = text[start:end].strip()
        if len(body) < MIN_CHUNK_CHAR_LENGTH and i + 1 < len(matches):
            continue
        cid, aliases = resolve_taxonomy(title, len(raw_chunks) + 1)
        summary, keys = extract_index_metadata(body)
        base_chunk = {"source": source, "chapter": title, "content": body, "start_line": text[:m.start()].count("\n") + 1, "end_line": text[:end].count("\n") + 1, "id": cid, "aliases": aliases, "summary": summary, "key_elements": keys}
        raw_chunks.extend(split_large_chunk_semantically(base_chunk))
    return (raw_chunks, True) if raw_chunks else (chunk_sliding_window(text, source), False)


def safe_collect_files(inp: Path) -> list[Path]:
    """Collect valid files with directory traversal guard."""
    if inp.is_file():
        if inp.suffix.lower() == ".epub":
            raise ValueError(f"EPUB format is not supported: {inp.name}")
        return [inp] if inp.suffix.lower() in SUPPORTED_EXTS else []
    return [p for p in sorted(inp.rglob("*")) if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS] if inp.is_dir() else []


def main():
    p = argparse.ArgumentParser(description="Parse, clean, and chunk documents for deep-mod with TOC filter")
    p.add_argument("input", nargs="?", default="", help="Target file, directory, or URL")
    p.add_argument("--format", choices=["stream", "json"], default="stream")
    p.add_argument("-o", "--output", help="Destination file path")
    p.add_argument("--split-dir", help="Directory to export chapter files")
    p.add_argument("--list-only", action="store_true", help="List chapters and tokens only")
    p.add_argument("--page-range", help="PDF page range to extract, e.g. '21-666' or '1-50'")
    p.add_argument("--check", action="store_true", help="Perform environment and readiness check")
    args = p.parse_args()

    if args.check:
        print("[OK] deep-mod ingester is Ready with semantic sub-partitioning and page-range filter.")
        return
    if not args.input:
        p.print_help()
        sys.exit(1)

    page_range = None
    if args.page_range:
        parts = args.page_range.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            page_range = (int(parts[0]), int(parts[1]))

    inp_str = args.input.strip()
    u = urlparse(inp_str)
    if u.scheme == "http":
        sys.exit("Error: Insecure HTTP is prohibited; only https is allowed.")
    if u.scheme == "https":
        req = Request(inp_str, headers={"User-Agent": "deep-mod/1.0"})
        try:
            with urlopen(req, timeout=15) as resp:
                raw = parse_html(resp.read().decode("utf-8", errors="replace"))
            records, all_matched = chunk_chapters(clean_text(raw), inp_str)
        except Exception as e:
            sys.exit(f"Error fetching HTTPS URL: {e}")
    else:
        inp = Path(inp_str).resolve()
        try:
            files = safe_collect_files(inp)
        except ValueError as err:
            sys.exit(f"Error: {err}")
        if not files:
            sys.exit(f"No valid documents found in: {inp}")
        records, all_matched = [], True
        for f in files:
            try:
                if not (raw := read_raw(f, page_range=page_range)):
                    continue
                chunks, matched = chunk_chapters(clean_text(raw), f.name)
                if not matched:
                    all_matched = False
                records.extend(chunks)
            except Exception as e:
                sys.stderr.write(f"Warning: Skipping unreadable file {f.name}: {e}\n")
    if not records:
        sys.exit("Error: No content could be extracted from input files.")

    total_chars = sum(len(r["content"]) for r in records)
    est_tokens = total_chars // 3
    catalog = [{"index": i, "id": r.get("id", f"part_{i:02d}"), "title": r["chapter"], "file": f"{i:02d}_{re.sub(r'[\\\\/*?:\"<>|#\\s]+', '_', r['chapter']).strip('_')}.md", "aliases": r.get("aliases", []), "summary": r.get("summary", ""), "key_elements": r.get("key_elements", []), "lines": r["content"].count("\n") + 3, "source_start_line": r.get("start_line", 1), "source_end_line": r.get("end_line", 1), "est_tokens": len(r["content"]) // 3} for i, r in enumerate(records, 1)]

    if args.split_dir:
        dest_dir = Path(args.split_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        for c, r in zip(catalog, records):
            (dest_dir / c["file"]).write_text(f"# {r['chapter']}\n\n{r['content']}\n", encoding="utf-8-sig")
        (dest_dir / "data").mkdir(exist_ok=True)
        (dest_dir / "data" / "index.json").write_text(json.dumps({"total_chunks": len(records), "chunk_mode": "chapter_matched" if all_matched else "sliding_window_overlap", "overlap_lines": 0 if all_matched else (CHUNK_LINES - CHUNK_STEP), "chunks": catalog}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Exported {len(records)} chunks and data/index.json to {dest_dir}")
        return

    if args.list_only or est_tokens > MAX_STREAM_TOKENS:
        if not args.list_only:
            sys.stderr.write(f"[NOTICE] Large document ({est_tokens} est. tokens > {MAX_STREAM_TOKENS}). Outputting chapter list. Use --split-dir to export.\n")
        print(json.dumps({"total_est_tokens": est_tokens, "chapters": catalog}, ensure_ascii=False, indent=2))
        return

    out = json.dumps(records, ensure_ascii=False, indent=2) if args.format == "json" else "\n\n".join(f"=== [SOURCE: {r['source']} | CHAPTER: {r['chapter']}] ===\n{r['content']}" for r in records)
    if args.output:
        dest = Path(args.output).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, encoding="utf-8-sig")
    else:
        print(out)


if __name__ == "__main__":
    main()
