"""Unit tests for python/ExtractFitParameters.py's split (decomposition plan section 5).

`FitParameterExtractor.Extract()` was one 42-line method that opened the fit result, built three
histograms, captured the signal yield and wrote all five onto the instance. It is now a
coordinator over four free functions. The output file's three histograms, their names, bin labels
and contents are unchanged, because `plot_postfit.cpp:64` reads `postfit_params` by name.

The falsy-cache and substring-match behaviours pinned at the bottom of this file are KNOWN_ISSUES
issue 53: recorded and pinned as they are today, not fixed here.
"""

import pytest
import ROOT

from conftest import FIXTURES

from ExtractFitParameters import (
    FitParameterExtractor,
    _read_fit_result,
    _build_parameter_histogram,
    _matrix_to_histogram,
    _find_signal_yield,
)

J100 = str(FIXTURES / "FitResult_J100_sixPar.root")

# Measured from the fixture, which is plan section 1's recorded J100 six-parameter fit.
EXPECTED_PARAMETERS = [
    ("nbkg", 765237718.833, 39025.8677374),
    ("p2", 7.21953930846, 0.0201032792167),
    ("p3", 7.41087406258, 0.00291048486276),
    ("p4", 1.5192757776, 0.00051073903652),
    ("p5", 0.43913684836, 0.000112480449343),
    ("p6", 0.0478363147871, 2.51821808792e-05),
]


# ---------------------------------------------------------------------------
# _read_fit_result
# ---------------------------------------------------------------------------

def test_read_fit_result_returns_the_six_recorded_parameters():
    parameters, _, _ = _read_fit_result(J100)

    assert [name for name, _, _ in parameters] == [n for n, _, _ in EXPECTED_PARAMETERS]
    for (_, value, error), (name, want_value, want_error) in zip(parameters, EXPECTED_PARAMETERS):
        assert value == pytest.approx(want_value, rel=1e-11), name
        assert error == pytest.approx(want_error, rel=1e-11), name


def test_read_fit_result_returns_six_by_six_matrices():
    _, covariance, correlation = _read_fit_result(J100)

    assert len(covariance) == 6 and all(len(row) == 6 for row in covariance)
    assert len(correlation) == 6 and all(len(row) == 6 for row in correlation)
    assert covariance[0][0] == pytest.approx(1523018354.03, rel=1e-11)
    assert correlation[0][0] == pytest.approx(1.0)
    # asymmetric spot-check, so a transposed read would show up here rather than nowhere
    assert correlation[0][1] == pytest.approx(-1.04729977538e-07, rel=1e-9)


def test_read_fit_result_closes_the_file_before_returning():
    n_before = ROOT.gROOT.GetListOfFiles().GetEntries()
    _read_fit_result(J100)
    n_after = ROOT.gROOT.GetListOfFiles().GetEntries()

    assert n_after == n_before


def test_read_fit_result_returns_plain_python_values_not_file_owned_objects():
    """The whole point of the signature: argset, mat_cov and mat_cor are owned by the TFile this
    function closes, so anything handed back has to be copied out first."""
    parameters, covariance, correlation = _read_fit_result(J100)

    name, value, error = parameters[0]
    assert isinstance(name, str)
    assert isinstance(value, float) and isinstance(error, float)
    assert isinstance(covariance, list) and isinstance(covariance[0], list)
    assert isinstance(covariance[0][0], float)
    assert isinstance(correlation[0][0], float)


# ---------------------------------------------------------------------------
# _build_parameter_histogram
# ---------------------------------------------------------------------------

def test_build_parameter_histogram_carries_values_errors_and_labels():
    parameters = [("alpha", 1.5, 0.25), ("beta", -2.0, 0.5), ("gamma", 0.0, 0.125)]

    h = _build_parameter_histogram(parameters)

    assert h.GetName() == "postfit_params"
    assert h.GetNbinsX() == 3
    for i, (name, value, error) in enumerate(parameters):
        assert h.GetXaxis().GetBinLabel(i + 1) == name
        assert h.GetBinContent(i + 1) == value
        assert h.GetBinError(i + 1) == error


def test_build_parameter_histogram_is_detached_from_any_directory():
    h = _build_parameter_histogram([("alpha", 1.0, 0.1)])
    assert not h.GetDirectory()


# ---------------------------------------------------------------------------
# _matrix_to_histogram
# ---------------------------------------------------------------------------

def test_matrix_to_histogram_places_element_i_j_in_bin_i_plus_one_j_plus_one():
    # deliberately asymmetric: a transposition would pass a symmetric matrix unnoticed
    matrix = [
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0],
    ]
    labels = ["a", "b", "c"]

    h = _matrix_to_histogram(matrix, "h2_test", "a test matrix", labels)

    assert h.GetName() == "h2_test"
    assert h.GetTitle() == "a test matrix"
    for i in range(3):
        for j in range(3):
            assert h.GetBinContent(h.GetBin(i + 1, j + 1)) == matrix[i][j], (i, j)


def test_matrix_to_histogram_labels_both_axes_and_detaches():
    labels = ["a", "b", "c"]
    h = _matrix_to_histogram([[0.0] * 3 for _ in range(3)], "h2_test", "t", labels)

    for i, label in enumerate(labels):
        assert h.GetXaxis().GetBinLabel(i + 1) == label
        assert h.GetYaxis().GetBinLabel(i + 1) == label
    assert not h.GetDirectory()


# ---------------------------------------------------------------------------
# _find_signal_yield
# ---------------------------------------------------------------------------

def test_find_signal_yield_returns_the_matching_parameter():
    parameters = [("nbkg", 100.0, 10.0), ("nsig_myModel", 42.0, 6.0), ("p2", 1.0, 0.1)]
    assert _find_signal_yield(parameters) == (42.0, 6.0)


def test_find_signal_yield_returns_none_when_no_parameter_matches():
    parameters = [("nbkg", 100.0, 10.0), ("p2", 1.0, 0.1)]
    assert _find_signal_yield(parameters) == (None, None)


def test_find_signal_yield_last_substring_match_wins_issue53():
    """Substring match, and the loop does not stop at the first hit: two parameters whose names
    both contain 'nsig' both match and the last one silently wins. KNOWN_ISSUES issue 53."""
    parameters = [("nsig_myModel", 42.0, 6.0), ("nsig_scale", 0.5, 0.05)]
    assert _find_signal_yield(parameters) == (0.5, 0.05)


def test_find_signal_yield_on_the_background_only_fixture_is_none():
    parameters, _, _ = _read_fit_result(J100)
    assert _find_signal_yield(parameters) == (None, None)


# ---------------------------------------------------------------------------
# Extract() as coordinator
# ---------------------------------------------------------------------------

def test_extract_sets_all_five_attributes_from_the_fixture():
    fpe = FitParameterExtractor(wsfile=J100)

    fpe.Extract()

    assert fpe.h1_params.GetName() == "postfit_params"
    assert fpe.h1_params.GetNbinsX() == 6
    assert fpe.h2_cov.GetName() == "h2_cov"
    assert fpe.h2_cor.GetName() == "h2_cor"
    assert fpe.h2_cov.GetNbinsX() == 6 and fpe.h2_cov.GetNbinsY() == 6
    # background-only fit: no nsig parameter exists, so both stay None
    assert fpe.nsig is None and fpe.nsigErr is None

    for i, (name, value, error) in enumerate(EXPECTED_PARAMETERS):
        assert fpe.h1_params.GetXaxis().GetBinLabel(i + 1) == name
        assert fpe.h1_params.GetBinContent(i + 1) == pytest.approx(value, rel=1e-11)
        assert fpe.h1_params.GetBinError(i + 1) == pytest.approx(error, rel=1e-11)


# ---------------------------------------------------------------------------
# WriteRoot
# ---------------------------------------------------------------------------

def test_writeroot_writes_the_three_histograms_and_extracts_exactly_once(tmp_path):
    fpe = FitParameterExtractor(wsfile=J100)
    calls = _count_extract_calls(fpe)

    outfile = str(tmp_path / "FitParameters.root")
    fpe.WriteRoot(outfile)

    assert len(calls) == 1

    f = ROOT.TFile(outfile, "READ")
    try:
        assert f.Get("postfit_params").GetNbinsX() == 6
        assert f.Get("h2_cov").GetNbinsX() == 6
        assert f.Get("h2_cor").GetNbinsX() == 6
        assert f.Get("postfit_params").GetXaxis().GetBinLabel(1) == "nbkg"
    finally:
        f.Close()


# ---------------------------------------------------------------------------
# The five lazy accessors - KNOWN_ISSUES issue 53
# ---------------------------------------------------------------------------

def _count_extract_calls(fpe):
    """Wrap an extractor's Extract() so the tests can count how often it really runs."""
    calls = []
    real = fpe.Extract

    def counting():
        calls.append(1)
        real()

    fpe.Extract = counting
    return calls


@pytest.mark.parametrize("accessor", ["GetH1Params", "GetH2Cov", "GetH2Cor"])
def test_histogram_accessors_extract_once_then_cache(accessor):
    fpe = FitParameterExtractor(wsfile=J100)
    calls = _count_extract_calls(fpe)

    first = getattr(fpe, accessor)()
    second = getattr(fpe, accessor)()

    assert first is second
    assert len(calls) == 1  # a truthy cache is not re-extracted


@pytest.mark.parametrize("accessor", ["GetNsig", "GetNsigErr"])
def test_yield_accessors_re_extract_on_every_call_when_the_value_is_falsy_issue53(accessor):
    """The J100 fit is background-only, so no parameter contains 'nsig' and the cached value
    stays None - which is falsy, so `if not self.nsig` re-opens the fit-result file and re-runs
    the whole extraction on every single call. KNOWN_ISSUES issue 53, pinned not fixed."""
    fpe = FitParameterExtractor(wsfile=J100)
    calls = _count_extract_calls(fpe)

    assert getattr(fpe, accessor)() is None
    assert getattr(fpe, accessor)() is None

    assert len(calls) == 2


def test_get_nsig_re_extracts_for_a_genuine_zero_yield_issue53():
    """The same falsiness test, for the case that would actually reach a physicist: a fitted
    signal yield of exactly 0.0 is indistinguishable from 'not extracted yet'."""
    fpe = FitParameterExtractor(wsfile=J100)
    fpe.nsig = 0.0
    calls = _count_extract_calls(fpe)

    fpe.GetNsig()

    assert len(calls) == 1
