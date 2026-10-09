"""Standard Oil quotations must sit in the held papers we name."""
import os

from tools.apparatus import apparatus
from tools.provenance_gate import check
from tools.week_standard_oil import (
    DAYS,
    ENTRY_STEM,
    HELD_SOURCE_IDS,
    SCOPE,
    validate,
    render_html,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS = os.path.join(HERE, "content", "chapters")
SOURCES = os.path.join(HERE, "content", "sources")


def _standard_oil_entries():
    return [
        e
        for e in apparatus(CHAPTERS, SOURCES)
        if e["chapter"] == "04-standard-oil"
    ]


def test_standard_oil_long_quotes_are_verified_against_named_sources():
    entries = _standard_oil_entries()
    assert len(entries) == 8
    assert all(e["status"] == "verified" for e in entries), [
        (e["status"], e["span"][:80]) for e in entries if e["status"] != "verified"
    ]
    by_span = {e["span"]: e for e in entries}

    competition = by_span[
        "The day of individual competition in large affairs is past and gone"
    ]
    assert competition["source_id"] == "rockefeller-random-reminiscences-1909"
    assert "individual competition" in competition["passages"][0]["quoted"]

    butcher = by_span[
        "Naturally, all sorts of people went into it: the butcher, the baker, and the candlestick-maker began to refine oil"
    ]
    assert butcher["source_id"] == "rockefeller-random-reminiscences-1909"
    assert "candlestick-maker" in butcher["passages"][0]["quoted"]

    rebates = by_span[
        "The Standard Oil Company of Ohio, of which I was president, did receive rebates from the railroads prior to 1880, but received no advantages for which it did not give full compensation."
    ]
    assert rebates["source_id"] == "rockefeller-random-reminiscences-1909"
    assert "did receive rebates" in rebates["passages"][0]["quoted"]

    drawback = by_span["He also had a drawback on every barrel his rivals shipped."]
    assert drawback["source_id"] == "tarbell-history-standard-oil-1904"
    assert "drawback" in drawback["passages"][0]["quoted"]

    ninety = by_span[
        "It manufactured fully ninety per cent. of this product, and aimed to manufacture 100 per cent."
    ]
    assert ninety["source_id"] == "tarbell-history-standard-oil-1904"
    assert "ninety per cent" in ninety["passages"][0]["quoted"]

    dice = by_span[
        "Yet Mr. Rockefeller has systematically played with loaded dice, and it is doubtful if there has ever been a time since 1872 when he has run a race with a competitor and started fair."
    ]
    assert dice["source_id"] == "tarbell-history-standard-oil-1904"
    assert "loaded dice" in dice["passages"][0]["quoted"]

    sherman = by_span[
        "Every contract, combination in the form of trust or other- wise, or conspiracy, in restraint of trade or commerce among the several States, or with foreign nations, is hereby declared to be illegal."
    ]
    assert sherman["source_id"] == "sherman-antitrust-act-1890"

    thirty_seven = by_span[
        "The Standard Oil Company of New Jersey was enjoined from voting the stocks or exerting any control over the said thirty-seven subsidiary companies"
    ]
    assert thirty_seven["source_id"] == "standard-oil-v-us-1911"
    assert "thirty-seven" in thirty_seven["passages"][0]["quoted"]


def test_us_chapters_including_standard_oil_pass_the_provenance_gate():
    errors = check(CHAPTERS, SOURCES)
    assert errors == [], errors


def test_standard_oil_week_is_five_held_days():
    assert validate() == []
    assert len(DAYS) == 5
    assert [d["weekday"] for d in DAYS] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]
    html = render_html()
    assert 'data-week="standard-oil"' in html
    assert "High school" in html
    assert "Shorter path" in html
    assert "not a school year" in SCOPE
    assert "A parent can skip" in html
    for sid in HELD_SOURCE_IDS:
        assert sid in html or sid == ENTRY_STEM
    assert "hepburn-committee-1879" not in html
    assert "$19" not in html
    assert "Buy this week" not in html
