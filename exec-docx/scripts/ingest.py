#!/usr/bin/env python3
"""
Unified DOCX to Markdown Ingester for exec-docx.
Pure standard library implementation inspired by deep-mod.
Read -> Clean -> Elevate Structure -> Markdown Output.
"""
import argparse
import html
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

W_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_DECOMPRESSED_BYTES = 150 * 1024 * 1024

CN_CHAPTER_PATTERN = re.compile(r'^[壹貳參肆伍陸柒捌玖拾]+[、\s]')
CN_SECTION_PATTERN = re.compile(r'^[一二三四五六七八九十]+[、\s]')
CN_SUBSECTION_PATTERN = re.compile(r'^[（\(][一二三四五六七八九十]+[）\)]')
ORDERED_LIST_PATTERN = re.compile(r'^\d+[\.\、]')


def check_file_boundary(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    st_size = path.stat().st_size
    if st_size > MAX_FILE_BYTES:
        raise ValueError(f"File size exceeds safety limit ({st_size} > {MAX_FILE_BYTES} bytes): {path.name}")
    if not zipfile.is_zipfile(path):
        raise ValueError(f"File is not a valid zip archive: {path.name}")
    with zipfile.ZipFile(path) as z:
        uncompressed = sum(info.file_size for info in z.infolist())
        if uncompressed > MAX_DECOMPRESSED_BYTES:
            raise ValueError(f"Decompressed size exceeds limit ({uncompressed} > {MAX_DECOMPRESSED_BYTES} bytes): {path.name}")


def parse_run(r_elem: ET.Element) -> str:
    text_elem = r_elem.find("w:t", W_NS)
    if text_elem is None or not text_elem.text:
        return ""
    text = text_elem.text

    r_pr = r_elem.find("w:rPr", W_NS)
    is_bold = r_pr is not None and r_pr.find("w:b", W_NS) is not None
    is_italic = r_pr is not None and r_pr.find("w:i", W_NS) is not None
    is_underline = r_pr is not None and r_pr.find("w:u", W_NS) is not None

    color_val = ""
    if r_pr is not None:
        c_node = r_pr.find("w:color", W_NS)
        if c_node is not None:
            color_val = c_node.attrib.get(f"{{{W_NS['w']}}}val", "").upper()

    is_red = color_val in ("FF0000", "EE0000", "RED")
    has_leading = text.startswith(" ")
    has_trailing = text.endswith(" ")
    core = html.escape(text.strip())
    if not core:
        return text

    if is_red and is_underline:
        core = f'<ins><font color="#FF0000">{core}</font></ins>'
    elif is_red:
        core = f'<font color="#FF0000">{core}</font>'
    elif is_underline:
        core = f'<u>{core}</u>'

    if is_bold:
        core = f'**{core}**'
    if is_italic:
        core = f'*{core}*'

    return f"{' ' if has_leading else ''}{core}{' ' if has_trailing else ''}"


def parse_paragraph(p_elem: ET.Element, *, is_first_p: bool = False) -> str:
    runs = [parse_run(r) for r in p_elem.findall("w:r", W_NS)]
    text = "".join(runs).strip()
    if not text:
        return ""

    raw = "".join(t.text for t in p_elem.findall(".//w:t", W_NS) if t.text).strip()
    p_pr = p_elem.find("w:pPr", W_NS)
    style_val = ""
    if p_pr is not None:
        style_elem = p_pr.find("w:pStyle", W_NS)
        if style_elem is not None:
            style_val = style_elem.attrib.get(f"{{{W_NS['w']}}}val", "").lower()

    if is_first_p or "title" in style_val:
        return f"# {text}\n"
    if "heading1" in style_val or "heading 1" in style_val or CN_CHAPTER_PATTERN.match(raw):
        return f"## {text}\n"
    if "heading2" in style_val or "heading 2" in style_val or CN_SECTION_PATTERN.match(raw):
        return f"### {text}\n"
    if "heading3" in style_val or "heading 3" in style_val or CN_SUBSECTION_PATTERN.match(raw):
        return f"#### {text}\n"
    if ORDERED_LIST_PATTERN.match(raw):
        return f"{text}"
    if "list" in style_val or (p_pr is not None and p_pr.find("w:numPr", W_NS) is not None):
        return f"* {text}"
    if raw.startswith("註：") or raw.startswith("附註："):
        return f"> [!NOTE]\n> {text}"

    return f"{text}\n"


def parse_table(tbl_elem: ET.Element) -> str:
    rows = tbl_elem.findall("w:tr", W_NS)
    if not rows:
        return ""
    md_rows = []
    for r_idx, row in enumerate(rows):
        cells = row.findall("w:tc", W_NS)
        cell_texts = []
        for cell in cells:
            p_lines = [parse_paragraph(p).strip() for p in cell.findall("w:p", W_NS)]
            cell_texts.append("<br>".join(l for l in p_lines if l).replace("\n", " ").replace("|", "&#124;"))
        md_rows.append("| " + " | ".join(cell_texts) + " |")
        if r_idx == 0:
            md_rows.append("| " + " | ".join([":---"] * len(cells)) + " |")
    return "\n".join(md_rows) + "\n"


def ingest_docx(path: Path) -> str:
    check_file_boundary(path)
    with zipfile.ZipFile(path) as z:
        xml_bytes = z.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        body = root.find("w:body", W_NS)
        if body is None:
            return ""

        output = []
        first_p = True
        for elem in body:
            tag = elem.tag.split("}")[-1]
            if tag == "p":
                md_p = parse_paragraph(elem, is_first_p=first_p)
                if md_p.strip():
                    output.append(md_p)
                    first_p = False
            elif tag == "tbl":
                md_tbl = parse_table(elem)
                if md_tbl.strip():
                    output.append(md_tbl)

        return "\n".join(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified DOCX to Markdown Ingester")
    parser.add_argument("file", help="Path to DOCX file to ingest")
    parser.add_argument("--output", help="Optional path to save Markdown file")
    args = parser.parse_args()

    target_path = Path(args.file).resolve()
    result = ingest_docx(target_path)

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.write_text(result, encoding="utf-8")
        print(f"Ingested Markdown saved to: {out_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
