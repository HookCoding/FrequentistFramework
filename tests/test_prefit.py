"""Unit tests for python/PreFit.py's split (decomposition plan section 4).

PreFitter.Fit() used to be one 131-line method. It is now a coordinator over eight private
helpers, seven of them free functions (they never touched `self`) and one,
`_find_best_parameter_sets`, kept as a method because it calls the existing `RandomizeParameters`
bound method. `_build_candidate_functions` keeps its twenty formula strings as literals rather
than generating them from a table (the plan left this as a judgement call): generating them saves
duplication but risks a generator bug corrupting one of twenty near-identical physics formulas,
and this is a straight cut-and-paste of the original text, so literal is the lower-risk choice.

KNOWN_ISSUES issue 50 correction: the plan, written before this section was implemented, claimed
`_find_best_parameter_sets`'s sampling loop is inert and that two different seeds would return
identical candidates. Measured, both claims are wrong. `RandomizeParameters()`'s draws for
parameters 1-9 are thrown away every iteration by the ten literal `SetParameter` calls that
follow it, but parameter 0 is computed from `fit_function.Integral()`, which is evaluated against
the *freshly randomized* parameters before they are overwritten - so p0 does vary, and it varies
differently for different seeds. The tests below pin the measured behaviour (p0 varies, p1-p9 are
constant at their literal values, different seeds give different results), not the plan's
original, incorrect prediction.
"""

import array
import math

import pytest
import ROOT

from PreFit import (
    PreFitter,
    _configure_root,
    _load_histogram,
    _prepare_histogram,
    _build_candidate_functions,
    _select_fit_function,
    _fit_best_candidates,
    _report_fit_result,
)

from roothelpers import make_hist


# ---------------------------------------------------------------------------
# __init__ / _configure_root
# ---------------------------------------------------------------------------

def test_constructing_a_prefitter_does_not_touch_root_globals():
    before_level = ROOT.gErrorIgnoreLevel
    before_calls = ROOT.Math.MinimizerOptions.DefaultMaxFunctionCalls()

    PreFitter(datafile="unused.root", datahist="unused", xMin=0, xMax=1)

    assert ROOT.gErrorIgnoreLevel == before_level
    assert ROOT.Math.MinimizerOptions.DefaultMaxFunctionCalls() == before_calls


def test_configure_root_sets_error_ignore_level_and_max_function_calls():
    ROOT.gErrorIgnoreLevel = 0
    ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(1)

    _configure_root()

    assert ROOT.gErrorIgnoreLevel == 6001
    assert ROOT.Math.MinimizerOptions.DefaultMaxFunctionCalls() == 50000


# ---------------------------------------------------------------------------
# _load_histogram
# ---------------------------------------------------------------------------

def test_load_histogram_opens_file_read_and_gets_named_histogram(tmp_path):
    path = tmp_path / "data.root"
    out = ROOT.TFile(str(path), "RECREATE")
    make_hist("src", [0, 1, 2, 3], [10, 20, 30]).Write("mjj")
    out.Close()

    f, h = _load_histogram(str(path), "mjj")
    try:
        assert not f.IsZombie()
        assert h.GetNbinsX() == 3
        assert h.GetBinContent(2) == 20
    finally:
        f.Close()


# ---------------------------------------------------------------------------
# _prepare_histogram
# ---------------------------------------------------------------------------

def test_prepare_histogram_fitlog_false_uses_fit_range_for_nbkg_not_whole_histogram():
    h = make_hist("h1", [0, 1, 2, 3, 4], [5, 10, 15, 20])
    expected_nbkg = h.Integral(h.GetXaxis().FindBin(1), h.GetXaxis().FindBin(3))
    expected_whole = h.Integral()
    assert expected_nbkg != expected_whole

    nbkg, integral = _prepare_histogram(h, xMin=1, xMax=3, fitLog=False)

    assert nbkg == expected_nbkg
    assert integral == expected_whole
    assert h.GetBinContent(1) == 5
    assert h.GetBinContent(4) == 20


def test_prepare_histogram_fitlog_true_transforms_positive_bins_error_divided_by_original_content():
    h = make_hist("h2", [0, 1, 2, 3], [0, 10, 20], errors=[0, 2, 4])
    bin_low = h.GetXaxis().FindBin(0)
    bin_high = h.GetXaxis().FindBin(2)
    expected_nbkg = h.Integral(bin_low, bin_high)  # computed before any transform

    nbkg, integral = _prepare_histogram(h, xMin=0, xMax=2, fitLog=True)

    assert nbkg == expected_nbkg
    # zero-valued bin is left alone
    assert h.GetBinContent(1) == 0
    assert h.GetBinError(1) == 0
    # error divided by the ORIGINAL content, then content replaced by its log - in that order
    assert h.GetBinError(2) == pytest.approx(2.0 / 10.0)
    assert h.GetBinContent(2) == pytest.approx(math.log(10))
    assert h.GetBinError(3) == pytest.approx(4.0 / 20.0)
    assert h.GetBinContent(3) == pytest.approx(math.log(20))
    # integral is taken AFTER the transform, over the whole histogram
    assert integral == pytest.approx(0 + math.log(10) + math.log(20))


# ---------------------------------------------------------------------------
# _build_candidate_functions
# ---------------------------------------------------------------------------

def test_build_candidate_functions_has_keys_1_to_10_with_matching_range_and_npar():
    normal, log_ = _build_candidate_functions(100, 500)

    for n in range(1, 11):
        assert normal[n].GetName() == "%dParFunction" % n
        assert log_[n].GetName() == "Log%dParFunction" % n
        assert normal[n].GetNpar() == n
        assert log_[n].GetNpar() == n
        assert (normal[n].GetXmin(), normal[n].GetXmax()) == (100.0, 500.0)
        assert (log_[n].GetXmin(), log_[n].GetXmax()) == (100.0, 500.0)


def test_build_candidate_functions_formula_text_matches_original_six_par():
    normal, log_ = _build_candidate_functions(0, 1)

    assert normal[6].GetTitle() == (
        "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.)"
        " + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.)))"
    )
    assert log_[6].GetTitle() == (
        "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.)"
        " - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.)"
        " - [5]*TMath::Power(TMath::Log(x/13000.),4.)"
    )
    # and the one-parameter edge, where both collections collapse to a single term
    assert normal[1].GetTitle() == "[0]"
    assert log_[1].GetTitle() == "TMath::Log([0])"


# ---------------------------------------------------------------------------
# _select_fit_function
# ---------------------------------------------------------------------------

def test_select_fit_function_picks_log_dict_when_fitlog_true():
    normal, log_ = _build_candidate_functions(0, 100)
    chosen = _select_fit_function(normal, log_, True, 4, [0, 0, 0, 0], [1, 1, 1, 1])
    assert chosen is log_[4]


def test_select_fit_function_picks_normal_dict_when_fitlog_false():
    normal, log_ = _build_candidate_functions(0, 100)
    chosen = _select_fit_function(normal, log_, False, 3, [0, 0, 0], [1, 1, 1])
    assert chosen is normal[3]


def test_select_fit_function_applies_parameter_limits_to_every_active_parameter():
    import ctypes

    normal, log_ = _build_candidate_functions(0, 100)
    low = [1.0, -30.0, -10.0]
    high = [2.0, 30.0, 10.0]

    chosen = _select_fit_function(normal, log_, False, 3, low, high)

    for i in range(3):
        lo, hi = ctypes.c_double(), ctypes.c_double()
        chosen.GetParLimits(i, lo, hi)
        assert lo.value == pytest.approx(low[i])
        assert hi.value == pytest.approx(high[i])


# ---------------------------------------------------------------------------
# _find_best_parameter_sets
# ---------------------------------------------------------------------------

def test_find_best_parameter_sets_keeps_the_n_lowest_scores_in_order():
    # xMin/xMax mirror a realistic dijet-mass domain (hundreds to thousands of GeV), the same
    # order of magnitude as the real drivers use. Every formula divides x by 13000 (13 TeV), so a
    # synthetic domain near x=0 makes fit_function.Integral() underflow to exactly 0 and
    # p0 = Exp(integral/0) raises ZeroDivisionError before score_function is ever reached.
    pf = PreFitter(datafile="unused", datahist="unused", xMin=481, xMax=3000, nPars=6,
                    parRangeLow=[1, -30, -30, -10, -1, -1], parRangeHigh=[1, 30, 30, 10, 1, 1],
                    seed=1)
    _configure_root()
    normal, log_ = _build_candidate_functions(481, 3000)
    fit_function = _select_fit_function(normal, log_, False, 6, pf.parRangeLow, pf.parRangeHigh)

    scores = [5.0, 3.0, 9.0, 1.0, 7.0, 2.0, 8.0]
    calls = iter(scores)
    score_function = lambda f: next(calls)

    result = pf._find_best_parameter_sets(fit_function, integral=1.0, score_function=score_function,
                                           nRetries1=len(scores), nRetries2=3, fitLog=False,
                                           xMin=481, xMax=3000)

    assert [s for s, _ in result] == [1.0, 2.0, 3.0]
    with pytest.raises(StopIteration):
        next(calls)  # every one of the nRetries1 scores was consumed, and no more
    assert result[0][1] is not result[1][1]  # independent parameter copies, not shared state


def test_find_best_parameter_sets_sentinel_survives_when_nretries1_below_nretries2():
    """Pins the sentinel behaviour: fewer draws than nRetries2 leaves (inf, []) in the result,
    exactly as the un-split Fit() does today. Not fixed here - see KNOWN_ISSUES issue 50's
    neighbourhood in the plan; this is a separate, undocumented-by-number quirk the plan itself
    flags as worth pinning rather than guarding."""
    pf = PreFitter(datafile="unused", datahist="unused", xMin=481, xMax=3000, nPars=6,
                    parRangeLow=[1, -30, -30, -10, -1, -1], parRangeHigh=[1, 30, 30, 10, 1, 1],
                    seed=1)
    _configure_root()
    normal, log_ = _build_candidate_functions(481, 3000)
    fit_function = _select_fit_function(normal, log_, False, 6, pf.parRangeLow, pf.parRangeHigh)

    scores = iter([5.0, 3.0])
    result = pf._find_best_parameter_sets(fit_function, integral=1.0,
                                           score_function=lambda f: next(scores),
                                           nRetries1=2, nRetries2=5, fitLog=False,
                                           xMin=481, xMax=3000)

    assert len(result) == 3  # the 2 real draws plus the surviving sentinel
    assert result[-1] == (float("inf"), [])


def test_find_best_parameter_sets_only_p0_varies_issue50():
    """Measured (KNOWN_ISSUES issue 50): RandomizeParameters()'s draws for parameters 1-5 never
    reach a scoring call - the five literal SetParameter calls that follow it overwrite them on
    every iteration. Only p0 varies, because it is computed from fit_function.Integral() while
    the just-randomized parameters are briefly still in place."""
    pf = PreFitter(datafile="unused", datahist="unused", xMin=481, xMax=3000, nPars=6,
                    parRangeLow=[1, -30, -30, -10, -1, -1], parRangeHigh=[1, 30, 30, 10, 1, 1],
                    seed=7)
    _configure_root()
    normal, log_ = _build_candidate_functions(481, 3000)
    fit_function = _select_fit_function(normal, log_, False, 6, pf.parRangeLow, pf.parRangeHigh)

    seen = []

    def score_function(f):
        seen.append([f.GetParameter(i) for i in range(6)])
        return float(len(seen))

    pf._find_best_parameter_sets(fit_function, integral=1.0, score_function=score_function,
                                  nRetries1=25, nRetries2=5, fitLog=False, xMin=481, xMax=3000)

    assert len(seen) == 25
    p0_values = [row[0] for row in seen]
    assert len(set(p0_values)) > 1  # p0 genuinely varies call to call

    for row in seen:
        assert row[1:] == [80.0, 10.0, 10.0, 2.0, 0.0]  # p1..p5: always the literal seeds


def test_find_best_parameter_sets_different_seeds_give_different_results_issue50():
    """The plan (written before this section existed) predicted the opposite of this: that two
    seeds would return identical candidates, because it believed the sampling loop was inert.
    Measured, that is wrong - see the module docstring and KNOWN_ISSUES issue 50."""
    edges = [481 + 250 * i for i in range(11)]  # 10 bins spanning the J100 domain, 481-3000ish
    h = make_hist("data", edges, [100 - 5 * i for i in range(10)])
    par_low = [1, -30, -30, -10, -1, -1]
    par_high = [1, 30, 30, 10, 1, 1]

    def run(seed):
        pf = PreFitter(datafile="unused", datahist="unused", xMin=481, xMax=2981, nPars=6,
                        parRangeLow=par_low, parRangeHigh=par_high, seed=seed)
        _configure_root()
        normal, log_ = _build_candidate_functions(481, 2981)
        fit_function = _select_fit_function(normal, log_, False, 6, par_low, par_high)
        return pf._find_best_parameter_sets(fit_function, integral=h.Integral(),
                                             score_function=h.Chisquare, nRetries1=200,
                                             nRetries2=5, fitLog=False, xMin=481, xMax=2981)

    result_a = run(seed=42)
    result_b = run(seed=12345)

    assert [s for s, _ in result_a] != [s for s, _ in result_b]
    assert result_a[0][1][0] != result_b[0][1][0]  # the winning p0 itself differs


# ---------------------------------------------------------------------------
# _fit_best_candidates
# ---------------------------------------------------------------------------

class _FakeFitResult:
    def __init__(self, chi2):
        self._chi2 = chi2

    def Chi2(self):
        return self._chi2


class _FakeHistogram:
    """Duck-typed histogram recording every Fit() call - the plan's own suggested style for this
    function, since the exact fit-option string matters more here than any real fit result."""

    def __init__(self, chi2_by_call):
        self._chi2_by_call = list(chi2_by_call)
        self.fit_calls = []

    def Integral(self):
        return 0.0

    def Fit(self, fit_function, option, goption, xMin, xMax):
        snapshot = [fit_function.GetParameter(i) for i in range(fit_function.GetNpar())]
        self.fit_calls.append((option, goption, xMin, xMax, snapshot))
        return _FakeFitResult(self._chi2_by_call[len(self.fit_calls) - 1])


def test_fit_best_candidates_loads_each_candidate_uses_r0qs_and_keeps_the_lowest_chi2():
    normal, log_ = _build_candidate_functions(0, 10)
    fit_function = _select_fit_function(normal, log_, False, 2, [0, 0], [10, 10])

    candidates = [
        (99.0, array.array('d', [1.0, 2.0])),
        (5.0, array.array('d', [3.0, 4.0])),
        (50.0, array.array('d', [5.0, 6.0])),
    ]
    fake_h = _FakeHistogram(chi2_by_call=[7.0, 2.0, 9.0])

    bestChi2, bestPars = _fit_best_candidates(fake_h, fit_function, candidates, nRetries2=3,
                                               xMin=0, xMax=10)

    assert len(fake_h.fit_calls) == 3
    for option, goption, xmin, xmax, _ in fake_h.fit_calls:
        assert option == "R0QS"
        assert goption == ""
        assert (xmin, xmax) == (0, 10)
    assert [snap for *_, snap in fake_h.fit_calls] == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]

    assert bestChi2 == 2.0
    assert list(bestPars) == [3.0, 4.0]


def test_fit_best_candidates_indexes_by_nretries2_not_by_len_candidates():
    """Deviates from the plan's literal _fit_best_candidates(histogram, fit_function, candidates,
    xMin, xMax) signature by keeping nRetries2 as an explicit parameter, so that a candidate list
    shorter than nRetries2 still raises IndexError exactly as the un-split Fit() does today -
    rather than silently fitting fewer candidates than were asked for. See the CHANGELOG entry for
    this section."""
    normal, log_ = _build_candidate_functions(0, 10)
    fit_function = _select_fit_function(normal, log_, False, 1, [0], [10])
    candidates = [(1.0, array.array('d', [5.0]))]
    fake_h = _FakeHistogram(chi2_by_call=[1.0])

    with pytest.raises(IndexError):
        _fit_best_candidates(fake_h, fit_function, candidates, nRetries2=3, xMin=0, xMax=10)


# ---------------------------------------------------------------------------
# _report_fit_result
# ---------------------------------------------------------------------------

def test_report_fit_result_prints_chi2_and_each_parameter(capsys):
    _report_fit_result(3.14159, [1.5, -2.25, 0.0], 3)

    out = capsys.readouterr().out
    assert "chi2 = 3.14159" in out
    assert "p1 = 1.50000000" in out
    assert "p2 = -2.25000000" in out
    assert "p3 = 0.00000000" in out


# ---------------------------------------------------------------------------
# RandomizeParameters (unchanged; previously untested)
# ---------------------------------------------------------------------------

class _FakeFunction:
    def __init__(self, npar):
        self._npar = npar
        self.set_calls = []

    def GetNpar(self):
        return self._npar

    def SetParameter(self, i, value):
        self.set_calls.append((i, value))


class _FakeRnd:
    def __init__(self, values):
        self._values = list(values)
        self.uniform_calls = []

    def Uniform(self, lo, hi):
        self.uniform_calls.append((lo, hi))
        return self._values[len(self.uniform_calls) - 1]


def test_randomize_parameters_draws_one_uniform_per_parameter_within_its_own_range():
    pf = PreFitter(datafile="unused", datahist="unused", xMin=0, xMax=1, nPars=3,
                    parRangeLow=[-1, -2, -3], parRangeHigh=[1, 2, 3], seed=1)
    pf.rnd = _FakeRnd([0.1, 0.2, 0.3])
    fn = _FakeFunction(npar=3)

    pf.RandomizeParameters(fn)

    assert pf.rnd.uniform_calls == [(-1, 1), (-2, 2), (-3, 3)]
    assert fn.set_calls == [(0, 0.1), (1, 0.2), (2, 0.3)]
