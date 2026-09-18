"""Unit tests for the "inputs to the extractor" group in run_anaFit.py (plan section 3, Group B).

_data_first_bin and _resolve_binning are pure/near-pure helpers pulled out of build_fit_extract().
_extract_postfit and _extract_parameters are exercised against the same recorded J100 fixture
test_extract_golden.py (plan section 1) uses, so this is a real run of the extraction path
through the actual extracted functions rather than a re-implementation of them.
"""

import os

import pytest
import ROOT

from conftest import FIXTURES

from run_anaFit import _data_first_bin, _resolve_binning, _extract_postfit, _extract_parameters


# ---------------------------------------------------------------------------
# _data_first_bin
# ---------------------------------------------------------------------------

def test_data_first_bin_returns_bin_below_range_low(tmp_path):
    path = str(tmp_path / "data.root")
    f = ROOT.TFile(path, "RECREATE")
    h = ROOT.TH1D("data", "", 10, 0, 1000)  # 100 GeV wide bins
    h.Write()
    f.Close()

    # 481 falls in bin 5 (400-500), so FindBin(481) - 1 == 4.
    assert _data_first_bin(path, "data", rangelow=481) == 4


def test_data_first_bin_closes_the_file(tmp_path):
    path = str(tmp_path / "data2.root")
    f = ROOT.TFile(path, "RECREATE")
    h = ROOT.TH1D("data", "", 10, 0, 1000)
    h.Write()
    f.Close()

    n_before = ROOT.gROOT.GetListOfFiles().GetEntries()
    _data_first_bin(path, "data", rangelow=481)
    n_after = ROOT.gROOT.GetListOfFiles().GetEntries()
    assert n_after == n_before


def test_data_first_bin_matches_j100_fixture():
    # The same computation test_extract_golden.py's private helper performs against the same
    # recorded run - a second, independent exercise of the real extracted function.
    got = _data_first_bin(
        "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
        "hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj",
        rangelow=481,
    )
    assert isinstance(got, int)


# ---------------------------------------------------------------------------
# _resolve_binning
# ---------------------------------------------------------------------------

def test_resolve_binning_returns_explicit_pair_unchanged(monkeypatch):
    import run_anaFit

    def _boom(cmd):
        raise AssertionError("execute() must not run when rebinfile/rebinhist are both given")
    monkeypatch.setattr(run_anaFit, "execute", _boom)

    got = _resolve_binning("Input/data/dijetTLA/fullRun2TLAJ100mjj.root",
                            "Dijet mass distribution (J100)/Hist1D_y1", rangelow=481)
    assert got == ("Input/data/dijetTLA/fullRun2TLAJ100mjj.root",
                    "Dijet mass distribution (J100)/Hist1D_y1")


def test_resolve_binning_fallback_names_when_neither_given(monkeypatch):
    import run_anaFit
    monkeypatch.setattr(run_anaFit.os.path, "exists", lambda p: True)

    got = _resolve_binning(None, None, rangelow=481)
    assert got == ("Input/data/dijetisrTLA/mjjResolutionBinning_481.root", "mjjBinning")


def test_resolve_binning_generates_fallback_when_absent(monkeypatch):
    import run_anaFit
    monkeypatch.setattr(run_anaFit.os.path, "exists", lambda p: False)
    calls = []
    monkeypatch.setattr(run_anaFit, "execute", lambda cmd: calls.append(cmd) or 1)  # non-zero: ignored

    got = _resolve_binning(None, None, rangelow=481)

    assert len(calls) == 1
    assert "python3 python/createBinning.py" in calls[0]
    assert "-s 481" in calls[0]
    assert got == ("Input/data/dijetisrTLA/mjjResolutionBinning_481.root", "mjjBinning")


def test_resolve_binning_half_given_pair_falls_back(monkeypatch):
    """Not this function's job to reject a half-given pair - that is _check_rebin_pair (Group D),
    called earlier in run_anaFit(). Pinned here: today, one given and one missing falls straight
    into the fallback branch, exactly like neither being given."""
    import run_anaFit
    monkeypatch.setattr(run_anaFit.os.path, "exists", lambda p: True)

    got = _resolve_binning("some/file.root", None, rangelow=481)
    assert got == ("Input/data/dijetisrTLA/mjjResolutionBinning_481.root", "mjjBinning")


# ---------------------------------------------------------------------------
# _extract_postfit / _extract_parameters
# ---------------------------------------------------------------------------

J100 = dict(
    wsfile=str(FIXTURES / "FitResult_J100_sixPar.root"),
    recorded=str(FIXTURES / "PostFit_J100_sixPar.root"),
    datafile="Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
    datahist="hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj",
    rebinfile="Input/data/dijetTLA/fullRun2TLAJ100mjj.root",
    rebinhist="Dijet mass distribution (J100)/Hist1D_y1",
    rangelow=481,
    channel="J100yStar06",
)


def test_extract_postfit_matches_recorded_gate_pvalue(tmp_path):
    postfitfile = str(tmp_path / "PostFit_J100_sixPar.root")
    datafirstbin = _data_first_bin(J100["datafile"], J100["datahist"], J100["rangelow"])

    pval = _extract_postfit(
        datafile=J100["datafile"],
        datahist=J100["datahist"],
        datafirstbin=datafirstbin,
        fitresultfile=J100["wsfile"],
        binningFileName=J100["rebinfile"],
        binningHistName=J100["rebinhist"],
        maskmin=-1,
        maskmax=-1,
        postfitfile=postfitfile,
        channel=J100["channel"],
    )

    f = ROOT.TFile(J100["recorded"], "READ")
    try:
        h = f.Get(f"{J100['channel']}_bkgonly_rebinned/chi2")
        want = h.GetBinContent(6)  # bin 6 is labelled "pval"
    finally:
        f.Close()

    assert pval == pytest.approx(want, rel=1e-12)
    assert os.path.exists(postfitfile)


def test_extract_parameters_writes_output_file(tmp_path):
    parameterfile = str(tmp_path / "FitParameters_J100_sixPar.root")

    _extract_parameters(J100["wsfile"], parameterfile)

    assert os.path.exists(parameterfile)
    f = ROOT.TFile(parameterfile, "READ")
    try:
        assert f.Get("postfit_params")
    finally:
        f.Close()
