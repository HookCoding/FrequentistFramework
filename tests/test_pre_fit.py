from __future__ import annotations

import array
import math
import random
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_DATAFILE = _REPO_ROOT / "Input" / "data" / "dijetTLA" / "mjj_spectra_J100_dataAll.root"
_FIXTURE_DATAHIST = "hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj"

# python/PreFit.py does `import ROOT` at module scope, unconditionally -
# like Chunk 15's ExtractFitParameters.py and Chunk 16's
# ExtractPostfitFromWS.py, this file's imports are not deferred.
# PreFitter.Fit() needs a real ROOT TH1/TF1/TStopwatch to do anything
# meaningful, so the two Fit()-level tests below run as real-ROOT
# subprocess snippets, the same probe pattern
# test_plot_post_fit.py/test_extract_fit_parameters.py/
# test_extract_postfit_from_ws.py already established. Unlike those two
# chunks' extractor classes, though, Chunk 17's two new private helpers
# (_build_candidate_functions()/_select_best_parameter_sets()) *are*
# testable against a fully-stubbed sys.modules["ROOT"] instead - see the
# fast, ROOT-stubbed tests near the bottom of this file for why.
#
# Fixture used, read directly from run_templates.py:86-96 and
# scripts/run_anaFit_J100.sh: the already-committed
# mjj_spectra_J100_dataAll.root as datafile, with the same datahist
# path production uses - no synthetic fixture needed, the same low
# fixture-sourcing risk Chunks 15/16 had.
#
# This file has zero existing test coverage of its own real behavior
# anywhere today - the only existing test
# (tests/test_run_templates.py::_install_fake_prefitter) fakes the
# whole PreFitter class to test run_templates.py's caller logic
# instead. This is PreFitter's first-ever direct test.
#
# Step A deliberately scales nPars/nRetries1/nRetries2 down from
# run_templates.py's real production values (nPars up to 10,
# nRetries1=2000*nPars, nRetries2=2*nPars) purely for test speed - real
# data, real ROOT TH1::Fit, real seed=42 determinism, just a smaller
# sample/retry count than production uses. This is a
# characterization-strategy choice distinct from Chunk 13's need for a
# wholly synthetic fixture (this fixture is real and committed).


def _run_real_root_snippet(snippet: str) -> subprocess.CompletedProcess[str]:
    probe = f"""
repo_dir="$PWD"
source "$repo_dir/scripts/setup_buildAndFit.sh" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    echo "setup_status=$setup_status"
    exit "$setup_status"
fi

python - <<'INNER_PY'
{snippet}
INNER_PY
"""
    return subprocess.run(
        ["bash", "-lc", probe],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_snippet_ok(completed: subprocess.CompletedProcess[str]) -> None:
    assert completed.returncode == 0, (
        "real-ROOT snippet failed:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "SNIPPET_OK" in completed.stdout, completed.stdout


_CONSTRUCT_PREFITTER = f"""
import sys
sys.path.insert(0, "python")
from PreFit import PreFitter

pf = PreFitter(
    datafile={str(_FIXTURE_DATAFILE)!r},
    datahist={_FIXTURE_DATAHIST!r},
    xMin=481,
    xMax=3000,
    nPars=3,
    nRetries1=50,
    nRetries2=3,
    fitLog=True,
    seed=42,
)
"""


# --- Fit(): real ROOT, real committed fixture, scaled-down retries --------


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_fit_returns_expected_shape_and_is_deterministic_for_real_fixture() -> None:
    assert _FIXTURE_DATAFILE.exists(), f"expected committed fixture missing: {_FIXTURE_DATAFILE}"

    snippet = f"""
{_CONSTRUCT_PREFITTER}

# plain manual tolerance, not pytest.approx() - pytest is not
# importable inside this bare subprocess snippet.
def approx(actual, expected, tol=1e-9):
    return abs(actual - expected) <= tol * max(1.0, abs(expected))

bestPars, nbkg = pf.Fit()

assert len(bestPars) == 3, len(bestPars)
assert approx(nbkg, 765243975.0)
assert approx(bestPars[0], 1.0327120331875124)
assert approx(bestPars[1], 9.191623586537986)
assert approx(bestPars[2], 4.8714483361038035)

# determinism: a second PreFitter with the same seed=42 on the same
# fixture reproduces the identical result - not a physics-correctness
# check, only a determinism check.
{_CONSTRUCT_PREFITTER}
bestPars2, nbkg2 = pf.Fit()
assert list(bestPars) == list(bestPars2)
assert nbkg == nbkg2

# Console-output characterization. Chunk 17.B changed Fit()'s own stdout
# twice and no test noticed: it started the fitting stopwatch after the
# "Starting fit" banner instead of before it, and it added a
# "==================" divider the pre-refactor code never printed. Both
# were caught by review and by hand-diffing against git history - this
# file's assertions above only ever covered the return value, so any
# print-level change was invisible to the gate. This pins the invariant
# the divider broke: "Finished sampling" is immediately preceded by one
# divider and immediately followed by the "Starting fit" banner, with
# nothing in between. (TStopwatch::Print writes from C++, so it never
# reaches this Python-level buffer.)
import contextlib
import io

{_CONSTRUCT_PREFITTER}
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    pf.Fit()

printed = [line for line in captured.getvalue().splitlines() if line.strip()]
finished = printed.index("Finished sampling")
assert printed[finished - 1] == "==================", printed[finished - 2 : finished + 2]
assert printed[finished + 1] == "Starting fit of 3 best samples", printed[finished : finished + 3]

print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


# --- parRangeLow/parRangeHigh 7-vs-10-element fragility: documented, ------
# --- not fixed --------------------------------------------------------
#
# PreFitter.__init__'s parRangeLow/parRangeHigh default to 7-element
# lists, but nPars can be requested up to 10 (run_templates.py already
# builds its own longer lists when it needs more parameters - see
# run_templates.py:62-63). Constructing a PreFitter with nPars=8 and
# the default ranges currently raises IndexError partway through
# Fit()'s first RandomizeParameters() call. Pinned down exactly as-is,
# matching Chunk 5's own precedent for characterizing rather than
# silently closing a pre-existing gap.


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_fit_raises_indexerror_for_npars_above_seven_with_default_ranges() -> None:
    assert _FIXTURE_DATAFILE.exists(), f"expected committed fixture missing: {_FIXTURE_DATAFILE}"

    snippet = f"""
import sys
sys.path.insert(0, "python")
from PreFit import PreFitter

pf = PreFitter(
    datafile={str(_FIXTURE_DATAFILE)!r},
    datahist={_FIXTURE_DATAHIST!r},
    xMin=481,
    xMax=3000,
    nPars=8,
    nRetries1=1,
    nRetries2=1,
    fitLog=True,
    seed=42,
)

try:
    pf.Fit()
    raise AssertionError("expected IndexError for nPars=8 with default 7-element ranges")
except IndexError:
    pass

print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


# --- _build_candidate_functions()/_select_best_parameter_sets(): ----------
# --- fast, ROOT-stubbed unit tests -----------------------------------------
#
# This repository's first fast, ROOT-stubbed unit test of any piece of
# PreFit.py's own logic. Both new private methods are exercised against
# a fully-stubbed sys.modules["ROOT"] instead of real ROOT - achievable
# here (unlike Chunk 15/16's extractor classes) because
# _select_best_parameter_sets() takes an already-built candidate
# function and a plain scoring callable rather than reaching into a
# live ROOT histogram itself; only PreFitter.__init__'s own ROOT touches
# (Math.MinimizerOptions, TRandom3, gROOT.ProcessLine) and
# _select_best_parameter_sets' own TMath.Exp/TMath.Log/TStopwatch calls
# need stubbing.


class _FakeTRandom3:
    """Deterministic stand-in for ROOT.TRandom3: wraps Python's own
    seeded random.Random so repeated construction with the same seed
    reproduces the same Uniform() draw sequence, without touching real
    ROOT."""

    def __init__(self, seed):
        self._rng = random.Random(seed)

    def Uniform(self, lo, hi):
        return self._rng.uniform(lo, hi)


class _FakeTStopwatch:
    def Start(self):
        pass

    def Stop(self):
        pass

    def Print(self):
        pass

    def Reset(self):
        pass


class _FakeTMath:
    Exp = staticmethod(math.exp)
    Log = staticmethod(math.log)


class _FakeConstructedTF1:
    """Records exactly what PreFitter._build_candidate_functions() passed
    to ROOT.TF1(name, formula, xMin, xMax) - used only for that method's
    own test, so real ROOT.TF1 construction is never needed."""

    def __init__(self, name, formula, xMin, xMax):
        self.name = name
        self.formula = formula
        self.xMin = xMin
        self.xMax = xMax


def _make_stubbed_prefitter(monkeypatch: pytest.MonkeyPatch, tf1_cls=None, **kwargs):
    fake_root_module = ModuleType("ROOT")
    fake_root_module.TRandom3 = _FakeTRandom3
    fake_root_module.TStopwatch = _FakeTStopwatch
    fake_root_module.TMath = _FakeTMath

    class _FakeMinimizerOptions:
        @staticmethod
        def SetDefaultMaxFunctionCalls(_n):
            pass

    class _FakeMath:
        MinimizerOptions = _FakeMinimizerOptions

    fake_root_module.Math = _FakeMath

    class _FakeGROOT:
        @staticmethod
        def ProcessLine(_s):
            pass

    fake_root_module.gROOT = _FakeGROOT
    if tf1_cls is not None:
        fake_root_module.TF1 = tf1_cls

    monkeypatch.setitem(sys.modules, "ROOT", fake_root_module)

    from python import PreFit as pre_fit

    # `python.PreFit` stays cached in sys.modules across tests once
    # imported once, so a later `from python import PreFit` here does
    # not re-run its `import ROOT` line - only rebinding the module's
    # own `ROOT` global directly (not just sys.modules["ROOT"]) makes
    # each call see its own fresh fake, regardless of test order.
    monkeypatch.setattr(pre_fit, "ROOT", fake_root_module)

    defaults = dict(
        datafile="unused",
        datahist="unused",
        xMin=481,
        xMax=3000,
        seed=42,
    )
    defaults.update(kwargs)
    return pre_fit.PreFitter(**defaults)


def test_build_candidate_functions_returns_ten_linear_and_ten_log_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pf = _make_stubbed_prefitter(monkeypatch, tf1_cls=_FakeConstructedTF1, xMin=481, xMax=3000)

    NParFunction, LogNParFunction = pf._build_candidate_functions()

    assert set(NParFunction.keys()) == set(range(1, 11))
    assert set(LogNParFunction.keys()) == set(range(1, 11))

    for n in range(1, 11):
        linear = NParFunction[n]
        assert linear.name == f"{n}ParFunction"
        assert linear.xMin == 481
        assert linear.xMax == 3000

        log = LogNParFunction[n]
        assert log.name == f"Log{n}ParFunction"
        assert log.xMin == 481
        assert log.xMax == 3000

    # Spot-check exact formula text only for the simplest (n=1) and most
    # complex (n=10) candidates in each family - the loop above already
    # confirms every candidate's name/xMin/xMax for n=1..10. The middle
    # forms' (n=2..9) formula text is preserved verbatim from today's
    # Fit(), not retyped, and not independently re-verified here.
    # Separately: the real-ROOT test above only ever exercises one of
    # these twenty forms end to end - Log3ParFunction, since it
    # constructs a PreFitter with fitLog=True, nPars=3 (Fit() selects
    # LogNParFunction[nPars] when fitLog is set, never NParFunction[nPars]
    # in the same run) - not a stand-in for fitting every form.
    assert NParFunction[1].formula == "[0]"
    assert (
        NParFunction[10].formula
        == "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)  + [7]*TMath::Power(TMath::Log(x/13000.),5.) + [8]*TMath::Power(TMath::Log(x/13000.),6.) + [9]*TMath::Power(TMath::Log(x/13000.),7.)  ))"  # noqa: E501
    )
    assert LogNParFunction[1].formula == "TMath::Log([0])"
    assert (
        LogNParFunction[10].formula
        == "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)- [7]*TMath::Power(TMath::Log(x/13000.),6.)- [8]*TMath::Power(TMath::Log(x/13000.),7.) - [9]*TMath::Power(TMath::Log(x/13000.),8.) "  # noqa: E501
    )


class _FakeCandidateTF1:
    """Minimal stand-in for a ROOT TF1 candidate, supporting exactly the
    interface _select_best_parameter_sets()/RandomizeParameters() call:
    GetNpar/SetParameter/SetParLimits/GetParameters/Integral."""

    def __init__(self, npar):
        self._npar = npar
        self._params = [0.0] * npar

    def GetNpar(self):
        return self._npar

    def SetParameter(self, i, value):
        if 0 <= i < self._npar:
            self._params[i] = value

    def SetParLimits(self, _i, _lo, _hi):
        pass

    def GetParameters(self, buf):
        for i in range(self._npar):
            buf[i] = self._params[i]

    def Integral(self, _xMin, _xMax, _tol=1e-10):
        # Depends on the current parameters, as ROOT's real
        # TF1::Integral does. This matters: _select_best_parameter_sets()
        # calls Integral() while the parameters are still the freshly
        # randomized ones, and *then* overwrites parameters 0-9 with
        # fixed values (p0, 80, 10, 10, 2, 0, ...). p0 - computed from
        # this return value - is therefore the only channel through
        # which each trial's randomization reaches the score at all. A
        # fake returning a constant here makes every trial score
        # identically, which silently reduces the ranking assertions
        # below to "the list is sorted", true of any five duplicates.
        return 1.0 + sum(abs(p) for p in self._params)


def _score_by_summed_abs_params(fitFunction) -> float:
    """Plain, ROOT-free scoring callable standing in for the real
    h.Chisquare(fitFunction) closure Fit() actually passes - varies with
    fitFunction's current (randomized) parameters, which is all
    _select_best_parameter_sets() requires from its score_fn."""
    npar = fitFunction.GetNpar()
    buf = array.array("d", [0.0] * npar)
    fitFunction.GetParameters(buf)
    return sum(abs(x) for x in buf)


def test_select_best_parameter_sets_ranks_and_bounds_output_and_is_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    npar = 3
    nRetries1 = 30
    nRetries2 = 5

    def _run():
        # every score this run hands out, in trial order, so the ranking
        # below is checked against the real population rather than only
        # against itself
        observed_scores: list[float] = []

        def _scoring_spy(fitFunction):
            score = _score_by_summed_abs_params(fitFunction)
            observed_scores.append(score)
            return score

        pf = _make_stubbed_prefitter(
            monkeypatch,
            xMin=481,
            xMax=3000,
            parRangeLow=[1, -30, -30],
            parRangeHigh=[1, 30, 30],
        )
        fitFunction = _FakeCandidateTF1(npar)
        return (
            pf._select_best_parameter_sets(
                fitFunction,
                integral=1.0,
                score_fn=_scoring_spy,
                nRetries1=nRetries1,
                nRetries2=nRetries2,
            ),
            observed_scores,
        )

    result, observed_scores = _run()

    # Guard the test's own premise first: if the trials do not actually
    # score differently, every ranking assertion below is vacuous - an
    # implementation keeping any nRetries2 entries would pass. (They
    # were in fact all identical until _FakeCandidateTF1.Integral() was
    # made parameter-dependent; see the comment there.)
    assert len(observed_scores) == nRetries1
    assert len(set(observed_scores)) == nRetries1, (
        "every trial scored identically, so this test cannot distinguish a real "
        f"ranking from any {nRetries2} duplicates: {sorted(set(observed_scores))}"
    )

    # nRetries1 (30) comfortably exceeds nRetries2 (5), so the initial
    # (inf, []) sentinel is guaranteed to be evicted by the end - the
    # returned list is exactly nRetries2 long, every entry finite, and
    # holds precisely the nRetries2 smallest scores of all nRetries1
    # trials, in ascending order.
    assert len(result) == nRetries2
    chi2_values = [entry[0] for entry in result]
    assert all(math.isfinite(c) for c in chi2_values)
    assert chi2_values == sorted(observed_scores)[:nRetries2]

    # Each retained parameter array really belongs to its own recorded
    # chi2, not to some other trial: this scorer returns
    # |p0| + |80| + |10|, and Fit()'s sampling loop overwrites
    # parameters 1 and 2 with exactly 80 and 10 before scoring, so
    # pars[0] must be chi2 - 90 for every entry. Five distinct arrays
    # therefore also confirm p0 - the only parameter that varies at all
    # here - was captured per trial rather than shared.
    for chi2, pars in result:
        assert len(pars) == npar
        assert pars[0] == pytest.approx(chi2 - 90.0, abs=1e-12)
        assert pars[1] == 80
        assert pars[2] == 10
    assert len({tuple(pars) for _chi2, pars in result}) == nRetries2

    # determinism: an independent PreFitter/candidate pair built with the
    # same seed reproduces an identical ranked result.
    result2, observed_scores2 = _run()
    assert [c for c, _ in result] == [c for c, _ in result2]
    assert [list(p) for _, p in result] == [list(p) for _, p in result2]
    assert observed_scores == observed_scores2


def test_select_best_parameter_sets_keeps_the_exact_minima_of_a_scripted_score_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The sharpest available check on the array/bisect bookkeeping
    # Chunk 17.B extracted: hand _select_best_parameter_sets() a known,
    # deliberately unsorted score sequence - with the global minimum
    # last and the maximum first, so any "keep the first N" or "keep the
    # last N" implementation is ruled out - and assert it returns
    # exactly the nRetries2 smallest, ascending. Unlike the test above,
    # this asserts against values chosen in advance rather than against
    # whatever the seeded randomization happened to produce.
    nRetries2 = 4
    scripted_scores = [
        99.0,
        12.0,
        45.5,
        3.0,
        45.4,
        8.0,
        61.0,
        3.5,
        70.0,
        12.5,
        30.0,
        1.0,
    ]
    expected = sorted(scripted_scores)[:nRetries2]
    assert expected == [1.0, 3.0, 3.5, 8.0]
    # sanity: the population really is unsorted at both ends
    assert scripted_scores[0] == max(scripted_scores)
    assert scripted_scores[-1] == min(scripted_scores)

    remaining = list(scripted_scores)

    def _scripted_score(_fitFunction) -> float:
        return remaining.pop(0)

    pf = _make_stubbed_prefitter(
        monkeypatch,
        xMin=481,
        xMax=3000,
        parRangeLow=[1, -30, -30],
        parRangeHigh=[1, 30, 30],
    )

    result = pf._select_best_parameter_sets(
        _FakeCandidateTF1(3),
        integral=1.0,
        score_fn=_scripted_score,
        nRetries1=len(scripted_scores),
        nRetries2=nRetries2,
    )

    assert not remaining, "score_fn was not called exactly nRetries1 times"
    assert [chi2 for chi2, _pars in result] == expected
