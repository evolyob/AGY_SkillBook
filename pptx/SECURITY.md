# Security Policy: pptx

## Scope
This skill provides create, read, edit, and analyze powerpoint presentation files (. It operates on local files or declared network targets provided via arguments. It does not collect telemetry, run silent daemons, or mutate unauthorized paths.

## Dependencies
- Standard library prioritized (Python >= 3.13).
- Declared dependencies: `[pptx, PIL, resvg_py, defusedxml, lxml]`.
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 2s). In-memory execution with explicit outputs directed to designated targets.
- Validated execution flags:
  - `--demo`: Execution option.
  - `--output`: Execution option.
  - `--theme`: Execution option.
