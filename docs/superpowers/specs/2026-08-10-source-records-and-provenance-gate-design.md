# Source records and the provenance gate — design

_2026-08-10. Stage 1 of three. Stages 2 (chapter reader) and 3 (the tap) get
their own specs; this one deliberately ships no UI._

## What this is for

History's Ledger promises that every claim is one tap from the document behind
it. Today the chapters carry **39 `**Primary Source:**` callouts (38 distinct)**,
and every one is a *citation* — a name, a title, a date. The documents
themselves are not in the repo. There is nothing on the other side of the tap.

Stage 1 puts real documents behind the citations and builds the machinery that
proves the chapters do not misquote them. No reader UI. The output is content
plus a gate.

## Why it comes first

It is the only stage whose value does not depend on the two after it:

- It fixes Atticus's citation selection. `sources.py` currently derives its
  source table by slugifying callout prose, which is how a claim about Article I
  **Section 9** was handed the id `u-s-constitution-article-i-section-2`
  (chapter 2's three-fifths callout). Real records with real ids make
  claim-to-source a checkable relationship instead of a string match.
- It tells us which of the 38 have retrievable documents and which do not. That
  answer shapes the reader and the tap interaction, so learning it late is
  expensive.

## The honesty constraint (applies to the author, not the code)

**Source texts are fetched from an archive and recorded with the URL they came
from. They are never typed out from memory.** A model that "remembers" the
Declaration well enough to reproduce it is exactly how an app built to prove
documents ends up fabricating them.

Anything that cannot be fetched and verified is recorded as **absent**. The
chapter keeps its citation; the card simply is not tappable yet. A missing
document is honest. A remembered one is not.

## Single source of truth

`~/american-history-app` is canonical. Everything else is generated:

```
content/chapters/     the prose            (canonical)
content/sources/      the documents        (canonical, new)
        |
        +--> generate --> ~/atticus/corpus/      (serving copy, tower + Spark)
        +--> generate --> historysledger-site/   (public reader, Stage 2)
```

Chapter 7 lived only in the Atticus corpus until 2026-08-10 — written into a
serving copy, invisible to the canonical repo, while being listed on the live
site. The `scp`-the-corpus-to-the-Spark step is the same hazard. A generator
ends both; hand-copying is what created them.

## Source record schema

One file per source, `content/sources/<id>.md`, frontmatter plus text:

```yaml
---
id: douglass-narrative-1845          # stable, hand-assigned, never slugified prose
title: Narrative of the Life of Frederick Douglass, an American Slave
author: Frederick Douglass           # omit entirely if the document has none
date: 1845
type: document | artifact | record-set
repository: Documenting the American South, UNC
url: https://...                     # only if it was fetched and returned 200
rights: public-domain | us-government | restricted
band: [1-6, 7-12]                    # grade bands this source is cleared for
cited_by: [02-slavery-and-emancipation]
---

<the document text, or the portion held, with any elision marked explicitly>
```

Rules that make the schema honest:

- **A field is absent rather than guessed.** No placeholder repositories, no
  approximate dates, no invented URLs. This continues the existing decision to
  leave repository URLs `None`.
- **`id` is assigned, not derived.** Slugified prose is what produced the
  Section 2 / Section 9 collision.
- **Partial holdings are marked.** If we hold three paragraphs of a long
  document, the record says so; it never presents an excerpt as the whole.

### Three record types, because three things are cited

`type: document` covers the ordinary case. Two others fall out of the inventory:

- **`artifact`** — the callout in chapter 7 cites a *steel spectacle case* and a
  speech manuscript with a bullet perforation. There is no text to fetch. These
  carry a description and, where one exists, an image credit.
- **`record-set`** — several callouts cite bodies of material rather than one
  document: Freedmen's Bureau records, Joint Select Committee testimony on Klan
  violence, Hepburn Committee rebate records. These get a record describing the
  set and, where possible, one representative document held in full.

### Compound callouts must be split

Six callouts name more than one document — Kennan's Long Telegram *and* the "X"
article; Marshall's Harvard address *and* Berlin Airlift records; Soviet naval
accounts *and* Petrov's testimony. Each becomes its own record. The chapter
callout then references several ids. So the real record count is **above 38**,
likely mid-40s.

## The provenance gate

A build-time check, run in CI and before any generate. Three assertions:

1. **Resolution** — every `**Primary Source:**` callout resolves to at least one
   existing source record. A callout pointing at nothing fails the build.
2. **Reachability** — every recorded `url` fetches and returns 200. A dead
   provenance link is a fabricated one with extra steps. Failures mark the record
   `url` absent rather than failing the build, and report.
3. **Quotation** — every quoted span of 25+ characters in a chapter appears
   verbatim in the text of a source that chapter cites. This is `guard.py`'s
   `quote_gate` inverted: instead of checking the model against the corpus, it
   checks the *prose* against the documents.

Assertion 3 is the one that earns the product its claim. It mechanically proves
the chapters do not misquote the record they are built on. Expect it to fail on
first run — that is the point, and each failure is either a transcription error
in a chapter or a source we do not actually hold.

Reuse note: the 25-character threshold and the straight-quote pairing must come
from `guard.py`'s `quoted_spans()`, not a fresh regex. Straight quotes are not
directional and pairing them by regex refused correct answers twice in
production; that function pairs them positionally and must not be reimplemented.

## Rights — two sources cannot be reproduced

Most of the corpus is safely public domain: pre-1929 publication (Equiano,
Douglass, Tarbell, Paine) or US government work (Supreme Court opinions,
executive orders, congressional testimony, FBI statements, the Emancipation
Proclamation).

**Two are not, and both are in chapter 5:**

- **"I Have a Dream," 1963**
- **"Letter from Birmingham Jail," 1963**

Both are under active copyright held by the King Estate, which enforces
vigorously. These get `rights: restricted`: no full text, a short quotation at
most, and the tap goes straight to option C — a link to an authorized copy. The
chapter prose already quotes both; assertion 3 must not demand a full text we
are not entitled to hold.

This is not a reason to cut the chapter. It is a reason to decide the handling
now rather than discover it in Stage 3.

## Scope

**In:** the `content/sources/` schema; fetching and verifying the ~45 records;
the provenance gate; the generator that produces the Atticus corpus from
canonical content; retiring `sources.py`'s prose-slug ids in favour of assigned
ids.

**Out:** the chapter reader (Stage 2), the tap interaction and source cards
(Stage 3), new chapters, grade-band content variants, audio/narration.

## How we will know it worked

- Every callout resolves; the gate passes.
- Atticus, asked about the slave-trade clause, cites the Article I Section 9
  record rather than the three-fifths one.
- The Atticus corpus is generated, and `~/american-history-app` is the only
  place a chapter is ever edited.
- We have an honest count: how many of the ~45 sources we hold in full, in part,
  and not at all — published in STATUS.md rather than implied.
