"""
PPTX Universal Composable Layout Engine (Next-Gen Multi-Modal Architecture)
Pure-geometry dynamic solver supporting Single-Layer & Multi-Layer slides,
atomic shape primitives, polymorphic slot renderers (table, flow, charts, kpi, image, cards),
and WCAG contrast auto-adaptation.
"""

import os, io, json, logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union

import resvg_py
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image

logger = logging.getLogger("pptx_engine")


def _hex_to_rgb(h: str) -> RGBColor:
    h = h.lstrip("#")
    return RGBColor(*(int(h[i:i+2], 16) for i in (0, 2, 4)))


def _rgb_to_hex(c: RGBColor) -> str:
    return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"


def _contrast_color(bg: RGBColor, th: float = 0.65) -> RGBColor:
    return RGBColor(51, 65, 85) if (0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]) / 255.0 > th else RGBColor(248, 250, 252)


def _load_theme_config() -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], Dict[str, float]]:
    theme_file = Path(__file__).parent / "themes.json"
    with open(theme_file, "r", encoding="utf-8") as f:
        raw = json.load(f)
    fonts_dict = raw.get("fonts", {})
    geometry = raw.get("geometry", {"card_radius": 0.04, "pill_radius": 0.50, "header_accent_bar_width": 0.10})
    themes: Dict[str, Dict[str, Any]] = {}
    for name, data in raw.get("themes", {}).items():
        td = {k: _hex_to_rgb(v) for k, v in data["colors"].items()}
        td["accents"] = [_hex_to_rgb(c) for c in data.get("accents", [])]
        td["font"] = data.get("font", "Noto Sans TC")
        themes[name] = td
    aliases = {
        "light": ["clean_corporate_light", "corporate_light", "monocle_magazine", "white"],
        "dark": ["executive_dark_navy", "executive_dark", "vibrant_dark_neon", "raycast", "linear_minimal_dark", "resn_storytelling", "black"],
        "yellow": ["warm_yellow_denim_slate", "warm_yellow_obsidian", "mailchimp_freddie", "warm_yellow"]
    }
    for base, names in aliases.items():
        if base in themes:
            for a in names: themes[a] = themes[base]
    return fonts_dict, themes, geometry


FONTS, THEMES, GEOMETRY = _load_theme_config()


# --- Layer 0: Pure Geometry Solver ---

def calc_cols(x: float, y: float, w: float, h: float, n_or_weights: Union[int, List[float]], gap: float = 0.35) -> List[Tuple[float, float, float, float]]:
    weights = [1.0] * max(1, n_or_weights) if isinstance(n_or_weights, int) else [float(wt) for wt in n_or_weights]
    total_wt, usable_w, res, cur_x = sum(weights), w - (len(weights) - 1) * gap, [], x
    for wt in weights:
        cw = usable_w * (wt / total_wt)
        res.append((cur_x, y, cw, h))
        cur_x += cw + gap
    return res


def calc_rows(x: float, y: float, w: float, h: float, n_or_weights: Union[int, List[float]], gap: float = 0.15) -> List[Tuple[float, float, float, float]]:
    weights = [1.0] * max(1, n_or_weights) if isinstance(n_or_weights, int) else [float(wt) for wt in n_or_weights]
    total_wt, usable_h, res, cur_y = sum(weights), h - (len(weights) - 1) * gap, [], y
    for wt in weights:
        rh = usable_h * (wt / total_wt)
        res.append((x, cur_y, w, rh))
        cur_y += rh + gap
    return res


class PPTXLayoutEngine:
    calc_cols = staticmethod(calc_cols)
    calc_rows = staticmethod(calc_rows)

    def __init__(self, theme: str = "light", font: Optional[str] = None, width: float = 13.333, height: float = 7.5):
        self.theme_name = theme
        self.t = THEMES.get(theme, THEMES["light"])
        self.geo = GEOMETRY
        self.card_r = self.geo.get("card_radius", 0.04)
        self.pill_r = self.geo.get("pill_radius", 0.50)
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(width), Inches(height)
        self.blank = self.prs.slide_layouts[6]
        self.font = FONTS[font]["name"] if font and font in FONTS else (font or self.t.get("font", "Noto Sans TC"))
        
        icons_dir = Path(__file__).parent.parent / "assets" / "icons"
        self._icon_cache = {p.stem: p for p in icons_dir.glob("*/*.svg")} if icons_dir.exists() else {}
        cat_file = Path(__file__).parent / "icons_catalog.json"
        self._aliases: Dict[str, str] = {}
        try:
            with open(cat_file, "r", encoding="utf-8") as f:
                cat_data = json.load(f)
                self._aliases.update(cat_data.get("semantic_aliases", {}))
                for dim_data in cat_data.get("meta_dimensions", {}).values():
                    for cat_entry in dim_data.get("categories", {}).values():
                        cat_icons = cat_entry.get("icons", [])
                        primary_icon = cat_icons[0] if cat_icons else "star"
                        for kw in cat_entry.get("intent_keywords", []):
                            self._aliases.setdefault(kw.lower(), primary_icon)
        except Exception as e:
            logger.warning(f"[PPTXEngine] Failed to load icon catalog: {e}")

    def color(self, c: Any, default: Optional[RGBColor] = None) -> RGBColor:
        if isinstance(c, RGBColor): return c
        if isinstance(c, str) and c.startswith("#"): return _hex_to_rgb(c)
        if isinstance(c, str) and c in self.t: return self.t[c]
        return default or self.t["cyan"]

    # --- Layer 1: Atomic Primitives ---

    def resolve_icon(self, token: Any) -> Optional[str]:
        if not token: return None
        raw = str(token).lower().strip().replace(" ", "-").replace("_", "-")
        if raw in self._icon_cache: return raw
        if raw in self._aliases and self._aliases[raw] in self._icon_cache: return self._aliases[raw]
        for k, v in self._aliases.items():
            if len(k) >= 3 and k in raw and v in self._icon_cache: return v
        for stem in self._icon_cache.keys():
            if len(raw) >= 3 and (raw in stem or stem in raw): return stem
        return "star" if "star" in self._icon_cache else (next(iter(self._icon_cache.keys())) if self._icon_cache else None)

    def _add_icon(self, slide, left: float, top: float, size: float, icon_token: Union[str, bytes, io.BytesIO], color: Optional[RGBColor] = None, bg: Optional[RGBColor] = None):
        if not icon_token: return None
        if bg:
            c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(left), Inches(top), Inches(size), Inches(size))
            c.fill.solid(); c.fill.fore_color.rgb = self.color(bg, self.t["card_alt"]); c.line.fill.background()
            left, top, size = left + size * 0.22, top + size * 0.22, size * 0.56

        if isinstance(icon_token, (bytes, io.BytesIO)):
            blob = icon_token if isinstance(icon_token, bytes) else icon_token.getvalue()
            return slide.shapes.add_picture(io.BytesIO(blob), Inches(left), Inches(top), Inches(size), Inches(size))
        if isinstance(icon_token, str) and icon_token.endswith(('.png', '.jpg', '.jpeg')):
            return slide.shapes.add_picture(icon_token, Inches(left), Inches(top), Inches(size), Inches(size))

        tok = self.resolve_icon(icon_token)
        if not tok or tok not in self._icon_cache: return None
        try:
            with open(self._icon_cache[tok], "r", encoding="utf-8") as f:
                svg_str = f.read().replace("currentColor", _rgb_to_hex(self.color(color, self.t["cyan"])))
            return slide.shapes.add_picture(io.BytesIO(resvg_py.svg_to_bytes(svg_str)), Inches(left), Inches(top), Inches(size), Inches(size))
        except Exception as e:
            logger.warning(f"[PPTXEngine] Failed to render SVG icon '{icon_token}': {e}")
            return None

    def _card(self, slide, left: float, top: float, w: float, h: float, bg=None, border=None, bw: float = 1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius: Optional[float] = None):
        card = slide.shapes.add_shape(shape, Inches(left), Inches(top), Inches(w), Inches(h))
        r = self.card_r if radius is None else radius
        if len(card.adjustments) > 0 and r is not None:
            card.adjustments[0] = r
        card.fill.solid(); card.fill.fore_color.rgb = self.color(bg, self.t["card"])
        if border:
            card.line.color.rgb, card.line.width = self.color(border, self.t["border"]), Pt(bw)
        else:
            card.line.fill.background()
        return card

    def _pill(self, slide, left: float, top: float, w: float, h: float, bg=None, border=None, bw: float = 1.0):
        return self._card(slide, left, top, w, h, bg=bg or self.t["cyan"], border=border, bw=bw, radius=self.pill_r)

    def _badge(self, slide, left: float, top: float, w: float, h: float, text: str, bg=None, fg: Optional[RGBColor] = None, size: float = 13.5):
        c_bg = self.color(bg, self.t["cyan"])
        badge = self._pill(slide, left, top, w, h, bg=c_bg)
        tf = badge.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.word_wrap = True; tf.auto_size = MSO_AUTO_SIZE.NONE
        p = tf.paragraphs[0]; p.text = str(text); p.font.size = Pt(size); p.font.bold = True
        p.font.color.rgb = self.color(fg, _contrast_color(c_bg)); p.font.name = self.font; p.alignment = PP_ALIGN.CENTER
        return badge

    def _text(self, slide, left: float, top: float, w: float, h: float, text: str, size: float = 13.5, color=None, bold: bool = False, align=PP_ALIGN.LEFT):
        return self._text_block(slide, left, top, w, h, [(text, size, color, bold, 0)], align=align)

    def _text_block(self, slide, left: float, top: float, w: float, h: float, paras: List[Tuple[str, float, Any, bool, int]], align=PP_ALIGN.LEFT):
        tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True; tf.auto_size = MSO_AUTO_SIZE.NONE
        for i, (txt, sz, col, bold, sa) in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = str(txt); p.font.size = Pt(sz); p.font.bold = bold; p.font.name = self.font
            p.font.color.rgb = self.color(col, self.t["text_primary"]); p.alignment = align
            if sa > 0: p.space_after = Pt(sa)
        return tb

    # --- Layer 2: Polymorphic Slot Renderers ---

    def _render_table(self, slide, box: Tuple[float, float, float, float], content: Dict[str, Any]):
        x, y, w, h = box
        headers, rows = content.get("headers", []), content.get("rows", [])
        if not rows and not headers: return
        n_rows = len(rows) + (1 if headers else 0)
        n_cols = max(len(headers), max((len(r) for r in rows), default=1))
        tbl = slide.shapes.add_table(n_rows, n_cols, Inches(x), Inches(y), Inches(w), Inches(h)).table
        col_weights = content.get("col_weights")
        if col_weights and len(col_weights) == n_cols:
            tot = sum(col_weights)
            for i, wt in enumerate(col_weights): tbl.columns[i].width = Inches(w * (wt / tot))
        curr_row = 0
        header_bg = self.color(content.get("header_bg"), self.t.get("card_alt", self.t["card"]))
        header_fg = self.color(content.get("header_fg"), self.t["cyan"])
        if headers:
            for c_idx, h_text in enumerate(headers):
                cell = tbl.cell(0, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = header_bg; cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf = cell.text_frame; tf.word_wrap = True; tf.auto_size = MSO_AUTO_SIZE.NONE
                p = tf.paragraphs[0]; p.text = str(h_text); p.font.size = Pt(13.5); p.font.bold = True
                p.font.color.rgb = header_fg; p.font.name = self.font; p.alignment = PP_ALIGN.LEFT
            curr_row = 1
        zebra = content.get("zebra", True)
        for r_idx, row_data in enumerate(rows):
            r_num = curr_row + r_idx
            bg_col = self.t["card_alt"] if (zebra and r_idx % 2 == 1) else self.t["card"]
            for c_idx, val in enumerate(row_data):
                if c_idx >= n_cols: break
                cell = tbl.cell(r_num, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = bg_col; cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf = cell.text_frame; tf.word_wrap = True; tf.auto_size = MSO_AUTO_SIZE.NONE
                p = tf.paragraphs[0]; p.text = str(val); p.font.size = Pt(13.5); p.font.color.rgb = self.t["text_primary"]; p.font.name = self.font; p.alignment = PP_ALIGN.LEFT

    def _render_image(self, slide, box: Tuple[float, float, float, float], content: Any):
        x, y, w, h = box
        src = content.get("source", content) if isinstance(content, dict) else content
        caption = content.get("caption") if isinstance(content, dict) else None
        self._card(slide, x, y, w, h, bg=self.t["card"], border=self.t["border_light"])
        try:
            blob = src if isinstance(src, bytes) else (src.getvalue() if isinstance(src, io.BytesIO) else open(src, "rb").read())
            im = Image.open(io.BytesIO(blob))
            ratio, pad = im.size[0] / float(im.size[1]), 0.15
            avail_w, avail_h = w - pad * 2, h - pad * 2 - (0.35 if caption else 0)
            tw, th = (avail_h * ratio, avail_h) if (avail_w / avail_h) > ratio else (avail_w, avail_w / ratio)
            slide.shapes.add_picture(io.BytesIO(blob), Inches(x + (w - tw) / 2.0), Inches(y + (avail_h - th) / 2.0 + pad), Inches(tw), Inches(th))
            if caption: self._text(slide, x + pad, y + h - 0.35, w - pad * 2, 0.30, str(caption), color=self.t["text_muted"], align=PP_ALIGN.CENTER)
        except Exception as e:
            logger.warning(f"[PPTXEngine] Failed to render image slot: {e}")

    def _render_stacked(self, slide, box: Tuple[float, float, float, float], content: List[Any]):
        x, y, w, h = box
        weights = [item.get("weight", 1.0) if isinstance(item, dict) else 1.0 for item in content]
        for sbox, item in zip(calc_rows(x, y, w, h, weights, gap=0.12), content):
            d = item if isinstance(item, dict) else {"title": item[0], "body": item[1] if len(item) > 1 else ""}
            self.render_slot(slide, sbox, d)

    def _render_flow(self, slide, box: Tuple[float, float, float, float], content: Dict[str, Any], col: RGBColor):
        x, y, w, h = box
        steps = content.get("steps", [])
        if not steps: return
        for i, (sbox, st) in enumerate(zip(calc_cols(x, y, w, h, len(steps), gap=0.55), steps)):
            sx, sy, sw, sh = sbox
            tag, title, tok = st.get("step") or st.get("tag") or f"STEP 0{i+1}", st.get("title", ""), st.get("icon")
            st_col, circle_sz = self.color(st.get("color"), col), min(0.50, sh * 0.38)
            cx, c_bg = sx + (sw - circle_sz) / 2.0, self.color(st.get("circle_bg"), self.t["card_alt"])
            if tok:
                self._add_icon(slide, cx, sy, circle_sz, tok, st_col, bg=c_bg)
            else:
                c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx), Inches(sy), Inches(circle_sz), Inches(circle_sz))
                c.fill.solid(); c.fill.fore_color.rgb = c_bg; c.line.fill.background()
            self._text_block(slide, sx, sy + circle_sz + 0.08, sw, sh - circle_sz - 0.08, [(tag, 13.5, st_col, True, 0), (title, 14.0, self.t["text_primary"], True, 2)], align=PP_ALIGN.CENTER)
            if i < len(steps) - 1:
                arr_x, arr_sz = sx + sw + 0.12, 0.28
                if not self._add_icon(slide, arr_x, sy + (circle_sz - arr_sz) / 2.0, arr_sz, "caret-right", self.t["cyan"]):
                    arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(arr_x), Inches(sy + (circle_sz - arr_sz) / 2.0), Inches(arr_sz), Inches(arr_sz))
                    arr.fill.solid(); arr.fill.fore_color.rgb = self.t["cyan"]; arr.line.fill.background()

    def _render_kpi(self, slide, box: Tuple[float, float, float, float], content: Dict[str, Any], col: RGBColor):
        x, y, w, h = box
        lbl, val, chg = content.get("label", ""), str(content.get("val") or content.get("value", "")), content.get("chg") or content.get("badge")
        tok, note = content.get("icon"), content.get("note")
        self._card(slide, x, y, w, h)
        self._pill(slide, x + 0.08, y + 0.2, 0.08, min(h - 0.4, 1.2) if h > 2.0 else max(h - 0.4, 0.6), bg=col)
        if tok: self._add_icon(slide, x + w - 0.55, y + 0.2, 0.38, tok, col)
        val_display = f"{val} ({chg})" if (chg and not str(chg).startswith("(")) else (f"{val} {chg}" if chg else val)
        paras = [(lbl, 13.5, self.t["text_muted"], False, 0), (val_display, 24 if chg else 26, col, True, 4)] + ([(note, 13.5, self.t["text_sub"], False, 2)] if note else [])
        self._text_block(slide, x + 0.35, y + 0.15, w - 0.55, h - 0.3, paras)

    def _render_bars(self, slide, box: Tuple[float, float, float, float], content: Dict[str, Any], col: RGBColor):
        x, y, w, h = box
        self._card(slide, x, y, w, h, bg=self.t["card"], border=self.t["border_light"])
        tag, cur_y = content.get("tag") or content.get("title"), y + 0.12
        if tag:
            tag_h = 0.34 if h < 3.0 else 0.40
            self._badge(slide, x + 0.15, cur_y, w - 0.3, tag_h, str(tag), bg=RGBColor(11, 37, 69), fg=RGBColor(255, 255, 255))
            cur_y += tag_h + 0.10

        raw_bars, insight = content.get("bars", []), content.get("insight") or content.get("note")
        insight_h = min(0.60, h * 0.26) if (insight and h < 3.2) else (min(0.85, h * 0.28) if insight else 0.0)
        iy = y + h - insight_h - 0.10 if insight else y + h
        bottom_limit = (iy - 0.08) if insight else (y + h - 0.10)
        avail_h = max(0.50, bottom_limit - cur_y)
        max_v, n = max((b[1] if isinstance(b, (list, tuple)) else b.get("val", 1) for b in raw_bars), default=1.0), max(len(raw_bars), 1)
        row_h = avail_h / n
        bar_h = min(0.20, max(0.08, row_h * 0.48))

        max_lbl_len = max((len(str(b[0] if isinstance(b, (list, tuple)) else b.get("label", ""))) for b in raw_bars), default=4)
        label_w = float(content.get("label_width", max(1.4, min(max_lbl_len * 0.16 + 0.30, w * 0.42))))
        axis_x, val_w = x + label_w + 0.12, 0.70
        max_bw = max(0.40, w - (axis_x - x) - val_w - 0.25)

        axis = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(axis_x), Inches(cur_y), Pt(1.5), Inches(avail_h))
        axis.fill.solid(); axis.fill.fore_color.rgb = self.color("border", RGBColor(203, 213, 225)); axis.line.fill.background()

        for idx, item in enumerate(raw_bars):
            lbl = item[0] if isinstance(item, (list, tuple)) else item.get("label", "")
            val = item[1] if isinstance(item, (list, tuple)) else item.get("val", 0)
            col_spec = item[2] if isinstance(item, (list, tuple)) and len(item) > 2 else (item.get("color") if isinstance(item, dict) else None)
            b_col = self.color(col_spec, self.t["accents"][idx % len(self.t["accents"])])
            row_center = cur_y + (idx + 0.5) * row_h
            text_y, bar_y = row_center - 0.16, row_center - (bar_h / 2.0)
            self._text(slide, x + 0.08, text_y, label_w, 0.32, lbl, size=13.5, align=PP_ALIGN.RIGHT)
            bw = max(0.08, (val / max_v) * max_bw) if max_v > 0 else 0.08
            bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(axis_x + 0.02), Inches(bar_y), Inches(bw), Inches(bar_h))
            bar.fill.solid(); bar.fill.fore_color.rgb = b_col; bar.line.fill.background()
            self._text(slide, axis_x + 0.06 + bw, text_y, val_w, 0.32, f"{val:.2f}" if isinstance(val, float) else str(val), size=13.5, bold=True)

        if insight:
            self._card(slide, x + 0.12, iy, w - 0.24, insight_h, bg=self.t["card_alt"], border=self.t["border"])
            icon_sz = min(0.36, max(0.24, insight_h * 0.55))
            self._add_icon(slide, x + 0.22, iy + (insight_h - icon_sz) / 2.0, icon_sz, content.get("insight_icon", "trend-up"), self.t["text_primary"], bg=RGBColor(219, 234, 254))
            self._text_block(slide, x + 0.22 + icon_sz + 0.12, iy + 0.06, w - 0.24 - icon_sz - 0.35, insight_h - 0.12, [(str(insight), 13.5, self.t["text_primary"], True, 0)])

    def _render_progress(self, slide, box: Tuple[float, float, float, float], content: Dict[str, Any]):
        x, y, w, h = box
        self._card(slide, x, y, w, h, bg=self.t["card"], border=self.t["border_light"])
        lbl, val = content.get("label", "Progress"), max(0, min(100, float(content.get("val", content.get("value", 0)))))
        p_col, tok = self.color(content.get("color"), self.t["emerald"]), content.get("icon")
        if tok: self._add_icon(slide, x + w - 0.55, y + 0.20, 0.38, tok, p_col)
        self._text(slide, x + 0.25, y + 0.20, w - (0.85 if tok else 0.50), 0.35, lbl, size=14.5, bold=True)
        self._pill(slide, x + 0.25, y + 0.65, w - 0.50, 0.22, bg=self.t["card_alt"])
        self._pill(slide, x + 0.25, y + 0.65, max(0.08, (val / 100.0) * (w - 0.50)), 0.22, bg=p_col)
        self._text(slide, x + 0.25, y + 0.95, w - 0.50, 0.35, f"{val:.1f}%", color=p_col, bold=True, align=PP_ALIGN.RIGHT)

    def _render_donut(self, slide, box: Tuple[float, float, float, float], content: Dict[str, Any]):
        x, y, w, h = box
        self._card(slide, x, y, w, h, bg=self.t["card"], border=self.t["border_light"])
        lbl, val = content.get("label", "Ratio"), max(0, min(100, float(content.get("val", content.get("value", 0)))))
        d_col, tok = self.color(content.get("color"), self.t["cyan"]), content.get("icon")
        if tok: self._add_icon(slide, x + w - 0.55, y + 0.20, 0.38, tok, d_col)
        dia = min(w - 0.8, h - 1.1, 1.7)
        cx, cy = x + (w - dia) / 2.0, y + 0.25
        ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx), Inches(cy), Inches(dia), Inches(dia))
        ring.fill.solid(); ring.fill.fore_color.rgb = self.t["card_alt"]; ring.line.color.rgb, ring.line.width = d_col, Pt(7.0)
        self._text(slide, cx, cy + (dia - 0.45) / 2.0, dia, 0.45, f"{val:.0f}%", size=22.0, bold=True, align=PP_ALIGN.CENTER)
        self._text(slide, x + 0.2, cy + dia + 0.15, w - 0.4, 0.35, lbl, color=self.t["text_muted"], align=PP_ALIGN.CENTER)

    def _render_standard_card(self, slide, box: Tuple[float, float, float, float], d: Dict[str, Any], accent: RGBColor):
        x, y, w, h = box
        c_border, c_bg = self.color(d.get("border") or d.get("color"), accent), self.color(d.get("bg"), self.t["card_alt"] if h < 2.0 else self.t["card"])
        self._card(slide, x, y, w, h, bg=c_bg, border=c_border)
        tag, tok, title, subtitle = d.get("tag") or d.get("badge"), d.get("icon"), d.get("title", ""), d.get("subtitle", "")
        body, flow_data = d.get("body", d.get("items", [])), d.get("flow") or ({"steps": d["steps"]} if "steps" in d else None)
        
        top_offset, tag_w = y + (0.08 if h < 1.8 else 0.18), 0.0
        if tok: self._add_icon(slide, x + 0.18, top_offset, 0.32 if h < 2.0 else 0.38, tok, c_border)
        if tag:
            tag_x = x + (0.58 if tok else 0.18)
            t_weight = sum(2.0 if ord(c) > 127 else 1.0 for c in str(tag))
            tag_w = max(0.95, min(t_weight * 0.12 + 0.35, w - (tag_x - x) - 0.3))
            self._badge(slide, tag_x, top_offset, tag_w, 0.32 if h < 2.0 else 0.34, str(tag), bg=c_border, fg=self.t["bg"])
        
        left_pad = ((0.58 if tok else 0.18) + (tag_w + 0.10 if tag else 0.0)) if (h < 1.4 and (tok or tag)) else 0.20
        if (tok or tag) and h >= 1.4: top_offset += (0.38 if h < 2.2 else 0.46)
        
        if flow_data:
            flow_h = min(1.6, (h - (top_offset - y)) * 0.40)
            self._render_flow(slide, (x + 0.20, top_offset, w - 0.40, flow_h), flow_data, c_border)
            top_offset += flow_h + 0.15

        paras = []
        if title: paras.append((str(title), 14.5 if h < 2.0 else 15.5, c_border if h < 2.0 else self.t["text_primary"], True, 0))
        if subtitle: paras.append((str(subtitle), 13.5, self.t["text_muted"], False, 1))
        if isinstance(body, list):
            for b in body: paras.append((str(b).strip(), 13.5, self.t["text_primary"] if h < 2.0 else self.t["text_muted"], False, 2 if h < 2.0 else 4))
        elif body:
            paras.append((str(body).strip(), 13.5, self.t["text_primary"] if h < 2.0 else self.t["text_muted"], False, 2 if h < 2.0 else 3))
        
        footer = d.get("footer")
        self._text_block(slide, x + left_pad, top_offset, w - left_pad - 0.20, h - (top_offset - y) - (0.45 if footer else 0.12), paras)
        if footer: self._badge(slide, x + 0.25, y + h - 0.45, w - 0.50, 0.32, str(footer), bg=self.t.get("card_alt", self.t["card"]), fg=self.t["text_muted"])

    def render_slot(self, slide, box: Tuple[float, float, float, float], content: Any, accent: Optional[RGBColor] = None):
        col = self.color(accent, self.t["cyan"])
        if isinstance(content, (str, bytes, io.BytesIO)) or (isinstance(content, dict) and content.get("type") == "image"):
            return self._render_image(slide, box, content)
        if isinstance(content, list) and len(content) > 0 and isinstance(content[0], (dict, list, tuple)):
            return self._render_stacked(slide, box, content)
        t = content.get("type") if isinstance(content, dict) else None
        if t == "flow": return self._render_flow(slide, box, content, col)
        if t in ("bars", "bento_bars"): return self._render_bars(slide, box, content, col)
        if t in ("progress", "progress_bar"): return self._render_progress(slide, box, content)
        if t in ("donut", "gauge"): return self._render_donut(slide, box, content)
        if t == "table": return self._render_table(slide, box, content)
        if t == "kpi" or (isinstance(content, dict) and ("val" in content or "value" in content)):
            return self._render_kpi(slide, box, content, col)
        d = content if isinstance(content, dict) else {"body": content}
        self._render_standard_card(slide, box, d, accent=col)

    # --- Layer 3: High-Level Slide Builders ---

    def _render_header(self, slide, x: float, y: float, w: float, title: Optional[str], subtitle: Optional[str] = None, kicker: Optional[str] = None, bar_gap: float = 0.20) -> float:
        if not title: return y
        char_weight = sum(2.0 if ord(c) > 127 else 1.0 for c in str(title))
        is_multiline = char_weight > 48.0 or len(str(title)) > 26
        paras = []
        if kicker: paras.append((str(kicker).upper(), 13.5, self.t["cyan"], True, 2))
        paras.append((str(title), 24.0 if is_multiline else 28.0, self.t["text_primary"], True, 4 if subtitle else 0))
        if subtitle: paras.append((str(subtitle), 14.5, self.t["text_sub"], False, 0))
        tb_h = (1.45 if is_multiline else 0.95) if (subtitle or kicker) else (0.85 if is_multiline else 0.56)
        bar_h = (1.30 if is_multiline else 0.88) if (subtitle or kicker) else (0.85 if is_multiline else 0.55)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y + 0.02), Inches(self.geo.get("header_accent_bar_width", 0.10)), Inches(bar_h))
        bar.fill.solid(); bar.fill.fore_color.rgb = self.t["amber"] if self.theme_name == "yellow" else self.t["cyan"]; bar.line.fill.background()
        self._text_block(slide, x + 0.10 + bar_gap, y, w - (0.10 + bar_gap) - 0.20, tb_h, paras)
        return y + tb_h + 0.10

    def create_slide(self, title: Optional[str] = None, subtitle: Optional[str] = None, kicker: Optional[str] = None, tags: Optional[List[str]] = None, bar_gap: float = 0.20, layers: Optional[List[Dict[str, Any]]] = None, layer_gap: float = 0.35):
        slide = self.prs.slides.add_slide(self.blank)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = self.t["bg"]
        canvas_l, canvas_w = 0.50, 12.333
        cur_y = self._render_header(slide, canvas_l, 0.40, canvas_w, title=title, subtitle=subtitle, kicker=kicker, bar_gap=bar_gap)
        if not layers: return slide

        avail_h = 7.10 - cur_y
        row_heights = [l.get("height", avail_h / len(layers)) for l in layers]
        layer_boxes = calc_rows(canvas_l, cur_y, canvas_w, avail_h, row_heights, gap=layer_gap)

        for (lx, ly, lw, lh), ldata in zip(layer_boxes, layers):
            section_tag = ldata.get("section_tag")
            if section_tag:
                sec_weight = sum(2.0 if ord(c) > 127 else 1.0 for c in str(section_tag))
                sec_w = max(1.60, min(sec_weight * 0.12 + 0.45, 3.50))
                self._badge(slide, lx, ly, sec_w, 0.34, section_tag, bg=self.t["cyan"], fg=self.t["bg"])
                ly += 0.42
                lh = max(0.20, lh - 0.42)
            
            cols = ldata.get("cols", ldata.get("columns", []))
            if cols:
                for cbox, c_content in zip(calc_cols(lx, ly, lw, lh, ldata.get("weights") or len(cols), gap=ldata.get("gap", 0.35)), cols):
                    self.render_slot(slide, cbox, c_content)
            elif "content" in ldata:
                self.render_slot(slide, (lx, ly, lw, lh), ldata["content"])
        return slide

    def save(self, filepath: str) -> str:
        path = os.path.expanduser(filepath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.prs.save(path)
        return path
