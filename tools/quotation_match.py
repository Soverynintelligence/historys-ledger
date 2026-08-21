"""Does this quotation actually appear in this source?

Not as a contiguous run — scholarship does not quote that way. An elided
quotation claims: these fragments appear in this source, in this order, with
omissions between. That is exactly what gets checked.

The consequence worth stating: the honest elided form passes and the spliced
form fails, because a splice is a contiguous run that does not exist in the
source. A rule that failed elided quotations pushed curators toward splicing —
it punished the honest form and rewarded the dishonest one.
"""
from __future__ import annotations

import re

from tools.quoted_spans import MIN_QUOTE_CHARS, norm

MIN_FRAGMENT_CHARS = 12

# Split points: ellipsis in its several forms, and editorial [brackets], which
# are alterations and so are not in the source by definition.
_GAP = re.compile(r"…|\.\s*\.\s*\.|\[[^\]]*\]")


def fragments(span: str) -> list[str]:
    """The pieces a quotation claims are present, normalised, in order."""
    return [f for f in (norm(part) for part in _GAP.split(span or "")) if f]


def verify_span(span: str, haystack: str) -> bool:
    parts = fragments(span)
    checked = [f for f in parts if len(f) >= MIN_FRAGMENT_CHARS]
    if sum(len(f) for f in checked) < MIN_QUOTE_CHARS:
        return False
    position = 0
    for fragment in checked:
        found = haystack.find(fragment, position)
        if found == -1:
            return False
        position = found + len(fragment)
    return True
