# Security Policy: exec-docx

## Scope
This skill provides create, read, edit, or convert word documents (. It operates on local files or declared network targets provided via arguments. It does not collect telemetry, run silent daemons, or mutate unauthorized paths.

## Dependencies
- Standard library prioritized (Python >= 3.13).
- Declared dependencies: `[docx, defusedxml, lxml]`.
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 2s). In-memory execution with explicit outputs directed to designated targets.
- Validated execution flags: `--author`, `--headless`, `--id`, `--initials`, `--norestore`, `--output`, `--parent`, `--raw`, `--terminate_after_init`.
