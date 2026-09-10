"""
XLSX Layout Engine (Modern Enterprise Edition)
Implements clean spreadsheet styling with Noto Sans TC, brand palettes,
KPI stat blocks, structured Zebra tables, group header rows, accounting formats,
and CJK auto-width calculation.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def _clean_hex(hex_str: str) -> str:
    """Returns 6-char upper hex string without leading '#'."""
    clean = hex_str.lstrip("#").upper()
    return "".join(c * 2 for c in clean) if len(clean) == 3 else clean


def _load_theme_config() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, str]]:
    theme_file = Path(__file__).parent / "themes.json"
    raw = json.loads(theme_file.read_text(encoding="utf-8")) if theme_file.exists() else {}
    return raw.get("fonts", {}), raw.get("themes", {}), raw.get("global_colors", {})


def _contrast_color(bg_hex: str, dark_hex: str = "#334155", light_hex: str = "#F8FAFC", *, threshold: float = 0.65) -> str:
    """Computes WCAG-compliant high-contrast text color based on RGB luminance."""
    c = _clean_hex(bg_hex)
    lum = (0.299 * int(c[0:2], 16) + 0.587 * int(c[2:4], 16) + 0.114 * int(c[4:6], 16)) / 255.0
    return _clean_hex(dark_hex if lum > threshold else light_hex)


def _format_stat_val(v: Any, *, prefix: str = "", suffix: str = "") -> str:
    """Universal numeric and KPI formatter: supports arbitrary currencies, units, and scales."""
    if isinstance(v, dict):
        prefix, suffix = v.get("prefix", prefix), v.get("suffix", suffix)
        v = v.get("val", v.get("value", ""))
    val_str = f"{v:,}" if isinstance(v, int) else (f"{v:,.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v))
    return f"{prefix}{val_str}{suffix}"


FONTS, THEMES, GLOBAL_COLORS = _load_theme_config()


class XLSXLayoutEngine:
    """Modern Enterprise XLSX Layout Engine with Noto Sans TC typography."""

    def __init__(self, theme: str = "light", font: str = "Noto Sans TC"):
        theme_map = {"white": "light", "corporate_light": "light", "black": "dark", "warm_yellow": "yellow"}
        self.theme_name = theme_map.get(theme, theme)
        self.t = THEMES.get(self.theme_name, THEMES.get("light", {
            "p": "#2B5C8F", "s": "#007A92", "a": "#EC6A00", "hl": "#F5E050",
            "alert": "#E95119", "card_bg": "#F8FAFC", "txt": "#0B0F19"
        }))
        self.font = font
        self.wb = Workbook()
        self.wb.active.title = "Summary"

    def get_sheet(self, sheet_name: str):
        """Retrieves an existing sheet or creates a new one with gridlines enabled."""
        ws = self.wb[sheet_name] if sheet_name in self.wb.sheetnames else self.wb.create_sheet(title=sheet_name)
        ws.views.sheetView[0].showGridLines = True
        return ws

    def add_title(self, sheet_name: str, title: str, *, subtitle: Optional[str] = None, category: Optional[str] = None, start_row: int = 2, start_col: int = 2) -> int:
        """Renders an executive title block at top-left of the worksheet."""
        ws, row = self.get_sheet(sheet_name), start_row
        if category:
            c = ws.cell(row=row, column=start_col, value=category.upper())
            c.font = Font(name=self.font, size=9, bold=True, color=_clean_hex(self.t.get("p", "#007A92")))
            row += 1
        c = ws.cell(row=row, column=start_col, value=title)
        c.font = Font(name=self.font, size=16, bold=True, color=_clean_hex(self.t.get("txt", "#0B0F19")))
        row += 1
        if subtitle:
            c = ws.cell(row=row, column=start_col, value=subtitle)
            c.font = Font(name=self.font, size=10.5, color=_clean_hex(GLOBAL_COLORS.get("subtitle", "#7E8287")))
            row += 1
        return row

    def add_kpi_cards(self, sheet_name: str, kpis: List[Dict[str, Any]], *, start_row: int = 5, start_col: int = 2) -> int:
        """Renders horizontal KPI stat summary boxes with themed accent border and change badges."""
        ws = self.get_sheet(sheet_name)
        thin_side = Side(border_style="thin", color=_clean_hex(GLOBAL_COLORS.get("border", "#CBD5E1")))
        card_fill = PatternFill(fill_type="solid", start_color=_clean_hex(GLOBAL_COLORS.get("zebra_fill", "#F8FAFC")), end_color=_clean_hex(GLOBAL_COLORS.get("zebra_fill", "#F8FAFC")))
        center_align = Alignment(horizontal="center", vertical="center")

        col = start_col
        for k in kpis:
            accent_hex = _clean_hex(k.get("color", k.get("acc", self.t.get("p", "#007A92"))))
            thick_left = Side(border_style="medium", color=accent_hex)
            chg = k.get("chg", "")
            chg_text = f"({chg})" if (chg and not str(chg).startswith("(")) else str(chg)
            card_items = [
                (_format_stat_val(k), 16, True, accent_hex, Border(left=thick_left, right=thin_side, top=thin_side)),
                (chg_text, 9, True, accent_hex, Border(left=thick_left, right=thin_side)),
                (k.get("label", ""), 9.5, False, _clean_hex(GLOBAL_COLORS.get("subtitle", "#7E8287")), Border(left=thick_left, right=thin_side, bottom=thin_side)),
            ]
            for offset, (val, sz, bld, clr, bdr) in enumerate(card_items):
                cell = ws.cell(row=start_row + offset, column=col, value=val)
                cell.font, cell.fill, cell.alignment, cell.border = Font(name=self.font, size=sz, bold=bld, color=clr), card_fill, center_align, bdr
            col += 2

        ws.row_dimensions[start_row].height = 24
        ws.row_dimensions[start_row + 1].height = 16
        ws.row_dimensions[start_row + 2].height = 18
        return start_row + 4

    def write_table(self, sheet_name: str, headers: List[str], rows: List[List[Any]], *, start_row: int = 9, start_col: int = 2, col_formats: Optional[List[str]] = None, zebra: bool = True, total_row: bool = False):
        """Renders a structured table with themed header, group rows, rich atoms, and accounting borders."""
        ws, n_cols = self.get_sheet(sheet_name), len(headers)
        hdr_hex = _clean_hex(self.t.get("s", GLOBAL_COLORS.get("header_fill", "#2B5C8F")))
        hdr_fill = PatternFill(fill_type="solid", start_color=hdr_hex, end_color=hdr_hex)
        hdr_font = Font(name=self.font, size=10, bold=True, color="FFFFFF")
        thin_side = Side(border_style="thin", color=_clean_hex(GLOBAL_COLORS.get("border", "#CBD5E1")))
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        zebra_hex = _clean_hex(GLOBAL_COLORS.get("zebra_fill", "#F8FAFC"))
        zebra_fill = PatternFill(fill_type="solid", start_color=zebra_hex, end_color=zebra_hex)
        white_fill = PatternFill(fill_type="solid", start_color="FFFFFF", end_color="FFFFFF")

        for j, h in enumerate(headers):
            cell = ws.cell(row=start_row, column=start_col + j, value=h)
            cell.font, cell.fill, cell.border = hdr_font, hdr_fill, cell_border
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[start_row].height = 24

        for i, row_data in enumerate(rows):
            curr_row = start_row + 1 + i
            is_last = (i == len(rows) - 1) and total_row
            if len(row_data) == 1:
                ws.merge_cells(start_row=curr_row, start_column=start_col, end_row=curr_row, end_column=start_col + n_cols - 1)
                grp_fill = PatternFill(fill_type="solid", start_color=_clean_hex(self.t.get("card_bg", "#E6F2F5")), end_color=_clean_hex(self.t.get("card_bg", "#E6F2F5")))
                c_grp = ws.cell(row=curr_row, column=start_col, value=f"▶ {row_data[0]}")
                c_grp.font = Font(name=self.font, size=10, bold=True, color=_clean_hex(self.t.get("p", "#007A92")))
                c_grp.alignment = Alignment(horizontal="left", vertical="center", indent=1)
                for c_i in range(start_col, start_col + n_cols):
                    ws.cell(row=curr_row, column=c_i).fill, ws.cell(row=curr_row, column=c_i).border = grp_fill, cell_border
                ws.row_dimensions[curr_row].height = 20
                continue

            for j, val in enumerate(row_data[:n_cols]):
                cell = ws.cell(row=curr_row, column=start_col + j)
                cell.fill = zebra_fill if (zebra and i % 2 == 1 and not is_last) else white_fill
                if is_last:
                    tot_hex = _clean_hex(GLOBAL_COLORS.get("total_border", "#0B0F19"))
                    cell.border = Border(left=thin_side, right=thin_side, top=Side(border_style="thin", color=tot_hex), bottom=Side(border_style="double", color=tot_hex))
                else:
                    cell.border = cell_border

                if isinstance(val, dict) and "progress" in val:
                    p = max(0, min(100, int(val["progress"])))
                    filled = int(round(p / 10))
                    cell.value = f"[{chr(9608) * filled}{chr(9617) * (10 - filled)}] {p}%"
                    bar_hex = "059669" if p >= 80 else (_clean_hex(self.t.get("a", "EC6A00")) if p >= 50 else _clean_hex(self.t.get("alert", "E95119")))
                    cell.font = Font(name=self.font, size=9.5, bold=True, color=bar_hex)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.value = val
                    cell.font = Font(name=self.font, size=10, bold=is_last or (j == 0), color=_clean_hex(self.t.get("txt", "#0B0F19")))
                    is_num = isinstance(val, (int, float)) or (isinstance(val, str) and val.startswith("="))
                    cell.alignment = Alignment(horizontal="right" if is_num else "left", vertical="center")
                    if col_formats and j < len(col_formats) and col_formats[j]:
                        cell.number_format = col_formats[j]
            ws.row_dimensions[curr_row].height = 20

    def apply_auto_width(self, sheet_name: str, *, min_width: int = 12, padding: int = 4):
        """Auto-adjusts column widths with CJK character width compensation."""
        ws = self.get_sheet(sheet_name)
        for col in ws.columns:
            max_len = max((sum(2.0 if ord(ch) > 127 else 1.0 for ch in str(cell.value)) for cell in col if cell.value is not None), default=0)
            ws.column_dimensions[get_column_letter(col[0].column)].width = max(max_len + padding, min_width)

    def save(self, output_path: str) -> str:
        """Saves the workbook to the specified output path."""
        path = os.path.expanduser(output_path)
        out_dir = os.path.dirname(path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        self.wb.save(path)
        return path
