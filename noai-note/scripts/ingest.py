#!/usr/bin/env python3
"""Unified Minimal Ingester: Read -> Clean -> Chunk -> Output."""
import argparse, json, re, sys, unicodedata, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Consolidated filter pattern: zero-width chars, invisible control codes, (cid:xx), and standalone page numbers
CLEAN_PATTERN = re.compile(
    r'[\u200b-\u200d\ufeff\u2060\u202a-\u202e\u2066-\u2069\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'
    r'|\(cid:\d+\)|\ufffd'
    r'|^\s*(?:[-—~]*\s*\d+\s*[-—~]*|Page\s+\d+(?:\s*(?:of|/)\s*\d+)?|\d+\s*/\s*\d+)\s*$',
    re.MULTILINE
)
CHAPTER_PATTERN = re.compile(
    r'^(?:#\s+|第[0-9一二三四五六七八九十]+章\s+|Chapter\s+\d+[:\s]+)(.+)$',
    re.MULTILINE
)


def read_raw(p: Path) -> str:
    """Phase 1: Format ingestion"""
    ext = p.suffix.lower()
    if ext == ".docx":
        with zipfile.ZipFile(p) as z:
            tree = ET.fromstring(z.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            return "\n".join("".join(t.text for t in n.findall(".//w:t", ns) if t.text) for n in tree.findall(".//w:p", ns))
    if ext == ".pdf":
        try:
            import pypdf
            return "\n".join(pg.extract_text() or "" for pg in pypdf.PdfReader(str(p)).pages)
        except Exception:
            return ""
    if ext in (".md", ".txt"):
        return p.read_text(encoding="utf-8-sig", errors="replace")
    return ""


def clean_text(raw: str) -> str:
    """Phase 2: Single-pass sanitization (NFKC normalization + artifact removal)"""
    text = re.sub(r'(\b[A-Za-z]+)-\n([A-Za-z]+\b)', r'\1\2', unicodedata.normalize("NFKC", raw))
    cleaned = CLEAN_PATTERN.sub("", text)
    lines = [L.strip() for L in cleaned.splitlines() if L.strip()]
    return "\n".join(lines)


def chunk_chapters(text: str, source: str) -> list[dict]:
    """Phase 3: Flat chapter chunking (Pattern A)"""
    matches = list(CHAPTER_PATTERN.finditer(text))
    if not matches:
        return [{"source": source, "chapter": "Full Document", "content": text}]
    chunks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunks.append({"source": source, "chapter": m.group(0).strip(), "content": text[start:end].strip()})
    return chunks


def main():
    p = argparse.ArgumentParser(description="Parse and clean documents with chapter chunking")
    p.add_argument("input", help="Target file or directory path")
    p.add_argument("--format", choices=["stream", "json"], default="stream", help="Output serialization format")
    p.add_argument("-o", "--output", help="Optional destination file path")
    p.add_argument("--split-dir", help="Directory to export individual chapter files")
    args = p.parse_args()

    inp, exts = Path(args.input).resolve(), {".docx", ".pdf", ".md", ".txt"}
    files = [inp] if inp.is_file() and inp.suffix.lower() in exts else sorted(x for x in inp.rglob("*") if x.suffix.lower() in exts) if inp.is_dir() else []
    if not files:
        sys.exit(f"No valid docs in {inp}")

    records = [c for f in files if (raw := read_raw(f)) for c in chunk_chapters(clean_text(raw), f.name)]

    if args.split_dir:
        dest_dir = Path(args.split_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)
        for i, r in enumerate(records, 1):
            name = re.sub(r'[\\/*?:"<>|#\s]+', '_', r["chapter"]).strip("_")
            (dest_dir / f"{i:02d}_{name}.md").write_text(f"# {r['chapter']}\n\n{r['content']}\n", encoding="utf-8-sig")
        print(f"Exported {len(records)} chapters to {dest_dir}")
        return

    out = json.dumps(records, ensure_ascii=False, indent=2) if args.format == "json" else "\n\n".join(
        f"=== [SOURCE: {r['source']} | CHAPTER: {r['chapter']}] ===\n{r['content']}" for r in records
    )
    if args.output:
        dest = Path(args.output).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()
