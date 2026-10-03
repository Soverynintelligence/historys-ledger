"""Cold War quotations must sit in the held papers we name."""
import os

from tools.apparatus import apparatus
from tools.provenance_gate import check
from tools.week_cold_war import (
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


def _cold_war_entries():
    return [
        e
        for e in apparatus(CHAPTERS, SOURCES)
        if e["chapter"] == "06-cold-war"
    ]


def test_cold_war_long_quotes_are_verified_against_named_sources():
    entries = _cold_war_entries()
    assert len(entries) == 7
    assert all(e["status"] == "verified" for e in entries), [
        (e["status"], e["span"][:80]) for e in entries if e["status"] != "verified"
    ]
    by_span = {e["span"]: e for e in entries}

    eisenhower = by_span[
        "we must guard against the acquisition of unwarranted influence, whether sought or unsought, by the military-industrial complex."
    ]
    assert eisenhower["source_id"] == "eisenhower-farewell-1961"
    assert "military-industrial complex" in eisenhower["passages"][0]["quoted"]

    kennan = by_span[
        "In summary, we have here a political force committed fanatically to the belief that with US there can be no permanent modus vivendi"
    ]
    assert kennan["source_id"] == "kennan-long-telegram-1946"
    assert "modus vivendi" in kennan["passages"][0]["quoted"]

    truman = by_span[
        "I believe that it must be the policy of the United States to support free peoples who are resisting attempted subjugation by armed minorities or by outside pressures."
    ]
    assert truman["source_id"] == "truman-doctrine-1947"
    assert "free peoples" in truman["passages"][0]["quoted"]

    marshall = by_span[
        "It is logical that the United States should do whatever it is able to do to assist in the return of normal economic health in the world, without which there can be no political stability and no assured peace."
    ]
    assert marshall["source_id"] == "marshall-harvard-1947"
    assert "normal economic health" in marshall["passages"][0]["quoted"]

    welch = by_span[
        "Let us not assassinate this lad further, senator. You have done enough. Have you no sense of decency?"
    ]
    assert welch["source_id"] == "army-mccarthy-hearings-1954"
    assert "sense of decency" in welch["passages"][0]["quoted"]

    eo = by_span[
        "Any criminal, infamous, dishonest, immoral, or notoriously disgraceful conduct, habitual use of intoxicants to excess, drug addiction, sexual perversion."
    ]
    assert eo["source_id"] == "executive-order-10450-1953"
    assert "sexual perversion" in eo["passages"][0]["quoted"]

    kennedy = by_span[
        "It shall be the policy of this Nation to regard any nuclear missile launched from Cuba against any nation in the Western Hemisphere as an attack by the Soviet Union on the United States, requiring a full retaliatory response upon the Soviet Union."
    ]
    assert kennedy["source_id"] == "kennedy-cuba-1962"
    assert "nuclear missile" in kennedy["passages"][0]["quoted"]


def test_us_chapters_including_cold_war_pass_the_provenance_gate():
    errors = check(CHAPTERS, SOURCES)
    assert errors == [], errors


def test_cold_war_week_is_five_held_days():
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
    assert 'data-week="cold-war"' in html
    assert "High school" in html
    assert "Shorter path" in html
    assert "not a school year" in SCOPE
    assert "A parent can skip" in html
    for sid in HELD_SOURCE_IDS:
        assert sid in html or sid == ENTRY_STEM
    assert "church-committee-1975" not in html
    assert "petrov-soviet-naval-accounts" not in html
    assert "$19" not in html
    assert "Buy this week" not in html
