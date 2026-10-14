# Security & Operational Boundary

## Scope
`deep-base` strictly operates on the user-designated directory `~/wiki/`. It performs local-first Markdown operations, SHA-256 content addressing, and wikilink integrity audits.

## Dependencies
- Standard Library only (`hashlib`, `json`, `re`, `argparse`, `pathlib`, `unittest`, `sqlite3`).
- Zero third-party network, compiler, or npm runtime dependencies.

## Execution
- File write operations are constrained to `~/wiki/raw/`, `~/wiki/wiki/` (including `entities/`, `topics/`, `sources/`, `comparisons/`, `synthesis/`, `queries/`), `~/wiki/data/` (including `glossary.json`), `~/wiki/index.md`, `~/wiki/log.md`, `~/wiki/.wiki-schema.md`, and `~/wiki/.wiki-cache.json`.
- Cache mutation adopts atomic write-replace (`.wiki-cache.tmp.<pid>` -> `.wiki-cache.json`) and aborts on corrupt cache files to protect existing indexing state.
- Link and quote validation in `scripts/lint_links.py` performs local-only deterministic verification against raw sources without remote network calls.
- In-memory SQLite FTS5 queries in `scripts/query.py` operate ephemerally with zero persistent disk overhead.
- No remote network requests are dispatched directly by the Python scripts.
