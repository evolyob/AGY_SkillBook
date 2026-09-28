# Security & Access Boundary

## Scope
- Read Scope: Local workspace and user-specified documents (.docx, .pdf, .md, .txt, .xlsx).
- Prohibitions: Zero network egress (no telemetry), zero execution outside declared scripts, zero access to sensitive files (.env, keys).

## Dependencies
- Standard Library: Python 3.10+ (`argparse`, `json`, `re`, `pathlib`, `xml.etree.ElementTree`, `zipfile`, `unicodedata`, `sys`).
- Optional Parser: `openpyxl` (XLSX reading), `pypdf` (PDF text reading).
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
- Invocation: Local deterministic scripts via `run_command` (`python3 scripts/ingest.py`).
- Performance: Single-shot ephemeral CLI (< 2s). In-memory execution with zero background daemons.
