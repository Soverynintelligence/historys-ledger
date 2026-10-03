"""Cold War week — wrap the held US entry. Not a second shelf.

The week is chrome on The Long Standoff. It names held source ids and
existing section headings only. It does not invent quotations, dates,
figures, or scenes. It does not open a kids shelf or a new chapter.
"""
from __future__ import annotations

import html
from pathlib import Path

from tools.source_cards import status_for
from tools.source_records import load_all

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "content/chapters/06-cold-war.md"
SOURCES = ROOT / "content/sources"

ENTRY_STEM = "06-cold-war"

# Every id the week may open. Must be held records cited by this entry.
HELD_SOURCE_IDS = (
    "kennan-long-telegram-1946",
    "truman-doctrine-1947",
    "marshall-harvard-1947",
    "army-mccarthy-hearings-1954",
    "executive-order-10450-1953",
    "kennedy-cuba-1962",
    "eisenhower-farewell-1961",
)

HUNT_IDS = (
    "kennan-long-telegram-1946",
    "marshall-harvard-1947",
)

FORBIDDEN_WEEK_COPY = (
    "WW1",
    "WWI",
    "World War I",
    "World War 1",
    "WWII",
    "World War II",
    "Family year",
    "not for sale",
    "waitlist",
    "$79",
    "$19",
    "Stripe",
    "checkout",
    "Buy this week",
    "Korea",
    "Vietnam",
    "mascot",
)

# Headings must match ## lines already in the chapter.
DAYS = (
    {
        "id": "mon",
        "weekday": "Monday",
        "title": "A telegram from Moscow",
        "heading": "The Threat Was Real",
        "read_id": "the-threat-was-real",
        "sources": ("kennan-long-telegram-1946",),
        "parent": (
            "Read “The Threat Was Real.” Open the Long Telegram. Find the "
            "modus vivendi sentence already quoted in this entry. At the "
            "table: what does Kennan say the Soviet leadership believes "
            "about a settlement with the United States?"
        ),
        "kid": (
            "Open the Long Telegram. Find the words modus vivendi. If a "
            "card is not held, stop."
        ),
    },
    {
        "id": "tue",
        "weekday": "Tuesday",
        "title": "Free peoples, and a speech at Harvard",
        "heading": "The Answer",
        "read_id": "the-answer",
        "sources": (
            "truman-doctrine-1947",
            "marshall-harvard-1947",
        ),
        "parent": (
            "Read “The Answer.” Open Truman and find the free peoples "
            "sentence already quoted here. Open Marshall and find the "
            "sentence about normal economic health. At the table: what "
            "does each man say the United States should do?"
        ),
        "kid": (
            "Open Truman. Find the words free peoples. Then open Marshall "
            "and find the words economic health. Stay on the cards we hold."
        ),
    },
    {
        "id": "wed",
        "weekday": "Wednesday",
        "title": "Decency, and a loyalty order",
        "heading": "The Price at Home",
        "read_id": "the-price-at-home",
        "sources": (
            "army-mccarthy-hearings-1954",
            "executive-order-10450-1953",
        ),
        "parent": (
            "Read “The Price at Home.” Open the Army–McCarthy card and find "
            "Welch’s decency sentence. Then open Executive Order 10450 and "
            "find the grounds-for-dismissal list already quoted here. A "
            "parent can skip that order paragraph with a younger reader. "
            "At the table: what words are on the two cards?"
        ),
        "kid": (
            "Skip the loyalty-order paragraph. Open the Army–McCarthy card. "
            "Find the word decency. If the card is not held, stop."
        ),
    },
    {
        "id": "thu",
        "weekday": "Thursday",
        "title": "A speech about missiles",
        "heading": "The Two Men Who Said No",
        "read_id": "the-two-men-who-said-no",
        "sources": ("kennedy-cuba-1962",),
        "parent": (
            "A parent can skip “The Price Abroad” — it names coups and "
            "prisons, and we do not hold the Church Committee pages. Then "
            "read “The Two Men Who Said No.” Open Kennedy. Find the "
            "sentence about a nuclear missile launched from Cuba. The "
            "Arkhipov account stays argued; we do not quote it. At the "
            "table: what does Kennedy say a missile from Cuba would be?"
        ),
        "kid": (
            "Skip the marked coups. Read “The Two Men Who Said No.” Open "
            "Kennedy. Find the words nuclear missile. If a card is not "
            "held, stop."
        ),
    },
    {
        "id": "fri",
        "weekday": "Friday",
        "title": "A farewell",
        "heading": "The Ending",
        "read_id": "the-ending",
        "sources": ("eisenhower-farewell-1961",),
        "parent": (
            "Read “The Ending,” then “What We Learned” if you want the "
            "takeaway. Open Eisenhower. Find the military-industrial "
            "complex sentence already quoted at the top of this entry. At "
            "the table: what does he say the country must guard against? "
            "Weigh stays optional. Nothing is scored."
        ),
        "kid": (
            "Read “The Ending” if you want. Open Eisenhower. Find the "
            "words military-industrial complex. Weigh is optional. "
            "Nothing is scored."
        ),
    },
)

SCOPE = (
    "This is a week on this entry. A parent can run Monday–Friday at the "
    "table from the held cards. High school is the default height. The "
    "shorter path skips the marked coups and the loyalty-order language. "
    "It is not a school year."
)

PROOF_LINE = (
    "Held papers, Monday through Friday. When we don't hold the page, "
    "the card says so."
)

HUNT_BLURB = (
    "The artifact is the held card. Open the Long Telegram or Marshall’s "
    "Harvard speech. Fun is do-we-hold-this."
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
        errors.append(f"week opens sources outside the held set: {sorted(extra)}")
    missing = set(HELD_SOURCE_IDS) - used
    if missing:
        errors.append(f"held week source unused by the parent week: {sorted(missing)}")

    for sid in HUNT_IDS:
        rec = records.get(sid)
        if not rec or status_for(rec) != "held":
            errors.append(f"hunt source {sid} is not held")

    copy = " ".join(
        [SCOPE, PROOF_LINE, HUNT_BLURB]
        + [d["parent"] for d in DAYS]
        + [d["kid"] for d in DAYS]
        + [d["title"] for d in DAYS]
        + [d["weekday"] for d in DAYS]
    )
    for token in FORBIDDEN_WEEK_COPY:
        if token in copy:
            errors.append(f"week copy contains forbidden token {token!r}")

    if "not a school year" not in SCOPE.lower():
        errors.append("scope must say this is not a school year")
    if "shorter path skips the marked coups" not in SCOPE.lower():
        errors.append("scope must name the shorter path / marked coups")
    if "not for sale" in copy.lower():
        errors.append("week copy must not say this is not for sale")
    if "$19" in copy or "Buy this week" in copy:
        errors.append("week copy must not sell the week at a price")

    return errors


def _btn(card_id: str, label: str) -> str:
    cid = html.escape(card_id, quote=True)
    return (
        f'<button type="button" class="btn quiet" data-open-card="{cid}">'
        f"{html.escape(label)}</button>"
    )


def _label(sid: str) -> str:
    return {
        "kennan-long-telegram-1946": "Open the Long Telegram",
        "truman-doctrine-1947": "Open Truman, 1947",
        "marshall-harvard-1947": "Open Marshall at Harvard",
        "army-mccarthy-hearings-1954": "Open Army–McCarthy",
        "executive-order-10450-1953": "Open Executive Order 10450",
        "kennedy-cuba-1962": "Open Kennedy, 1962",
        "eisenhower-farewell-1961": "Open Eisenhower’s farewell",
    }.get(sid, sid)


def render_html() -> str:
    problems = validate()
    if problems:
        raise ValueError(
            "Cold War week failed honesty checks: " + "; ".join(problems)
        )

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
      <section class="week-path" data-week="cold-war" data-height="parent" aria-labelledby="week-cold-war-h">
        <p class="mono week-kicker">Cold War week · held papers</p>
        <h2 id="week-cold-war-h">One week on this entry</h2>
        <p class="sub">{html.escape(SCOPE)}</p>
        <p class="sub week-proof">{html.escape(PROOF_LINE, quote=False)}</p>
        <div class="week-height" role="group" aria-label="Path height">
          <button type="button" class="week-hbtn is-on" data-week-height="parent" aria-pressed="true">High school</button>
          <button type="button" class="week-hbtn" data-week-height="kid" aria-pressed="false">Shorter path</button>
        </div>
        <div class="week-hunt" id="week-hunt">
          <h3 class="mono">Hunt · do we hold this?</h3>
          <p>{html.escape(HUNT_BLURB)}</p>
          <p class="week-actions">
            {_btn("kennan-long-telegram-1946", "The Long Telegram")}
            {_btn("marshall-harvard-1947", "Marshall at Harvard")}
            <button type="button" class="atticus-chip" data-ask-atticus="Do we hold Kennan’s Long Telegram in this entry? Cite or stop.">Ask Atticus: the Long Telegram</button>
            <button type="button" class="atticus-chip" data-ask-atticus="Do we hold Marshall’s Harvard address in this entry? Cite or stop.">Ask Atticus: Marshall at Harvard</button>
          </p>
        </div>
        <nav class="week-rail" aria-label="Cold War week">{days_nav}</nav>
        <ol class="week-days">
          {''.join(days_html)}
        </ol>
        <p class="note">Weigh stays optional. Nothing is scored. The Church Committee card and the Arkhipov account stay citations until we hold a clean official page.</p>
      </section>
"""
