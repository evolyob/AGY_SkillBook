# Security Policy: noai-note

## Scope
This skill provides two-phase executive assistant tool for meeting notes, executive briefs, presentation outlines (PPTX), and 1-pager visual blueprints (PDF/DOCX) with Shift-Left Anti-AI filtering. It operates on local files or declared network targets provided via arguments. It does not collect telemetry, run silent daemons, or mutate unauthorized paths.

## Dependencies
- Standard library prioritized (Python >= 3.13).
- Declared dependencies: `[]`.
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 2s). In-memory execution with explicit outputs directed to designated targets.
