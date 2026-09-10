"""Kids Declaration Hunt — held cards only; Constitution is out of scope."""
from pathlib import Path

from tools.source_cards import status_for
from tools.source_records import load_all
from tools.week_kids_declaration import (
    CHAPTER,
    DAYS,
    ENTRY_STEM,
    FORBIDDEN_WEEK_COPY,
    HELD_SOURCE_IDS,
    INTRO,
    THIN_SOURCE_ID,
    slug,
    validate,
    week_source_ids,
    render_html,
)
from tools.build_folios import chapter_to_html, main as build_main

REPO = Path(__file__).resolve().parent.parent
KIDS_CH = REPO / "content/collections/kids/chapters"
KIDS_SRC = REPO / "content/collections/kids/sources"


def test_week_is_five_days_and_validate_is_clean():
    assert validate() == []
    assert len(DAYS) == 5
    assert [d["weekday"] for d in DAYS] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]
    assert [d["title"] for d in DAYS] == [
        "The Promise",
        "Life, Liberty…",
        "The Island",
        "Remember the Ladies",
        "Who used the words",
    ]


def test_held_hunts_open_only_cited_held_cards():
    records = {r["id"]: r for r in load_all(str(KIDS_SRC))}
    chapter = CHAPTER.read_text(encoding="utf-8")
    used = week_source_ids()
    assert used == set(HELD_SOURCE_IDS) | {THIN_SOURCE_ID}
    for sid in HELD_SOURCE_IDS:
        rec = records[sid]
        assert status_for(rec) == "held"
        assert ENTRY_STEM in (rec.get("cited_by") or [])
    thin = records[THIN_SOURCE_ID]
    assert status_for(thin) == "citation-only"
    assert not (thin.get("text") or "").strip()
    assert ENTRY_STEM in (thin.get("cited_by") or [])
    for day in DAYS:
        assert f"## {day['heading']}" in chapter
        assert day["read_id"] == slug(day["heading"])


def test_hunt_copy_is_cite_or_stop_and_unscored():
    html = render_html()
    assert "One week on this entry" in html
    assert 'data-week="kids-declaration"' in html
    assert 'data-height="kid"' in html
    assert INTRO in html
    assert "Atticus stopped" in html
    assert "If we don’t hold it, we stop" in html or "If we don't hold it, we stop" in html
    assert "Weigh stays optional. Nothing is scored." in html
    assert "Clear hunts" in html
    assert "data-hunt-stamp" in html
    assert "data-hunt-clear" in html
    assert "Parent sit-with" in html
    assert "Friday dinner" in html
    assert "Parents: Year 1" in html
    assert 'href="/family"' in html
    assert "What does our card actually say" in html
    assert 'data-open-card="declaration-of-independence-1776"' in html
    assert 'data-open-card="common-sense-1776"' in html
    assert 'data-open-card="adams-family-papers"' in html
    assert 'data-open-card="brom-and-bett-v-ashley-1781"' in html
    assert "data-ask-atticus" in html
    assert "Cite or stop" in html
    for token in FORBIDDEN_WEEK_COPY:
        assert token not in html
    assert "quiz" not in html.lower()
    assert "leaderboard" not in html.lower()
    assert "courtroom" not in html.lower()
    assert "jefferson" not in html.lower()
    assert "blockquote" not in html
    assert "$19" not in html
    assert "waitlist" not in html.lower()


def test_friday_is_honest_thin_card_not_a_courtroom():
    fri = DAYS[4]
    assert fri["sources"] == ("brom-and-bett-v-ashley-1781",)
    assert fri["held"] is False
    html = render_html()
    assert "What does our card actually say?" in html
    assert "your honor" not in html.lower()
    assert "elizabeth said" not in html.lower()
    assert "walked into court" not in html.lower()
    # Chapter may narrate Freeman; hunt chrome must not invent dialogue.
    hunt_only = html
    assert "I heard" not in hunt_only


def test_week_does_not_add_quotations_to_the_chapter():
    before = CHAPTER.read_text(encoding="utf-8")
    render_html()
    after = CHAPTER.read_text(encoding="utf-8")
    assert before == after
    assert before.count('> *"') == 4


def test_chapter_headings_get_week_read_ids():
    text = CHAPTER.read_text(encoding="utf-8")
    html = chapter_to_html(text)
    for day in DAYS:
        assert f'id="{day["read_id"]}"' in html


def test_folio_carries_hunt_on_declaration_only(tmp_path):
    build_main([str(tmp_path)])
    decl = (tmp_path / "kids" / "01-the-declaration.html").read_text(encoding="utf-8")
    const = (tmp_path / "kids" / "02-the-constitution.html").read_text(encoding="utf-8")
    kids_idx = (tmp_path / "kids" / "index.html").read_text(encoding="utf-8")
    assert 'data-week="kids-declaration"' in decl
    assert "The Promise" in decl
    assert "Remember the Ladies" in decl
    assert "Who used the words" in decl
    assert "Weigh stays optional. Nothing is scored." in decl
    assert "panel-weigh" in decl
    assert "Nothing here is scored" in decl
    js = (REPO / "site" / "app.js").read_text(encoding="utf-8")
    assert "hl-hunt-stamps-" in js
    assert "localStorage.getItem(key)" in js
    assert "data-hunt-clear" in js
    assert 'data-week="kids-declaration"' not in const
    assert "data-hunt-stamp" not in const
    assert "One week on this entry" not in const
    assert "Hunt week" not in kids_idx
    assert "quiz" not in decl.lower()
    assert "$19" not in decl
    assert "waitlist" not in decl.lower()
