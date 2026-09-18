"""Unit tests for the prefit parameter plumbing in run_anaFit.py (plan section 3, Group E).

These six functions decide how many background parameters the prefit uses, read the card's own
declared bounds, cross-check the two, build the bounds array, and write the fitted starting
values back into the card. Two real quirks are pinned rather than fixed: KNOWN_ISSUES 42 (an
unrecognised file name silently defaults to 5 parameters) and the PAR1-before-PAR10 substitution
order (a ten-parameter card corrupts its own PAR10 placeholder).
"""

import sys

import pytest

from run_anaFit import (
    _npars_from_filename,
    _parse_card_par_ranges,
    _check_card_pars,
    _card_par_ranges,
    _substitute_prefit_parameters,
    _format_nbkg,
)


# ---------------------------------------------------------------------------
# _npars_from_filename
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("keyword,n", [
    ("three", 3), ("four", 4), ("five", 5), ("six", 6),
    ("seven", 7), ("eight", 8), ("nine", 9), ("ten", 10),
])
def test_npars_from_filename_keyword(keyword, n):
    assert _npars_from_filename(f"background_dijetTLA_{keyword}Par.template") == n


def test_npars_from_filename_pins_issue_42_unknown_name_defaults_to_five():
    assert _npars_from_filename("background_dijetTLA_mysteryPar.template") == 5


def test_npars_from_filename_pins_if_elif_split_three_and_four_gives_four():
    """"three" and "four" are each tested by their own top-level `if` (not chained to one
    another), and "four" starts the elif chain for five..ten - so a name containing both
    keywords sets nPars=3 first and then nPars=4, landing on 4, not 3."""
    assert _npars_from_filename("background_threeandfourPar.template") == 4


# ---------------------------------------------------------------------------
# _parse_card_par_ranges
# ---------------------------------------------------------------------------

def test_parse_card_par_ranges_reads_modelitem_line(tmp_path):
    card = tmp_path / "background.xml"
    card.write_text('<ModelItem Name="p1" Range="[PAR1,-30,30]"/>\n')

    assert _parse_card_par_ranges(str(card)) == [("1", "-30", "30")]


def test_parse_card_par_ranges_skips_commented_line_even_with_placeholders(tmp_path):
    card = tmp_path / "background.xml"
    card.write_text('<!-- <ModelItem Name="p1" Range="[PAR1,-30,30]"/> -->\n')

    assert _parse_card_par_ranges(str(card)) == []


def test_parse_card_par_ranges_skips_non_modelitem_line(tmp_path):
    card = tmp_path / "background.xml"
    card.write_text('<Item Name="p1" Range="[PAR1,-30,30]"/>\n')

    assert _parse_card_par_ranges(str(card)) == []


def test_parse_card_par_ranges_captures_several_placeholders_on_one_line(tmp_path):
    card = tmp_path / "background.xml"
    card.write_text('<ModelItem Range="[PAR1,-30,30] [PAR2,-5,5]"/>\n')

    assert _parse_card_par_ranges(str(card)) == [("1", "-30", "30"), ("2", "-5", "5")]


def test_parse_card_par_ranges_negative_and_decimal_bounds(tmp_path):
    card = tmp_path / "background.xml"
    card.write_text('<ModelItem Range="[PAR3,-12.5,7.25]"/>\n')

    assert _parse_card_par_ranges(str(card)) == [("3", "-12.5", "7.25")]


# ---------------------------------------------------------------------------
# _check_card_pars
# ---------------------------------------------------------------------------

def test_check_card_pars_matching_indices_pass_silently(capsys):
    _check_card_pars([("1", "-30", "30"), ("6", "-1", "1")], nPars=6, backgroundfile="bg.template")
    assert capsys.readouterr().out == ""


def test_check_card_pars_empty_matches_warns_without_exiting(capsys):
    _check_card_pars([], nPars=6, backgroundfile="bg.template")
    assert "WARNING" in capsys.readouterr().out


def test_check_card_pars_mismatch_exits_and_names_both_numbers(capsys):
    with pytest.raises(SystemExit):
        _check_card_pars([("7", "-1", "1")], nPars=6, backgroundfile="bg.template")
    out = capsys.readouterr().out
    assert "PAR7" in out
    assert "nPars=6" in out


# ---------------------------------------------------------------------------
# _card_par_ranges
# ---------------------------------------------------------------------------

def test_card_par_ranges_defaults_with_no_matches():
    low, high = _card_par_ranges([], nPars=4)
    assert low == [1, -30, -30, -30]
    assert high == [1, 30, 30, 30]


def test_card_par_ranges_match_overrides_only_its_own_index():
    low, high = _card_par_ranges([("3", "-12.5", "7.25")], nPars=4)
    assert low == [1, -30, -12.5, -30]
    assert high == [1, 30, 7.25, 30]


def test_card_par_ranges_first_entry_stays_one_unless_par1_overridden():
    low, _ = _card_par_ranges([("2", "-5", "5")], nPars=3)
    assert low[0] == 1

    low, _ = _card_par_ranges([("1", "-99", "99")], nPars=3)
    assert low[0] == -99.0


# ---------------------------------------------------------------------------
# _substitute_prefit_parameters
# ---------------------------------------------------------------------------

def test_substitute_prefit_parameters_five_params(tmp_path):
    card = tmp_path / "background.xml"
    card.write_text("PAR1 PAR2 PAR3 PAR4 PAR5\n")

    _substitute_prefit_parameters(str(card), [1.1, 2.2, 3.3, 4.4, 5.5], nPars=5)

    assert card.read_text().split() == ["1.1", "2.2", "3.3", "4.4", "5.5"]


def test_substitute_prefit_parameters_pins_par1_before_par10_corruption(tmp_path):
    """KNOWN_ISSUES: PAR1 is substituted first, and its pattern is a prefix of PAR10, so a
    ten-parameter card's PAR10 placeholder is corrupted rather than filled with initPars[9]."""
    card = tmp_path / "background.xml"
    card.write_text(" ".join("PAR%d" % i for i in range(1, 11)) + "\n")

    initPars = [float(i) for i in range(1, 11)]  # 1.0 .. 10.0
    _substitute_prefit_parameters(str(card), initPars, nPars=10)

    text = card.read_text()
    assert "1.00" in text          # "PAR10" -> "1.0" + the leftover "0"
    assert "10.0" not in text      # the intended value never lands


# ---------------------------------------------------------------------------
# _format_nbkg
# ---------------------------------------------------------------------------

def test_format_nbkg_upper_bound_is_twice_the_value():
    assert _format_nbkg(1.0e5) == "1.0E+05, 0, 2.0E+05"
