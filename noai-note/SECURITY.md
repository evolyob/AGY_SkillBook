# Security & Access Boundary

## Scope
- Read Scope: Local workspace and user-specified documents (.docx, .pdf, .md, .txt).
- Prohibitions: Zero network egress (no telemetry), zero execution outside declared scripts, zero access to sensitive files (.env, keys).

## Dependencies
- Standard Library: Python 3.13+ (`argparse`, `json`, `re`, `pathlib`, `xml.etree.ElementTree`, `zipfile`).
- Zero external package dependencies.

## Execution
- Invocation: Local deterministic scripts via `run_command` (`python3 scripts/ingest.py`, `python3 scripts/scan.py`).
- Security Posture: Static analysis only; sandboxed file operations within declared scope.
