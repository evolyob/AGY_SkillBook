"""
Universal OpenXML Patcher for Excel (.xlsx) - Lean Edition
Decoupled Mutation Engine: lossless in-place cell & range patching,
preserving Office 2010+ extended validations (<extLst>/<x14:dataValidations>),
macros, formulas, and delicate styles byte-for-byte.
Zero external dependencies (Python stdlib only).
"""

import os
import re
import sys
import html
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, Callable


def _render_cell_xml(ref: str, val: Any, style_attr: str) -> str:
    if val is None or val == "":
        return f'<c r="{ref}"{style_attr}/>'
    if isinstance(val, (int, float)):
        return f'<c r="{ref}"{style_attr}><v>{val}</v></c>'
    escaped = html.escape(str(val))
    xml_space = ' xml:space="preserve"' if ("\n" in str(val) or "  " in str(val)) else ""
    return f'<c r="{ref}"{style_attr} t="inlineStr"><is><t{xml_space}>{escaped}</t></is></c>'


def patch_sheet_xml(xml_content: str, cell_updates: Dict[str, Any]) -> str:
    """Pure transformation: in-place updates or inserts cells in sheet XML with style preservation."""
    updated = xml_content
    for ref, item in cell_updates.items():
        if not re.match(r"^[A-Z]+\d+$", ref.upper()):
            continue
        row_str = re.search(r"\d+", ref).group(0)
        val = item.get("value") if isinstance(item, dict) else item
        custom_style = item.get("style") if isinstance(item, dict) else None

        cell_pattern = rf'<c r="{ref}"([^>]*)>(.*?)</c>|<c r="{ref}"([^>]*)/>'
        m_cell = re.search(cell_pattern, updated)
        if m_cell:
            attrs = (m_cell.group(1) or m_cell.group(3) or "").strip()
            s_match = re.search(r's="(\d+)"', attrs)
            active_s = custom_style if custom_style is not None else (s_match.group(1) if s_match else None)
            s_attr = f' s="{active_s}"' if active_s is not None else ""
            updated = re.sub(cell_pattern, _render_cell_xml(ref, val, s_attr), updated, count=1)
            continue

        s_attr = f' s="{custom_style}"' if custom_style is not None else ""
        new_tag = _render_cell_xml(ref, val, s_attr)
        row_pat = rf'(<row r="{row_str}"[^>]*>)(.*?)(</row>)'
        m_row = re.search(row_pat, updated)
        if m_row:
            updated = updated[:m_row.end(1)] + new_tag + updated[m_row.end(1):]
        else:
            updated = updated.replace("</sheetData>", f'<row r="{row_str}">{new_tag}</row></sheetData>', 1)

    return updated


class XLSX_XMLPatcher:
    """Lossless OpenXML Patcher for existing Excel workbooks."""

    def __init__(self, xlsx_path: str):
        self.xlsx_path = os.path.expanduser(xlsx_path)
        if not os.path.exists(self.xlsx_path):
            raise FileNotFoundError(f"XLSX file not found: {self.xlsx_path}")

    def has_extended_validations(self) -> bool:
        """Guard check: returns True if workbook contains Office 2010+ <extLst> data validations."""
        with zipfile.ZipFile(self.xlsx_path, "r") as z:
            return any(
                n.startswith("xl/worksheets/sheet") and "<extLst>" in z.read(n).decode("utf-8", "ignore")
                for n in z.namelist()
            )

    def resolve_sheet_part(self, sheet: str) -> str:
        """Resolves sheet tab name or relative XML path to full zip part path (e.g. 'xl/worksheets/sheet1.xml')."""
        if sheet.startswith("xl/") or sheet.endswith(".xml"):
            return sheet if sheet.startswith("xl/") else f"xl/worksheets/{sheet}"
        with zipfile.ZipFile(self.xlsx_path, "r") as z:
            wb_xml = z.read("xl/workbook.xml").decode("utf-8")
            m = re.search(rf'<sheet[^>]+name="{re.escape(sheet)}"[^>]+r:id="([^"]+)"', wb_xml) or re.search(rf'r:id="([^"]+)"[^>]+name="{re.escape(sheet)}"', wb_xml)
            if not m:
                raise KeyError(f"Sheet '{sheet}' not found in workbook.")
            rels_xml = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
            m_rel = re.search(rf'<Relationship[^>]+Id="{m.group(1)}"[^>]*>', rels_xml)
            if m_rel:
                m_t = re.search(r'Target="([^"]+)"', m_rel.group(0))
                target = m_t.group(1).lstrip("/") if m_t else f"worksheets/{sheet}.xml"
            else:
                target = f"worksheets/{sheet}.xml"
            return target if target.startswith("xl/") else f"xl/{target}"

    def patch_parts(self, part_transforms: Dict[str, Callable[[str], str]], *, output_path: Optional[str] = None) -> str:
        """Applies pure XML transformations to specified parts while keeping everything else byte-for-byte."""
        out_target = os.path.expanduser(output_path) if output_path else self.xlsx_path
        tmp_target = out_target + ".tmp_patch"

        with zipfile.ZipFile(self.xlsx_path, "r") as zin:
            with zipfile.ZipFile(tmp_target, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if item.filename in part_transforms:
                        orig = zin.read(item.filename).decode("utf-8")
                        zout.writestr(item, part_transforms[item.filename](orig).encode("utf-8"))
                    else:
                        zout.writestr(item, zin.read(item.filename))

        shutil.move(tmp_target, out_target)
        return out_target

    def update_cells(self, sheet: str, cell_updates: Dict[str, Any], *, output_path: Optional[str] = None) -> str:
        """In-place updates specified cells in a worksheet without altering namespaces, formulas, or <extLst>."""
        sheet_part = self.resolve_sheet_part(sheet)
        return self.patch_parts({sheet_part: lambda content: patch_sheet_xml(content, cell_updates)}, output_path=output_path)

    def update_range_references(self, sheet: str, ref_replacements: Dict[str, str], *, output_path: Optional[str] = None) -> str:
        """Updates cell range formulas (e.g. '$F$1:$K$1' -> '$F$1:$O$1') losslessly."""
        sheet_part = self.resolve_sheet_part(sheet)
        def transform(xml_content: str) -> str:
            res = xml_content
            for old_r, new_r in ref_replacements.items():
                res = res.replace(old_r, new_r)
            return res
        return self.patch_parts({sheet_part: transform}, output_path=output_path)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 xml_patcher.py <file.xlsx> [--sheet <name_or_part>] (--updates <json_str> | --updates-file <json_file>)")
        sys.exit(1)

    xlsx_file = sys.argv[1]
    sheet = "xl/worksheets/sheet1.xml"
    updates: Dict[str, Any] = {}

    idx = 2
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        if arg in ("--sheet", "-s") and idx + 1 < len(sys.argv):
            sheet = sys.argv[idx + 1]
            idx += 2
        elif arg in ("--updates", "-u") and idx + 1 < len(sys.argv):
            updates.update(json.loads(sys.argv[idx + 1]))
            idx += 2
        elif arg in ("--updates-file", "-f") and idx + 1 < len(sys.argv):
            updates.update(json.loads(Path(sys.argv[idx + 1]).read_text(encoding="utf-8")))
            idx += 2
        else:
            idx += 1

    patcher = XLSX_XMLPatcher(xlsx_file)
    resolved_part = patcher.resolve_sheet_part(sheet)
    patcher.update_cells(resolved_part, updates)
    print(f"Successfully patched {len(updates)} cells in {xlsx_file} [{resolved_part}].")


if __name__ == "__main__":
    main()
