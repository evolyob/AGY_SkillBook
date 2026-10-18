#!/usr/bin/env python3
"""Fast Telemetry & Scale Dashboard for deep-base."""

import sys
from pathlib import Path


def main():
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "~/wiki").expanduser().resolve()
    if not target.exists():
        print(f"Error: Target path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    raw_files = list((target / "raw").glob("**/*")) if (target / "raw").exists() else []
    raw_files = [f for f in raw_files if f.is_file() and not f.name.startswith(".")]

    entities = list((target / "wiki" / "entities").glob("*.md")) if (target / "wiki" / "entities").exists() else []
    topics = list((target / "wiki" / "topics").glob("*.md")) if (target / "wiki" / "topics").exists() else []
    sources = list((target / "wiki" / "sources").glob("*.md")) if (target / "wiki" / "sources").exists() else []
    comparisons = list((target / "wiki" / "comparisons").glob("*.md")) if (target / "wiki" / "comparisons").exists() else []
    synthesis = list((target / "wiki" / "synthesis").glob("*.md")) if (target / "wiki" / "synthesis").exists() else []
    queries = list((target / "wiki" / "queries").glob("*.md")) if (target / "wiki" / "queries").exists() else []

    total_pages = len(entities) + len(topics) + len(sources) + len(comparisons) + len(synthesis) + len(queries)

    print(f"=== Personal Knowledge Base Telemetry ({target.name}) ===")
    print(f"• Raw Sources (Layer 1)     : {len(raw_files)} files")
    print(f"• Synthesized Pages (Layer 2): {total_pages} pages")
    print(f"    - Entities              : {len(entities)}")
    print(f"    - Topics                : {len(topics)}")
    print(f"    - Source Summaries      : {len(sources)}")
    print(f"    - Comparisons           : {len(comparisons)}")
    print(f"    - Synthesis             : {len(synthesis)}")
    print(f"    - Cached Queries        : {len(queries)}")


if __name__ == "__main__":
    main()
