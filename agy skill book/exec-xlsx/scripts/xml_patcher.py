"""
Universal XML Patcher for Excel (.xlsx)
Preserves Office 2010+ Extended Data Validations (<extLst>/<x14:dataValidations>),
macros, charts, and delicate layouts that openpyxl strips upon saving.
Zero external dependencies (Python stdlib only: zipfile, xml.etree, re).
"""

import zipfile
import re
import os
import shutil
import xml.etree.ElementTree as ET
from typing import Dict, List, Callable, Optional


class XLSX_XMLPatcher:
    """High-fidelity OpenXML patcher for .xlsx files."""

    def __init__(self, xlsx_path: str):
        self.xlsx_path = os.path.expanduser(xlsx_path)
        if not os.path.exists(self.xlsx_path):
            raise FileNotFoundError(f"XLSX file not found: {self.xlsx_path}")

    def list_parts(self) -> List[str]:
        """Lists all internal XML parts inside the .xlsx ZIP container."""
        with zipfile.ZipFile(self.xlsx_path, "r") as z:
            return z.namelist()

    def get_part_content(self, part_path: str) -> str:
        """Reads and decodes the UTF-8 XML content of a specific part."""
        with zipfile.ZipFile(self.xlsx_path, "r") as z:
            return z.read(part_path).decode("utf-8")

    def patch_parts(
        self,
        part_transforms: Dict[str, Callable[[str], str]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Applies transformation functions to specified XML parts while keeping
        all other parts 100% byte-for-byte identical.
        """
        out_target = os.path.expanduser(output_path) if output_path else self.xlsx_path
        tmp_target = out_target + ".tmp_patch"

        with zipfile.ZipFile(self.xlsx_path, "r") as zin:
            with zipfile.ZipFile(tmp_target, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if item.filename in part_transforms:
                        orig_content = zin.read(item.filename).decode("utf-8")
                        transform_fn = part_transforms[item.filename]
                        modified_content = transform_fn(orig_content)
                        if item.filename.endswith((".xml", ".rels")):
                            try:
                                ET.fromstring(modified_content.encode("utf-8"))
                            except ET.ParseError as pe:
                                raise ValueError(f"[XML Patcher Corrupted] Patching {item.filename} resulted in invalid XML: {pe}") from pe
                        zout.writestr(item, modified_content.encode("utf-8"))
                    else:
                        zout.writestr(item, zin.read(item.filename))

        shutil.move(tmp_target, out_target)
        return out_target

    def update_range_references(
        self,
        sheet_part: str,
        ref_replacements: Dict[str, str],
        output_path: Optional[str] = None
    ) -> str:
        """
        Updates cell range references (e.g. '參數表!$F$2:$F$16' -> '參數表!$F$2:$F$19')
        without breaking <extLst> or formula tags.
        """
        def transform(xml_content: str) -> str:
            updated = xml_content
            for old_ref, new_ref in ref_replacements.items():
                updated = updated.replace(old_ref, new_ref)
            return updated

        return self.patch_parts({sheet_part: transform}, output_path)

    def enable_wrap_text(
        self,
        style_part: str = "xl/styles.xml",
        xf_index: int = 3,
        output_path: Optional[str] = None
    ) -> str:
        """
        Enables wrapText and vertical center alignment for a specified cellXf style
        using lossless string replacement without altering OpenXML namespaces.
        """
        def transform(xml_content: str) -> str:
            # Match cellXfs block
            m = re.search(r'<cellXfs count="(\d+)">', xml_content)
            if not m:
                return xml_content
            
            if len(xfs) <= xf_index:
                return xml_content
            target_xf = xfs[xf_index]
            if 'wrapText="1"' in target_xf:
                return xml_content
            if '<alignment' in target_xf:
                new_xf = re.sub(r'<alignment ([^>]*)/>', r'<alignment \1 wrapText="1"/>', target_xf)
            else:
                new_xf = target_xf.replace('/>', ' applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>')
            return xml_content.replace(target_xf, new_xf, 1)

        return self.patch_parts({style_part: transform}, output_path)

    def append_inline_cells(
        self,
        sheet_part: str,
        rows_data: Dict[int, Dict[str, str]],
        row_heights: Optional[Dict[int, float]] = None,
        col_styles: Optional[Dict[str, str]] = None,
        new_dimension: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Appends or injects inlineStr cells into <sheetData> cleanly and updates <dimension>.
        Supports xml:space="preserve", HTML escaping, row heights, and custom column styles.
        rows_data schema: {row_num: {col_letter: text_value}}
        """
        import html

        def transform(xml_content: str) -> str:
            content = xml_content
            if new_dimension:
                content = re.sub(r'<dimension ref="[^"]*"/>', f'<dimension ref="{new_dimension}"/>', content)

            rows_xml = []
            for r_num in sorted(rows_data.keys()):
                cols = rows_data[r_num]
                ht_attr = f' ht="{row_heights[r_num]}" customHeight="1"' if (row_heights and r_num in row_heights) else ''
                cell_strs = []
                for col_letter, val in cols.items():
                    s_attr = f' s="{col_styles[col_letter]}"' if (col_styles and col_letter in col_styles) else ''
                    if val is None or val == '':
                        cell_strs.append(f'<c r="{col_letter}{r_num}"{s_attr}/>')
                    elif isinstance(val, (int, float)):
                        cell_strs.append(f'<c r="{col_letter}{r_num}"{s_attr}><v>{val}</v></c>')
                    elif '\n' in str(val) or '  ' in str(val):
                        val_str = html.escape(str(val))
                        cell_strs.append(f'<c r="{col_letter}{r_num}"{s_attr} t="inlineStr"><is><t xml:space="preserve">{val_str}</t></is></c>')
                    else:
                        val_str = html.escape(str(val))
                        cell_strs.append(f'<c r="{col_letter}{r_num}"{s_attr} t="inlineStr"><is><t>{val_str}</t></is></c>')
                cells_joined = "".join(cell_strs)
                rows_xml.append(f'<row r="{r_num}" spans="1:{len(cols)}"{ht_attr}>{cells_joined}</row>')

            joined_rows = "".join(rows_xml)
            content = content.replace("</sheetData>", f"{joined_rows}</sheetData>")
            return content

        return self.patch_parts({sheet_part: transform}, output_path)

