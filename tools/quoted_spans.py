"""Quoted-span extraction, vendored from ~/atticus/guard.py.

Vendored rather than imported: Atticus is a separately deployed service on the
Spark and this repo must not depend on its checkout. The algorithm is pinned by
tests/test_quoted_spans.py — straight quotes are paired POSITIONALLY (split on
the quote character, take odd segments), never by regex, because straight quotes
carry no direction and a regex restarts at the closing quote.
"""
from __future__ import annotations

import re

MIN_QUOTE_CHARS = 25  # keep in sync with ~/atticus/guard.py:104

_CURLY = re.compile("“([^“”]*)”")


def quoted_spans(text: str | None) -> list[str]:
    """Every span the writer actually put in quotation marks.

    Straight quotes are paired positionally (1st–2nd, 3rd–4th). An unpaired
    trailing quote yields no span — the content after an opening quote with no
    closer is not a quoted span.
    """
    text = text or ""
    spans = _CURLY.findall(text)
    rest = _CURLY.sub(" ", text)
    parts = rest.split('"')
    # Odd indices sit between paired quotes. range stops before the last part
    # so an unclosed trailing quote (odd number of ") produces no extra span.
    spans += [parts[i] for i in range(1, len(parts) - 1, 2)]
    return spans


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("—", " ").replace("–", " ").replace("…", " ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return " ".join(s.split())
