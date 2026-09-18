"""Unit tests for the card-preparation group in run_anaFit.py (plan section 3, Group D).

_check_rebin_pair now lives in ExtractPostfitFromWS.py and is imported here, replacing what used
to be two copies of the same guard (one in each module) that could drift apart independently.
The rest are pure file/string builders pulled out of run_anaFit().
"""

import os

import pytest

from run_anaFit import (
    _link_dtd,
    _temp_card_paths,
    _stage_cards,
    _fill_top_card,
    _fill_category_card,
    _signal_replacements,
)
from ExtractPostfitFromWS import _check_rebin_pair


# ---------------------------------------------------------------------------
# _check_rebin_pair (shared with ExtractPostfitFromWS.PostfitExtractor.__init__)
# ---------------------------------------------------------------------------

def test_check_rebin_pair_both_given_passes():
    _check_rebin_pair("some/file.root", "somehist")


def test_check_rebin_pair_neither_given_passes():
    _check_rebin_pair(None, None)


def test_check_rebin_pair_only_file_raises():
    with pytest.raises(ValueError):
        _check_rebin_pair("some/file.root", None)


def test_check_rebin_pair_only_hist_raises():
    with pytest.raises(ValueError):
        _check_rebin_pair(None, "somehist")


# ---------------------------------------------------------------------------
# _link_dtd
# ---------------------------------------------------------------------------

def test_link_dtd_creates_symlink_to_dijetisrTLA_copy(tmp_path):
    _link_dtd(str(tmp_path))

    link = tmp_path / "AnaWSBuilder.dtd"
    assert os.path.islink(str(link))
    assert os.path.realpath(str(link)) == os.path.realpath("config/dijetisrTLA/AnaWSBuilder.dtd")


def test_link_dtd_does_nothing_when_already_present(tmp_path, monkeypatch):
    (tmp_path / "AnaWSBuilder.dtd").write_text("already here")

    import run_anaFit
    def _boom(cmd):
        raise AssertionError("execute() must not run when the link already exists")
    monkeypatch.setattr(run_anaFit, "execute", _boom)

    _link_dtd(str(tmp_path))  # must not raise


# ---------------------------------------------------------------------------
# _temp_card_paths
# ---------------------------------------------------------------------------

def test_temp_card_paths_plain_names():
    top, cat, sig, bkg = _temp_card_paths("run", sigwidth=8., sigmean=1000)
    assert top == "run/dijetTLA_fromTemplate.xml"
    assert cat == "run/category_dijetTLA_fromTemplate.xml"
    assert sig == "run/signal_dijetTLA_fromTemplate.xml"
    assert bkg == "run/background_dijetTLA_fromTemplate.xml"


def test_temp_card_paths_zprime_sentinel_tags_top_and_category_only():
    top, cat, sig, bkg = _temp_card_paths("run", sigwidth=-999, sigmean=2500)
    assert top == "run/dijetTLA_fromTemplate_mR2500.xml"
    assert cat == "run/category_dijetTLA_fromTemplate_mR2500.xml"
    # signal and background cards are the same shape regardless of mass point.
    assert sig == "run/signal_dijetTLA_fromTemplate.xml"
    assert bkg == "run/background_dijetTLA_fromTemplate.xml"


# ---------------------------------------------------------------------------
# _stage_cards
# ---------------------------------------------------------------------------

def test_stage_cards_copies_top_category_and_signal(tmp_path):
    topfile = tmp_path / "top_src.xml"; topfile.write_text("top")
    categoryfile = tmp_path / "cat_src.xml"; categoryfile.write_text("cat")
    signalfile = tmp_path / "sig_src.xml"; signalfile.write_text("sig")
    tmptop = tmp_path / "top_dst.xml"
    tmpcat = tmp_path / "cat_dst.xml"
    tmpsig = tmp_path / "sig_dst.xml"

    _stage_cards(str(topfile), str(categoryfile), str(signalfile), str(tmptop), str(tmpcat), str(tmpsig))

    assert tmptop.read_text() == "top"
    assert tmpcat.read_text() == "cat"
    assert tmpsig.read_text() == "sig"


def test_stage_cards_signalfile_none_copies_nothing_for_signal(tmp_path):
    topfile = tmp_path / "top_src.xml"; topfile.write_text("top")
    categoryfile = tmp_path / "cat_src.xml"; categoryfile.write_text("cat")
    tmptop = tmp_path / "top_dst.xml"
    tmpcat = tmp_path / "cat_dst.xml"
    tmpsig = tmp_path / "sig_dst.xml"

    _stage_cards(str(topfile), str(categoryfile), None, str(tmptop), str(tmpcat), str(tmpsig))

    assert tmptop.read_text() == "top"
    assert tmpcat.read_text() == "cat"
    assert not tmpsig.exists()


# ---------------------------------------------------------------------------
# _fill_top_card
# ---------------------------------------------------------------------------

def test_fill_top_card_replaces_its_three_placeholders(tmp_path):
    card = tmp_path / "top.xml"
    card.write_text("cat=CATEGORYFILE\nout=OUTPUTFILE\nsig=SIGNAME\n")

    _fill_top_card(str(card), "run/category.xml", "run/ws.root", "mean1000_width7.0")

    text = card.read_text()
    assert "cat=run/category.xml" in text
    assert "out=run/ws.root" in text
    assert "sig=mean1000_width7.0" in text


# ---------------------------------------------------------------------------
# _fill_category_card
# ---------------------------------------------------------------------------

def test_fill_category_card_replaces_all_nine_placeholders(tmp_path):
    card = tmp_path / "category.xml"
    card.write_text(
        "DATAFILE DATAHIST RANGELOW RANGEHIGH BINS NBKG NSIG SIGNAME SIGNALFILE\n"
    )

    _fill_category_card(
        str(card),
        datafile="data.root", datahist="h_mjj", rangelow=481, rangehigh=3000, nbins=2519,
        nbkg="2E8,0,3E8", nsig="0,-1E6,1E6", signame="mean1000_width7.0",
        tmpsignalfile="run/signal.xml",
    )

    text = card.read_text()
    assert "data.root h_mjj 481 3000 2519 2E8,0,3E8 0,-1E6,1E6 mean1000_width7.0 run/signal.xml" == text.strip()


def test_fill_category_card_rangelow_and_rangehigh_do_not_corrupt_each_other(tmp_path):
    """RANGEHIGH is not a substring of RANGELOW and vice versa, so a sequential re.sub over both
    must not let one substitution eat into the other's placeholder."""
    card = tmp_path / "category.xml"
    card.write_text("lo=RANGELOW hi=RANGEHIGH\n")

    _fill_category_card(
        str(card),
        datafile="d", datahist="h", rangelow=481, rangehigh=3000, nbins=1,
        nbkg="n", nsig="s", signame="sig", tmpsignalfile="f",
    )

    assert card.read_text().strip() == "lo=481 hi=3000"


# ---------------------------------------------------------------------------
# _signal_replacements
# ---------------------------------------------------------------------------

def test_signal_replacements_no_systdict_has_exactly_four_entries_sweep_last():
    replacements = _signal_replacements("mean1000_width7.0", 1000, 7.0, systdict=None)

    assert replacements[:3] == [
        ("SIGNAME", "mean1000_width7.0"),
        ("SIGMEAN", "1000"),
        ("SIGWIDTH", "7.0"),
    ]
    assert len(replacements) == 4
    assert replacements[-1] == ("\[MAG_[a-zA-Z0-9_\-]*\]", "[0]")


def test_signal_replacements_with_systdict_includes_nominal_and_source_entries():
    systdict = {
        "nominal_mean": 1000.0,
        "nominal_sigma": 70.0,
        "nominal_alpha_l": 1.5,
        "nominal_alpha_h": 1.5,
        "nominal_n_l": 5,
        "nominal_n_h": 5,
        "unc_mean_sources": {"JES": 0.01},
        "unc_sigma_sources": {"JER": 0.02},
    }

    replacements = _signal_replacements("mean1000_width7.0", 1000, 7.0, systdict)

    keys = [pattern for pattern, _ in replacements]
    assert "NOMINAL_MEAN" in keys
    assert "NOMINAL_WIDTH" in keys
    assert "NOMINAL_ALPHAL" in keys
    assert "NOMINAL_ALPHAH" in keys
    assert "NOMINAL_NL" in keys
    assert "NOMINAL_NH" in keys
    assert ("\[MAG_SCALE_JES\]", "[0.01]") in replacements
    assert ("\[MAG_RESOLUTION_JER\]", "[0.02]") in replacements
    # the zero-sweep is still last, after everything systdict added.
    assert replacements[-1] == ("\[MAG_[a-zA-Z0-9_\-]*\]", "[0]")


def test_signal_replacements_missing_systdict_key_raises():
    with pytest.raises(KeyError):
        _signal_replacements("s", 1000, 7.0, systdict={"nominal_mean": 1000.0})
