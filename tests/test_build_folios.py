"""The folio generator must not invent prose, and must emit the app shell."""
from pathlib import Path

from tools.build_folios import parse_chapter, render, chapter_to_html


def test_parse_chapter_reads_title_and_ledger_blocks(tmp_path):
    p = tmp_path / "01-x.md"
    p.write_text(
        "# Title — Subtitle\n\n"
        "✅ **The achievement is real.** Prose about it.\n\n"
        "❌ **The failure is real.** Prose about that.\n\n"
        '> *"a short quote that is long enough xx"*\n'
        "> — Someone, 1776\n\n"
        "**The takeaway:** Decide for yourself.\n",
        encoding="utf-8",
    )
    ch = parse_chapter(p)
    assert ch["name"] == "Title"
    assert ch["subtitle"] == "Subtitle"
    assert "achievement is real" in ch["achieved"]
    assert "failure is real" in ch["cost"]
    assert ch["takeaway"].startswith("Decide")
    assert len(ch["quotes"]) == 1


def test_render_is_tabbed_app_shell_not_wizard_gate():
    ch = {
        "stem": "01-x",
        "name": "Title",
        "subtitle": "Sub",
        "achieved": "**The achievement is real.** Yes.",
        "cost": "**The failure is real.** Yes.",
        "takeaway": "You decide.",
        "quotes": [
            {
                "span": "all men are created equal enough chars",
                "attribution": "Doc",
            }
        ],
        "text": "# Title — Sub\n\nHello body.\n",
        "callouts": ["Doc, 1776"],
    }
    entries = [
        {
            "chapter": "01-x",
            "span": "all men are created equal enough chars",
            "status": "verified",
            "source_id": "decl-1776",
            "source_title": "Declaration",
            "url": "https://example.org/d",
            "passages": [
                {
                    "before": "before words",
                    "quoted": "all men are created equal enough chars",
                    "after": "after words",
                }
            ],
        }
    ]
    page = render(
        ch,
        entries,
        "",
        cards={"decl-1776": {"id": "decl-1776", "title": "Declaration", "status": "held"}},
        callout_to={"Doc, 1776": "decl-1776"},
        span_to={"all men are created equal enough chars": "decl-1776"},
    )
    assert 'role="tablist"' in page
    assert "panel-established" in page
    assert "panel-sources" in page
    assert "panel-conflict" in page
    assert "panel-unknown" in page
    assert "panel-read" in page
    assert "Verified" in page
    assert "See it where it is written" in page
    assert "app-shell" in page
    assert "app.css" in page
    assert "source-drawer" in page
    assert "source-cards-data" in page
    # not a hard gate before the record
    assert "Choose one to continue" not in page
    assert 'id="go0"' not in page


def test_chapter_to_html_keeps_primary_source_callouts():
    html = chapter_to_html(
        "# T — S\n\n**Chapter 1**\n\n## Section\n\n"
        "**Primary Source:** Declaration of Independence, 1776.\n\n"
        "A paragraph.\n"
    )
    assert "primary-source" in html
    assert "Declaration of Independence" in html
    assert "<h2>" in html


def test_chapter_to_html_makes_callouts_and_quotes_tappable():
    html = chapter_to_html(
        "# T — S\n\n"
        "**Primary Source:** Declaration of Independence, 1776.\n\n"
        'He wrote "all men are created equal enough chars for gate" plainly.\n',
        callout_to={"Declaration of Independence, 1776": "decl-1776"},
        span_to={"all men are created equal enough chars for gate": "decl-1776"},
    )
    assert 'data-open-card="decl-1776"' in html
    assert "tap-callout" in html or "tap-quote" in html
