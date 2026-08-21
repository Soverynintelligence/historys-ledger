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
