"""Reconstruction quotations must sit in the held papers we name."""
import os

from tools.apparatus import apparatus
from tools.provenance_gate import check
from tools.week_reconstruction import (
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


def _reconstruction_entries():
    return [
        e
        for e in apparatus(CHAPTERS, SOURCES)
        if e["chapter"] == "03-reconstruction"
    ]


def test_reconstruction_long_quotes_are_verified_against_named_sources():
    entries = _reconstruction_entries()
    assert len(entries) == 7
    assert all(e["status"] == "verified" for e in entries), [
        (e["status"], e["span"][:80]) for e in entries if e["status"] != "verified"
    ]
    by_span = {e["span"]: e for e in entries}

    justice = by_span[
        "What I ask for the Negro is not benevolence, not pity, not sympathy, but simply justice."
    ]
    assert justice["source_id"] == "douglass-what-the-black-man-wants-1865"
    assert "simply justice" in justice["passages"][0]["quoted"]

    wages = by_span[
        "we have concluded to test your sincerity by asking you to send us our wages for the time we served you."
    ]
    assert wages["source_id"] == "cincinnati-commercial-letter-1865"
    assert "test your sincerity" in wages["passages"][0]["quoted"]

    fourteenth = by_span[
        "All persons born or naturalized in the United States, and subject to the jurisdiction thereof, are citizens of the United States and of the State wherein they reside."
    ]
    assert fourteenth["source_id"] == "fourteenth-amendment-1868"

    fifteenth = by_span[
        "The right of citizens of the United States to vote shall not be denied or abridged by the United States or by any State on account of race, color, or previous condition of servitude."
    ]
    assert fifteenth["source_id"] == "fifteenth-amendment-1870"

    thirteenth = by_span[
        "except as a punishment for crime whereof the party shall have been duly convicted."
    ]
    assert thirteenth["source_id"] == "thirteenth-amendment-1865"

    wanted = by_span[
        "who were owned by a family of the name of Bailey, who lived at Clarksville, Va."
    ]
    assert wanted["source_id"] == "freedmens-bureau-records"
    assert "Clarksville" in wanted["passages"][0]["quoted"]

    cruikshank = by_span[
        "The fourteenth amendment prohibits a State from depriving any person of life, liberty, or property, without due process of law; but this adds nothing to the rights of one citizen as against another."
    ]
    assert cruikshank["source_id"] == "us-v-cruikshank-1876"
    assert "adds nothing to the rights" in cruikshank["passages"][0]["quoted"]


def test_us_chapters_including_reconstruction_pass_the_provenance_gate():
    errors = check(CHAPTERS, SOURCES)
    assert errors == [], errors


def test_reconstruction_week_is_five_held_days():
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
    assert 'data-week="reconstruction"' in html
    assert "High school" in html
    assert "Shorter path" in html
    assert "not a school year" in SCOPE
    assert "A parent can skip" in html
    for sid in HELD_SOURCE_IDS:
        assert sid in html or sid == ENTRY_STEM
    assert "klan-joint-select-committee-1871" not in html
    assert "$19" not in html
    assert "Buy this week" not in html
