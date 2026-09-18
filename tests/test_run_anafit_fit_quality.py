"""Unit tests for the fit-quality group in run_anaFit.py (plan section 3, Group C).

report_fit_quality() used to do two jobs in one function: read status/covQual out of the fit
result file (or bail with a warning if there is none), and decide whether the covariance is good
enough to proceed. Split so the decision - pure integers, no ROOT - can be tested without a file.
"""

import pytest
import ROOT

from conftest import FIXTURES

from run_anaFit import _read_fit_quality, _require_covqual, report_fit_quality


# ---------------------------------------------------------------------------
# _read_fit_quality
# ---------------------------------------------------------------------------

def test_read_fit_quality_matches_j100_fixture():
    # Recorded fit: status=1 (MIGRAD did not fully converge), covQual=2 (forced positive-definite) -
    # the same fit report_fit_quality accepted when this run was produced (mincovqual defaults to 2).
    got = _read_fit_quality(str(FIXTURES / "FitResult_J100_sixPar.root"))
    assert got == (1, 2)


def test_read_fit_quality_returns_none_and_closes_file_when_no_fit_result(tmp_path):
    path = str(tmp_path / "no_fitresult.root")
    f = ROOT.TFile(path, "RECREATE")
    ROOT.TH1D("not_a_fit_result", "", 1, 0, 1).Write()
    f.Close()

    n_before = ROOT.gROOT.GetListOfFiles().GetEntries()
    got = _read_fit_quality(path)
    n_after = ROOT.gROOT.GetListOfFiles().GetEntries()

    assert got is None
    assert n_after == n_before


# ---------------------------------------------------------------------------
# _require_covqual
# ---------------------------------------------------------------------------

def test_require_covqual_passes_when_equal_to_floor():
    _require_covqual(status=1, covqual=2, mincovqual=2, fitresultfile="run/FitResult.root")


def test_require_covqual_raises_and_names_both_numbers_when_below_floor():
    with pytest.raises(RuntimeError) as excinfo:
        _require_covqual(status=1, covqual=1, mincovqual=2, fitresultfile="run/FitResult.root")
    msg = str(excinfo.value)
    assert "covQual=1" in msg
    assert "required 2" in msg


@pytest.mark.parametrize("covqual,meaning", [
    (-1, "not available"),
    (0, "not calculated"),
    (1, "approximate"),
    (2, "full, but forced positive-definite"),
    (3, "accurate"),
])
def test_require_covqual_prints_documented_meaning(capsys, covqual, meaning):
    _require_covqual(status=1, covqual=covqual, mincovqual=-1, fitresultfile="run/FitResult.root")
    assert meaning in capsys.readouterr().out


def test_require_covqual_prints_unknown_for_unrecognised_value(capsys):
    _require_covqual(status=1, covqual=99, mincovqual=-1, fitresultfile="run/FitResult.root")
    assert "unknown" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# report_fit_quality (retained coordinator)
# ---------------------------------------------------------------------------

def test_report_fit_quality_accepts_the_j100_fixture():
    report_fit_quality(str(FIXTURES / "FitResult_J100_sixPar.root"), mincovqual=2)


def test_report_fit_quality_rejects_the_j100_fixture_at_a_higher_floor():
    with pytest.raises(RuntimeError):
        report_fit_quality(str(FIXTURES / "FitResult_J100_sixPar.root"), mincovqual=3)


def test_report_fit_quality_warns_and_returns_none_without_raising_when_no_fit_result(tmp_path, capsys):
    path = str(tmp_path / "no_fitresult2.root")
    f = ROOT.TFile(path, "RECREATE")
    ROOT.TH1D("not_a_fit_result", "", 1, 0, 1).Write()
    f.Close()

    assert report_fit_quality(path, mincovqual=2) is None
    assert "WARNING" in capsys.readouterr().out
