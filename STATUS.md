# History's Ledger — where the project actually stands

_Last verified against disk: 2026-08-14 (evening)._

## Site brand + premium landing (2026-08-14)

Live at **https://historysledger.com** (Cloudflare Pages project `historysledger`).

| Surface | What it is |
|---|---|
| **Landing** (`index.html`) | Premium desk: full-bleed library shelves (`brand/bg-books-shelf.jpg`), center folio on real 1830s ledger paper (`brand/bg-ledger-page.jpg`), transparent red seal, Enter → `/read/` |
| **Inside the ledger** | Entries + entry folios: washed ledger paper **outside** the center leaf; solid leaf for reading |
| **Brand** | Oxblood red medallion only on pages (`hl-seal-red-*`); wax/dark/parchment kept off-page |
| **Deploy** | `npx wrangler pages deploy . --project-name historysledger --branch main` from `~/historysledger-site` |

Site git: `~/historysledger-site` (main). Folio generator: `american-history-app` → `python3 -m tools.build_folios`.

---

## App shell + Stage 3 taps (2026-08-14)

Shared chrome + tabbed ledger entries live on historysledger.com.
Entry spine: Established · Sources · Conflicting · Unknown · Read · Weigh
(optional). Weigh never gates the record.

**Stage 3:** In Read (and Sources), tap a Primary Source callout or long
quotation to open a source card — held text with passage context, restricted,
citation-only, or an honest gap. Cards use the same assigned ids as Atticus.


## Stage 2 — Chapter reader and assigned source ids (2026-08-14)

The public reader is generated from canonical chapters + source records, not
hand-maintained HTML. Atticus cites hand-assigned source ids.

| Check | Command | Result |
|---|---|---|
| Full suite | `./tools/check.sh` | tests + gate + corpus drift + folios |
| Folio generator | `python3 -m tools.build_folios` | writes `~/historysledger-site/read/` |
| Apparatus | verified / unverified / unsourced counts printed on the index | honest |

### What Stage 2 delivers

1. **`tools/quotation_match.py`** — elision-aware matching (honest `…` quotations
   pass; spliced continuous fabrications fail).
2. **`tools/apparatus.py`** — every long quotation labelled `verified`,
   `unverified` (restricted / record-set covers), or `unsourced`, with surrounding
   passage when verified.
3. **`tools/build_folios.py`** — regenerates the seven reading folios and the
   index into `~/historysledger-site/read/` from chapters + sources. No invented
   prose: missing ✅/❌ sections are omitted, not filled.
4. **Atticus `sources.py`** — table built from `content/sources/` assigned ids,
   not slugified callout prose (the Section 2 / Section 9 collision class of bug).

### Honest apparatus count (after Stage 1 quote alignment)

As of 2026-08-14, apparatus over the current chapters:

- **20 verified** — located in a held source document
- **0 unverified** (covers_quotations reserved for restricted/record-set claims
  still written as long quotes; King material is attributed without long quotes)
- **7 unsourced** — all in chapter 7 (TR / Reagan / Butler), where we hold
  citation records but not the document text yet

That last number is printed on the reader index for the same reason it is
printed everywhere else.

### What is not done (Stage 3+)

- In-chapter **tap** on a claim → open the source card (Stage 3)
- Fetch remaining citation-only documents (ch7 speech/FBI, CRA/VRA full text, …)
- Deploy site + restart Atticus on the Spark after scp

---

## Stage 1 — Source records and the provenance gate (2026-08-14)

The content repo now holds primary-source **records** next to the chapters, and
a build-time gate that proves the prose does not invent long quotations.

| Check | Command | Result |
|---|---|---|
| Unit tests | `python3 -m pytest tests/ -q` | green |
| Provenance gate | `python3 tools/provenance_gate.py` | green |
| Full suite | `./tools/check.sh` | tests + gate + corpus drift |

### Honest coverage count (`content/sources/`)

Run:

```bash
python3 - <<'EOF'
from tools.source_records import load_all
records = load_all("content/sources")
full = [r for r in records if r.get("text")]
none = [r for r in records if not r.get("text")]
print(f"{len(records)} records: {len(full)} with document text, {len(none)} citation-only")
EOF
```

As of 2026-08-14:

- **40 source records** — one per Primary Source callout, plus Federalist 51 and
  Eisenhower's farewell (quoted in chapters without their own callout line).
- **20 with full document text** fetched from public-domain / US-government URLs
  (NARA, Gutenberg, Avalon, LII/FindLaw, American Rhetoric). Text enters the
  repo **only** through `tools/fetch_source.py` (URL + sha256 + fetched_at).
- **2 restricted** (King Estate: *Letter from Birmingham Jail*, *I Have a Dream*)
  — records exist, **no body text**, by rule.
- **18 citation-only** — callout resolves, no usable clean transcript held yet
  (auction notices, FBI files, Hepburn committee, CRA/VRA full text, etc.).
  A missing document is honest; a remembered one is not.

Chapter long-quotes that could not yet be pinned to held text were rewritten as
attributed prose or continuous verbatim spans from the fetched document. That
is the gate working: it forced the prose toward the archive, not the other way
around.

### Stage 1 leftovers absorbed into Stage 2 / later

- Atticus now reads `content/sources/` (Stage 2).
- Reachability: `python3 tools/fetch_source.py --reverify` (network).
- Tap UI remains Stage 3.

## Written — 7 chapters, 8,534 words

| # | Chapter | File | Words |
|---|---|---|---|
| 1 | The Founding | `content/chapters/01-the-founding.md` | 1,294 |
| 2 | Slavery & Emancipation | `content/chapters/02-slavery-and-emancipation.md` | 1,260 |
| 3 | Reconstruction | `content/chapters/03-reconstruction.md` | 1,280 |
| 4 | Standard Oil | `content/chapters/04-standard-oil.md` | 989 |
| 5 | Civil Rights | `content/chapters/05-civil-rights.md` | 1,231 |
| 6 | The Cold War | `content/chapters/06-cold-war.md` | 1,251 |
| 7 | The Bullet and the Podium | `content/chapters/07-the-bullet-and-the-podium.md` | 1,229 |

⚠️ **Chapter 7 was written straight into `~/atticus/corpus/` and lived there
alone until 2026-08-10** — present on the tower, on the Spark, and listed on
historysledger.com, but absent from this repo, which is the canonical home and
what the reader packet builds from. Backfilled byte-identical; chapters 1-6 were
verified against the corpus at the same time and had not drifted.
**Write chapters HERE first.** The corpus is a serving copy.

## The validation gate — Jon's call, 2026-08-10

The gate was self-imposed: readers first, then spec, then site. Jon's judgement
as of 2026-08-10 is that the material is **marketable as it stands**, so the
gate is lifted and the work is now (a) more chapters and (b) in-chapter
interactivity — every claim one tap from the document behind it.

## Chapters beyond the six (roadmap, not written)

Two future chapters were previously named in "Next Chapter" links, which made
them dead ends inside a numbered set. The links now chain 1→6; the ideas are
parked here instead:

- **The Trust-Busters** — Roosevelt, Wilson, and the Progressive Era
- **The Unfinished Work** — from the Great Society to today (this is where ch. 6
  points, which is correct: it is the end of the set)

## Chapter numbering — RESOLVED 2026-07-26

Canonical order is **`VALIDATION_COVER_NOTE.md`** — the reader-facing document.
All files and headers match it:

1. The Founding · 2. Slavery & Emancipation · 3. Reconstruction ·
4. Standard Oil · 5. Civil Rights · 6. The Cold War ·
7. The Bullet and the Podium

⚠️ Chapter 7 sits outside the cover note's set of six. The cover note has not
been updated to mention it.

## The open question the 2026-07-26 board raises

`design/brand-and-ui-board-2026-07-26.png` shows a **record browser**: an event,
its established facts, sources split primary/secondary, a CONFLICTING ACCOUNTS
panel, and a WHAT REMAINS UNKNOWN panel with a count.

The three written chapters are **narrative essays**. These are two different
products, and the validation ask is built on the first while the design is built
on the second.

They compose rather than compete, if that's the call: the chapter is the
narrative spine, the record layer is the primary-source floor beneath it, and a
line in a chapter opens the record behind it. That matches the "Foundation
Layer" language already in `content/sourcing-map.md`. **Decide it before
writing the remaining three chapters** — it changes what a chapter is.

## Two things to fix in the brand board

- **The logo marks say "EST. 2024".** The name was locked 2026-07-13. On a brand
  whose entire promise is "Truth on Record", a wrong founding date on the seal is
  the one detail a critic would most enjoy finding.
- **Palette hex values need pulling from source.** Read off the image, two of the
  six contain characters that aren't valid hex, so the board image is not a
  reliable reference for them.

## Designed, not built

- `ATTICUS_SPEC.md` — the guide's persona: curator, present-don't-pronounce,
  silence-is-honest, hand the verdict back. Design-complete.
- `design/historys-ledger-fullpage.png`, `design/historys-ledger-mobile.png` —
  visual mockups (2026-07-13).
- `content/sourcing-map.md` — where the primary sources come from. The useful
  conclusion: Avalon + Founders Online + Gutenberg + govinfo are already clean
  transcribed text, so the Foundation Layer needs **zero OCR**. OCR is deferred
  to Phase 2, which cuts the hardest technical problem out of the MVP.
- **No implementation spec yet** — deliberately the next artifact, not an
  oversight.

## Rights watch-out

MLK's speeches and writings are still under copyright (King estate). Quote
briefly under fair use or license; do not reproduce in full. Flag any 20th-century
*published* text for a rights check. See `content/sourcing-map.md`.
