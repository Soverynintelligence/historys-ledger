"""Atticus's open shelf is computed, and 1914 is on it."""
import os
import tempfile
from pathlib import Path

from tools.generate_corpus import generate_open
from tools.open_shelf import entries, render, stems

REPO = Path(__file__).resolve().parent.parent
WWII = REPO / "content/collections/modern-wars/chapters/01-world-war-ii.md"
WWI = REPO / "content/collections/modern-wars/chapters/01-how-europe-walked-in.md"


def test_open_shelf_includes_1914_how_europe_walked_in():
    ids = stems()
    assert "01-how-europe-walked-in" in ids
    assert "01-world-war-ii" in ids
    titles = {e["stem"]: e["title"] for e in entries()}
    assert "How Europe walked in" in titles["01-how-europe-walked-in"]
    inventory = render()
    assert "01-how-europe-walked-in" in inventory
    assert "1914" in inventory
    assert "How Europe walked in" in inventory


def test_generate_open_copies_1914_and_writes_shelf_inventory():
    with tempfile.TemporaryDirectory() as tmp:
        written = generate_open(tmp)
        names = {os.path.basename(p) for p in written}
        assert "01-how-europe-walked-in.md" in names
        assert "01-world-war-ii.md" in names
        assert "OPEN-SHELF.md" in names
        shelf = Path(tmp, "OPEN-SHELF.md").read_text(encoding="utf-8")
        assert "How Europe walked in" in shelf
        assert "1914" in shelf
        copied = Path(tmp, "01-how-europe-walked-in.md").read_text(encoding="utf-8")
        assert copied == WWI.read_text(encoding="utf-8")


def test_committed_open_shelf_matches_computed_inventory():
    committed = (REPO / "content/open-shelf.md").read_text(encoding="utf-8")
    assert committed == render()


def test_wwii_next_does_not_call_wwi_planned():
    text = WWII.read_text(encoding="utf-8")
    assert "WWI, Korea, Vietnam) — planned, not yet open" not in text
    assert "How Europe walked in (1914)" in text
    footer = text.split("**Further Reading")[-1]
    assert "WWI" not in footer
    assert "Korea and Vietnam — planned, not yet open" in footer
