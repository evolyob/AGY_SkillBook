# Security Policy: exec-xlsx

## Scope
This skill provides create, read, edit, format, or clean spreadsheet files (. It operates on local files or declared network targets provided via arguments. It does not collect telemetry, run silent daemons, or mutate unauthorized paths.

## Dependencies
- Standard library prioritized (Python >= 3.13).
- Declared dependencies: `[openpyxl, pandas, defusedxml, lxml]`.
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 2s). In-memory execution with explicit outputs directed to designated targets.
- Validated execution flags:
  - `--convert-to`: Execution option.
  - `--headless`: Execution option.
  - `--outdir`: Execution option.
  - `--sheet`: Execution option.
  - `--updates`: Execution option.
  - `--updates-file`: Execution option.
