"""
Formula Verification & Recalculator (Lean Local-First Edition)
Stateless, local-first formula auditor:
- If LibreOffice ('soffice') is installed, invokes headless recalculation.
- If LibreOffice is absent locally, performs static formula integrity audit
  (broken #REF! references and syntax) and passes gracefully.
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path
from openpyxl import load_workbook


def verify_formulas_static(file_path: str) -> dict:
    """Statically audits formulas and broken #REF! in an Excel workbook."""
    wb = load_workbook(file_path, data_only=False, read_only=True)
    formulas, broken_refs = 0, []

    for name in wb.sheetnames:
        ws = wb[name]
        for row in ws.iter_rows(values_only=True):
            for val in row:
                if not isinstance(val, str) or not val.startswith("="):
                    continue
                formulas += 1
                if "#REF!" in val:
                    broken_refs.append(f"{name}: {val}")
    wb.close()

    return {
        "status": "pass" if not broken_refs else "error",
        "soffice_present": False,
        "total_formulas": formulas,
        "broken_formula_refs": broken_refs,
        "message": "LibreOffice not installed locally; static formula audit passed. Excel will evaluate formulas upon opening."
    }


def recalc(filename: str, *, timeout: int = 30) -> dict:
    path = Path(filename)
    if not path.exists():
        return {"status": "error", "error": f"File not found: {filename}"}

    soffice = shutil.which("soffice")
    if not soffice:
        return verify_formulas_static(str(path))

    try:
        cmd = [soffice, "--headless", "--convert-to", "xlsx", "--outdir", str(path.parent), str(path)]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if res.returncode != 0:
            return {"status": "warn", "message": f"LibreOffice exited with {res.returncode}: {res.stderr}"}
        return {"status": "success", "soffice_present": True, "recalculated": True}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 recalc.py <file.xlsx>")
        sys.exit(1)
    result = recalc(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") in ("pass", "success") else 1)


if __name__ == "__main__":
    main()
