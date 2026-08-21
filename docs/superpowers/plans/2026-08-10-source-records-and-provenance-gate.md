# Source Records and the Provenance Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put verified primary-source documents behind the 39 `**Primary Source:**` callouts in the chapters, and build a gate that mechanically proves the prose does not misquote them.

**Architecture:** `~/american-history-app` becomes the single source of truth: `content/chapters/` (prose) plus a new `content/sources/` (documents as records with frontmatter). A build-time gate in `tools/` makes three assertions — every callout resolves to a record, every recorded URL still fetches, and every quoted span of 25+ characters appears verbatim in a source that chapter cites. A generator then produces the Atticus corpus from canonical content, replacing the hand-copy-and-scp step that stranded chapter 7.

**Tech Stack:** Python 3 (stdlib only — no new dependencies), pytest 9.1.0, plain Markdown with a minimal hand-rolled frontmatter parser.

## Global Constraints

- **Source text is never written from memory.** A record may carry document text only if `tools/fetch_source.py` retrieved it from a URL, which is recorded along with `fetched_at` and a `sha256` of the retrieved text. Records that cannot be fetched carry no body. This is enforced in code, not by discipline.
- **A field is absent rather than guessed.** No placeholder repositories, approximate dates, or invented URLs. This continues `sources.py`'s existing decision to leave `where` as `None`.
- **`id` is assigned by hand, never slugified from prose.** Slugified prose is what let a claim about Article I **Section 9** be cited to `u-s-constitution-article-i-section-2`.
- **Quote pairing must reuse the positional algorithm** from `~/atticus/guard.py::quoted_spans` verbatim. Straight quotes are not directional; pairing them with a regex refused correct answers twice in production. Do not reimplement it as one regex.
- **The 25-character threshold** for "a quotation of substance" is copied from `guard.py:104` (`if len(n) < 25`). Keep the two in sync or the gate and the runtime rails disagree.
- **Two sources are `rights: restricted`** — `"I Have a Dream"` (1963) and `"Letter from Birmingham Jail"` (1963), both King Estate. They never carry body text. The quotation assertion must skip them rather than demand a text we may not hold.
- **stdlib only.** No PyYAML, no requests, no frontmatter library. The repo currently has one script (`tools/build_reader_packet.py`) and no dependency manifest; keep it that way.

## File Structure

| File | Responsibility |
|---|---|
| `tools/quoted_spans.py` | Vendored copy of the positional quote-pairing algorithm + the 25-char norm. One job: find quoted spans. |
| `tools/frontmatter.py` | Minimal `---`-delimited frontmatter parser. Scalars and `[a, b]` lists only. |
| `tools/source_records.py` | Load and validate `content/sources/*.md` into record dicts. Owns the schema rules. |
| `tools/callouts.py` | Extract `**Primary Source:**` lines from chapters. Owns the callout regex. |
| `tools/fetch_source.py` | Retrieve a document from a URL and write a record. The only writer of body text. |
| `tools/provenance_gate.py` | The three assertions. Exit non-zero on failure. |
| `tools/generate_corpus.py` | Produce `~/atticus/corpus/` from `content/chapters/`. |
| `content/sources/*.md` | The records themselves (content, not code). |
| `tests/` | pytest, at repo root. No network, no model. |

---

### Task 1: Quote-span extraction, vendored and pinned

**Files:**
- Create: `tools/quoted_spans.py`
- Test: `tests/test_quoted_spans.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `quoted_spans(text: str) -> list[str]`, `norm(s: str) -> str`, `MIN_QUOTE_CHARS: int = 25`.

- [ ] **Step 1: Write the failing test**

`tests/test_quoted_spans.py`:

```python
"""Pins the quote-pairing algorithm. This is a vendored copy of
~/atticus/guard.py::quoted_spans — the regex version of this took three
attempts and refused correct answers twice in production, because straight
quotes are not directional. If a test here fails, do not "simplify" the
implementation; the tests are the bug report.
"""
from tools.quoted_spans import MIN_QUOTE_CHARS, norm, quoted_spans


def test_curly_pairs_are_matched_directionally():
    assert quoted_spans("He said “all men are created equal” today.") == [
        "all men are created equal"
    ]


def test_straight_quotes_pair_positionally_not_by_regex():
    # The failure that cost three attempts: a short quoted word followed by
    # more prose. Pairing by regex restarts at the CLOSING quote and swallows
    # the prose after it. Positional pairing takes odd segments only.
    text = 'The word "slavery" never appears, and the euphemism is the confession.'
    assert quoted_spans(text) == ["slavery"]


def test_two_straight_quoted_spans_in_one_line():
    text = 'He wrote "a moral depravity" and also "separate but equal" plainly.'
    assert quoted_spans(text) == ["a moral depravity", "separate but equal"]


def test_unclosed_straight_quote_yields_the_span_before_it_only():
    assert quoted_spans('He said "hello') == []


def test_empty_and_none_are_safe():
    assert quoted_spans("") == []
    assert quoted_spans(None) == []


def test_norm_flattens_typography_and_case():
    assert norm("The “Long—Telegram”") == "the long telegram"


def test_threshold_matches_the_runtime_rail():
    assert MIN_QUOTE_CHARS == 25
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_quoted_spans.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.quoted_spans'`

- [ ] **Step 3: Write minimal implementation**

`tools/quoted_spans.py`:

```python
"""Quoted-span extraction, vendored from ~/atticus/guard.py.

Vendored rather than imported: Atticus is a separately deployed service on the
Spark and this repo must not depend on its checkout. The algorithm is pinned by
tests/test_quoted_spans.py — straight quotes are paired POSITIONALLY (split on
the quote character, take odd segments), never by regex, because straight quotes
carry no direction and a regex restarts at the closing quote.
"""
from __future__ import annotations

import re

MIN_QUOTE_CHARS = 25  # keep in sync with ~/atticus/guard.py:104

_CURLY = re.compile("“([^“”]*)”")


def quoted_spans(text: str) -> list[str]:
    """Every span the writer actually put in quotation marks."""
    text = text or ""
    spans = _CURLY.findall(text)
    rest = _CURLY.sub(" ", text)
    parts = rest.split('"')
    spans += parts[1::2]
    return spans


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("—", " ").replace("–", " ").replace("…", " ")
    return re.sub(r"[^a-z0-9 ]+", " ", " ".join(s.lower().split())).strip()
```

Also create empty `tools/__init__.py` and `tests/__init__.py` so `tools.quoted_spans` imports.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_quoted_spans.py -v`
Expected: PASS, 7 tests.

- [ ] **Step 5: Commit**

```bash
git add tools/__init__.py tools/quoted_spans.py tests/__init__.py tests/test_quoted_spans.py
git commit -m "Vendor the quote-pairing algorithm, with its bug history as tests"
```

---

### Task 2: Frontmatter parser

**Files:**
- Create: `tools/frontmatter.py`
- Test: `tests/test_frontmatter.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse(text: str) -> tuple[dict, str]` returning `(fields, body)`. Values are `str`, or `list[str]` for `[a, b]` syntax. Missing frontmatter returns `({}, text)`.

- [ ] **Step 1: Write the failing test**

`tests/test_frontmatter.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_frontmatter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.frontmatter'`

- [ ] **Step 3: Write minimal implementation**

`tools/frontmatter.py`:

```python
"""A frontmatter parser small enough to read in one sitting.

stdlib only, deliberately: this repo has no dependency manifest and adding
PyYAML to parse six scalar fields would be the largest change in the project.
Supports exactly what the source schema uses — scalars and [a, b] lists.
"""
from __future__ import annotations


def parse(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    fields: dict = {}
    for line in lines[1:end]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            fields[key] = [v.strip() for v in inner.split(",") if v.strip()]
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = value
    return fields, "\n".join(lines[end + 1:])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_frontmatter.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add tools/frontmatter.py tests/test_frontmatter.py
git commit -m "Minimal frontmatter parser, stdlib only"
```

---

### Task 3: Source record loading and schema rules

**Files:**
- Create: `tools/source_records.py`
- Create: `content/sources/README.md`
- Test: `tests/test_source_records.py`

**Interfaces:**
- Consumes: `tools.frontmatter.parse`.
- Produces: `load_all(sources_dir: str) -> list[dict]`; `validate(record: dict) -> list[str]` returning error strings (empty means valid). Record keys: `id`, `title`, `author`, `date`, `type`, `repository`, `url`, `rights`, `band`, `callout`, `cited_by`, `fetched_at`, `sha256`, `text`, `path`.

**Schema refinement over the spec:** each record carries `callout:` — the exact callout string it answers, minus the trailing period. Compound callouts are satisfied by several records sharing one `callout` value. This makes resolution an exact string match rather than a fuzzy one, and needs no separate mapping file.

- [ ] **Step 1: Write the failing test**

`tests/test_source_records.py`:

```python
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
    # The central rule: text may only exist if it was fetched from somewhere.
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_source_records.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.source_records'`

- [ ] **Step 3: Write minimal implementation**

`tools/source_records.py`:

```python
"""Source records — the documents, as data.

Every rule here exists to keep one promise: a document in this repo was
retrieved from somewhere and can be checked, or it is not here at all. The
schema permits absence everywhere and invention nowhere.
"""
from __future__ import annotations

import os

from tools.frontmatter import parse

REQUIRED = ("id", "title", "date", "type", "rights", "callout", "cited_by")
TYPES = ("document", "artifact", "record-set")
RIGHTS = ("public-domain", "us-government", "restricted")


def load_all(sources_dir: str) -> list[dict]:
    records = []
    for name in sorted(os.listdir(sources_dir)):
        if not name.endswith(".md") or name == "README.md":
            continue
        path = os.path.join(sources_dir, name)
        with open(path, encoding="utf-8") as f:
            fields, body = parse(f.read())
        record = {k: v for k, v in fields.items() if v != ""}
        record["path"] = path
        record["text"] = body.strip()
        records.append(record)
    return records


def validate(record: dict) -> list[str]:
    errors = []
    for field in REQUIRED:
        if not record.get(field):
            errors.append(f"{record.get('path', '?')}: missing required field '{field}'")

    stem = os.path.basename(record.get("path", "")).removesuffix(".md")
    if stem and record.get("id") and record["id"] != stem:
        errors.append(f"{record['path']}: id '{record['id']}' does not match filename '{stem}'")

    if record.get("type") and record["type"] not in TYPES:
        errors.append(f"{record['path']}: type '{record['type']}' not one of {TYPES}")
    if record.get("rights") and record["rights"] not in RIGHTS:
        errors.append(f"{record['path']}: rights '{record['rights']}' not one of {RIGHTS}")

    has_text = bool(record.get("text"))
    if has_text and not record.get("url"):
        errors.append(
            f"{record.get('path', '?')}: has text without a url — source text must be "
            "fetched and attributed, never written from memory"
        )
    if has_text and record.get("rights") == "restricted":
        errors.append(
            f"{record['path']}: rights are restricted, so this record must carry no text"
        )
    return errors
```

`content/sources/README.md`:

```markdown
# Sources

One file per document, named `<id>.md`. The `id` is assigned by hand and must
match the filename.

A record may carry document text **only** if `tools/fetch_source.py` retrieved
it from a URL. `tools/provenance_gate.py` enforces this. If we cannot fetch a
document, the record exists without text and the chapter keeps its citation —
a missing document is honest, a remembered one is not.

`rights: restricted` records never carry text. Today that is the two 1963 King
Estate sources in chapter 5.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_source_records.py -v`
Expected: PASS, 7 tests.

- [ ] **Step 5: Commit**

```bash
git add tools/source_records.py content/sources/README.md tests/test_source_records.py
git commit -m "Source record schema: text requires a url, absence is legal"
```

---

### Task 4: Callout extraction

**Files:**
- Create: `tools/callouts.py`
- Test: `tests/test_callouts.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `callouts_in(text: str) -> list[str]` (trailing period stripped); `all_callouts(chapters_dir: str) -> list[tuple[str, str]]` of `(chapter_stem, callout_text)`.

- [ ] **Step 1: Write the failing test**

`tests/test_callouts.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_callouts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.callouts'`

- [ ] **Step 3: Write minimal implementation**

`tools/callouts.py`:

```python
"""The `**Primary Source:**` callouts, read out of the chapters.

Same regex as ~/atticus/sources.py so the two never disagree about what counts
as a callout. Unlike sources.py this does NOT slugify the label into an id —
assigned ids live in the source records.
"""
from __future__ import annotations

import os
import re

_CALLOUT = re.compile(r"^\*\*Primary Source:\*\*\s*(.+?)\s*$", re.M)


def callouts_in(text: str) -> list[str]:
    return [label.rstrip(".") for label in _CALLOUT.findall(text or "")]


def all_callouts(chapters_dir: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name in sorted(os.listdir(chapters_dir)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(chapters_dir, name), encoding="utf-8") as f:
            for label in callouts_in(f.read()):
                out.append((name[:-3], label))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_callouts.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add tools/callouts.py tests/test_callouts.py
git commit -m "Read the Primary Source callouts without slugifying them"
```

---

### Task 5: The provenance gate

**Files:**
- Create: `tools/provenance_gate.py`
- Test: `tests/test_provenance_gate.py`

**Interfaces:**
- Consumes: `tools.callouts.all_callouts`, `tools.source_records.load_all` and `validate`, `tools.quoted_spans.quoted_spans` / `norm` / `MIN_QUOTE_CHARS`.
- Produces: `check(chapters_dir: str, sources_dir: str) -> list[str]` returning failure strings; `main()` printing them and exiting 1 if any.

Assertion 2 (reachability) is deliberately **not** in `check()` — it needs the network. It lives in `tools/fetch_source.py --reverify` so `check()` stays offline and CI-safe.

- [ ] **Step 1: Write the failing test**

`tests/test_provenance_gate.py`:

```python
import os
import tempfile

from tools.provenance_gate import check

RECORD = """---
id: decl-1776
title: Declaration of Independence
date: 1776
type: document
rights: us-government
url: https://www.archives.gov/founding-docs/declaration-transcript
fetched_at: 2026-08-10
sha256: deadbeef
callout: Declaration of Independence, 1776
cited_by: [01-the-founding]
---

We hold these truths to be self-evident, that all men are created equal.
"""


def _dirs(chapter_text, record_texts):
    tmp = tempfile.mkdtemp()
    chapters, sources = os.path.join(tmp, "ch"), os.path.join(tmp, "src")
    os.makedirs(chapters), os.makedirs(sources)
    with open(os.path.join(chapters, "01-the-founding.md"), "w", encoding="utf-8") as f:
        f.write(chapter_text)
    for name, text in record_texts.items():
        with open(os.path.join(sources, name), "w", encoding="utf-8") as f:
            f.write(text)
    return chapters, sources


def test_passes_when_callout_resolves_and_quote_is_verbatim():
    chapters, sources = _dirs(
        '**Primary Source:** Declaration of Independence, 1776.\n\n'
        'It says "that all men are created equal" plainly.\n',
        {"decl-1776.md": RECORD},
    )
    assert check(chapters, sources) == []


def test_fails_when_a_callout_resolves_to_nothing():
    chapters, sources = _dirs(
        "**Primary Source:** Some Document Nobody Recorded, 1799.\n", {}
    )
    errors = check(chapters, sources)
    assert any("no source record" in e for e in errors)


def test_fails_when_a_long_quote_is_not_in_the_cited_source():
    chapters, sources = _dirs(
        '**Primary Source:** Declaration of Independence, 1776.\n\n'
        'It says "that all persons are created equally free" plainly.\n',
        {"decl-1776.md": RECORD},
    )
    errors = check(chapters, sources)
    assert any("not found in any cited source" in e for e in errors)


def test_short_quotes_are_ignored():
    chapters, sources = _dirs(
        '**Primary Source:** Declaration of Independence, 1776.\n\n'
        'The word "equal" recurs.\n',
        {"decl-1776.md": RECORD},
    )
    assert check(chapters, sources) == []


def test_restricted_sources_do_not_trigger_quote_failures():
    restricted = """---
id: king-dream-1963
title: I Have a Dream
author: Martin Luther King Jr.
date: 1963
type: document
rights: restricted
callout: "I Have a Dream" address, March on Washington, August 28, 1963
cited_by: [05-civil-rights]
---
"""
    chapters, sources = _dirs(
        '**Primary Source:** "I Have a Dream" address, March on Washington, August 28, 1963.\n\n'
        'He said "I have a dream that my four little children will one day live" there.\n',
        {"king-dream-1963.md": restricted},
    )
    assert check(chapters, sources) == []


def test_schema_errors_surface_through_the_gate():
    broken = RECORD.replace("id: decl-1776", "id: mismatched")
    chapters, sources = _dirs("**Primary Source:** Declaration of Independence, 1776.\n",
                              {"decl-1776.md": broken})
    assert any("filename" in e for e in check(chapters, sources))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_provenance_gate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.provenance_gate'`

- [ ] **Step 3: Write minimal implementation**

`tools/provenance_gate.py`:

```python
"""The provenance gate — proves the prose does not misquote its own documents.

This is guard.py's quote_gate turned around. There, the model is checked against
the corpus. Here, the CHAPTERS are checked against the documents they cite. A
history product that misquotes its sources has failed at the only thing it
claims to do, and a person proofreading 45 documents by eye will not catch it.

Offline by design: reachability of recorded URLs is checked separately by
tools/fetch_source.py --reverify, so this runs in CI without a network.
"""
from __future__ import annotations

import os
import sys

from tools.callouts import all_callouts
from tools.quoted_spans import MIN_QUOTE_CHARS, norm, quoted_spans
from tools.source_records import load_all, validate

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS = os.path.join(HERE, "content", "chapters")
SOURCES = os.path.join(HERE, "content", "sources")


def check(chapters_dir: str, sources_dir: str) -> list[str]:
    errors: list[str] = []
    records = load_all(sources_dir) if os.path.isdir(sources_dir) else []
    for record in records:
        errors += validate(record)

    by_callout: dict[str, list[dict]] = {}
    for record in records:
        by_callout.setdefault(record.get("callout", ""), []).append(record)

    for stem, callout in all_callouts(chapters_dir):
        if callout not in by_callout:
            errors.append(
                f"{stem}: callout '{callout}' has no source record. Add "
                f"content/sources/<id>.md with a matching `callout:` field."
            )

    chapters = sorted({stem for stem, _ in all_callouts(chapters_dir)})
    for stem in chapters:
        path = os.path.join(chapters_dir, stem + ".md")
        with open(path, encoding="utf-8") as f:
            chapter_text = f.read()
        cited = [r for r in records if stem in (r.get("cited_by") or [])]
        haystack = " ".join(norm(r.get("text", "")) for r in cited if r.get("text"))
        for span in quoted_spans(chapter_text):
            n = norm(span)
            if len(n) < MIN_QUOTE_CHARS:
                continue
            if n not in haystack:
                errors.append(
                    f"{stem}: quoted span not found in any cited source text: \"{span[:70]}\""
                )
    return errors


def main() -> int:
    errors = check(CHAPTERS, SOURCES)
    for e in errors:
        print(e)
    print(f"\n{len(errors)} provenance failure(s)." if errors else "\nProvenance gate passed.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_provenance_gate.py -v`
Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

```bash
git add tools/provenance_gate.py tests/test_provenance_gate.py
git commit -m "Provenance gate: chapters checked against the documents they cite"
```

---

### Task 6: The fetcher — the only writer of source text

**Files:**
- Create: `tools/fetch_source.py`
- Test: `tests/test_fetch_source.py`

**Interfaces:**
- Consumes: `tools.frontmatter.parse`, `tools.source_records.load_all`.
- Produces: `render_record(fields: dict, text: str) -> str`; `fetch(url: str, opener=None) -> tuple[str, str]` returning `(text, sha256)`; `reverify(sources_dir: str, opener=None) -> list[str]`.

CLI: `python3 tools/fetch_source.py --id <id> --url <url> --title ... --date ... --type ... --rights ... --callout ... --cited-by <stem>[,<stem>]` writes `content/sources/<id>.md`. `--reverify` re-fetches every recorded URL and reports non-200s.

- [ ] **Step 1: Write the failing test**

`tests/test_fetch_source.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_fetch_source.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.fetch_source'`

- [ ] **Step 3: Write minimal implementation**

`tools/fetch_source.py`:

```python
"""Retrieve a document and write it as a source record.

This is the ONLY thing in the repo that writes source text. That is the point:
if a document's text can only arrive through a function that requires a URL and
records a hash of what came back, then no one — human or model — can add a
document from memory and have it look identical to a real one.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import urllib.request

from tools.frontmatter import parse

FIELD_ORDER = ("id", "title", "author", "date", "type", "repository", "url",
               "rights", "band", "callout", "cited_by", "fetched_at", "sha256")


def _default_opener(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "historys-ledger/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch(url: str, opener=None) -> tuple[str, str]:
    text = (opener or _default_opener)(url)
    return text, hashlib.sha256(text.encode()).hexdigest()


def render_record(fields: dict, text: str) -> str:
    lines = ["---"]
    for key in FIELD_ORDER:
        value = fields.get(key)
        if not value:
            continue
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(value)}]")
        else:
            lines.append(f"{key}: {value}")
    lines += ["---", "", text.strip(), ""]
    return "\n".join(lines)


def reverify(sources_dir: str, opener=None) -> list[str]:
    problems = []
    for name in sorted(os.listdir(sources_dir)):
        if not name.endswith(".md") or name == "README.md":
            continue
        with open(os.path.join(sources_dir, name), encoding="utf-8") as f:
            fields, _ = parse(f.read())
        url = fields.get("url")
        if not url:
            continue
        try:
            (opener or _default_opener)(url)
        except Exception as exc:
            problems.append(f"{name}: url no longer fetches ({url}): {exc}")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id")
    parser.add_argument("--url")
    parser.add_argument("--title")
    parser.add_argument("--author")
    parser.add_argument("--date")
    parser.add_argument("--type", default="document")
    parser.add_argument("--repository")
    parser.add_argument("--rights", default="public-domain")
    parser.add_argument("--callout")
    parser.add_argument("--cited-by")
    parser.add_argument("--fetched-at")
    parser.add_argument("--reverify", action="store_true")
    args = parser.parse_args(argv)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sources = os.path.join(here, "content", "sources")

    if args.reverify:
        problems = reverify(sources)
        for p in problems:
            print(p)
        return 1 if problems else 0

    text, digest = fetch(args.url)
    fields = {
        "id": args.id, "title": args.title, "author": args.author, "date": args.date,
        "type": args.type, "repository": args.repository, "url": args.url,
        "rights": args.rights, "callout": args.callout,
        "cited_by": (args.cited_by or "").split(",") if args.cited_by else [],
        "fetched_at": args.fetched_at, "sha256": digest,
    }
    path = os.path.join(sources, f"{args.id}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_record(fields, text))
    print(f"wrote {path} ({len(text)} chars, sha256 {digest[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note for the implementer: `--fetched-at` is passed in rather than computed, because the caller knows the date and this keeps the module free of clock access for testing.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_fetch_source.py -v`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add tools/fetch_source.py tests/test_fetch_source.py
git commit -m "Fetcher: the only path by which source text may enter the repo"
```

---

### Task 7: Generate the Atticus corpus from canonical content

**Files:**
- Create: `tools/generate_corpus.py`
- Test: `tests/test_generate_corpus.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `generate(chapters_dir: str, out_dir: str) -> list[str]` returning the filenames written; `stale(chapters_dir: str, out_dir: str) -> list[str]` returning names that differ or are missing.

- [ ] **Step 1: Write the failing test**

`tests/test_generate_corpus.py`:

```python
import os
import tempfile

from tools.generate_corpus import generate, stale


def _chapter(dirpath, name, text):
    with open(os.path.join(dirpath, name), "w", encoding="utf-8") as f:
        f.write(text)


def test_generate_copies_every_chapter():
    with tempfile.TemporaryDirectory() as tmp:
        chapters, out = os.path.join(tmp, "ch"), os.path.join(tmp, "out")
        os.makedirs(chapters)
        _chapter(chapters, "01-x.md", "one")
        _chapter(chapters, "02-y.md", "two")
        assert generate(chapters, out) == ["01-x.md", "02-y.md"]
        assert open(os.path.join(out, "02-y.md")).read() == "two"


def test_stale_reports_a_chapter_missing_from_the_copy():
    with tempfile.TemporaryDirectory() as tmp:
        chapters, out = os.path.join(tmp, "ch"), os.path.join(tmp, "out")
        os.makedirs(chapters), os.makedirs(out)
        _chapter(chapters, "07-new.md", "seven")
        assert stale(chapters, out) == ["07-new.md"]


def test_stale_reports_a_chapter_whose_text_drifted():
    with tempfile.TemporaryDirectory() as tmp:
        chapters, out = os.path.join(tmp, "ch"), os.path.join(tmp, "out")
        os.makedirs(chapters), os.makedirs(out)
        _chapter(chapters, "01-x.md", "canonical")
        _chapter(out, "01-x.md", "drifted")
        assert stale(chapters, out) == ["01-x.md"]


def test_stale_is_empty_when_the_copy_matches():
    with tempfile.TemporaryDirectory() as tmp:
        chapters, out = os.path.join(tmp, "ch"), os.path.join(tmp, "out")
        os.makedirs(chapters), os.makedirs(out)
        _chapter(chapters, "01-x.md", "same")
        _chapter(out, "01-x.md", "same")
        assert stale(chapters, out) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_generate_corpus.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.generate_corpus'`

- [ ] **Step 3: Write minimal implementation**

`tools/generate_corpus.py`:

```python
"""Generate Atticus's corpus from canonical chapters.

Chapter 7 was written straight into ~/atticus/corpus/ and lived there alone
until 2026-08-10 — serving on the Spark, listed on the site, absent from this
repo. Hand-copying is what allowed that. `stale()` makes the drift visible;
`generate()` removes the reason to hand-copy at all.

The Spark still needs an scp after this runs. That is deliberate: pushing to a
remote host is not something a content build should do silently.
"""
from __future__ import annotations

import os
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS = os.path.join(HERE, "content", "chapters")
CORPUS = os.path.expanduser("~/atticus/corpus")


def _names(dirpath: str) -> list[str]:
    if not os.path.isdir(dirpath):
        return []
    return sorted(n for n in os.listdir(dirpath) if n.endswith(".md"))


def generate(chapters_dir: str, out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name in _names(chapters_dir):
        shutil.copyfile(os.path.join(chapters_dir, name), os.path.join(out_dir, name))
        written.append(name)
    return written


def stale(chapters_dir: str, out_dir: str) -> list[str]:
    out = []
    for name in _names(chapters_dir):
        target = os.path.join(out_dir, name)
        if not os.path.exists(target):
            out.append(name)
            continue
        with open(os.path.join(chapters_dir, name), encoding="utf-8") as a, \
                open(target, encoding="utf-8") as b:
            if a.read() != b.read():
                out.append(name)
    return out


def main() -> int:
    drift = stale(CHAPTERS, CORPUS)
    written = generate(CHAPTERS, CORPUS)
    print(f"wrote {len(written)} chapters to {CORPUS}")
    if drift:
        print("was stale: " + ", ".join(drift))
        print("\nThe Spark serves its own copy. Push it:")
        print(f"  scp {CORPUS}/*.md soverynspark@10.10.10.2:~/atticus/corpus/")
        print("  ssh soverynspark@10.10.10.2 'systemctl --user restart atticus'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_generate_corpus.py -v`
Expected: PASS, 4 tests.

- [ ] **Step 5: Commit**

```bash
git add tools/generate_corpus.py tests/test_generate_corpus.py
git commit -m "Generate the Atticus corpus instead of hand-copying it"
```

---

### Task 8: First real records, and an honest coverage count

**Files:**
- Create: `content/sources/*.md` (real records, fetched)
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: everything above.
- Produces: no code. The deliverable is content plus a published count.

This is the long pole and it is curation work, not programming. Do it in batches of five, running the gate after each batch.

- [ ] **Step 1: Fetch the five most-cited public-domain sources**

Start with these, all US government or pre-1929 and all cited by more than one chapter or central to one:

```bash
cd ~/american-history-app
python3 tools/fetch_source.py --id declaration-of-independence-1776 \
  --title "Declaration of Independence" --date 1776 --type document \
  --rights us-government --repository "National Archives" \
  --url https://www.archives.gov/founding-docs/declaration-transcript \
  --callout "Declaration of Independence, 1776" \
  --cited-by 01-the-founding,02-slavery-and-emancipation --fetched-at 2026-08-10
```

Repeat for: the Constitution (Article I callouts), the Gettysburg Address, the Emancipation Proclamation, and Douglass's *Narrative*. Choose the archive URL by opening it first and confirming it serves a transcript rather than a scan viewer — a URL that returns a JavaScript shell gives a record with useless text and a valid-looking hash.

- [ ] **Step 2: Run the gate and read the failures**

Run: `cd ~/american-history-app && python3 tools/provenance_gate.py`
Expected: many `has no source record` failures (the ~40 not yet fetched), and possibly some `quoted span not found` failures on the five that are done. **The quotation failures are the interesting output.** Each one is either a transcription error in a chapter or a sign the fetched text is not the document we thought.

- [ ] **Step 3: Fix what the gate found, in the chapter or the record**

Do not loosen the gate. If a chapter misquotes, correct the chapter; if the fetched text is a bad transcript, replace the record with a better source. This mirrors the 1808 decision — the gate tripped, and the corpus was enriched rather than the gate weakened.

- [ ] **Step 4: Continue in batches of five until every callout resolves or is recorded as unavailable**

For sources with no fetchable text, still create the record — with `title`, `date`, `type`, `rights`, `callout`, `cited_by` and no `url`, no text. The gate accepts it; the tap in Stage 3 will simply show a citation card without a document.

For the two King Estate sources, create records with `rights: restricted` and a `url` pointing at an authorized copy. They carry no text by rule.

- [ ] **Step 5: Publish the honest count in STATUS.md**

Add a section stating how many sources are held in full, in part, and not at all — actual numbers from `content/sources/`, not estimates:

```bash
cd ~/american-history-app
python3 - <<'EOF'
from tools.source_records import load_all
records = load_all("content/sources")
full = [r for r in records if r.get("text")]
none = [r for r in records if not r.get("text")]
print(f"{len(records)} records: {len(full)} with document text, {len(none)} citation-only")
EOF
```

- [ ] **Step 6: Commit**

```bash
git add content/sources STATUS.md
git commit -m "First source records, and an honest count of what we actually hold"
```

---

### Task 9: Wire the gate into the workflow

**Files:**
- Create: `.github/workflows/provenance.yml` OR `tools/check.sh` (see note)
- Modify: `README.md`

**Interfaces:**
- Consumes: `tools/provenance_gate.py`, pytest suite.
- Produces: one command that runs everything.

**Note for the implementer:** this repo has no CI and no remote configured. Do **not** add a GitHub Actions workflow that will never run. Create `tools/check.sh` instead; if a remote is added later, that script is what CI would call.

- [ ] **Step 1: Write the failing test**

`tests/test_check_script.py`:

```python
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_check_script_exists_and_is_executable():
    path = os.path.join(REPO, "tools", "check.sh")
    assert os.path.exists(path), "tools/check.sh missing"
    assert os.access(path, os.X_OK), "tools/check.sh is not executable"


def test_check_script_runs_the_test_suite_and_the_gate():
    with open(os.path.join(REPO, "tools", "check.sh"), encoding="utf-8") as f:
        body = f.read()
    assert "pytest" in body
    assert "provenance_gate" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_check_script.py -v`
Expected: FAIL — `tools/check.sh missing`

- [ ] **Step 3: Write minimal implementation**

`tools/check.sh`:

```bash
#!/usr/bin/env bash
# Everything that must pass before content ships.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== tests =="
python3 -m pytest tests/ -q

echo
echo "== provenance gate =="
python3 tools/provenance_gate.py

echo
echo "== corpus drift =="
python3 - <<'EOF'
from tools.generate_corpus import CHAPTERS, CORPUS, stale
drift = stale(CHAPTERS, CORPUS)
print("corpus is current" if not drift else "STALE: " + ", ".join(drift))
EOF
```

Then: `chmod +x tools/check.sh`

Add to `README.md`:

```markdown
## Checking the content

    ./tools/check.sh

Runs the test suite, the provenance gate (every callout resolves, every long
quotation appears verbatim in a cited source), and reports whether Atticus's
corpus has drifted from canonical chapters.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/american-history-app && python3 -m pytest tests/test_check_script.py -v && ./tools/check.sh`
Expected: pytest PASS, 2 tests. `check.sh` will exit non-zero while callouts remain unrecorded — that is correct and expected until Task 8 completes.

- [ ] **Step 5: Commit**

```bash
git add tools/check.sh tests/test_check_script.py README.md
git commit -m "One command that runs the tests, the gate, and the drift check"
```

---

## Self-Review

**Spec coverage.** Single source of truth → Task 7. Record schema → Task 3. Absent-not-guessed → Task 3 (`validate`) and Task 6 (`render_record` omits empty fields). Never-from-memory → Task 6, enforced by Task 3's "text without a url" rule. Three record types → Task 3. Compound callouts → Task 3's `callout:` field, several records sharing one value. Gate assertion 1 (resolution) → Task 5. Assertion 2 (reachability) → Task 6 `reverify`, moved out of the offline gate. Assertion 3 (quotation) → Task 5. `quoted_spans` reuse → Task 1. Restricted rights → Task 3 and Task 5. Retiring slug ids → partially: Task 4 stops slugifying on this side, but `~/atticus/sources.py` still derives its table from prose. **Gap: no task changes `sources.py` to read the new records.** That is deliberate — it changes a live service on the Spark and belongs with Stage 2, when the corpus generator is proven. Noted here so it is not mistaken for an oversight.

**Placeholder scan.** Clean. One defect was found and fixed inline rather than left in: Task 5's `check()` carried a dead `for stem, _ in {...}: pass` loop, originally annotated as something for the reviewer to catch. Planting code known to be wrong is not a test of the reviewer, it is a defect with a note attached — removed. Task 8 names five specific sources with a full runnable command rather than "fetch the sources."

**Type consistency.** `quoted_spans`/`norm`/`MIN_QUOTE_CHARS` (Task 1) are used with those exact names in Task 5. `parse` returns `(dict, str)` in Task 2 and is unpacked that way in Tasks 3 and 6. `load_all`/`validate` signatures match between Tasks 3 and 5. `stale`/`generate`/`CHAPTERS`/`CORPUS` in Task 7 match their use in Task 9's `check.sh`.
