# Security & Operational Boundary

## Scope
`deep-base` strictly operates on the user-designated directory `~/wiki/`. It performs local-first Markdown operations, SHA-256 content addressing, and wikilink integrity audits.

## Dependencies
- Standard Library only (`hashlib`, `json`, `re`, `argparse`, `pathlib`, `unittest`).
- Zero third-party network, compiler, or npm runtime dependencies.

## Execution
- File write operations are constrained to `~/wiki/raw/`, `~/wiki/wiki/`, `~/wiki/index.md`, and `~/wiki/log.md`.
- No remote network requests are dispatched directly by the Python scripts.
