"""Book-local style whitelist loader and text masking helpers."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from pathlib import Path

__all__ = ["load_style_whitelist", "style_spans", "mask_style_text"]


def load_style_whitelist(file: str | os.PathLike[str]) -> list[str]:
    """Load book-local `.deslop-whitelist` literals sorted longest-first.

    Never inherits an unrelated workspace or another book's choices.
    Returns an empty list if `.deslop-whitelist` does not exist.
    """
    parent = Path(file).resolve().parent
    book = parent.parent if parent.name == "chapters" else parent
    whitelist_path = book / ".deslop-whitelist"
    try:
        raw = whitelist_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    lines = (line.strip() for line in re.split(r"\r?\n", raw))
    filtered = [line for line in lines if line and not line.startswith("#")]
    return sorted(filtered, key=len, reverse=True)


def style_spans(text: str, whitelist: Iterable[str]) -> list[tuple[int, int]]:
    """Return `(start, end)` character spans for all whitelist matches in `text`."""
    spans: list[tuple[int, int]] = []
    for literal in whitelist:
        if not literal:
            continue
        at = text.find(literal)
        while at != -1:
            spans.append((at, at + len(literal)))
            at = text.find(literal, at + 1)
    return spans


def mask_style_text(text: str, whitelist: Iterable[str]) -> str:
    """Replace whitelisted spans in `text` with full-width `？` preserving length."""
    chars = list(text)
    for start, end in style_spans(text, whitelist):
        chars[start:end] = ["？"] * (end - start)
    return "".join(chars)
