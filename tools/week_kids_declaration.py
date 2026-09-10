"""Kids Hunt week — wrap the held Declaration entry. Not a second app.

Monday–Friday chrome on the kids Declaration folio only. It names held
source ids and existing section headings. It does not invent quotations,
courtroom scenes, or a Constitution hunt. Friday's Brom and Bett card is
citation-only: the hunt is what the card actually says, and a stop is a win.
"""
from __future__ import annotations

import html
from pathlib import Path

from tools.quotation_match import verify_span
from tools.quoted_spans import norm
from tools.source_cards import status_for
from tools.source_records import load_all

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "content/collections/kids/chapters/01-the-declaration.md"
SOURCES = ROOT / "content/collections/kids/sources"

ENTRY_STEM = "01-the-declaration"

# Held cards the hunt may open for a find-the-line stamp.
HELD_SOURCE_IDS = (
    "declaration-of-independence-1776",
    "common-sense-1776",
    "adams-family-papers",
)

# Named Friday source. Citation-only is the honest thin card — not a scene to fill.
THIN_SOURCE_ID = "brom-and-bett-v-ashley-1781"

FORBIDDEN_WEEK_COPY = (
    "XP",
    "stars",
    "leaderboard",
    "coin",
    "streak",
    "Jefferson",
    "courtroom",
    "Your Honor",
    "chatbot",
    "$19",
    "$79",
    "$",
    "Stripe",
    "checkout",
    "Buy this week",
    "waitlist",
    "Family year",
    "mascot",
    "WW1",
    "WWI",
    "World War",
    "artifact",
    "Cite or stop",
)

# Headings must match ## lines already in the chapter.
DAYS = (
    {
        "id": "mon",
        "weekday": "Monday",
        "title": "The Promise",
        "heading": "They put it on paper",
        "read_id": "they-put-it-on-paper",
        "sources": ("declaration-of-independence-1776",),
        "held": True,
        "find": "We hold these truths to be self-evident, that all men are created equal",
        "read_cue": "Read “They put it on paper.”",
        "hunt": (
            "Open the Declaration card. Find “We hold these truths to be "
            "self-evident, that all men are created equal…”"
        ),
        "atticus": (
            "Do we hold the Declaration line “We hold these truths to be "
            "self-evident, that all men are created equal” in this entry? "
            "Show the line, or stop."
        ),
        "stamp": "Stamp: I opened the card and found the line",
    },
    {
        "id": "tue",
        "weekday": "Tuesday",
        "title": "Life, Liberty…",
        "heading": "They put it on paper",
        "read_id": "they-put-it-on-paper",
        "sources": ("declaration-of-independence-1776",),
        "held": True,
        "find": "Life, Liberty and the pursuit of Happiness",
        "read_cue": "Read “They put it on paper.” Same Declaration card.",
        "hunt": (
            "Same Declaration card. Find “Life, Liberty and the pursuit of "
            "Happiness” in the same sentence."
        ),
        "atticus": (
            "Does our held Declaration card include “Life, Liberty and the "
            "pursuit of Happiness”? Show the line, or stop."
        ),
        "stamp": "Stamp: I opened the card and found the line",
    },
    {
        "id": "wed",
        "weekday": "Wednesday",
        "title": "The Island",
        "heading": "Why they were angry",
        "read_id": "why-they-were-angry",
        "sources": ("common-sense-1776",),
        "held": True,
        "find": (
            "There is something very absurd, in supposing a continent to be "
            "perpetually governed by an island."
        ),
        "read_cue": "Read “Why they were angry.”",
        "hunt": (
            "Open Common Sense. Find “There is something very absurd, in "
            "supposing a continent to be perpetually governed by an island.”"
        ),
        "atticus": (
            "Do we hold Paine’s Common Sense line about a continent governed "
            "by an island? Show the line, or stop."
        ),
        "stamp": "Stamp: I opened the card and found the line",
    },
    {
        "id": "thu",
        "weekday": "Thursday",
        "title": "Remember the Ladies",
        "heading": "The people left out said so right away",
        "read_id": "the-people-left-out-said-so-right-away",
        "sources": ("adams-family-papers",),
        "held": True,
        "find": "Do not put such unlimited power into the hands of the Husbands.",
        "read_cue": "Read “The people left out said so right away.”",
        "hunt": (
            "Open Abigail Adams’s letter. Find “Do not put such unlimited "
            "power into the hands of the Husbands.”"
        ),
        "atticus": (
            "Do we hold Abigail Adams’s line “Do not put such unlimited power "
            "into the hands of the Husbands”? Show the line, or stop."
        ),
        "stamp": "Stamp: I opened the card and found the line",
    },
    {
        "id": "fri",
        "weekday": "Friday",
        "title": "Who used the words",
        "heading": "The people left out said so right away",
        "read_id": "the-people-left-out-said-so-right-away",
        "sources": ("brom-and-bett-v-ashley-1781",),
        "held": False,
        "find": "",
        "read_cue": "Read “The people left out said so right away.”",
        "hunt": (
            "Open the Brom and Bett card. What does our card actually say? "
            "If we don’t hold it, we stop."
        ),
        "atticus": (
            "What does our Brom and Bett card actually say? "
            "If we don’t hold it, we stop."
        ),
        "stamp": "Stamp: I opened the named source — or saw it is not held",
    },
)

INTRO = (
    "Same papers as the grown-up table. Open the card. Find the marked line. "
    "If we don’t hold it, we stop. "
    "“Atticus stopped” is a win for honesty."
)

HUNT_BLURB = (
    "The hunt is the card we hold. Open the Declaration, Common Sense, or "
    "Abigail’s letter. Find the line. If we don’t hold it, we stop."
)

SIT_TEACH = (
    "Sit with them while they open the same cards. The hunt is the line on "
    "the card — not a scored test. If Atticus stops, that is the win."
)

SIT_ATTICUS = (
    "What does our Brom and Bett card actually say? If we don’t hold it, we stop."
)

SIT_DINNER = (
    "Friday dinner: what did our Brom and Bett card actually say? "
    "What was not on the card?"
)


def slug(heading: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


def week_source_ids() -> set[str]:
    ids = set(HELD_SOURCE_IDS)
    ids.add(THIN_SOURCE_ID)
    for day in DAYS:
        ids.update(day["sources"])
    return ids


def _records() -> dict[str, dict]:
    return {r.get("id"): r for r in load_all(str(SOURCES)) if r.get("id")}


def validate() -> list[str]:
    """Structural honesty. Empty list means the week may ship."""
    errors: list[str] = []
    text = CHAPTER.read_text(encoding="utf-8")
    records = _records()

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
            cited = rec.get("cited_by") or []
            if ENTRY_STEM not in cited:
                errors.append(f"{day['id']}: {sid} not cited by {ENTRY_STEM}")
            st = status_for(rec)
            if day["held"]:
                if st != "held":
                    errors.append(f"{day['id']}: {sid} is {st}, not held")
                find = day.get("find") or ""
                if not find:
                    errors.append(f"{day['id']}: held hunt missing find line")
                elif not verify_span(find, norm(rec.get("text") or "")):
                    errors.append(
                        f"{day['id']}: find line not in held text of {sid}"
                    )
            else:
                if st == "held" and (rec.get("text") or "").strip():
                    errors.append(
                        f"{day['id']}: thin hunt {sid} unexpectedly has held text"
                    )
                if st not in ("citation-only", "restricted"):
                    errors.append(
                        f"{day['id']}: thin hunt {sid} should be citation-only, got {st}"
                    )

    extra = used - set(HELD_SOURCE_IDS) - {THIN_SOURCE_ID}
    if extra:
        errors.append(f"week opens sources outside the kids Declaration set: {sorted(extra)}")
    missing_held = set(HELD_SOURCE_IDS) - used
    if missing_held:
        errors.append(f"held Declaration source unused by the hunt: {sorted(missing_held)}")
    if THIN_SOURCE_ID not in used:
        errors.append(f"thin named source {THIN_SOURCE_ID} unused")

    copy = " ".join(
        [INTRO, HUNT_BLURB, SIT_TEACH, SIT_ATTICUS, SIT_DINNER]
        + [d["hunt"] for d in DAYS]
        + [d["atticus"] for d in DAYS]
        + [d["title"] for d in DAYS]
        + [d["read_cue"] for d in DAYS]
        + [d["stamp"] for d in DAYS]
        + [d["weekday"] for d in DAYS]
    )
    for token in FORBIDDEN_WEEK_COPY:
        if token in copy:
            errors.append(f"week copy contains forbidden token {token!r}")

    if "If we don’t hold it, we stop" not in INTRO and "If we don't hold it, we stop" not in INTRO:
        errors.append("intro must say we stop when we do not hold it")
    if "Atticus stopped" not in INTRO:
        errors.append("intro must celebrate Atticus stopped")
    if "What does our card actually say" not in DAYS[4]["hunt"]:
        errors.append("Friday hunt must ask what the card actually says")
    if "If we don’t hold it, we stop" not in DAYS[4]["hunt"] and (
        "If we don't hold it, we stop" not in DAYS[4]["hunt"]
    ):
        errors.append("Friday hunt must treat a stop as the honest end")

    return errors


def _btn(card_id: str, label: str) -> str:
    cid = html.escape(card_id, quote=True)
    return (
        f'<button type="button" class="btn quiet" data-open-card="{cid}">'
        f"{html.escape(label)}</button>"
    )


def _atticus(prompt: str, label: str = "Ask Atticus") -> str:
    return (
        f'<button type="button" class="atticus-chip" data-ask-atticus="'
        f'{html.escape(prompt, quote=True)}">{html.escape(label)}</button>'
    )


def _label(sid: str) -> str:
    return {
        "declaration-of-independence-1776": "Open the Declaration",
        "common-sense-1776": "Open Common Sense",
        "adams-family-papers": "Open Abigail’s letter",
        "brom-and-bett-v-ashley-1781": "Open Brom and Bett",
    }.get(sid, sid)


def render_html() -> str:
    problems = validate()
    if problems:
        raise ValueError(
            "kids Declaration hunt failed honesty checks: " + "; ".join(problems)
        )

    days_nav = "".join(
        f'<a href="#week-{html.escape(d["id"])}">{html.escape(d["weekday"][:3])}</a>'
        for d in DAYS
    )
    days_html = []
    for d in DAYS:
        actions = "".join(_btn(sid, _label(sid)) for sid in d["sources"])
        actions += _atticus(d["atticus"])
        actions += (
            f'<button type="button" class="btn quiet" data-week-read="'
            f'{html.escape(d["read_id"], quote=True)}">Read this day’s section</button>'
        )
        days_html.append(
            f"""
    <li class="week-day" id="week-{html.escape(d["id"])}" data-day="{html.escape(d["id"])}">
      <h3><span class="mono">{html.escape(d["weekday"])}</span> {html.escape(d["title"])}</h3>
      <p class="week-read-cue">{html.escape(d["read_cue"])}</p>
      <p class="week-hunt-prompt"><strong>Hunt:</strong> {html.escape(d["hunt"])}</p>
      <p class="week-actions">{actions}</p>
      <label class="hunt-stamp">
        <input type="checkbox" data-hunt-stamp="{html.escape(d["id"], quote=True)}">
        <span class="hunt-seal" aria-hidden="true"></span>
        <span>{html.escape(d["stamp"])}</span>
      </label>
    </li>"""
        )

    return f"""
      <section class="week-path" data-week="kids-declaration" data-height="kid" aria-labelledby="week-kids-decl-h">
        <p class="mono week-kicker">Kids hunt · cards we hold</p>
        <h2 id="week-kids-decl-h">This week’s hunt</h2>
        <p class="sub">{html.escape(INTRO)}</p>
        <p class="note week-family"><a href="/family">Parents: Year 1 →</a></p>
        <div class="week-hunt" id="week-hunt">
          <h3 class="mono">Hunt · do we hold this?</h3>
          <p>{html.escape(HUNT_BLURB)}</p>
          <p class="week-actions">
            {_btn("declaration-of-independence-1776", "The Declaration")}
            {_btn("common-sense-1776", "Common Sense")}
            {_btn("adams-family-papers", "Abigail’s letter")}
            {_atticus("If we don’t hold a paper named on this entry, stop. Show the line, or stop.", "Ask Atticus: show the line — or stop")}
          </p>
        </div>
        <details class="week-sit">
          <summary>Parent sit-with</summary>
          <p>{html.escape(SIT_TEACH)}</p>
          <p class="week-actions">{_atticus(SIT_ATTICUS, "Ask Atticus: what does the card say?")}</p>
          <p>{html.escape(SIT_DINNER)}</p>
          <p class="week-grownup"><a href="/read/">Grown-up shelf</a></p>
        </details>
        <nav class="week-rail" aria-label="Declaration hunt week">{days_nav}</nav>
        <ol class="week-days">
          {''.join(days_html)}
        </ol>
        <p class="week-actions">
          <button type="button" class="btn quiet" data-hunt-clear>Clear hunts</button>
        </p>
        <p class="note">Weigh stays optional. Nothing is scored. This is not a test.</p>
      </section>
"""
