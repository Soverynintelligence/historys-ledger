"""1914 wraps as a July crisis week on the held entry — not a new war."""
from pathlib import Path

from tools.source_cards import status_for
from tools.source_records import load_all
from tools.week_1914 import (
    BUY_LABEL,
    BUY_LINE,
    BUY_URL,
    CHAPTER,
    DAYS,
    ENTRY_STEM,
    FORBIDDEN_WEEK_COPY,
    HELD_SOURCE_IDS,
    HUNT_IDS,
    SCOPE,
    slug,
    validate,
    week_source_ids,
    render_html,
)
from tools.build_folios import chapter_to_html, main as build_main

REPO = Path(__file__).resolve().parent.parent
WARS_CH = REPO / "content/collections/modern-wars/chapters"
WARS_SRC = REPO / "content/collections/modern-wars/sources"
HOME = REPO / "site/index.html"


def test_week_is_five_held_days_and_validate_is_clean():
    assert validate() == []
    assert len(DAYS) == 5
    assert [d["weekday"] for d in DAYS] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]


def test_week_opens_only_held_1914_sources_cited_by_this_entry():
    records = {r["id"]: r for r in load_all(str(WARS_SRC))}
    chapter = CHAPTER.read_text(encoding="utf-8")
    used = week_source_ids()
    assert used == set(HELD_SOURCE_IDS)
    for sid in used:
        rec = records[sid]
        assert status_for(rec) == "held"
        assert ENTRY_STEM in (rec.get("cited_by") or [])
        assert rec["id"].endswith("-1914")
    for day in DAYS:
        assert f"## {day['heading']}" in chapter
        assert day["read_id"] == slug(day["heading"])


def test_hunt_artifacts_are_held_grey_book_and_ultimatum():
    assert HUNT_IDS == (
        "belgian-grey-book-1914",
        "austro-hungarian-ultimatum-1914",
    )
    html = render_html()
    assert 'data-open-card="belgian-grey-book-1914"' in html
    assert "Grey Book No. 20" in html
    assert 'data-open-card="austro-hungarian-ultimatum-1914"' in html
    assert "do-we-hold-this" in html or "do we hold" in html.lower()
    assert "cite-or-stop" in html or "Cite or stop" in html


def test_week_copy_is_a_complete_1914_set_priced_nineteen():
    html = render_html()
    assert "complete 1914 set" in html
    assert "July crisis week" in html
    assert "not a school year" in html
    assert "not for sale" not in html.lower()
    assert BUY_LINE in html
    assert "$19. One week at the table." in html
    assert "Fourteen held documents, Monday through Friday." in html
    assert "When we don't hold the page, Atticus stops." in html
    assert BUY_LABEL in html
    assert BUY_URL in html
    assert html.count(BUY_URL) == 1
    assert f'data-week-buy href="{BUY_URL}"' in html
    assert "Nothing is scored" in html
    assert "Weigh stays optional" in html
    assert "Parent table" in html
    assert "Shorter path" in html
    for token in FORBIDDEN_WEEK_COPY:
        assert token not in html
    assert "quiz" not in html.lower()
    assert "$79" not in html
    assert "waitlist" not in html.lower()
    assert "Family year" not in html
    assert "mailto:" not in html
    assert "not a school year" in SCOPE
    assert "not for sale" not in SCOPE.lower()
    assert BUY_URL == "https://buy.stripe.com/14A4gz3Bp3S67Kcf9s83C00"


def test_week_html_does_not_invent_quotations():
    html = render_html()
    # Point at cards; do not reprint chapter quotations in the week chrome.
    assert "peace of Europe cannot be preserved" not in html
    assert "necessity knows no law" not in html
    assert "blockquote" not in html


def test_chapter_headings_get_week_read_ids():
    text = CHAPTER.read_text(encoding="utf-8")
    html = chapter_to_html(text)
    for day in DAYS:
        assert f'id="{day["read_id"]}"' in html


def test_no_new_war_chapter_files_and_no_redirects_loop():
    stems = sorted(p.stem for p in WARS_CH.glob("*.md"))
    assert stems == ["01-how-europe-walked-in", "01-world-war-ii"]
    assert not (REPO / "site/_redirects").exists()
    assert not (REPO / "_redirects").exists()
    for name in (
        "1917",
        "1919",
        "holocaust",
        "korea",
        "vietnam",
        "classical",
        "empires",
        "pacific",
    ):
        assert not list(WARS_CH.glob(f"*{name}*"))


def test_folio_and_indexes_carry_the_week_at_nineteen(tmp_path):
    build_main([str(tmp_path)])
    folio = (tmp_path / "modern-wars" / "01-how-europe-walked-in.html").read_text(
        encoding="utf-8"
    )
    wars = (tmp_path / "modern-wars" / "index.html").read_text(encoding="utf-8")
    assert 'data-week="1914"' in folio
    assert "Parent table" in folio
    assert "Shorter path" in folio
    assert "Grey Book No. 20" in folio
    assert "panel-weigh" in folio
    assert "quiz" not in folio.lower()
    assert BUY_LINE in folio
    assert BUY_LABEL in folio
    assert BUY_URL in folio
    assert folio.count(BUY_URL) == 1
    assert "not for sale" not in folio.lower()
    assert "waitlist" not in folio.lower()
    assert "Family year" not in folio
    assert "mailto:" not in folio
    assert "$79" not in folio
    assert "July crisis week" in wars
    assert "only complete Modern Wars set" in wars
    assert "not for sale" not in wars.lower()
    assert "not a school year" in wars
    assert "$79" not in wars
    assert BUY_URL not in wars
    home = HOME.read_text(encoding="utf-8")
    assert "July crisis week" in home
    assert "complete" in home
    assert "The Bullet and the Podium" not in home
    assert BUY_URL not in home
