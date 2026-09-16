#!/usr/bin/env python3
"""
Universal Composable PDF Layout Engine (ReportLab) - 4-Tier Architecture
Layer 0: SSOT Config (themes.json + CJK fonts)
Layer 1: Pure Geometry Solver & Card Factory (calc_cols, build_card, build_split_row)
Layer 2: Semantic Facades (Pill Badges, Flow, Action Board, KPI Row, Checklist, Hero Header, Tables, Charts)
Layer 3: Master Document Generators (1-Pager Infographics & Multi-Page Reports)
"""

import os, re, json, argparse, contextvars
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.legends import Legend

# ==============================================================================
# LAYER 0: SSOT CONFIGURATION & FONT DISCOVERY
# ==============================================================================

def load_theme_config() -> Dict[str, Any]:
    for p in [Path(__file__).parent / "themes.json" if "__file__" in globals() else None,
             Path.home() / ".gemini/config/skills/pdf/scripts/themes.json",
             Path.home() / ".gemini/skills/pdf/scripts/themes.json"]:
        if p and p.exists():
            with open(p, "r", encoding="utf-8") as f: return json.load(f)
    return {"fonts": {}, "themes": {}, "global_colors": {}, "geometry": {}}

def load_detox_rules() -> Dict[str, Any]:
    for p in [Path(__file__).parent / "rules_gate.json" if "__file__" in globals() else None,
             Path.home() / ".gemini/hooks/rules_gate.json"]:
        if p and p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f: return json.load(f)
            except Exception: pass
    return {}

_CFG = load_theme_config()
_DETOX_RULES = load_detox_rules()
_THEMES, _GC = _CFG.get("themes", {}), _CFG.get("global_colors", {})
_GEO = _CFG.get("geometry", {
    "page_printable_width": 540.0,
    "grid_gap": 10.0,
    "card_padding": 4.5,
    "card_radius": 4.0,
    "pill_radius": 0.50,
    "card_border_width": 0.75,
    "pipeline_height": 50.0,
    "action_board_height": 70.0,
    "kpi_row_height": 52.0,
    "chart_width": 240.0,
    "chart_height": 115.0,
})
_current_theme = contextvars.ContextVar("current_theme", default="light")

def get_theme_palette(theme_name: Optional[str] = None) -> Dict[str, Any]:
    th = _THEMES.get(theme_name or _current_theme.get(), _THEMES.get("light", {}))
    cd = th.get("colors", {})
    acc = _CFG.get("accent_catalog", {})
    
    p = colors.HexColor(cd.get("cyan", acc.get("teal", "#007A92")))
    s = colors.HexColor(cd.get("text_sub", acc.get("denim", "#2B5C8F")))
    a = colors.HexColor(cd.get("amber", acc.get("orange", "#EC6A00")))
    hl = colors.HexColor(cd.get("pink", acc.get("magenta", "#FF0080")))
    alert = colors.HexColor(cd.get("pink", acc.get("red_orange", "#E95119")))
    emerald = colors.HexColor(cd.get("emerald", acc.get("emerald", "#10B981")))
    
    txt = colors.HexColor(cd.get("text_primary", "#0B0F19"))
    muted = colors.HexColor(cd.get("text_muted", "#7E8287"))
    border = colors.HexColor(cd.get("border", "#CBD5E1"))
    bg = colors.HexColor(cd.get("bg", "#FFFFFF"))
    card = colors.HexColor(cd.get("card", "#F8FAFC"))
    
    return {
        "primary": p, "secondary": s, "accent": a, "highlight": hl, "alert": alert, "emerald": emerald,
        "dark": txt, "text_primary": txt,
        "muted": muted, "text_muted": muted,
        "border": border, "bg": bg, "card": card,
        "pink_bg": colors.HexColor("#FEF2F2"), "green_bg": colors.HexColor("#ECFDF5"),
        "yellow": colors.HexColor("#FEF08A"), "chart_palette": [p, s, a, hl, alert, emerald]
    }

def resolve_color(c: Any, default: Optional[colors.Color] = None) -> colors.Color:
    """Polymorphic Color Resolver: Supports ReportLab Color, Hex strings (#RRGGBB), and theme token names."""
    if isinstance(c, colors.Color):
        return c
    if isinstance(c, str):
        if c.startswith("#"):
            return colors.HexColor(c)
        pal = get_theme_palette()
        if c in pal and isinstance(pal[c], colors.Color):
            return pal[c]
        acc = _CFG.get("accent_catalog", {})
        if c in acc:
            return colors.HexColor(acc[c])
    return default or get_theme_palette()["primary"]

def get_cjk_font() -> str:
    for f_cfg in _CFG.get("fonts", {}).values():
        name = f_cfg.get("name", "CustomCJK")
        for p_str in f_cfg.get("paths", []):
            p = Path(os.path.expanduser(p_str))
            if p.exists():
                try:
                    pdfmetrics.registerFont(TTFont(name, str(p)))
                    return name
                except Exception: pass
        fallback = f_cfg.get("fallback")
        if fallback:
            try:
                pdfmetrics.registerFont(UnicodeCIDFont(fallback))
                return fallback
            except Exception: pass
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
        return "MSung-Light"
    except Exception: return "Helvetica"

CJK_FONT = get_cjk_font()
FONT_NAME = CJK_FONT
BASE_FONT_SZ = 10.5

def clean_text(s: Any) -> str:
    if s is None: return ""
    text_str = str(s)
    tech_terms = _DETOX_RULES.get("tech_terms_zh", {})
    for src, target in tech_terms.items():
        if src in text_str: text_str = text_str.replace(src, target)
    buzz_map = {
        "賦能": "強化", "閉環": "完整循環", "落地": "推行", "抓手": "著力點",
        "助力": "協助", "打法": "策略", "底層邏輯": "核心原理", "顆粒度": "精細度",
        "復盤": "檢討", "深耕細作": "扎實經營", "體感": "直觀感受", "打造": "建置",
        "雙刃劍": "雙面刃", "組合拳": "多元措施", "頂層設計": "整體規劃", "對標": "借鑑"
    }
    for w, subst in buzz_map.items():
        if w in text_str: text_str = text_str.replace(w, subst)
    text_str = re.sub(r'[𐀀-]', '', text_str)
    parts = re.split(r'(</?(?:b|i|u|font|br|super|sub|strike)(?:\s+[^>]*)?>)', text_str, flags=re.IGNORECASE)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+);)', '&amp;', parts[i]).replace('<', '&lt;').replace('>', '&gt;')
    return "".join(parts)

# ==============================================================================
# LAYER 1: PURE GEOMETRY SOLVER & UNIVERSAL CARD FACTORY
# ==============================================================================

def calc_cols(total_w: float, n_or_weights: Union[int, List[float]], gap: float = 10.0) -> List[float]:
    """SSOT Geometry: Partitions total width into columns dynamically."""
    if isinstance(n_or_weights, int):
        n = max(1, n_or_weights)
        return [(total_w - (n - 1) * gap) / n] * n
    weights = [float(w) for w in n_or_weights]
    n, tot = len(weights), sum(weights) or 1.0
    if n == 0: return [total_w]
    return [(total_w - (n - 1) * gap) * (w / tot) for w in weights]

def _p(text: str, sz: float = BASE_FONT_SZ, col: Any = None, bold: bool = False, align: int = 0, lead: Optional[float] = None) -> Paragraph:
    """SSOT Typography Atom: Strict >= 10.5pt rule & golden leading."""
    actual_sz = max(BASE_FONT_SZ, float(sz))
    pal = get_theme_palette()
    c = resolve_color(col, pal["dark"]) if col else pal["dark"]
    st = ParagraphStyle(f"p_{actual_sz}_{bold}_{align}_{hash(c)}", fontName=CJK_FONT, fontSize=actual_sz, leading=lead or (actual_sz * 1.35), textColor=c, alignment=align)
    cleaned = clean_text(text)
    return Paragraph(f"<b>{cleaned}</b>" if bold and not str(cleaned).startswith("<b>") else str(cleaned), st)

def build_card(content: Any, width: float, height: Optional[float] = None, bg: Optional[Union[colors.Color, str]] = None, border: Optional[Union[colors.Color, str]] = None, border_width: Optional[float] = None, radius: Optional[float] = None, pad: Optional[float] = None, valign: str = 'MIDDLE') -> Table:
    """SSOT Card Factory: Single point for all rounded container rendering."""
    pal = get_theme_palette()
    bw = border_width if border_width is not None else _GEO.get("card_border_width", 0.75)
    rad = radius if radius is not None else _GEO.get("card_radius", 4.0)
    p = pad if pad is not None else _GEO.get("card_padding", 6.0)
    bg_col = resolve_color(bg, pal["card"])
    border_col = resolve_color(border, pal["border"])
    t = Table([[content if isinstance(content, list) else [content]]], colWidths=[width], rowHeights=[height] if height else None)
    t.hAlign = "LEFT"
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), bg_col), ('BOX', (0,0), (-1,-1), bw, border_col), ('ROUNDEDCORNERS', [rad, rad, rad, rad]), ('VALIGN', (0,0), (-1,-1), valign), ('TOPPADDING', (0,0), (-1,-1), p), ('BOTTOMPADDING', (0,0), (-1,-1), p), ('LEFTPADDING', (0,0), (-1,-1), p), ('RIGHTPADDING', (0,0), (-1,-1), p)]))
    return t

def build_split_row(cols_content: List[Any], weights: Optional[List[float]] = None, total: float = _GEO["page_printable_width"], gap: float = _GEO["grid_gap"], row_height: Optional[float] = None, valign: str = 'MIDDLE') -> Table:
    """SSOT Multi-Column Slot: Single point for horizontal layout and equal-height alignment."""
    n = len(cols_content)
    col_ws = calc_cols(total, weights or n, gap=gap)
    final_w, final_c = [], []
    for i, (w, c) in enumerate(zip(col_ws, cols_content)):
        final_w.append(w); final_c.append(c)
        if i < n - 1 and gap > 0: final_w.append(gap); final_c.append("")
    t = Table([final_c], colWidths=final_w, rowHeights=[row_height] if row_height else None)
    t.hAlign = "LEFT"
    t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), valign), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0)]))
    return t

# ==============================================================================
# LAYER 2: SEMANTIC FACADES (Zero Redundant Math)
# ==============================================================================

def build_pill_badge(text: str, bg: Optional[Union[colors.Color, str]] = None, fg: Optional[Union[colors.Color, str]] = None, font_size: float = 12.0, height: float = 22.0, total: float = _GEO["page_printable_width"]) -> Table:
    pal = get_theme_palette()
    fg_col = resolve_color(fg, colors.white)
    bg_col = resolve_color(bg, pal["primary"])
    p = _p(f"<b>{text}</b>", sz=font_size, col=fg_col, align=1)
    w = min(total, max(120.0, sum(1.15 if ord(c) > 127 else 0.65 for c in str(text)) * font_size + 24.0))
    return build_card(p, width=w, height=height, bg=bg_col, border_width=0, radius=height/2, pad=0)

def build_pipeline_flow(steps: List[Dict[str, Any]], total: float = _GEO["page_printable_width"], uniform_height: float = _GEO["pipeline_height"], gap: float = _GEO["grid_gap"]) -> Table:
    pal = get_theme_palette()
    n = len(steps)
    col_ws = calc_cols(total, n, gap=gap)
    row_cells, row_w = [], []
    for i, st in enumerate(steps):
        cell_w = col_ws[i]
        paras = [_p(f"<b>{st.get('step', f'0{i+1}')}</b>", sz=BASE_FONT_SZ, col=pal["primary"], align=1), Spacer(1, 1), _p(st.get("title", ""), sz=BASE_FONT_SZ, col=pal["dark"], align=1, lead=14.0)]
        if st.get("desc"): paras.append(_p(st["desc"], sz=BASE_FONT_SZ, col=pal["muted"], align=1, lead=13.5))
        row_cells.append(build_card(paras, width=cell_w, height=uniform_height, bg=pal["card"], border=pal["border"], pad=3))
        row_w.append(cell_w)
        if i < n - 1:
            row_cells.append(_p("▶", sz=BASE_FONT_SZ, col=pal["primary"], align=1))
            row_w.append(gap)
    t = Table([row_cells], colWidths=row_w)
    t.hAlign = "LEFT"
    t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    return t

def build_action_board(as_is_dict: Dict[str, Any], to_be_dict: Dict[str, Any], total: float = _GEO["page_printable_width"], uniform_height: float = _GEO["action_board_height"], gap: float = _GEO["grid_gap"]) -> Table:
    pal = get_theme_palette()
    col_ws = calc_cols(total, 2, gap=gap)
    half_w = col_ws[0]
    def _box(d, is_pink):
        col, bg = (pal["alert"], pal["pink_bg"]) if is_pink else (pal["emerald"], pal["green_bg"])
        paras = [_p(f"{'✖' if is_pink else '✓'} {d.get('title', '')}", sz=12.0, col=col, bold=True), Spacer(1, 2)]
        for it in d.get("items", []): paras.append(_p(f"• {it}", sz=BASE_FONT_SZ, col=pal["dark"], lead=14.5))
        if "highlight" in d: paras.extend([Spacer(1, 1), _p(f"<b>{d['highlight']}</b>", sz=BASE_FONT_SZ, col=col, bold=True, lead=14.5)])
        return build_card(paras, width=half_w, height=uniform_height, bg=bg, border=col, border_width=1.2, pad=6)
    return build_split_row([_box(as_is_dict, True), _box(to_be_dict, False)], weights=[0.5, 0.5], total=total, gap=gap)

def build_checklist_grid(items: List[Tuple[int, str, str]], total: float = _GEO["page_printable_width"], cols: int = 2, gap: float = _GEO["grid_gap"]) -> Table:
    pal = get_theme_palette()
    col_ws = calc_cols(total, cols, gap=gap)
    half_w = col_ws[0]
    half = (len(items) + 1) // cols
    def _col(chunk):
        rows = []
        for num, title, desc in chunk:
            b_node = build_card(_p(f"<b>{num}</b>", sz=BASE_FONT_SZ, col=colors.white, align=1), width=20, height=18, bg=pal["primary"], border_width=0, radius=2, pad=0)
            rows.append([b_node, [_p(f"<b>{title}</b>：{desc}", sz=BASE_FONT_SZ, col=pal["dark"], lead=14.5)]])
        t_sub = Table(rows, colWidths=[24, half_w - 24])
        t_styles = [('VALIGN', (0,0), (-1,-1), 'TOP'), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2), ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2)]
        for r_i in range(len(rows)):
            if r_i % 2 == 1: t_styles.append(('BACKGROUND', (0, r_i), (-1, r_i), pal["card"]))
        t_sub.setStyle(TableStyle(t_styles))
        return t_sub
    return build_split_row([_col(items[:half]), _col(items[half:])], weights=[0.5, 0.5], total=total, gap=gap)

def build_product_hero_header(title: str, subtitle: str, desc: str, product_img_path: Optional[str] = None, specs: Optional[List[str]] = None, total: float = _GEO["page_printable_width"], gap: float = 10.0) -> Table:
    pal = get_theme_palette()
    left = [_p(f"<b>{title}</b>", sz=20.0, col=pal["primary"], bold=True, lead=24.0), Spacer(1, 2), _p(f"<b>{subtitle}</b>", sz=12.5, col=pal["alert"], bold=True, lead=16.0), Spacer(1, 3), _p(desc, sz=BASE_FONT_SZ, col=pal["dark"], lead=15.0)]
    right = []
    if product_img_path and os.path.exists(product_img_path):
        try: right.append(RLImage(product_img_path, width=65, height=70))
        except Exception: pass
    if specs:
        for sp in specs: right.append(_p(f"• {sp}", sz=BASE_FONT_SZ, col=pal["muted"], lead=14.5))
    return build_split_row([left, right], weights=[0.68, 0.32], total=total, gap=gap)

def build_kpi_row(kpis: List[Dict[str, Any]], total: float = _GEO["page_printable_width"], uniform_height: float = _GEO["kpi_row_height"], gap: float = 8.0) -> Table:
    pal = get_theme_palette()
    col_ws = calc_cols(total, len(kpis), gap=gap)
    cards = []
    for idx, k in enumerate(kpis):
        col = resolve_color(k.get("color"), pal["primary"])
        col_hex = col.hexval() if hasattr(col, "hexval") else str(col)
        chg_str = f" <font size=11.5 color='{col_hex}'>({k['chg']})</font>" if k.get("chg") else ""
        paras = [_p(k.get("label", ""), sz=BASE_FONT_SZ, col=pal["muted"]), _p(f"<b>{k.get('val', '')}</b>{chg_str}", sz=16.0, col=col, bold=True)]
        if k.get("note"): paras.append(_p(k["note"], sz=BASE_FONT_SZ, col=pal["muted"]))
        cards.append(build_card(paras, width=col_ws[idx], height=uniform_height, bg=pal["card"], border=col, border_width=1.0, pad=5))
    return build_split_row(cards, total=total, gap=gap)

def build_card_grid(cards: List[Dict[str, Any]], cols: int = 3, total: float = _GEO["page_printable_width"], uniform_height: Optional[float] = None, gap: float = 10.0) -> Table:
    pal = get_theme_palette()
    col_ws = calc_cols(total, cols, gap=gap)
    out_cards = []
    for idx, c in enumerate(cards):
        paras = []
        if c.get("badge"): paras.append(_p(f"<b>[{c['badge']}]</b>", sz=BASE_FONT_SZ, col=pal["primary"]))
        if c.get("title"): paras.append(_p(f"<b>{c['title']}</b>", sz=12.0, col=pal["dark"]))
        if c.get("body"):
            for b in (c["body"] if isinstance(c["body"], list) else [c["body"]]): paras.append(_p(f"• {b}", sz=BASE_FONT_SZ, col=pal["muted"]))
        w = col_ws[idx % len(col_ws)]
        out_cards.append(build_card(paras, width=w, height=uniform_height, bg=pal["card"], border=pal["border"], pad=6))
    return build_split_row(out_cards, total=total, gap=gap)

def build_zebra_table(headers: List[str], rows: List[List[Any]], total: float = _GEO["page_printable_width"], col_widths: Optional[List[float]] = None) -> Table:
    pal = get_theme_palette()
    c_ws = col_widths or calc_cols(total, len(headers), gap=0.0)
    data = [[_p(f"<b>{h}</b>", sz=BASE_FONT_SZ, col=colors.white, align=1) for h in headers]]
    for r in rows: data.append([_p(str(c), sz=BASE_FONT_SZ, col=pal["dark"]) for c in r])
    t = Table(data, colWidths=c_ws, repeatRows=1)
    t_styles = [('BACKGROUND', (0,0), (-1,0), pal["primary"]), ('ALIGN', (0,0), (-1,0), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, pal["border"]), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]
    for i in range(1, len(data)):
        if i % 2 == 0: t_styles.append(('BACKGROUND', (0, i), (-1, i), pal["card"]))
    t.setStyle(TableStyle(t_styles))
    return t

def build_pie_chart(data: List[float], labels: List[str], width: float = _GEO["chart_width"], height: float = _GEO["chart_height"]) -> Drawing:
    pal = get_theme_palette()
    palette = pal.get("chart_palette", [pal["primary"], pal["secondary"], pal["accent"], pal["emerald"], pal["alert"]])
    d, dia = Drawing(width, height), height - 10
    pc = Pie()
    pc.x, pc.y, pc.width, pc.height = 5, 5, dia, dia
    pc.data, pc.labels, pc.simpleLabels = data, [str(v) for v in data], 0
    pc.slices.fontName, pc.slices.fontSize = CJK_FONT, BASE_FONT_SZ
    for i in range(len(data)):
        pc.slices[i].fillColor = palette[i % len(palette)]
        pc.slices[i].strokeColor = colors.white
    d.add(pc)
    leg = Legend()
    leg.x, leg.y, leg.dx, leg.dy = dia + 10, height - 10, 8, 8
    leg.fontName, leg.fontSize = CJK_FONT, BASE_FONT_SZ
    leg.boxAnchor, leg.columnMaximum, leg.strokeWidth, leg.strokeColor = "nw", 5, 0, colors.transparent
    leg.colorNamePairs = [(palette[i % len(palette)], labels[i]) for i in range(len(labels))]
    d.add(leg)
    return d

def build_bar_chart(data: Union[List[float], List[List[float]]], categories: List[str], width: float = _GEO["chart_width"], height: float = _GEO["chart_height"], is_vertical: bool = True) -> Drawing:
    pal = get_theme_palette()
    palette = pal.get("chart_palette", [pal["primary"], pal["secondary"], pal["accent"]])
    d = Drawing(width, height)
    matrix = data if isinstance(data[0], (list, tuple)) else [data]
    bc = VerticalBarChart() if is_vertical else HorizontalBarChart()
    if is_vertical:
        bc.x, bc.y, bc.width, bc.height = 25, 20, width - 35, height - 35
        bc.categoryAxis.labels.dy = -10
    else:
        bc.x, bc.y, bc.width, bc.height = 45, 15, width - 55, height - 30
        bc.categoryAxis.labels.dx = -5
    bc.data, bc.categoryAxis.categoryNames = matrix, categories
    bc.categoryAxis.labels.fontName, bc.categoryAxis.labels.fontSize = CJK_FONT, BASE_FONT_SZ
    bc.valueAxis.valueMin, bc.valueAxis.labels.fontName, bc.valueAxis.labels.fontSize = 0, CJK_FONT, BASE_FONT_SZ
    for i in range(len(matrix)):
        bc.bars[i].fillColor, bc.bars[i].strokeColor = palette[i % len(palette)], colors.transparent
    d.add(bc)
    return d

def build_document_header(title: str, subtitle: Optional[str] = None, meta: Optional[str] = None, total: float = _GEO["page_printable_width"]) -> List[Any]:
    pal = get_theme_palette()
    paras = [_p(f"<b>{title}</b>", sz=22.0, col=pal["primary"], bold=True)]
    if subtitle: paras.extend([Spacer(1, 3), _p(f"<b>{subtitle}</b>", sz=12.5, col=pal["primary"])])
    if meta: paras.extend([Spacer(1, 3), _p(meta, sz=BASE_FONT_SZ, col=pal["muted"])])
    return paras

def build_section_heading(title: str, subtitle: Optional[str] = None) -> List[Any]:
    pal = get_theme_palette()
    paras = [_p(f"<b>{title}</b>", sz=15.0, col=pal["primary"], bold=True)]
    if subtitle: paras.extend([Spacer(1, 2), _p(subtitle, sz=BASE_FONT_SZ, col=pal["muted"])])
    return paras

def build_body(text: str, space_after: float = 6) -> List[Any]:
    return [_p(text, sz=BASE_FONT_SZ), Spacer(1, space_after)]

# ==============================================================================
# LAYER 3: MASTER DOCUMENT GENERATORS
# ==============================================================================

class NumberedCanvas(canvas.Canvas):
    doc_title = ""
    confidential_note = ""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if num_pages > 1: self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        self.setFont(CJK_FONT, BASE_FONT_SZ)
        self.setFillColor(colors.HexColor("#7E8287"))
        self.drawString(28, 790, self.doc_title)
        self.drawRightString(540 + 28, 20, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()

def _flatten(items: List[Any]) -> List[Any]:
    out = []
    for it in items:
        if isinstance(it, (list, tuple)): out.extend(_flatten(it))
        elif it in ("PAGE_BREAK", "---"): out.append(PageBreak())
        elif it is not None: out.append(it)
    return out

def generate_multipage_report(filename: str, title: str, subtitle: str = "", story_elements: Optional[List[Any]] = None, running_title: Optional[str] = None, note: str = "", theme: str = "light") -> str:
    token = _current_theme.set(theme)
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28)
        header = build_document_header(title, subtitle, note)
        class BoundCanvas(NumberedCanvas): pass
        BoundCanvas.doc_title, BoundCanvas.confidential_note = running_title or title, note or ""
        doc.build(_flatten([header] + (story_elements or [])), canvasmaker=BoundCanvas)
    finally: _current_theme.reset(token)
    return filename

def generate_infographic_1pager(filename: str, story_elements: List[Any], theme: str = "light") -> str:
    token = _current_theme.set(theme)
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=24, rightMargin=24, topMargin=20, bottomMargin=20)
        doc.build(_flatten(story_elements))
    finally: _current_theme.reset(token)
    return filename

def main():
    parser = argparse.ArgumentParser(description="Universal Composable PDF Builder CLI")
    parser.add_argument("input", nargs="?", help="Input markdown or text file")
    parser.add_argument("-o", "--output", help="Output PDF file path")
    parser.add_argument("-t", "--title", help="Document Title", default="Technical Report")
    parser.add_argument("-s", "--subtitle", help="Document Subtitle", default="")
    parser.add_argument("--theme", help="Theme palette", default="light")
    args = parser.parse_args()
    if args.input and args.output:
        story = [build_section_heading("1. Overview"), build_body(f"Automated technical report compiled from {args.input}.")]
        generate_multipage_report(args.output, args.title, args.subtitle, story, theme=args.theme)
    else:
        print(f"Universal Composable PDF Builder Engine Ready | Font: {CJK_FONT}")

if __name__ == '__main__':
    main()
