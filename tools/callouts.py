"""The `**Primary Source:**` callouts, read out of the chapters.

Same regex as ~/atticus/sources.py so the two never disagree about what counts
as a callout. Unlike sources.py this does NOT slugify the label into an id —
assigned ids live in the source records.
"""
from __future__ import annotations

import os
import re

_CALLOUT = re.compile(r"^\*\*Primary Source:\*\*\s*(.+?)\s*$", re.M)


def callouts_in(text: str) -> list[str]:
    return [label.rstrip(".") for label in _CALLOUT.findall(text or "")]


def all_callouts(chapters_dir: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name in sorted(os.listdir(chapters_dir)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(chapters_dir, name), encoding="utf-8") as f:
            for label in callouts_in(f.read()):
                out.append((name[:-3], label))
    return out
