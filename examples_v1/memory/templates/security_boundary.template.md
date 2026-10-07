# Security Policy: [skill-name]

## Scope
This skill is a [local tool / network egress tool]. It [reads/writes target files] provided via arguments. It does not upload files, phone home, collect telemetry, or run network services [adjust if egress is explicitly declared].

## Dependencies
- Standard library prioritized (Python >= 3.13).
- Declared dependencies: `[pkg1, pkg2]` (zero unapproved external packages).
- Zero silent background installations: package installs require explicit user confirmation.

## Execution
Single-shot ephemeral CLI (< 2s). [Read-only / explicit output writing] in-memory execution with zero background daemons.
