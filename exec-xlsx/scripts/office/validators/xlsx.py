"""
Validator for Excel spreadsheet XML files against OpenXML schemas, namespaces, and formatting integrity.
"""

import re
from .base import BaseSchemaValidator


class XLSXSchemaValidator(BaseSchemaValidator):
    SPREADSHEETML_NAMESPACE = (
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    )

    def validate(self) -> bool:
        if not self.validate_xml():
            return False

        all_valid = True

        if not self.validate_namespaces():
            all_valid = False

        if not self.validate_ignorable_namespaces():
            all_valid = False

        if not self.validate_multiline_whitespace():
            all_valid = False

        if not self.validate_wrap_text_styles():
            all_valid = False

        return all_valid

    def validate_ignorable_namespaces(self) -> bool:
        """
        Checks that all namespaces referenced in mc:Ignorable attributes
        are properly declared on the root element. Missing declarations cause
        Office error HRESULT 0x808c0002.
        """
        valid = True
        xml_files = list(self.unpacked_dir.rglob("*.xml"))
        for xml_file in xml_files:
            try:
                content = xml_file.read_text(encoding="utf-8")
            except Exception:
                continue

            ignorable_match = re.search(r'mc:Ignorable="([^"]+)"', content)
            if not ignorable_match:
                continue

            prefixes = ignorable_match.group(1).split()
            root_tag_match = re.search(r'<[a-zA-Z0-9_:]+([^>]+)>', content)
            root_attrs = root_tag_match.group(1) if root_tag_match else ""
            for prefix in prefixes:
                missing_root = f"xmlns:{prefix}=" not in root_attrs and prefix != "x14ac"
                missing_doc = f"xmlns:{prefix}=" not in content
                if missing_root and missing_doc:
                    self._error(
                        f"{xml_file.relative_to(self.unpacked_dir)}: "
                        f"mc:Ignorable references prefix '{prefix}' but xmlns:{prefix} is not declared on root element (triggers HRESULT 0x808c0002)."
                    )
                    valid = False
        return valid

    def validate_multiline_whitespace(self) -> bool:
        """
        Checks that <t> elements containing newlines or leading/trailing spaces
        have xml:space="preserve".
        """
        valid = True
        sheets = list(self.unpacked_dir.glob("xl/worksheets/sheet*.xml"))
        for sheet in sheets:
            try:
                content = sheet.read_text(encoding="utf-8")
            except Exception:
                continue

            matches = re.finditer(r'<t(?:\s+[^>]*)?>([\s\S]*?)</t>', content)
            for m in matches:
                full_tag = m.group(0)
                text_content = m.group(1)
                if ('\n' in text_content or '  ' in text_content) and 'xml:space="preserve"' not in full_tag:
                    self._error(
                        f"{sheet.relative_to(self.unpacked_dir)}: "
                        f"Multi-line or spaced <t> text missing xml:space=\"preserve\"."
                    )
                    valid = False
                    break
        return valid

    def validate_wrap_text_styles(self) -> bool:
        """
        Warns or checks if cells contain multi-line text but styles.xml has no wrapText="1".
        """
        styles_file = self.unpacked_dir / "xl" / "styles.xml"
        if not styles_file.exists():
            return True

        styles_content = styles_file.read_text(encoding="utf-8")
        sheets = list(self.unpacked_dir.glob("xl/worksheets/sheet*.xml"))
        has_multiline = False
        for sheet in sheets:
            content = sheet.read_text(encoding="utf-8")
            if '\n' in content:
                has_multiline = True
                break

        if has_multiline and 'wrapText="1"' not in styles_content:
            self._error("xl/styles.xml: Workbook contains multi-line cells but no cellXfs style has wrapText=\"1\".")
            return False

        return True

    def repair(self) -> int:
        """
        Auto-repairs common XLSX XML issues:
        - Adds xml:space="preserve" to <t> tags with newlines
        - Enables wrapText="1" in styles.xml
        """
        repairs = 0

        # 1. Repair multiline xml:space="preserve"
        sheets = list(self.unpacked_dir.glob("xl/worksheets/sheet*.xml"))
        for sheet in sheets:
            content = sheet.read_text(encoding="utf-8")
            
            def fix_t(match):
                nonlocal repairs
                full_tag = match.group(0)
                text = match.group(1)
                if ('\n' in text or '  ' in text) and 'xml:space="preserve"' not in full_tag:
                    repairs += 1
                    return f'<t xml:space="preserve">{text}</t>'
                return full_tag

            new_content = re.sub(r'<t(?:\s+[^>]*)?>([\s\S]*?)</t>', fix_t, content)
            if new_content != content:
                sheet.write_text(new_content, encoding="utf-8")

        # 2. Repair styles.xml wrapText
        styles_file = self.unpacked_dir / "xl" / "styles.xml"
        if not styles_file.exists():
            return repairs

        styles_content = styles_file.read_text(encoding="utf-8")
        if 'wrapText="1"' not in styles_content:
            orig_xf = '<xf numFmtId="0" fontId="2" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>'
            new_xf = '<xf numFmtId="0" fontId="2" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>'
            if orig_xf in styles_content:
                styles_content = styles_content.replace(orig_xf, new_xf, 1)
                styles_file.write_text(styles_content, encoding="utf-8")
                repairs += 1

        return repairs
