# Security & Operational Boundary

## Scope
`deep-base` strictly operates on the user-designated directory `~/.gemini/wiki/`. It performs local-first Markdown operations, SHA-256 content addressing, and wikilink integrity audits.

## Dependencies
- Standard Library only (`hashlib`, `json`, `re`, `argparse`, `pathlib`, `unittest`, `sqlite3`).
- Zero third-party network, compiler, or npm runtime dependencies.

## Data Quarantine & Zero-PII / Secret Policy
- **Prohibited Sensitive Data**: Never store phone numbers, physical addresses, plaintext passwords, API tokens, private cryptographic keys, or host-specific user home absolute paths inside `~/.gemini/wiki/`.
- **Path Normalization**: Automatically normalize host home paths to `~/...` or wiki-relative paths prior to writing into `raw/`, `wiki/`, `log.md`, or `.wiki-cache.json`.
- **Secret & PII Redaction**: Strip or replace personal identifiers and credentials with `<REDACTED>` before ingestion or note buffering.

## Execution
- File write operations are constrained to `~/.gemini/wiki/raw/`, `~/.gemini/wiki/wiki/` (including `entities/`, `topics/`, `sources/`, `comparisons/`, `synthesis/`, `queries/`, `archive/`), `~/.gemini/wiki/data/` (including `glossary.json`), `~/.gemini/wiki/index.md`, `~/.gemini/wiki/log.md`, `~/.gemini/wiki/.wiki-schema.md`, and `~/.gemini/wiki/.wiki-cache.json`.
- Cache mutation adopts atomic write-replace (`.wiki-cache.tmp.<pid>` -> `.wiki-cache.json`) and aborts on corrupt cache files to protect existing indexing state.
- Link and quote validation in `scripts/lint_links.py` performs local-only deterministic verification against raw sources without remote network calls.
- In-memory SQLite FTS5 queries in `scripts/query.py` operate ephemerally with zero persistent disk overhead.
- No remote network requests are dispatched directly by the Python scripts.
