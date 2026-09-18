"""Unit tests for the chi2 group in ExtractPostfitFromWS.py (plan section 2).

getChi2() used to do six different jobs in one 86-line function: sum a chi2 over the unmasked
bins, derive ndof and a p-value, build a residual histogram, build a six-bin summary histogram,
print a diagnostic, and mutate seven dictionaries on its caller. Each is now a function with one
job; this file tests each in isolation, plus the two retained free functions it depends on.

Nothing here moves a physics number: every formula, print statement, dictionary key and bin
label is copied verbatim from the pre-refactor function.
"""

import math

import pytest
import ROOT

from roothelpers import make_hist

from ExtractPostfitFromWS import (
    getNPars,
    expHist,
    _compute_chi2_terms,
    _degrees_of_freedom,
    _chi2_probability,
    _build_residual_histogram,
    _build_chi2_summary,
    _record_chi2,
)


# ---------------------------------------------------------------------------
# _compute_chi2_terms
# ---------------------------------------------------------------------------

def test_compute_chi2_terms_zero_when_postfit_equals_data():
    data = make_hist("d", [0, 1, 2, 3], [10, 20, 30])
    postfit = make_hist("p", [0, 1, 2, 3], [10, 20, 30], errors=[0, 0, 0])

    chi2, chi2bins, maskedchi2bins, residuals = _compute_chi2_terms(
        data, postfit, nbins=3, maskmin=-1, maskmax=-1, maskisbinnumber=False, useSumW2=False,
    )

    assert chi2 == 0.0
    assert chi2bins == 3
    assert maskedchi2bins == 0
    assert len(residuals) == 3


def test_compute_chi2_terms_pearson_vs_sumw2_denominator():
    data = make_hist("d", [0, 1], [110], errors=[5])
    postfit = make_hist("p", [0, 1], [100], errors=[0])

    chi2, _, _, residuals = _compute_chi2_terms(
        data, postfit, nbins=1, maskmin=-1, maskmax=-1, maskisbinnumber=False, useSumW2=False,
    )
    assert chi2 == pytest.approx(1.0)  # ((110-100)/sqrt(100))**2
    assert residuals == [(1, 1.0)]

    chi2, _, _, residuals = _compute_chi2_terms(
        data, postfit, nbins=1, maskmin=-1, maskmax=-1, maskisbinnumber=False, useSumW2=True,
    )
    assert chi2 == pytest.approx(4.0)  # ((110-100)/5)**2
    assert residuals == [(1, 2.0)]


def test_compute_chi2_terms_mask_window_excludes_middle_bin():
    data = make_hist("d", [0, 1, 2, 3], [10, 20, 30], errors=[1, 1, 1])
    postfit = make_hist("p", [0, 1, 2, 3], [10, 20, 30], errors=[0, 0, 0])

    # bin centres are 0.5, 1.5, 2.5 - a window of (1, 2) covers only the middle one.
    chi2, chi2bins, maskedchi2bins, residuals = _compute_chi2_terms(
        data, postfit, nbins=3, maskmin=1, maskmax=2, maskisbinnumber=False, useSumW2=False,
    )

    assert chi2bins == 2
    assert maskedchi2bins == 1
    assert [ibin for ibin, _ in residuals] == [1, 2, 3]  # masked bin still gets a residual


def test_compute_chi2_terms_mask_by_bin_number():
    data = make_hist("d", [0, 1, 2, 3], [10, 20, 30], errors=[1, 1, 1])
    postfit = make_hist("p", [0, 1, 2, 3], [10, 20, 30], errors=[0, 0, 0])

    # bin 2's centre (1.5) is far outside (1.4, 1.6), but as a bin *number* (2.5) it is inside.
    chi2, chi2bins, maskedchi2bins, residuals = _compute_chi2_terms(
        data, postfit, nbins=3, maskmin=1.4, maskmax=1.6, maskisbinnumber=True, useSumW2=False,
    )

    assert chi2bins == 2
    assert maskedchi2bins == 1


def test_compute_chi2_terms_no_mask_excludes_nothing():
    data = make_hist("d", [0, 1, 2], [10, 20], errors=[1, 1])
    postfit = make_hist("p", [0, 1, 2], [10, 20], errors=[0, 0])

    chi2, chi2bins, maskedchi2bins, residuals = _compute_chi2_terms(
        data, postfit, nbins=2, maskmin=-1, maskmax=-1, maskisbinnumber=False, useSumW2=False,
    )

    assert chi2bins == 2
    assert maskedchi2bins == 0


def test_compute_chi2_terms_pins_issue_41_zero_error_and_zero_postfit_vanish():
    """KNOWN_ISSUES issue 41: a bin with zero data error or zero postfit value is dropped
    entirely, not counted as agreeing. This test pins that behaviour rather than fixing it."""
    data = make_hist("d", [0, 1, 2], [10, 20], errors=[0, 1])   # bin 1: zero data error
    postfit = make_hist("p", [0, 1, 2], [0, 20], errors=[0, 0])  # bin 1: zero postfit value too

    chi2, chi2bins, maskedchi2bins, residuals = _compute_chi2_terms(
        data, postfit, nbins=2, maskmin=-1, maskmax=-1, maskisbinnumber=False, useSumW2=False,
    )

    assert chi2bins == 1
    assert maskedchi2bins == 0
    assert [ibin for ibin, _ in residuals] == [2]


# ---------------------------------------------------------------------------
# _degrees_of_freedom / _chi2_probability
# ---------------------------------------------------------------------------

def test_degrees_of_freedom_can_reach_zero_or_below():
    """Not worth testing as arithmetic; worth recording that ndof <= 0 is reachable and that
    the caller's chi2/ndof then raises ZeroDivisionError - preserved fails-closed behaviour."""
    assert _degrees_of_freedom(chi2bins=6, npars=6) == 0
    assert _degrees_of_freedom(chi2bins=6, npars=8) == -2

    with pytest.raises(ZeroDivisionError):
        _build_chi2_summary(chi2=10.0, chi2bins=6, npars=6, ndof=0, pval=1.0)


def test_chi2_probability_reference_value():
    ndof = 5
    chi2 = 3.2
    want = ROOT.Math.chisquared_cdf_c(chi2, ndof)
    assert _chi2_probability(chi2, ndof) == pytest.approx(want)


def test_chi2_probability_zero_chi2_gives_one():
    assert _chi2_probability(0.0, 5) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# _build_residual_histogram
# ---------------------------------------------------------------------------

def test_build_residual_histogram():
    postfit = make_hist("p", [0, 1, 2, 3], [10, 20, 30], errors=[0, 0, 0])
    residuals = [(1, 0.5), (3, -1.5)]

    h = _build_residual_histogram(postfit, "J100yStar06", residuals)

    assert h.GetName() == "J100yStar06/residuals"
    assert h.GetDirectory() is None or not h.GetDirectory()
    assert h.GetBinContent(1) == pytest.approx(0.5)
    assert h.GetBinContent(2) == 0.0
    assert h.GetBinContent(3) == pytest.approx(-1.5)
    for i in range(1, 4):
        assert h.GetBinError(i) == 0.0


# ---------------------------------------------------------------------------
# _build_chi2_summary
# ---------------------------------------------------------------------------

def test_build_chi2_summary_bin_order_labels_and_directory():
    h = _build_chi2_summary(chi2=12.0, chi2bins=8, npars=6, ndof=2, pval=0.25)

    assert h.GetDirectory() is None or not h.GetDirectory()
    assert [h.GetBinContent(i) for i in range(1, 7)] == pytest.approx(
        [12.0, 6.0, 8.0, 6.0, 2.0, 0.25]
    )
    assert [h.GetXaxis().GetBinLabel(i) for i in range(1, 7)] == [
        "chi2", "chi2/ndof", "nbins", "npars", "ndof", "pval",
    ]
    # ndoferr is hardcoded to 0, so bin 2's error is always 0 today - pinned so a future
    # non-zero ndoferr is a visible change rather than a silent one.
    assert h.GetBinError(2) == 0.0


# ---------------------------------------------------------------------------
# _record_chi2
# ---------------------------------------------------------------------------

class _FakeExtractor:
    def __init__(self):
        self.channel_chi2 = {}
        self.channel_nbins = {}
        self.channel_npars = {}
        self.channel_ndof = {}
        self.channel_pval = {}
        self.channel_hresiduals = {}
        self.channel_hchi2 = {}


def test_record_chi2_writes_all_seven_dictionaries():
    extractor = _FakeExtractor()
    h_residuals = make_hist("r", [0, 1], [0])
    h_chi2 = make_hist("c", [0, 1], [0])

    _record_chi2(
        extractor, "J100yStar06",
        chi2=12.0, chi2bins=8, npars=6, ndof=2, pval=0.25,
        h_residuals=h_residuals, h_chi2=h_chi2,
    )

    assert extractor.channel_chi2["J100yStar06"] == 12.0
    assert extractor.channel_nbins["J100yStar06"] == 8
    assert extractor.channel_npars["J100yStar06"] == 6
    assert extractor.channel_ndof["J100yStar06"] == 2
    assert extractor.channel_pval["J100yStar06"] == 0.25
    assert extractor.channel_hresiduals["J100yStar06"] is h_residuals
    assert extractor.channel_hchi2["J100yStar06"] is h_chi2


# ---------------------------------------------------------------------------
# getNPars (retained, unchanged)
# ---------------------------------------------------------------------------

def test_get_n_pars_counts_free_non_observable_parameters():
    w = ROOT.RooWorkspace("w")
    w.factory("Gaussian::g(x[0,10],m[5,0,10],s[1,0.1,5])")
    w.factory("Gaussian::g2(x,m,sfixed[1])")
    w.var("sfixed").setConstant(True)

    x = w.var("x")
    g = w.pdf("g")
    # observable x and the pdf itself are not counted; m and s are free -> 2.
    assert getNPars(g, x, exclSyst=False) == 2

    g2 = w.pdf("g2")
    # sfixed is constant and must not be counted.
    assert getNPars(g2, x, exclSyst=False) == 1


# ---------------------------------------------------------------------------
# expHist (retained, unchanged)
# ---------------------------------------------------------------------------

def test_exp_hist_undoes_log_transform_in_place():
    h = make_hist("h", [0, 1, 2, 3], [0, math.log(10), math.log(100)], errors=[0, 0.1, 0.2])

    expHist(h)

    assert h.GetBinContent(1) == 0.0
    assert h.GetBinError(1) == 0.0
    assert h.GetBinContent(2) == pytest.approx(10.0)
    assert h.GetBinError(2) == pytest.approx(0.1 * 10.0)  # error scaled by the NEW content
    assert h.GetBinContent(3) == pytest.approx(100.0)
    assert h.GetBinError(3) == pytest.approx(0.2 * 100.0)
