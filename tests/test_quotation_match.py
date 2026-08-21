"""Elision-aware matching.

The property that matters: the honest elided quotation passes, and the version
with the ellipsis removed — fragments spliced into apparently continuous text —
fails. The old contiguous-only rule had this exactly backwards.
"""
from tools.quotation_match import MIN_FRAGMENT_CHARS, verify_span
from tools.quoted_spans import norm

THIRTEENTH = norm(
    "Neither slavery nor involuntary servitude, except as a punishment for crime "
    "whereof the party shall have been duly convicted, shall exist within the "
    "United States, or any place subject to their jurisdiction."
)


def test_the_honest_elided_quotation_passes():
    assert verify_span(
        "Neither slavery nor involuntary servitude… shall exist within the United States.",
        THIRTEENTH,
    )


def test_the_spliced_version_fails():
    # The ellipsis deleted and the gap closed — reads as continuous
    # constitutional text and erases the punishment clause.
    assert not verify_span(
        "Neither slavery nor involuntary servitude shall exist within the United States.",
        THIRTEENTH,
    )


def test_fragments_must_appear_in_order():
    assert not verify_span(
        "shall exist within the United States… Neither slavery nor involuntary servitude",
        THIRTEENTH,
    )


def test_three_dot_ellipsis_is_also_understood():
    assert verify_span(
        "Neither slavery nor involuntary servitude... shall exist within the United States.",
        THIRTEENTH,
    )


def test_editorial_brackets_are_treated_as_a_gap():
    source = norm("the enforced separation of the two races stamps the colored race "
                  "with a badge of inferiority")
    assert verify_span(
        "the enforced separation of the two races [does not stamp] the colored race",
        source,
    )


def test_a_contiguous_quotation_still_behaves_exactly_as_before():
    assert verify_span("shall exist within the United States", THIRTEENTH)
    assert not verify_span("shall exist within the Confederate States", THIRTEENTH)


def test_scraps_too_short_to_check_cannot_smuggle_a_fabrication():
    # Chopping an invented quote into tiny pieces must not buy a pass.
    assert not verify_span("the… of… a… to… in… and… for", THIRTEENTH)


def test_fragment_floor_is_exposed_for_the_gate_to_reason_about():
    assert MIN_FRAGMENT_CHARS == 12
