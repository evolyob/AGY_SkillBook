# Security Policy: cross-map

## Scope
This skill is a local-first semantic routing and intent matrix scanner. It performs read-only static analysis on Skill directories (`SKILL.md`, `SECURITY.md`, `scripts/`, `references/`). It does not upload data, collect telemetry, or run network daemons.

## Dependencies
- Standard library prioritized (Python >= 3.13: `ast`, `re`, `json`, `pathlib`, `argparse`).
- Declared dependencies: `[]` (zero external package overhead).
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 20ms). Read-only in-memory analysis with zero filesystem mutations and zero background daemons.
- Validated execution flags:
  - `--check`: Output dependency readiness status report.
  - `--json`: Output raw structured JSON analysis to stdout.
  - `--sync`: Synchronize skills registry to ~/.gemini/config/skills/SKILLS.md.


