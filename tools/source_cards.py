"""Source cards — the data behind a tap.

A card is what the reader sees when they tap a Primary Source callout or a
quotation in the entry. It is assembled from assigned source records and the
apparatus (verified passages / honest gaps). Nothing is invented: absence of
text is a status, not a blank to fill.
"""
from __future__ import annotations

from tools.quoted_spans import MIN_QUOTE_CHARS, norm


def status_for(record: dict) -> str:
    if record.get("rights") == "restricted":
        return "restricted"
    if record.get("text"):
        return "held"
    return "citation-only"


def card_from_record(record: dict, apparatus_for_source: list[dict] | None = None) -> dict:
    """One UI card for one source record."""
    passages = []
    for e in apparatus_for_source or []:
        if e.get("status") == "verified" and e.get("passages"):
            p = e["passages"][0]
            passages.append(
                {
                    "span": e.get("span", ""),
                    "before": p.get("before", ""),
                    "quoted": p.get("quoted", ""),
                    "after": p.get("after", ""),
                }
            )
    return {
        "id": record.get("id") or "",
        "title": record.get("title") or record.get("callout") or "",
        "author": record.get("author") or "",
        "date": record.get("date") or "",
        "type": record.get("type") or "document",
        "rights": record.get("rights") or "",
        "callout": record.get("callout") or "",
        "url": record.get("url") or "",
        "repository": record.get("repository") or "",
        "status": status_for(record),
        "has_text": bool(record.get("text")),
        "passages": passages,
        "kind": "source",
    }


def gap_card(entry: dict) -> dict:
    """A card for a quotation we cannot open into a held document."""
    return {
        "id": f"gap:{norm(entry.get('span', ''))[:48]}",
        "title": "Not held in full",
        "author": "",
        "date": "",
        "type": "gap",
        "rights": "",
        "callout": "",
        "url": entry.get("url") or "",
        "repository": "",
        "status": entry.get("status") or "unsourced",
        "has_text": False,
        "passages": [],
        "kind": "gap",
        "span": entry.get("span") or "",
        "reason": entry.get("reason")
        or "no source record we hold contains this quotation",
        "source_id": entry.get("source_id") or "",
        "source_title": entry.get("source_title") or "",
    }


def build_for_chapter(
    records: list[dict],
    stem: str,
    apparatus_entries: list[dict],
) -> tuple[dict[str, dict], dict[str, str], dict[str, str]]:
    """Return (cards_by_id, callout_to_card_id, span_norm_to_card_id)."""
    cited = [r for r in records if stem in (r.get("cited_by") or [])]
    # also include any record matched by apparatus even if cited_by drifted
    by_id = {r.get("id"): r for r in records if r.get("id")}

    cards: dict[str, dict] = {}
    callout_to: dict[str, str] = {}
    span_to: dict[str, str] = {}

    for r in cited:
        rid = r.get("id") or ""
        if not rid:
            continue
        related = [
            e
            for e in apparatus_entries
            if e.get("source_id") == rid or (
                e.get("status") == "verified"
                and e.get("source_title")
                and e.get("source_title") == r.get("title")
            )
        ]
        cards[rid] = card_from_record(r, related)
        if r.get("callout"):
            callout_to[r["callout"]] = rid

    for e in apparatus_entries:
        key = " ".join((e.get("span") or "").split()).lower()
        if not key or len(norm(e.get("span") or "")) < MIN_QUOTE_CHARS:
            continue
        if e.get("status") == "verified" and e.get("source_id"):
            sid = e["source_id"]
            if sid not in cards and sid in by_id:
                cards[sid] = card_from_record(by_id[sid], [e])
            span_to[key] = sid
        else:
            gid = gap_card(e)["id"]
            cards[gid] = gap_card(e)
            span_to[key] = gid
            if e.get("source_id") and e["source_id"] in by_id:
                # also keep the restricted/record-set card available
                sid = e["source_id"]
                if sid not in cards:
                    cards[sid] = card_from_record(by_id[sid], [])

    return cards, callout_to, span_to
