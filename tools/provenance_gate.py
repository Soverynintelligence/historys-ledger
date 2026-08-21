"""The provenance gate — proves the prose does not misquote its own documents.

This is guard.py's quote_gate turned around. There, the model is checked against
the corpus. Here, the CHAPTERS are checked against the documents they cite. A
history product that misquotes its sources has failed at the only thing it
claims to do, and a person proofreading 45 documents by eye will not catch it.

Offline by design: reachability of recorded URLs is checked separately by
tools/fetch_source.py --reverify, so this runs in CI without a network.
"""
from __future__ import annotations

import os
import sys

from tools.callouts import all_callouts
from tools.quoted_spans import MIN_QUOTE_CHARS, norm, quoted_spans
from tools.source_records import load_all, validate

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS = os.path.join(HERE, "content", "chapters")
SOURCES = os.path.join(HERE, "content", "sources")


def check(chapters_dir: str, sources_dir: str) -> list[str]:
    errors: list[str] = []
    records = load_all(sources_dir) if os.path.isdir(sources_dir) else []
    for record in records:
        errors += validate(record)

    by_callout: dict[str, list[dict]] = {}
    for record in records:
        by_callout.setdefault(record.get("callout", ""), []).append(record)

    for stem, callout in all_callouts(chapters_dir):
        if callout not in by_callout:
            errors.append(
                f"{stem}: callout '{callout}' has no source record. Add "
                f"content/sources/<id>.md with a matching `callout:` field."
            )

    # Quote check: only demand verbatim presence when the chapter has at least
    # one cited source WITH text. Restricted/absent sources skip that span.
    chapters = sorted({stem for stem, _ in all_callouts(chapters_dir)})
    for stem in chapters:
        path = os.path.join(chapters_dir, stem + ".md")
        with open(path, encoding="utf-8") as f:
            chapter_text = f.read()
        cited = [r for r in records if stem in (r.get("cited_by") or [])]
        # Sources with rights restricted never contribute text (and may not have it).
        with_text = [
            r for r in cited
            if r.get("text") and r.get("rights") != "restricted"
        ]
        if not with_text:
            # All callouts may still resolve (records without body); no quote check.
            continue
        haystack = " ".join(norm(r.get("text", "")) for r in with_text)
        for span in quoted_spans(chapter_text):
            n = norm(span)
            if len(n) < MIN_QUOTE_CHARS:
                continue
            if n not in haystack:
                errors.append(
                    f'{stem}: quoted span not found in any cited source: "{span[:70]}"'
                )
    return errors


def main() -> int:
    from tools.content_roots import roots

    errors: list[str] = []
    pairs = [(CHAPTERS, SOURCES)]
    for r in roots():
        pair = (r["chapters_dir"], r["sources_dir"])
        if pair not in pairs:
            pairs.append(pair)
    for ch_dir, src_dir in pairs:
        if not os.path.isdir(ch_dir):
            continue
        err = check(ch_dir, src_dir)
        if err:
            label = os.path.relpath(ch_dir, HERE)
            errors += [f"[{label}] {e}" for e in err]
    for e in errors:
        print(e)
    print(
        f"\n{len(errors)} provenance failure(s)."
        if errors
        else "\nProvenance gate passed."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
