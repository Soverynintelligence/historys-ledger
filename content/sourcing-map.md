# Primary-Source Sourcing Map

Where to actually pull the documents. Everything below is **public domain** (U.S. government works + pre-1929 texts), so no licensing cost. Ranked by usefulness.

| Repository | What it has | Access | Clean text or OCR? |
|---|---|---|---|
| **Avalon Project** (Yale Law) | Founding, legal & diplomatic docs — Constitution, treaties, Court cases, key speeches. *The* best-organized source for the app's spine. | Web, scrapeable HTML | **Clean text** — best quality |
| **Founders Online** (National Archives) | ~180k fully-transcribed Washington/Jefferson/Adams/Franklin/Hamilton/Madison letters & papers | **Public API** (JSON) | **Clean text** |
| **Library of Congress** | Digitized manuscripts, photos, maps, newspapers (Chronicling America) | **API** (loc.gov/apis, Chronicling America API) | Mixed — modern items clean, scans need OCR |
| **National Archives (DocsTeach / catalog)** | Founding docs, presidential papers, scanned originals (great for *images* of documents) | **API** (catalog.archives.gov) | Images + some OCR |
| **govinfo.gov** (GPO) | Statutes, the *Statutes at Large* (Sherman Act, Highway Act, Kefauver-Harris), Supreme Court opinions | **API** | **Clean text** |
| **Oyez / Justia** | Supreme Court cases — full opinions + oral-argument audio (*Standard Oil*, *Brown v. Board*, etc.) | Web / Oyez API | **Clean text** (+ audio) |
| **Project Gutenberg** | Full public-domain books — Douglass's *Narrative*, Equiano, Tarbell, the Federalist Papers | Bulk download | **Clean text** |
| **TeachingAmericanHistory.org** | Curated primary sources with context — a shortcut to "the top 25 documents" | Web scrape | Clean text |

## Build order that follows from this

Start with **Avalon + Founders Online + Gutenberg + govinfo** — they're already clean transcribed text, which means **zero OCR pipeline** for the entire Foundation Layer and most of the narrative anchors.

OCR (from LOC / NARA scans) is only needed for handwritten items and newspaper clippings — **defer to Phase 2.** That single decision cuts the hardest technical problem out of the MVP.

## Rights note
- U.S. federal government works = public domain (statutes, Court opinions, presidential documents, most gov photos).
- Pre-1929 published texts = public domain in the U.S.
- MLK's speeches/writings ("I Have a Dream," "Letter from Birmingham Jail") are **still under copyright** (King estate) — quote briefly under fair use, or license; do NOT reproduce in full without clearance. Flag any 20th-century *published* text for a rights check before full reproduction.
