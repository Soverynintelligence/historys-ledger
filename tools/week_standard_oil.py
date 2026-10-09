"""Standard Oil week — wrap the held US entry. Not a second shelf.

The week is chrome on Standard Oil. It names held source ids and
existing section headings only. It does not invent quotations, dates,
figures, or scenes. It does not open a kids shelf or a new chapter.
"""
from __future__ import annotations

import html
from pathlib import Path

from tools.source_cards import status_for
from tools.source_records import load_all

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "content/chapters/04-standard-oil.md"
SOURCES = ROOT / "content/sources"

ENTRY_STEM = "04-standard-oil"

# Every id the week may open. Must be held records cited by this entry.
HELD_SOURCE_IDS = (
    "rockefeller-random-reminiscences-1909",
    "tarbell-history-standard-oil-1904",
    "sherman-antitrust-act-1890",
    "standard-oil-v-us-1911",
)

HUNT_IDS = (
    "rockefeller-random-reminiscences-1909",
    "sherman-antitrust-act-1890",
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
    "Exxon",
    "Mobil",
    "Chevron",
    "Amoco",
)

# Headings must match ## lines already in the chapter.
DAYS = (
    {
        "id": "mon",
        "weekday": "Monday",
        "title": "The oil trade, in his words",
        "heading": "The Light",
        "read_id": "the-light",
        "sources": ("rockefeller-random-reminiscences-1909",),
        "parent": (
            "Read “The Light.” Open the Rockefeller card. Find the line about "
            "individual competition already quoted at the top of this entry. "
            "Then find the butcher, the baker, and the candlestick-maker. At "
            "the table: what does he say happened to the price?"
        ),
        "kid": (
            "Open Rockefeller, 1909. Find the butcher and the baker. Find "
            "the word oil. If a card is not held, stop."
        ),
    },
    {
        "id": "tue",
        "weekday": "Tuesday",
        "title": "Rebates and a drawback",
        "heading": "The Machine",
        "read_id": "the-machine",
        "sources": (
            "rockefeller-random-reminiscences-1909",
            "tarbell-history-standard-oil-1904",
        ),
        "parent": (
            "Read “The Machine.” Open Rockefeller and find the rebate "
            "sentence. Open Tarbell and find the drawback on every barrel "
            "his rivals shipped. A parent can skip the marked contract "
            "page. At the table: what does he admit, and what does she add?"
        ),
        "kid": (
            "Open Rockefeller. Find the word rebates. Then open Tarbell "
            "and find drawback. Stay on the cards we hold."
        ),
    },
    {
        "id": "wed",
        "weekday": "Wednesday",
        "title": "Ninety per cent.",
        "heading": "The Muckraker",
        "read_id": "the-muckraker",
        "sources": ("tarbell-history-standard-oil-1904",),
        "parent": (
            "Read “The Muckraker.” Open Tarbell. Find the ninety per cent. "
            "sentence already quoted here, then the loaded-dice sentence. "
            "At the table: which words are hers in 1904, and which later "
            "line does this entry leave as a citation?"
        ),
        "kid": (
            "Open Tarbell. Find ninety per cent. If the card is not held, "
            "stop."
        ),
    },
    {
        "id": "thu",
        "weekday": "Thursday",
        "title": "The statute on the page",
        "heading": "The Law",
        "read_id": "the-law",
        "sources": ("sherman-antitrust-act-1890",),
        "parent": (
            "Read “The Law.” Open the Sherman Act. Find the sentence that "
            "begins “Every contract.” At the table: which words does the "
            "act make illegal?"
        ),
        "kid": (
            "Open the Sherman Act. Find the words restraint of trade. Stay "
            "on the card we hold."
        ),
    },
    {
        "id": "fri",
        "weekday": "Friday",
        "title": "Thirty-seven companies",
        "heading": "The Court",
        "read_id": "the-court",
        "sources": ("standard-oil-v-us-1911",),
        "parent": (
            "Read “The Court,” then “What We Learned” if you want the "
            "takeaway. Open the 1911 opinion. Find thirty-seven subsidiary "
            "companies. At the table: what does the Court tell New Jersey "
            "it may not do? Weigh stays optional. Nothing is scored."
        ),
        "kid": (
            "Read “The Court” if you want. Open the 1911 card. Find "
            "thirty-seven. Weigh is optional. Nothing is scored."
        ),
    },
)

SCOPE = (
    "This is a week on this entry. A parent can run Monday–Friday at the "
    "table from the held cards. High school is the default height. The "
    "shorter path stays on the named sentences and skips the marked "
    "contract page. It is not a school year."
)

PROOF_LINE = (
    "Held papers, Monday through Friday. When we don't hold the page, "
    "the card says so."
)

HUNT_BLURB = (
    "The artifact is the held card. Open Rockefeller, 1909, or the "
    "Sherman Act. Fun is do-we-hold-this."
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
    if "shorter path stays on the named sentences" not in SCOPE.lower():
        errors.append("scope must name the shorter path / named sentences")
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
        "rockefeller-random-reminiscences-1909": "Open Rockefeller, 1909",
        "tarbell-history-standard-oil-1904": "Open Tarbell, 1904",
        "sherman-antitrust-act-1890": "Open the Sherman Act",
        "standard-oil-v-us-1911": "Open the 1911 opinion",
    }.get(sid, sid)


def render_html() -> str:
    problems = validate()
    if problems:
        raise ValueError(
            "Standard Oil week failed honesty checks: " + "; ".join(problems)
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
      <section class="week-path" data-week="standard-oil" data-height="parent" aria-labelledby="week-standard-oil-h">
        <p class="mono week-kicker">Standard Oil week · held papers</p>
        <h2 id="week-standard-oil-h">One week on this entry</h2>
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
            {_btn("rockefeller-random-reminiscences-1909", "Rockefeller, 1909")}
            {_btn("sherman-antitrust-act-1890", "The Sherman Act")}
            <button type="button" class="atticus-chip" data-ask-atticus="Do we hold Rockefeller’s 1909 Random Reminiscences in this entry? Cite or stop.">Ask Atticus: Rockefeller, 1909</button>
            <button type="button" class="atticus-chip" data-ask-atticus="Do we hold the Sherman Antitrust Act in this entry? Cite or stop.">Ask Atticus: the Sherman Act</button>
          </p>
        </div>
        <nav class="week-rail" aria-label="Standard Oil week">{days_nav}</nav>
        <ol class="week-days">
          {''.join(days_html)}
        </ol>
        <p class="note">Weigh stays optional. Nothing is scored. The Hepburn card is a citation until we hold a clean official page.</p>
      </section>
"""
