# Security Policy: deep-mod

## Scope
This skill provides universal interactive deep research, architecture visualization, and surgical skill extraction pipeline with anti-ai enforcement. It operates on local files or declared network targets provided via arguments. It does not collect telemetry, run silent daemons, or mutate unauthorized paths.

## Dependencies
- Standard library prioritized (Python >= 3.10).
- Declared dependencies: `[]`.
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 2s). In-memory execution with explicit outputs directed to designated targets.
- Validated execution flags:
  - `--format`: Execution option.
  - `--list-only`: Execution option.
  - `--output`: Execution option.
  - `--split-dir`: Execution option.
  - `--page-range`: Execution option.
  - `--check`: Execution option.
  - `--text`: Execution option.
