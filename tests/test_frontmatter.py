from tools.frontmatter import parse


def test_parses_scalars_and_body():
    fields, body = parse(
        "---\nid: douglass-narrative-1845\ndate: 1845\n---\n\nFour score.\n"
    )
    assert fields["id"] == "douglass-narrative-1845"
    assert fields["date"] == "1845"
    assert body.strip() == "Four score."


def test_parses_inline_lists():
    fields, _ = parse("---\nband: [1-6, 7-12]\n---\n")
    assert fields["band"] == ["1-6", "7-12"]


def test_values_containing_colons_survive():
    fields, _ = parse("---\nurl: https://example.org/a:b\n---\n")
    assert fields["url"] == "https://example.org/a:b"


def test_absent_frontmatter_returns_empty_fields_and_whole_text():
    fields, body = parse("no frontmatter here")
    assert fields == {}
    assert body == "no frontmatter here"


def test_quoted_values_are_unquoted():
    fields, _ = parse('---\ntitle: "Common Sense, 1776"\n---\n')
    assert fields["title"] == "Common Sense, 1776"


def test_block_sequences_preserve_commas_in_items():
    fields, _ = parse(
        "---\ncovers_quotations:\n"
        "  - Injustice anywhere is a threat to justice everywhere.\n"
        "  - prefers a negative peace… to a positive peace\n---\n"
    )
    assert fields["covers_quotations"] == [
        "Injustice anywhere is a threat to justice everywhere.",
        "prefers a negative peace… to a positive peace",
    ]
