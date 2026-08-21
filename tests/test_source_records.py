
import os
import tempfile

from tools.source_records import load_all, validate

VALID = """---
id: douglass-narrative-1845
title: Narrative of the Life of Frederick Douglass, an American Slave
author: Frederick Douglass
date: 1845
type: document
rights: public-domain
url: https://docsouth.unc.edu/neh/douglass/douglass.html
fetched_at: 2026-08-10
sha256: abc123
callout: Narrative of the Life of Frederick Douglass, 1845
cited_by: [02-slavery-and-emancipation]
---

You have seen how a man was made a slave.
"""


def _write(tmp, name, text):
    with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
        f.write(text)


def test_loads_a_valid_record_with_its_body():
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "douglass-narrative-1845.md", VALID)
        records = load_all(tmp)
        assert len(records) == 1
        assert records[0]["id"] == "douglass-narrative-1845"
        assert "made a slave" in records[0]["text"]
        assert validate(records[0]) == []


def test_body_text_without_a_url_is_rejected():
    bad = VALID.replace("url: https://docsouth.unc.edu/neh/douglass/douglass.html\n", "")
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "x.md", bad)
        errors = validate(load_all(tmp)[0])
        assert any("text without a url" in e for e in errors)


def test_restricted_rights_must_not_carry_text():
    bad = VALID.replace("rights: public-domain", "rights: restricted")
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "x.md", bad)
        errors = validate(load_all(tmp)[0])
        assert any("restricted" in e for e in errors)


def test_id_must_match_filename():
    bad = VALID.replace("id: douglass-narrative-1845", "id: something-else")
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "douglass-narrative-1845.md", bad)
        errors = validate(load_all(tmp)[0])
        assert any("filename" in e for e in errors)


def test_missing_required_fields_are_named_individually():
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "x.md", "---\nid: x\n---\n")
        errors = validate(load_all(tmp)[0])
        assert any("title" in e for e in errors)
        assert any("callout" in e for e in errors)


def test_empty_optional_fields_are_absent_not_empty_strings():
    no_author = VALID.replace("author: Frederick Douglass\n", "")
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "douglass-narrative-1845.md", no_author)
        assert "author" not in load_all(tmp)[0]


def test_artifact_type_may_have_no_text_and_no_url():
    artifact = """---
id: roosevelt-spectacle-case-1912
title: Steel spectacle case, Milwaukee, 1912
date: 1912
type: artifact
rights: public-domain
callout: Speech manuscript, Progressive Cause Greater Than Any Individual, with bullet perforation; steel spectacle case, 1912
cited_by: [07-the-bullet-and-the-podium]
---
"""
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "roosevelt-spectacle-case-1912.md", artifact)
        assert validate(load_all(tmp)[0]) == []
