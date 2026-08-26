"""July crisis week — wrap the held 1914 entry. Not a second site.

The week is chrome on How Europe walked in. It names held source ids and
existing section headings only. It does not invent quotations, dates,
figures, or scenes. It does not claim a war name, a school year, or a sale.
"""
from __future__ import annotations

import html
from pathlib import Path

from tools.source_cards import status_for
from tools.source_records import load_all

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = (
    ROOT / "content/collections/modern-wars/chapters/01-how-europe-walked-in.md"
)
SOURCES = ROOT / "content/collections/modern-wars/sources"

ENTRY_STEM = "01-how-europe-walked-in"

# Every id the week may open. Must be held 1914 records cited by this entry.
HELD_SOURCE_IDS = (
    "austro-hungarian-ultimatum-1914",
    "serbian-reply-1914",
    "austro-hungarian-war-serbia-1914",
    "german-war-russia-1914",
    "german-war-france-1914",
    "belgian-grey-book-1914",
    "grey-commons-1914",
)

HUNT_IDS = (
    "belgian-grey-book-1914",  # Grey Book No. 20 sits on this held card
    "austro-hungarian-ultimatum-1914",
)

# Product copy must not claim these. Existing chapter body is out of scope here.
# Claims the week must not make. Negations ("not a school year") are required separately.
FORBIDDEN_WEEK_COPY = (
    "WW1",
    "WWI",
    "World War I",
    "World War 1",
    "WWII",
    "World War II",
    "1917",
    "1919",
    "Holocaust",
    "Family year",
    "Stripe",
    "checkout",
    "Korea",
    "Vietnam",
    "mascot",
)

# Headings must match ## lines already in the chapter.
DAYS = (
    {
        "id": "mon",
        "weekday": "Monday",
        "title": "The Clock",
        "heading": "The Clock",
        "read_id": "the-clock",
        "sources": ("austro-hungarian-ultimatum-1914",),
        "parent": (
            "Read “The Clock.” Open the ultimatum card. Find the Saturday "
            "6 p.m. line already quoted in this entry. Then find clause 6 on "
            "the same card. At the table: what does that clause demand, in "
            "the words on the card?"
        ),
        "kid": (
            "Open the ultimatum. Find the Saturday 6 p.m. line. Then find "
            "clause 6. If the card is not held, stop."
        ),
    },
    {
        "id": "tue",
        "weekday": "Tuesday",
        "title": "What Belgrade accepted, and what it would not",
        "heading": "What Belgrade Accepted, and What It Would Not",
        "read_id": "what-belgrade-accepted-and-what-it-would-not",
        "sources": (
            "serbian-reply-1914",
            "austro-hungarian-war-serbia-1914",
        ),
        "parent": (
            "Read “What Belgrade Accepted, and What It Would Not.” Open the "
            "Serbian reply: clause 2 and clause 6. Then open the 28 July war "
            "telegram. At the table: which clause accepts, which refuses, and "
            "what did Vienna send next?"
        ),
        "kid": (
            "Open the Serbian reply. Find clause 2. Find clause 6. Then open "
            "the war telegram. Stay on the cards we hold."
        ),
    },
    {
        "id": "wed",
        "weekday": "Wednesday",
        "title": "The declarations that followed",
        "heading": "The Declarations That Followed",
        "read_id": "the-declarations-that-followed",
        "sources": (
            "german-war-russia-1914",
            "german-war-france-1914",
        ),
        "parent": (
            "Read “The Declarations That Followed.” Open the German note to "
            "Russia and the German note to France (Yellow Book No. 147). The "
            "entry already says Viviani challenged the allegations; the ledger "
            "holds both sentences and does not pick a winner. At the table: "
            "what does each note close with?"
        ),
        "kid": (
            "Open the two German notes. Read the closing sentence on each "
            "card. Stop if a card is not held."
        ),
    },
    {
        "id": "thu",
        "weekday": "Thursday",
        "title": "Passage, or the decision of arms",
        "heading": "Passage, or the Decision of Arms",
        "read_id": "passage-or-the-decision-of-arms",
        "sources": (
            "belgian-grey-book-1914",
            "grey-commons-1914",
        ),
        "parent": (
            "Read “Passage, or the Decision of Arms.” Open Grey Book No. 20 "
            "(the German note to Belgium), then No. 22 (the Belgian reply), "
            "then Grey in the Commons. Hunt first: do we hold No. 20? At the "
            "table: what does the note say if Belgium opposes the march?"
        ),
        "kid": (
            "Hunt: open Grey Book No. 20. Do we hold it? Then open the Belgian "
            "reply on the same Grey Book card."
        ),
    },
    {
        "id": "fri",
        "weekday": "Friday",
        "title": "The Chancellor names the wrong",
        "heading": "The Chancellor Names the Wrong",
        "read_id": "the-chancellor-names-the-wrong",
        "sources": ("belgian-grey-book-1914",),
        "parent": (
            "Read “The Chancellor Names the Wrong.” Open Grey Book No. 35. "
            "The two lines already quoted in this entry sit on that card. "
            "Then read “What We Learned” if you want the takeaway. Weigh "
            "stays optional. Nothing is scored."
        ),
        "kid": (
            "Open Grey Book No. 35. Find the two lines already marked in this "
            "entry. Weigh is optional. Nothing is scored."
        ),
    },
)

SCOPE = (
    "This is a complete 1914 set — a July crisis week on this entry. "
    "A parent can run Monday–Friday at the table without leaving this page "
    "or its held cards. It is not a school year. It is not for sale. It does "
    "not claim a war beyond the papers we hold."
)

HUNT_BLURB = (
    "The artifact is the held card. Open Grey Book No. 20 or the ultimatum. "
    "Fun is do-we-hold-this. Atticus stays cite-or-stop."
)


def slug(heading: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


def week_source_ids() -> set[str]:
    ids = set(HELD_SOURCE_IDS)
    for day in DAYS:
        ids.update(day["sources"])
    ids.update(HUNT_IDS)
    return ids


def _held_records() -> dict[str, dict]:
    return {r.get("id"): r for r in load_all(str(SOURCES)) if r.get("id")}


def validate() -> list[str]:
    """Structural honesty. Empty list means the week may ship."""
    errors: list[str] = []
    text = CHAPTER.read_text(encoding="utf-8")
    records = _held_records()

    if len(DAYS) != 5:
        errors.append(f"week must be five days, got {len(DAYS)}")
    weekdays = [d["weekday"] for d in DAYS]
    if weekdays != ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        errors.append(f"days must be Mon–Fri in order, got {weekdays}")

    used: set[str] = set()
    for day in DAYS:
        heading = day["heading"]
        if f"## {heading}" not in text:
            errors.append(f"{day['id']}: heading {heading!r} not in chapter")
        if day["read_id"] != slug(heading):
            errors.append(
                f"{day['id']}: read_id {day['read_id']!r} != slug({heading!r})"
            )
        for sid in day["sources"]:
            used.add(sid)
            rec = records.get(sid)
            if not rec:
                errors.append(f"{day['id']}: missing source {sid}")
                continue
            if status_for(rec) != "held":
                errors.append(f"{day['id']}: {sid} is {status_for(rec)}, not held")
            cited = rec.get("cited_by") or []
            if ENTRY_STEM not in cited:
                errors.append(f"{day['id']}: {sid} not cited by {ENTRY_STEM}")

    extra = used - set(HELD_SOURCE_IDS)
    if extra:
        errors.append(f"week opens sources outside the held 1914 set: {sorted(extra)}")
    missing = set(HELD_SOURCE_IDS) - used
    if missing:
        errors.append(f"held 1914 source unused by the parent week: {sorted(missing)}")

    for sid in HUNT_IDS:
        rec = records.get(sid)
        if not rec or status_for(rec) != "held":
            errors.append(f"hunt source {sid} is not held")

    copy = " ".join(
        [SCOPE, HUNT_BLURB]
        + [d["parent"] for d in DAYS]
        + [d["kid"] for d in DAYS]
        + [d["title"] for d in DAYS]
        + [d["weekday"] for d in DAYS]
    )
    for token in FORBIDDEN_WEEK_COPY:
        if token in copy:
            errors.append(f"week copy contains forbidden token {token!r}")

    if "complete 1914 set" not in SCOPE or "July crisis week" not in SCOPE:
        errors.append("scope must name a complete 1914 set / July crisis week")
    if "not a school year" not in SCOPE.lower():
        errors.append("scope must say this is not a school year")
    if "not for sale" not in SCOPE.lower():
        errors.append("scope must say this is not for sale")

    return errors


def _btn(card_id: str, label: str) -> str:
    cid = html.escape(card_id, quote=True)
    return (
        f'<button type="button" class="btn quiet" data-open-card="{cid}">'
        f"{html.escape(label)}</button>"
    )


def _label(sid: str) -> str:
    return {
        "austro-hungarian-ultimatum-1914": "Open the ultimatum",
        "serbian-reply-1914": "Open the Serbian reply",
        "austro-hungarian-war-serbia-1914": "Open the war telegram",
        "german-war-russia-1914": "Open the note to Russia",
        "german-war-france-1914": "Open the note to France",
        "belgian-grey-book-1914": "Open the Grey Book",
        "grey-commons-1914": "Open Grey, Commons",
    }.get(sid, sid)


def render_html() -> str:
    problems = validate()
    if problems:
        raise ValueError("1914 week failed honesty checks: " + "; ".join(problems))

    days_nav = "".join(
        f'<a href="#week-{html.escape(d["id"])}">{html.escape(d["weekday"][:3])}</a>'
        for d in DAYS
    )
    days_html = []
    for d in DAYS:
        actions = "".join(_btn(sid, _label(sid)) for sid in d["sources"])
        actions += (
            f'<button type="button" class="btn quiet" data-week-read="'
            f'{html.escape(d["read_id"], quote=True)}">Read this day’s section</button>'
        )
        days_html.append(
            f"""
    <li class="week-day" id="week-{html.escape(d["id"])}" data-day="{html.escape(d["id"])}">
      <h3><span class="mono">{html.escape(d["weekday"])}</span> {html.escape(d["title"])}</h3>
      <p class="week-parent">{html.escape(d["parent"])}</p>
      <p class="week-kid">{html.escape(d["kid"])}</p>
      <p class="week-actions">{actions}</p>
    </li>"""
        )

    return f"""
      <section class="week-path" data-week="1914" data-height="parent" aria-labelledby="week-1914-h">
        <p class="mono week-kicker">July crisis week · complete 1914 set</p>
        <h2 id="week-1914-h">One week on this entry</h2>
        <p class="sub">{html.escape(SCOPE)}</p>
        <div class="week-height" role="group" aria-label="Path height">
          <button type="button" class="week-hbtn is-on" data-week-height="parent" aria-pressed="true">Parent table</button>
          <button type="button" class="week-hbtn" data-week-height="kid" aria-pressed="false">Shorter path</button>
        </div>
        <div class="week-hunt" id="week-hunt">
          <h3 class="mono">Hunt · do we hold this?</h3>
          <p>{html.escape(HUNT_BLURB)}</p>
          <p class="week-actions">
            {_btn("belgian-grey-book-1914", "Grey Book No. 20")}
            {_btn("austro-hungarian-ultimatum-1914", "The ultimatum")}
            <button type="button" class="atticus-chip" data-ask-atticus="Do we hold Belgian Grey Book No. 20 in this entry? Cite or stop.">Ask Atticus: Grey Book No. 20</button>
            <button type="button" class="atticus-chip" data-ask-atticus="Do we hold the Austro-Hungarian ultimatum in this entry? Cite or stop.">Ask Atticus: the ultimatum</button>
          </p>
        </div>
        <nav class="week-rail" aria-label="July crisis week">{days_nav}</nav>
        <ol class="week-days">
          {''.join(days_html)}
        </ol>
        <p class="note">Weigh stays optional. Nothing is scored.</p>
      </section>
"""
