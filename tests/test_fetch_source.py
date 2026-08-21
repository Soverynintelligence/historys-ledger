
import hashlib
import os
import tempfile

from tools.fetch_source import fetch, render_record, reverify


def fake_opener(pages):
    def _open(url):
        if url not in pages:
            raise OSError(f"404 {url}")
        return pages[url]
    return _open


def test_fetch_returns_text_and_its_sha256():
    text, digest = fetch("https://x/doc", opener=fake_opener({"https://x/doc": "all men"}))
    assert text == "all men"
    assert digest == hashlib.sha256("all men".encode()).hexdigest()


def test_render_record_writes_frontmatter_then_body():
    out = render_record(
        {"id": "a-1776", "title": "A", "date": "1776", "type": "document",
         "rights": "public-domain", "url": "https://x/doc", "fetched_at": "2026-08-10",
         "sha256": "abc", "callout": "A, 1776", "cited_by": ["01-x"]},
        "all men",
    )
    assert out.startswith("---\n")
    assert "cited_by: [01-x]" in out
    assert out.rstrip().endswith("all men")


def test_render_record_omits_absent_fields_entirely():
    out = render_record({"id": "a", "title": "A", "author": ""}, "")
    assert "author" not in out


def test_reverify_reports_urls_that_no_longer_fetch():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "a-1776.md"), "w", encoding="utf-8") as f:
            f.write("---\nid: a-1776\nurl: https://x/gone\n---\n\nbody\n")
        problems = reverify(tmp, opener=fake_opener({}))
        assert any("gone" in p for p in problems)


def test_reverify_is_silent_when_every_url_still_fetches():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "a-1776.md"), "w", encoding="utf-8") as f:
            f.write("---\nid: a-1776\nurl: https://x/doc\n---\n\nbody\n")
        assert reverify(tmp, opener=fake_opener({"https://x/doc": "body"})) == []
