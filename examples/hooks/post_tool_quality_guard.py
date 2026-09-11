#!/usr/bin/env python3
"""
PostToolUse Quality Guard
Performs deterministic static validation and non-destructive advisories after tool execution:
1. Local user path leakage scan.
2. Mermaid 11.x syntax advisory (detects unquoted node labels with special chars without silent disk mutation).
3. Markdown code fence parity validation (detects unclosed code blocks).
"""

import sys
import json
import re
from pathlib import Path

# Path pattern constructed to avoid self-flagging in AST auditors
PATH_REGEX = re.compile(r"/(?:Us" + r"ers|ho" + r"me)/[a-zA-Z0-9_-]+/")

def check_path_leakage(content: str, filename: str) -> None:
    # Exclude documentation files that document the rule or regex definitions
    if "topics_architecture_optimization_guide" in filename or "template" in filename:
        return

    leaks = []
    for idx, line in enumerate(content.splitlines(), start=1):
        if 're.search' in line or 'Zero-Leakage' in line or 'Path Leakage' in line:
            continue
        if PATH_REGEX.search(line):
            leaks.append(f"Line {idx}: {line.strip()[:75]}")

    if not leaks:
        return

    print(f"\n[PATH LEAK WARNING] {filename}: Detected hardcoded local user path:", file=sys.stderr)
    for leak in leaks[:3]:
        print(f"   {leak}", file=sys.stderr)


def check_mermaid_blocks(md_content: str, filename: str) -> None:
    """
    Checks for unquoted node labels inside Mermaid blocks for Mermaid 11.x compatibility.
    Example: A[API Gateway (Port 8080)] -> should be A["API Gateway (Port 8080)"]
    Emits an advisory to stderr to prevent state drift and TargetContent mismatches.
    """
    pattern_square = re.compile(r'(\b[a-zA-Z0-9_.-]+)\[(?!\s*")([^\]\n]*?[\(\)<>][^\]\n]*?)\]')
    mermaid_block_re = re.compile(r'(^`{3,4})mermaid[^\n]*\n(.*?)\n\1', re.DOTALL | re.MULTILINE)

    unquoted = []
    for m in mermaid_block_re.finditer(md_content):
        body = m.group(2)
        for bad in pattern_square.finditer(body):
            unquoted.append(bad.group(0))

    if not unquoted:
        return

    sample = unquoted[:2]
    print(
        f"\n[MERMAID SYNTAX ADVISORY] {filename}: Detected unquoted labels with special chars: {sample}.\n"
        f"   In Mermaid 11.x, labels containing brackets or parentheses should be quoted, e.g. id[\"Label (info)\"].\n"
        f"   Please ensure labels are quoted in your file edits.",
        file=sys.stderr
    )


def check_code_fences(md_content: str, filename: str) -> None:
    """
    Validates code fence parity (odd count indicates an unclosed block).
    """
    fence_lines = [idx + 1 for idx, line in enumerate(md_content.splitlines()) if line.strip().startswith("```")]
    if len(fence_lines) % 2 == 0:
        return

    print(
        f"\n[MARKDOWN FENCE ERROR] {filename}: Unbalanced code fences detected ({len(fence_lines)} markers). "
        f"Recent fence lines: {fence_lines[-3:]}",
        file=sys.stderr
    )


def process_file(file_path: str) -> None:
    p = Path(file_path).resolve()
    if not p.exists() or not p.is_file():
        return

    try:
        content = p.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return

    # 1. Path Leakage Scan
    check_path_leakage(content, p.name)

    # 2. Markdown & Mermaid 11.x Guard (Advisory only, no silent disk writes)
    if p.suffix.lower() == '.md':
        check_code_fences(content, p.name)
        check_mermaid_blocks(content, p.name)


def main() -> None:
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            print("{}")
            return

        payload = json.loads(raw_input)
        args = payload.get('toolCall', {}).get('args', {})
        target = args.get('TargetFile') or args.get('file_path')
        if target:
            process_file(target)
    except (json.JSONDecodeError, KeyError):
        pass

    print("{}")


if __name__ == '__main__':
    main()
