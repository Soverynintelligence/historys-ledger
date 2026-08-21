from tools.source_cards import build_for_chapter, card_from_record, gap_card, status_for


def test_status_held_restricted_citation_only():
    assert status_for({"text": "body", "rights": "public-domain"}) == "held"
    assert status_for({"text": "", "rights": "restricted"}) == "restricted"
    assert status_for({"text": "", "rights": "us-government"}) == "citation-only"


def test_card_from_record_includes_passage_from_apparatus():
    rec = {
        "id": "decl-1776",
        "title": "Declaration",
        "date": "1776",
        "type": "document",
        "rights": "us-government",
        "callout": "Declaration of Independence, 1776",
        "url": "https://example.org/d",
        "text": "all men",
    }
    app = [
        {
            "status": "verified",
            "source_id": "decl-1776",
            "span": "all men are created equal",
            "passages": [
                {"before": "we hold", "quoted": "all men are created equal", "after": "that"}
            ],
        }
    ]
    card = card_from_record(rec, app)
    assert card["status"] == "held"
    assert card["passages"][0]["quoted"] == "all men are created equal"


def test_build_maps_callout_and_verified_span():
    records = [
        {
            "id": "decl-1776",
            "title": "Declaration",
            "date": "1776",
            "type": "document",
            "rights": "us-government",
            "callout": "Declaration of Independence, 1776",
            "cited_by": ["01-x"],
            "url": "https://example.org/d",
            "text": "all men are created equal",
        }
    ]
    apparatus = [
        {
            "chapter": "01-x",
            "span": "all men are created equal",
            "status": "verified",
            "source_id": "decl-1776",
            "source_title": "Declaration",
            "url": "https://example.org/d",
            "passages": [
                {"before": "x", "quoted": "all men are created equal", "after": "y"}
            ],
        }
    ]
    cards, callout_to, span_to = build_for_chapter(records, "01-x", apparatus)
    assert callout_to["Declaration of Independence, 1776"] == "decl-1776"
    assert span_to["all men are created equal"] == "decl-1776"
    assert cards["decl-1776"]["status"] == "held"


def test_gap_card_for_unsourced():
    g = gap_card(
        {
            "span": "a long quotation that is not in any held source here",
            "status": "unsourced",
            "reason": "no source record we hold contains this quotation",
        }
    )
    assert g["kind"] == "gap"
    assert "no source record" in g["reason"]
