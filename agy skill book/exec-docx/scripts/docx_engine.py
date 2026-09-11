"""
DOCX Layout Engine (Enterprise Standard Edition) - 3-Tier Decoupled Architecture
Tier 0: SSOT Config & Formatting Primitives (Themes, WCAG contrast, XML cleaning, OOXML cell styling)
Tier 1: Atomic Cell Renderers & Geometry Solver (Data normalization, rich table/card cell atoms)
Tier 2: DOCXLayoutEngine Facade (High-level declarative layout API)
"""

import os, re, json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_ALIGN_MAP = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER, "right": WD_ALIGN_PARAGRAPH.RIGHT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}

# ==============================================================================
# TIER 0: SSOT CONFIG & FORMATTING PRIMITIVES
# ==============================================================================

def _clean_text(val: Any) -> str:
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(val)) if val is not None else ""

def _hex_to_rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return RGBColor(*(int(h[i:i+2], 16) for i in (0, 2, 4)))

def _contrast_color(bg_hex: str, dark_hex: str = "#334155", light_hex: str = "#F8FAFC", threshold: float = 0.65) -> RGBColor:
    h = bg_hex.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    return _hex_to_rgb(dark_hex if (0.299 * r + 0.587 * g + 0.114 * b) > threshold else light_hex)

def _format_cell(cell, bg_color: Optional[str] = None, left_border_color: Optional[str] = None, left_border_size: int = 24, all_borders_color: Optional[str] = None, all_borders_size: int = 4, v_align: Optional[str] = None):
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag in ("tcBorders", "shd", "vAlign"): tcPr.remove(child)
    if left_border_color:
        tcPr.append(parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="single" w:sz="{left_border_size}" w:space="0" w:color="{left_border_color.lstrip("#")}"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>'))
    elif all_borders_color:
        sz, col = all_borders_size, all_borders_color.lstrip("#")
        tcPr.append(parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{col}"/><w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{col}"/><w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{col}"/><w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{col}"/></w:tcBorders>'))
    if bg_color: tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{bg_color.lstrip("#")}"/>'))
    if v_align: tcPr.append(parse_xml(f'<w:vAlign {nsdecls("w")} w:val="{v_align}"/>'))

def _format_stat_val(v: Any, prefix: str = "", suffix: str = "") -> str:
    if isinstance(v, dict):
        prefix, suffix = v.get("prefix", prefix), v.get("suffix", suffix)
        v = v.get("val", v.get("value", ""))
    if isinstance(v, (int, float)):
        v_str = f"{v:,}" if isinstance(v, int) else f"{v:,.2f}".rstrip("0").rstrip(".")
        return _clean_text(f"{prefix}{v_str}{suffix}")
    return _clean_text(f"{prefix}{v}{suffix}")

def _load_theme_config() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, str]]:
    p = Path(__file__).parent / "themes.json"
    if not p.exists(): return {}, {}, {}
    with open(p, "r", encoding="utf-8") as f: raw = json.load(f)
    return raw.get("fonts", {}), raw.get("themes", {}), raw.get("global_colors", {})

FONTS, THEMES, GLOBAL_COLORS = _load_theme_config()

# ==============================================================================
# TIER 1: ATOMIC CELL RENDERERS & GEOMETRY SOLVER
# ==============================================================================

def _parse_item_dict(it: Any, default_tag: Optional[str] = None) -> Dict[str, Any]:
    if isinstance(it, dict): return it
    if isinstance(it, (list, tuple)):
        if len(it) >= 3: return {"tag": it[0], "title": it[1], "body": it[2]}
        if len(it) == 2: return {"title": it[0], "body": it[1]}
        if len(it) == 1: return {"body": it[0]}
    return {"body": str(it), "tag": default_tag}

def _render_table_cell(engine, cell, val: Any, col_idx: int, is_alt: bool, align: Optional[Union[str, WD_ALIGN_PARAGRAPH]] = None):
    _format_cell(cell, bg_color="#FFFFFF" if not is_alt else GLOBAL_COLORS.get("card_bg", "#F8FAFC"), v_align="center")
    if isinstance(val, dict) and "progress" in val:
        pv = max(0, min(100, int(val["progress"])))
        bar = f"[{'█' * int(round(pv / 10))}{'░' * (10 - int(round(pv / 10)))}] {pv}%"
        col = "#059669" if pv >= 80 else (engine.t.get("a", "#EC6A00") if pv >= 50 else engine.t.get("alert", "#E95119"))
        engine._p(cell, text=bar, sz=10, col=col, bold=True, sa=2, align=align or "center")
    elif isinstance(val, dict) and "badge" in val:
        b_cols = {"success": "#059669", "warning": engine.t.get("a", "#EC6A00"), "danger": engine.t.get("alert", "#E95119"), "info": engine.t.get("p", "#007A92")}
        engine._p(cell, text=f" [ {val['badge']} ] ", sz=10, col=b_cols.get(val.get("status", "info"), engine.t.get("p", "#007A92")), bold=True, sa=2, align=align or "center")
    else:
        is_num = isinstance(val, (int, float))
        txt = _format_stat_val(val) if is_num else str(val)
        engine._p(cell, text=txt, sz=11, col=engine.t.get("txt", "#0B0F19"), bold=(col_idx == 0), sa=2, align=align or ("right" if is_num else "left"))

def _render_vertical_step(engine, tbl, row_idx: int, d: Dict[str, Any], total_width: float):
    tag, title, body = d.get("tag") or d.get("badge") or d.get("step") or f"0{row_idx+1}", d.get("title", ""), d.get("body") or d.get("desc", "")
    c_tag, c_body = tbl.cell(row_idx, 0), tbl.cell(row_idx, 1)
    c_tag.width, c_body.width = Inches(0.65), Inches(total_width - 0.65)
    _format_cell(c_tag, v_align="top")
    _format_cell(c_body, left_border_color=GLOBAL_COLORS.get("border", "#CBD5E1"), left_border_size=8, v_align="top")
    engine._p(c_tag, text=str(tag), sz=13, col=d.get("acc") or d.get("border") or engine.t.get("p", "#007A92"), bold=True, sa=2)
    if title: engine._p(c_body, text=title, sz=11.5, col=engine.t.get("txt", "#0B0F19"), bold=True, sa=2)
    if body: engine._p(c_body, text=str(body), sz=10.5, col=GLOBAL_COLORS.get("subtitle", "#7E8287"), sa=2)

def _render_grid_cell(engine, cell, d: Dict[str, Any], is_pipe: bool):
    tag, title, body = d.get("tag") or d.get("badge") or d.get("step"), d.get("title", ""), d.get("body") or d.get("desc", "")
    acc = d.get("acc") or d.get("color") or d.get("border") or engine.t.get("p", "#007A92")
    _format_cell(cell, bg_color=d.get("bg", GLOBAL_COLORS.get("card_bg", "#F8FAFC")), left_border_color=acc, left_border_size=20 if is_pipe else 24, v_align="top")
    p_title = engine._p(cell, sa=2)
    if tag:
        r_b = p_title.add_run(f"[{_clean_text(tag)}] ")
        r_b.font.size, r_b.font.bold, r_b.font.color.rgb = Pt(10 if not is_pipe else 11), True, _hex_to_rgb(acc)
    if title:
        r_t = p_title.add_run(_clean_text(title))
        r_t.font.size, r_t.font.bold, r_t.font.color.rgb = Pt(11.5 if not is_pipe else 11), True, _hex_to_rgb(engine.t.get("txt", "#0B0F19"))
    if isinstance(body, list):
        for b_it in body:
            p_b = engine._p(cell, sa=2)
            r_dot = p_b.add_run("• ")
            r_dot.font.bold, r_dot.font.color.rgb = True, _hex_to_rgb(acc)
            r_txt = p_b.add_run(_clean_text(b_it))
            r_txt.font.size, r_txt.font.color.rgb = Pt(10.5), _hex_to_rgb(engine.t.get("txt", "#0B0F19"))
    elif body:
        engine._p(cell, text=str(body), sz=9.5 if is_pipe else 10.5, col=GLOBAL_COLORS.get("subtitle", "#7E8287") if is_pipe else engine.t.get("txt", "#0B0F19"), sa=2)

# ==============================================================================
# TIER 2: DOCX LAYOUT ENGINE FACADE
# ==============================================================================

class DOCXLayoutEngine:
    """Modern Enterprise DOCX Layout Engine with Noto Sans TC typography."""

    def __init__(self, theme: str = "ocean_executive", font: str = "Noto Sans TC"):
        self.theme_name = theme
        self.t = THEMES.get(theme, THEMES.get("ocean_executive", {"p": "#007A92", "s": "#2B5C8F", "a": "#EC6A00", "hl": "#F5E050", "alert": "#E95119", "card_bg": "#E6F2F5", "txt": "#0B0F19"}))
        self.font, self.doc = font, Document()
        self._init_styles()

    def _init_styles(self):
        st = self.doc.styles["Normal"]
        st.font.name, st.font.size = self.font, Pt(11)
        st.font.color.rgb = _hex_to_rgb(self.t.get("txt", "#0B0F19"))
        st.paragraph_format.line_spacing, st.paragraph_format.space_after = 1.0, Pt(4)
        st.element.rPr.append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Segoe UI" w:hAnsi="Segoe UI" w:eastAsia="{self.font}"/>'))

    def _p(self, container=None, text: str = "", sz: float = 11, col=None, bold: bool = False, italic: bool = False, sa: float = 2, sb: float = 0, align=None, keep: bool = False, font_name: Optional[str] = None):
        target = self.doc if container is None else container
        p = target.paragraphs[0] if (container is not None and len(container.paragraphs) == 1 and not container.paragraphs[0].text) else target.add_paragraph()
        p.paragraph_format.line_spacing, p.paragraph_format.space_after, p.paragraph_format.space_before = 1.0, Pt(sa), Pt(sb)
        if keep: p.paragraph_format.keep_with_next = True
        if align is not None: p.alignment = _ALIGN_MAP.get(align, align) if isinstance(align, str) else align
        if text:
            r = p.add_run(_clean_text(text))
            f_name = font_name or self.font
            r.font.size, r.font.bold, r.font.italic, r.font.name = Pt(sz), bold, italic, f_name
            r._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), f_name)
            if col is not None: r.font.color.rgb = _hex_to_rgb(col) if isinstance(col, str) else col
        return p

    def _spacer(self, pts: float = 6):
        p = self.doc.add_paragraph()
        p.paragraph_format.line_spacing, p.paragraph_format.space_after = 1.0, Pt(pts)

    def add_title(self, title: str, subtitle: Optional[str] = None, category: Optional[str] = None):
        if category: self._p(text=category.upper(), sz=11, col=self.t.get("p", "#007A92"), bold=True, sa=2)
        self._p(text=title, sz=22, col=self.t.get("txt", "#0B0F19"), bold=True, sa=4)
        if subtitle: self._p(text=subtitle, sz=12, col=GLOBAL_COLORS.get("subtitle", "#7E8287"), sa=12)

    def add_heading(self, text: str, level: int = 1):
        p = self.doc.add_paragraph()
        p.paragraph_format.keep_with_next, p.paragraph_format.line_spacing = True, 1.0
        cfg = {1: ("▶ ", 14, self.t.get("p", "#007A92"), 16, self.t.get("s", "#2B5C8F"), 14, 6), 2: ("▶ ", 12, self.t.get("s", "#2B5C8F"), 13.5, self.t.get("p", "#007A92"), 10, 4)}.get(level, ("", 11, self.t.get("txt", "#0B0F19"), 12, self.t.get("txt", "#0B0F19"), 8, 2))
        ch_arrow, arr_sz, arr_col, t_sz, t_col, sb, sa = cfg
        p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(sb), Pt(sa)
        if ch_arrow:
            r_arr = p.add_run(ch_arrow)
            r_arr.font.size, r_arr.font.bold, r_arr.font.color.rgb = Pt(arr_sz), True, _hex_to_rgb(arr_col)
        r_t = p.add_run(_clean_text(text))
        r_t.font.size, r_t.font.bold, r_t.font.color.rgb = Pt(t_sz), True, _hex_to_rgb(t_col)
        return p

    def add_paragraph(self, text: str, bold: bool = False, italic: bool = False, align: Optional[Union[str, WD_ALIGN_PARAGRAPH]] = None):
        return self._p(text=text, bold=bold, italic=italic, sa=4, align=align)

    def add_kpi_cards(self, kpis: List[Dict[str, Any]]):
        n = max(1, min(len(kpis), 4))
        tbl = self.doc.add_table(rows=1, cols=n)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, k in enumerate(kpis[:n]):
            cell = tbl.cell(0, i)
            col_acc = k.get("color", k.get("acc", self.t.get("p", "#007A92")))
            _format_cell(cell, bg_color=GLOBAL_COLORS.get("card_bg", "#F8FAFC"), left_border_color=col_acc, left_border_size=24, v_align="center")
            self._p(cell, text=_format_stat_val(k), sz=20, col=col_acc, bold=True, sa=2)
            chg = k.get("chg", "")
            if chg: self._p(cell, text=f"({chg})" if not str(chg).startswith("(") else str(chg), sz=9.5, col=col_acc, bold=True, sa=2)
            self._p(cell, text=k.get("label", ""), sz=10.5, col=GLOBAL_COLORS.get("subtitle", "#7E8287"), sa=0)
        self._spacer(8)

    def add_table(self, headers: List[str], rows: List[List[Any]], col_widths: Optional[List[float]] = None, col_weights: Optional[List[float]] = None, alignments: Optional[List[Union[str, WD_ALIGN_PARAGRAPH]]] = None, total_width: float = 7.0):
        n_cols = len(headers)
        tbl = self.doc.add_table(rows=len(rows) + 1, cols=n_cols)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        c_widths = col_widths[:n_cols] if col_widths else ([total_width * (w / (sum(col_weights[:n_cols]) or 1.0)) for w in col_weights[:n_cols]] if col_weights else None)

        for j, h in enumerate(headers):
            cell = tbl.cell(0, j)
            _format_cell(cell, bg_color=self.t.get("s", "#2B5C8F"), v_align="center")
            self._p(cell, text=h, sz=11, col=RGBColor(255, 255, 255), bold=True, sa=2, align=alignments[j] if (alignments and j < len(alignments)) else "left")

        for i, row in enumerate(rows):
            if len(row) == 1:
                c_first = tbl.cell(i + 1, 0)
                if n_cols > 1: c_first.merge(tbl.cell(i + 1, n_cols - 1))
                _format_cell(c_first, bg_color=self.t.get("card_bg", "#E6F2F5"), v_align="center")
                self._p(c_first, text=f"▶ {_clean_text(row[0])}", sz=11, col=self.t.get("p", "#007A92"), bold=True, sa=2)
                continue
            for j, val in enumerate(row[:n_cols]):
                _render_table_cell(self, tbl.cell(i + 1, j), val, j, i % 2 == 1, align=alignments[j] if (alignments and j < len(alignments)) else None)

        if c_widths:
            for row_obj in tbl.rows:
                for j, w in enumerate(c_widths): row_obj.cells[j].width = Inches(w)
        self._spacer(6)

    def _add_grid_container(self, n_items: int, cols: int, total_width: float, gutter: float) -> Tuple[Any, int, float]:
        n = max(1, min(cols, n_items, 4))
        w = (total_width - (n - 1) * gutter) / n
        tbl = self.doc.add_table(rows=(n_items + n - 1) // n, cols=2 * n - 1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for row in tbl.rows:
            for ci in range(2 * n - 1): row.cells[ci].width = Inches(w if ci % 2 == 0 else gutter)
        return tbl, n, w

    def add_items_layout(self, items: List[Union[Dict[str, Any], Tuple, List]], layout: str = "grid", cols: Optional[int] = None, total_width: float = 7.0, gutter: float = 0.15):
        if layout in ("vertical", "steps", "timeline"):
            tbl = self.doc.add_table(rows=len(items), cols=2)
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, it in enumerate(items): _render_vertical_step(self, tbl, i, _parse_item_dict(it, default_tag=f"0{i+1}"), total_width)
            self._spacer(6)
            return tbl

        is_pipe = layout in ("horizontal", "pipeline")
        n = max(1, min(cols or len(items), 4)) if not is_pipe else max(1, len(items))
        tbl, _, _ = self._add_grid_container(len(items), n, total_width, gutter)
        for idx, it in enumerate(items):
            _render_grid_cell(self, tbl.cell(idx // n, (idx % n) * 2), _parse_item_dict(it), is_pipe)
        self._spacer(8)
        return tbl

    def add_card_grid(self, cards: List[Dict[str, Any]], cols: int = 2, total_width: float = 7.0, gutter: float = 0.2):
        return self.add_items_layout(cards, layout="grid", cols=cols, total_width=total_width, gutter=gutter)

    def add_pipeline_flow(self, steps: List[Dict[str, str]], total_width: float = 7.0, gutter: float = 0.15):
        return self.add_items_layout(steps, layout="horizontal", total_width=total_width, gutter=gutter)

    def add_callout(self, text: str, title: Optional[str] = None, border_color: Optional[str] = None):
        col = border_color or self.t.get("p", "#007A92")
        tbl = self.doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        _format_cell(cell, bg_color=GLOBAL_COLORS.get("card_bg", "#F8FAFC"), left_border_color=col, left_border_size=24)
        if title: self._p(cell, text=title, sz=11.5, col=col, bold=True, sa=2)
        self._p(cell, text=text, sz=11, col=self.t.get("txt", "#0B0F19"), sa=2)
        self._spacer(6)

    def add_split_comparison(self, left_title: str, left_items: List[str], right_title: str, right_items: List[str], left_color: Optional[str] = None, right_color: Optional[str] = None):
        cards = [{"title": left_title, "body": left_items, "acc": left_color or self.t.get("p", "#007A92")}, {"title": right_title, "body": right_items, "acc": right_color or self.t.get("a", "#EC6A00")}]
        return self.add_items_layout(cards, layout="grid", cols=2)

    def add_step_flow(self, steps: List[Dict[str, str]], total_width: float = 7.0):
        return self.add_items_layout(steps, layout="vertical", total_width=total_width)

    def add_code_block(self, code_lines: Union[str, List[str]], title: Optional[str] = None):
        tbl = self.doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        _format_cell(cell, bg_color="#1E293B", left_border_color=self.t.get("p", "#007A92"), left_border_size=24)
        if title: self._p(cell, text=title, sz=10, col=RGBColor(148, 163, 184), bold=True, font_name="Consolas", sa=4)
        code_text = "\n".join(_clean_text(l) for l in code_lines) if isinstance(code_lines, list) else _clean_text(code_lines)
        self._p(cell, text=code_text, sz=10, col=RGBColor(56, 189, 248), font_name="Consolas", sa=2)
        self._spacer(6)

    def add_picture(self, image_path: str, width_inches: float = 6.0, caption: Optional[str] = None):
        if os.path.exists(image_path):
            p_img = self.doc.add_paragraph()
            p_img.alignment, p_img.paragraph_format.line_spacing = WD_ALIGN_PARAGRAPH.CENTER, 1.0
            p_img.add_run().add_picture(image_path, width=Inches(width_inches))
            if caption: self._p(text=f"Figure: {_clean_text(caption)}", sz=11, col=GLOBAL_COLORS.get("subtitle", "#7E8287"), italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)

    def save(self, output_path: str):
        out_dir = os.path.dirname(output_path)
        if out_dir: os.makedirs(out_dir, exist_ok=True)
        for elem in self.doc.settings.element.iter():
            if elem.tag.endswith("zoom") and f"{{{WORD_NS}}}percent" not in elem.attrib and "percent" not in elem.attrib:
                elem.set(f"{{{WORD_NS}}}percent", "100")
        self.doc.save(output_path)
