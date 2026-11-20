# Security Policy: deep-story

## Scope
This skill is a local tool. It reads and writes target story project files provided via CLI arguments (`--project`, `--file`, `--input`). It does not upload files, phone home, collect telemetry, or run network services.

## Dependencies
- Standard library prioritized (Python >= 3.13).
- Declared dependencies: `[]` (zero external packages; 100% Python 3 standard library).
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 2s). Explicit output writing within the target story project directory with zero background daemons.
