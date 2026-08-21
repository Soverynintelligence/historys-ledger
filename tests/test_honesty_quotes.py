"""Long quotations must be in the held record — never silently cleaned."""
from pathlib import Path

from tools.apparatus import apparatus
from tools.quotation_match import verify_span
from tools.quoted_spans import norm
from tools.source_records import load_all

REPO = Path(__file__).resolve().parent.parent
CH = REPO / "content/collections/modern-wars/chapters"
SRC = REPO / "content/collections/modern-wars/sources"


def test_1914_long_quotes_are_in_held_sources():
    entries = apparatus(str(CH), str(SRC))
    wwi = [e for e in entries if e["chapter"] == "01-how-europe-walked-in"]
    unsourced = [e for e in wwi if e["status"] == "unsourced"]
    assert unsourced == [], [e["span"][:80] for e in unsourced]


def test_1914_does_not_quote_a_silently_corrected_grey_book_line():
    text = (REPO / "content/collections/modern-wars/chapters/01-how-europe-walked-in.md").read_text(encoding="utf-8")
    # The held BYU page has OCR damage (reiations / betweell). Do not print a cleaned quote.
    assert (
        "the eventual adjustment of the relations between the two States must be left"
        not in text
    )
    records = load_all(str(SRC))
    grey = next(r for r in records if r.get("id") == "belgian-grey-book-1914")
    span = "In this event, Germany can undertake no obligations towards Belgium"
    assert verify_span(span, norm(grey.get("text") or ""))
