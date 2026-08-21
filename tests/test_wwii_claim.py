"""Victory and the Bill must not read as a complete WWII set or Holocaust coverage."""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WWII = REPO / "content/collections/modern-wars/chapters/01-world-war-ii.md"
WWI = REPO / "content/collections/modern-wars/chapters/01-how-europe-walked-in.md"
HOME = REPO / "site/index.html"
US_INDEX = REPO / "site/read/index.html"
WARS_INDEX = REPO / "site/read/modern-wars/index.html"

HELD_QUOTES = [
    "Yesterday, December 7, 1941—a date which will live in infamy—the United States of America was suddenly and deliberately attacked by naval and air forces of the Empire of Japan.",
    "a date which will live in infamy",
    "First, their countries seek no aggrandizement, territorial or other",
    "they respect the right of all peoples to choose the form of government under which they will live",
    "any or all persons may be excluded",
    "all legal restrictions which curtail the civil rights of a single racial group are immediately suspect",
    "racial antagonism never can",
    "The German armed forces on land, at sea and in the air have been completely defeated and have surrendered unconditionally",
    "It is an atomic bomb. It is a harnessing of the basic power of the universe.",
    "We hereby proclaim the unconditional surrender to the Allied Powers of the Japanese Imperial General Headquarters and of all Japanese armed forces and all armed forces under the Japanese control wherever situated.",
]


def test_wwii_folio_names_what_the_ten_papers_hold():
    text = WWII.read_text(encoding="utf-8")
    for span in HELD_QUOTES:
        assert span in text
    assert "not a complete WWII set" in text
    assert "American papers, not the war" in text
    assert "does not hold papers on the Holocaust" in text or "does not cover the fighting or the Holocaust" in text
    assert "1939–1945" not in text
    assert "1939-1945" not in text


def test_wwii_does_not_present_holocaust_or_fighting_as_covered():
    text = WWII.read_text(encoding="utf-8")
    assert "industrialized mass murder" not in text
    assert "tens of millions" not in text
    assert "How the War Ended in Europe" not in text
    assert "How the War Ended in the Pacific" not in text
    assert "The War America Entered" not in text


def test_1914_next_footer_does_not_claim_a_1939_1945_war():
    text = WWI.read_text(encoding="utf-8")
    footer = text.split("**Further Reading")[-1]
    assert "1939–1945" not in footer
    assert "1939-1945" not in footer
    assert "Victory and the Bill" in footer
    assert "How Europe walked in" in text
    assert text.count("it is clear that the peace of Europe cannot be preserved.") == 1


def test_homepage_and_indexes_agree_with_the_open_shelf():
    home = HOME.read_text(encoding="utf-8")
    us = US_INDEX.read_text(encoding="utf-8")
    wars = WARS_INDEX.read_text(encoding="utf-8")

    assert "7 entries" not in home
    assert "6 entries" in home
    assert "The Bullet and the Podium" not in home
    assert "The Bullet and the Podium" not in us
    assert "07-the-bullet-and-the-podium" not in us
    assert "Across all 6 entries" in us
    assert "7 unverified" not in us
    assert not (REPO / "site/read/07-the-bullet-and-the-podium.html").exists()

    assert "1939–1945" not in home
    assert "1939–1945" not in wars
    assert "not a complete WWII set" in home or "American papers, not the war" in home
    assert "Victory and the Bill" in wars
    assert "How Europe walked in" in wars
    assert "of 14 quotations" in wars
