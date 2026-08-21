
import os
import tempfile

from tools.callouts import all_callouts, callouts_in


def test_extracts_a_callout_and_strips_the_trailing_period():
    assert callouts_in("**Primary Source:** Declaration of Independence, 1776.") == [
        "Declaration of Independence, 1776"
    ]


def test_keeps_internal_punctuation_and_markdown_emphasis():
    text = "**Primary Source:** *Plessy v. Ferguson*, 1896 — the doctrine."
    assert callouts_in(text) == ["*Plessy v. Ferguson*, 1896 — the doctrine"]


def test_finds_every_callout_in_a_multi_section_chapter():
    text = "intro\n\n**Primary Source:** A, 1900.\n\nmore\n\n**Primary Source:** B, 1901.\n"
    assert callouts_in(text) == ["A, 1900", "B, 1901"]


def test_ignores_prose_that_merely_mentions_primary_sources():
    assert callouts_in("We rely on primary sources throughout.") == []


def test_all_callouts_pairs_each_with_its_chapter_stem():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "01-x.md"), "w", encoding="utf-8") as f:
            f.write("**Primary Source:** A, 1900.\n")
        assert all_callouts(tmp) == [("01-x", "A, 1900")]
