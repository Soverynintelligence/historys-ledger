"""The apparatus must show the reader the same three states the gate sees.

The failure this guards against is a reader packet that looks authoritative
because every quotation is printed the same way, whether it was checked against
a held document, taken on trust from a source we may not reproduce, or never
located at all.
"""
import os
import tempfile

from tools.apparatus import apparatus, counts, locate, passage, _tokens

DOC = ("There is something very absurd, in supposing a continent to be "
       "perpetually governed by an island. In no instance hath nature made "
       "the satellite larger than its primary planet.")


def _dirs(chapter: str, *records: tuple[str, str]):
    tmp = tempfile.mkdtemp()
    ch, sr = os.path.join(tmp, "ch"), os.path.join(tmp, "sr")
    os.makedirs(ch), os.makedirs(sr)
    with open(os.path.join(ch, "01-x.md"), "w", encoding="utf-8") as f:
        f.write(chapter)
    for name, body in records:
        with open(os.path.join(sr, name), "w", encoding="utf-8") as f:
            f.write(body)
    return ch, sr


def _doc_record(text=DOC):
    return ("paine-1776.md",
            "---\nid: paine-1776\ntitle: Common Sense\ndate: 1776\ntype: document\n"
            "rights: public-domain\nurl: https://example.org/cs\n"
            "callout: Common Sense, 1776\ncited_by: [01-x]\nfetched_at: 2026-08-13\n"
            "sha256: x\nsource_sha256: y\nextraction: raw\n---\n\n" + text + "\n")


def test_locate_finds_the_span_in_readable_source():
    at = locate("perpetually governed by an island", _tokens(DOC))
    assert at is not None
    assert DOC[at[0]:at[1]] == "perpetually governed by an island"


def test_locate_ignores_punctuation_and_case_the_way_norm_does():
    at = locate("something very absurd in supposing", _tokens(DOC))
    # The source has a comma inside the phrase; the match must survive it.
    assert at is not None
    assert "absurd, in supposing" in DOC[at[0]:at[1]]


def test_a_verified_quotation_carries_the_surrounding_passage():
    ch, sr = _dirs('"perpetually governed by an island"\n', _doc_record())
    e = apparatus(ch, sr)[0]
    assert e["status"] == "verified"
    assert e["source_id"] == "paine-1776"
    # The reader gets the source's own words either side — that is the whole
    # point: a bare citation cannot show whether a quotation was fair.
    assert "supposing a continent" in e["passages"][0]["before"]
    assert "satellite larger" in e["passages"][0]["after"]


def test_an_unlocatable_quotation_is_reported_as_unsourced_not_dropped():
    ch, sr = _dirs('"Jefferson wrote that commerce must be watered often"\n', _doc_record())
    e = apparatus(ch, sr)[0]
    assert e["status"] == "unsourced"
    assert "no source record" in e["reason"]


def test_a_restricted_declaration_says_copyright_not_missing():
    rec = ("king-1963.md",
           "---\nid: king-1963\ntitle: Letter from Birmingham Jail\ndate: 1963\n"
           "type: document\nrights: restricted\nurl: https://example.org/k\n"
           "callout: Letter from Birmingham Jail, 1963\ncited_by: [01-x]\n"
           "covers_quotations:\n  - Injustice anywhere is a threat to justice everywhere.\n---\n")
    ch, sr = _dirs('"Injustice anywhere is a threat to justice everywhere."\n', rec)
    e = apparatus(ch, sr)[0]
    assert e["status"] == "unverified"
    assert "copyright" in e["reason"]


def test_a_record_set_declaration_says_aggregate_not_copyright():
    rec = ("mccarthy.md",
           "---\nid: mccarthy\ntitle: Army-McCarthy transcripts\ndate: 1954\n"
           "type: record-set\nrights: us-government\nurl: https://example.org/m\n"
           "callout: Army-McCarthy hearing transcripts, 1954\ncited_by: [01-x]\n"
           "covers_quotations:\n  - Have you no sense of decency, sir, at long last?\n---\n")
    ch, sr = _dirs('"Have you no sense of decency, sir, at long last?"\n', rec)
    e = apparatus(ch, sr)[0]
    assert e["status"] == "unverified"
    assert "aggregate" in e["reason"]
    assert "copyright" not in e["reason"]


def test_an_elided_quotation_locates_every_fragment_separately():
    ch, sr = _dirs('"There is something very absurd… made the satellite larger"\n',
                   _doc_record())
    e = apparatus(ch, sr)[0]
    assert e["status"] == "verified"
    assert len(e["passages"]) == 2


def test_counts_add_up_to_every_quotation():
    ch, sr = _dirs('"perpetually governed by an island"\n\n"a thing nobody ever wrote down"\n',
                   _doc_record())
    entries = apparatus(ch, sr)
    c = counts(entries)
    assert sum(c.values()) == len(entries) == 2
    assert c["verified"] == 1 and c["unsourced"] == 1
