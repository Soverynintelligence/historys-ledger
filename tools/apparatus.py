"""Where each quotation is written, so the reader can decide instead of trusting us.

The reader packet's cover says "The record speaks. You decide." and then prints
the prose with no apparatus at all — the reader is asked to take every quotation
on faith, which is the posture this project exists to refuse. The gate already
knows, for every quoted span, whether it is verified, unverifiable-with-a-reason,
or unsourced. That knowledge stopped at the build log. This puts it in front of
the person actually reading.

Three states, and none of them is hidden:

  verified    the span was located in a document we hold, and the surrounding
              passage is carried along so the reader can see the context it was
              lifted from — the check against fair quotation that a bare
              citation cannot give them.
  unverified  a real source we cannot quote against: restricted by copyright, or
              an archival aggregate with no single file. The reason is shown.
  unsourced   no cited source contains it. Said plainly, in the reader's copy,
              rather than quietly passing.

`unsourced` is the state a footnote normally conceals. Printing it is the point:
a citation the reader cannot check is worth less than an admission that we
could not check it either.
"""
from __future__ import annotations

import os
import re

from tools.quotation_match import fragments
from tools.quoted_spans import MIN_QUOTE_CHARS, norm, quoted_spans
from tools.source_records import load_all

CONTEXT_CHARS = 320

_WORD = re.compile(r"[A-Za-z0-9]+")


def _tokens(text: str) -> list[tuple[str, int, int]]:
    """Every alphanumeric run, lowercased, with its offsets in the ORIGINAL text.

    norm() reduces text to alphanumeric words separated by single spaces, so the
    word sequence here is exactly the sequence norm() produces — which is what
    lets a match found in normalised space be read back out of readable source.
    """
    return [(m.group(0).lower(), m.start(), m.end()) for m in _WORD.finditer(text)]


def locate(fragment: str, tokens: list[tuple[str, int, int]]) -> tuple[int, int] | None:
    """Character span of `fragment` in the original text, or None."""
    want = fragment.split()
    if not want:
        return None
    words = [t[0] for t in tokens]
    for i in range(len(words) - len(want) + 1):
        if words[i:i + len(want)] == want:
            return tokens[i][1], tokens[i + len(want) - 1][2]
    return None


def passage(text: str, start: int, end: int, width: int = CONTEXT_CHARS) -> dict:
    """The quoted span with the source's own words either side of it."""
    left = max(0, start - width)
    right = min(len(text), end + width)
    return {
        "before": " ".join(text[left:start].split()),
        "quoted": " ".join(text[start:end].split()),
        "after": " ".join(text[end:right].split()),
        "truncated_left": left > 0,
        "truncated_right": right < len(text),
    }


def _find_in_record(span: str, record: dict) -> list[dict] | None:
    """Every fragment of an elided quotation, located in this record's text."""
    text = record.get("text") or ""
    if not text:
        return None
    tokens = _tokens(text)
    found = []
    for fragment in fragments(span):
        if len(fragment) < 12:
            continue
        at = locate(fragment, tokens)
        if at is None:
            return None
        found.append(passage(text, *at))
    return found or None


def apparatus(chapters_dir: str, sources_dir: str) -> list[dict]:
    """One entry per quotation in every chapter, with where it is written."""
    records = load_all(sources_dir) if os.path.isdir(sources_dir) else []
    entries = []

    for name in sorted(n for n in os.listdir(chapters_dir) if n.endswith(".md")):
        stem = name[:-3]
        with open(os.path.join(chapters_dir, name), encoding="utf-8") as f:
            chapter = f.read()
        cited = [r for r in records if stem in (r.get("cited_by") or [])]

        for span in quoted_spans(chapter):
            if len(norm(span)) < MIN_QUOTE_CHARS:
                continue
            entry = {"chapter": stem, "span": span.strip()}

            located = next(
                ((r, p) for r in cited for p in [_find_in_record(span, r)] if p), None
            )
            if located:
                record, passages = located
                entry.update(
                    status="verified", source_id=record.get("id"),
                    source_title=record.get("title"), url=record.get("url"),
                    passages=passages,
                )
                entries.append(entry)
                continue

            declared = next(
                (r for r in cited
                 if (r.get("rights") == "restricted" or r.get("type") == "record-set")
                 and any(norm(d) == norm(span) for d in (r.get("covers_quotations") or []))),
                None,
            )
            if declared is not None:
                entry.update(
                    status="unverified", source_id=declared.get("id"),
                    source_title=declared.get("title"), url=declared.get("url"),
                    reason=("held under copyright — we may not reproduce it, so it is "
                            "cited and left unchecked"
                            if declared.get("rights") == "restricted" else
                            "held as an archival aggregate — there is no single file "
                            "to check it against"),
                )
            else:
                entry.update(
                    status="unsourced",
                    reason="no source record we hold contains this quotation",
                )
            entries.append(entry)

    return entries


def counts(entries: list[dict]) -> dict:
    out = {"verified": 0, "unverified": 0, "unsourced": 0}
    for e in entries:
        out[e["status"]] += 1
    return out
