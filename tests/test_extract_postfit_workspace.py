"""Unit tests for the workspace half of PostfitExtractor.Extract() (decomposition plan section 6b).

Six functions, all of which touch RooFit objects owned by the workspace, which is owned by the
file `Extract()` closes on its last line. That ownership is the reason this half was split from
section 6a's histogram plumbing and done second: `_open_workspace` hands back its file precisely
so the caller can keep it alive, while `_load_data_histogram` detaches its histogram and closes
its file, and the difference between those two signatures is the contract.

Plus the deletion of `WriteRoot`'s `dirPerCategory=False` branch - KNOWN_ISSUES issue 54 - and the
multi-channel behaviour recorded as issue 55.
"""

import math

import pytest
import ROOT

from conftest import FIXTURES
from roothelpers import make_hist

from ExtractPostfitFromWS import (
    PostfitExtractor,
    _open_workspace,
    _load_data_histogram,
    _model_components,
    _channel_npars,
    _background_only_pdf,
    _pdf_histogram,
)

J100_WS = str(FIXTURES / "FitResult_J100_sixPar.root")
J100_CHANNEL = "J100yStar06"


@pytest.fixture
def workspace():
    """The fixture workspace, with its file held open for the test's duration.

    Written this way on purpose: it is the calling convention `_open_workspace` exists to force.
    """
    f, w = _open_workspace(J100_WS, "combWS")
    yield w
    f.Close()


# ---------------------------------------------------------------------------
# _open_workspace
# ---------------------------------------------------------------------------

def test_open_workspace_returns_the_named_workspace_and_its_file():
    f, w = _open_workspace(J100_WS, "combWS")
    try:
        assert w.GetName() == "combWS"
        assert f.IsOpen()
    finally:
        f.Close()


def test_open_workspace_returns_a_falsy_workspace_for_a_missing_name():
    """TFile.Get returns a null pointer rather than raising, so the caller sees a falsy object
    and only finds out at the first attribute access. Pinned as-is."""
    f, w = _open_workspace(J100_WS, "no_such_workspace")
    try:
        assert not w
    finally:
        f.Close()


# ---------------------------------------------------------------------------
# _load_data_histogram
# ---------------------------------------------------------------------------

def _write_data_file(tmp_path, contents, name="h_mjj"):
    path = str(tmp_path / "data.root")
    f = ROOT.TFile(path, "RECREATE")
    h = make_hist(name, list(range(len(contents) + 1)), contents)
    h.SetDirectory(f)
    h.Write()
    f.Close()
    return path, name


def test_load_data_histogram_returns_the_histogram_detached(tmp_path):
    path, name = _write_data_file(tmp_path, [1.0, 2.0, 3.0])

    h = _load_data_histogram(path, name, undolog=False)

    assert not h.GetDirectory()
    assert [h.GetBinContent(i) for i in range(1, 4)] == [1.0, 2.0, 3.0]


def test_load_data_histogram_closes_the_file_before_returning(tmp_path):
    """The detachment above is what makes this safe, and it is why this function closes its file
    where _open_workspace cannot."""
    path, name = _write_data_file(tmp_path, [1.0, 2.0, 3.0])

    n_before = ROOT.gROOT.GetListOfFiles().GetEntries()
    h = _load_data_histogram(path, name, undolog=False)

    assert ROOT.gROOT.GetListOfFiles().GetEntries() == n_before
    # still readable with its file gone
    assert h.GetBinContent(2) == 2.0


def test_load_data_histogram_undoes_the_log_when_asked(tmp_path):
    path, name = _write_data_file(tmp_path, [1.0, 2.0, 0.0])

    h = _load_data_histogram(path, name, undolog=True)

    assert h.GetBinContent(1) == pytest.approx(math.exp(1.0))
    assert h.GetBinContent(2) == pytest.approx(math.exp(2.0))
    assert h.GetBinContent(3) == 0.0  # expHist leaves empty bins alone


def test_load_data_histogram_leaves_contents_alone_without_undolog(tmp_path):
    path, name = _write_data_file(tmp_path, [1.0, 2.0, 3.0])

    h = _load_data_histogram(path, name, undolog=False)

    assert [h.GetBinContent(i) for i in range(1, 4)] == [1.0, 2.0, 3.0]


# ---------------------------------------------------------------------------
# _model_components
# ---------------------------------------------------------------------------

def test_model_components_returns_one_channel_for_the_j100_fixture(workspace, capsys):
    pdf, cat, nChan, obs, data, dataList = _model_components(workspace, "ModelConfig")

    assert nChan == 1
    assert cat.getLabel() == J100_CHANNEL
    assert dataList.At(0) is not None
    assert "There are 1 channels" in capsys.readouterr().out


def test_model_components_category_is_never_advanced_issue55(workspace):
    """KNOWN_ISSUES issue 55. `Extract()` reads `cat.getLabel()` once per iteration of
    `for i in range(nChan)` and nothing in the loop advances the category, so above one channel
    every iteration would report the same label and overwrite the previous channel's entry in all
    seven dictionaries. Unreachable on both locked analyses, which are single-channel - asserted
    here so that stays true by test rather than by assumption."""
    _, cat, nChan, _, _, _ = _model_components(workspace, "ModelConfig")

    assert nChan == 1
    assert cat.numTypes() == 1
    assert [cat.getLabel() for _ in range(3)] == [J100_CHANNEL] * 3


# ---------------------------------------------------------------------------
# _channel_npars
# ---------------------------------------------------------------------------

def _j100_channel_pdf(workspace):
    pdf, cat, _, _, _, dataList = _model_components(workspace, "ModelConfig")
    pdfi = pdf.getPdf(cat.getLabel())
    x = pdfi.getObservables(dataList.At(0)).first()
    return pdfi, x


def test_channel_npars_counts_the_pdf_when_not_overridden(workspace):
    pdfi, x = _j100_channel_pdf(workspace)

    assert _channel_npars(pdfi, x, externalnpars=None) == 6


def test_channel_npars_prefers_the_external_value(workspace):
    pdfi, x = _j100_channel_pdf(workspace)

    assert _channel_npars(pdfi, x, externalnpars=9) == 9


def test_channel_npars_treats_zero_as_an_override_not_as_absent(workspace):
    """The test is `!= None`, not truthiness - unlike the five accessors in
    ExtractFitParameters (issue 53). An externalnpars of 0 overrides."""
    pdfi, x = _j100_channel_pdf(workspace)

    assert _channel_npars(pdfi, x, externalnpars=0) == 0


# ---------------------------------------------------------------------------
# _background_only_pdf
# ---------------------------------------------------------------------------

def test_background_only_pdf_is_the_extended_background_for_the_channel(workspace):
    pdf_bkg = _background_only_pdf(workspace, J100_CHANNEL)

    assert pdf_bkg.GetName() == "pdf__background_ext_" + J100_CHANNEL
    assert pdf_bkg.InheritsFrom("RooAbsPdf")


def test_background_only_pdf_adds_the_object_to_a_read_only_workspace(workspace):
    """factory() mutates a workspace opened "READ". Harmless only because Extract() reopens the
    file on every call and so works on a fresh workspace each time."""
    assert not workspace.pdf("pdf__background_ext_" + J100_CHANNEL)

    _background_only_pdf(workspace, J100_CHANNEL)

    assert workspace.pdf("pdf__background_ext_" + J100_CHANNEL)


# ---------------------------------------------------------------------------
# _pdf_histogram
# ---------------------------------------------------------------------------

class _FakePdf:
    """Duck type for the two cases a real RooFit pdf cannot easily produce."""

    def __init__(self, hist):
        self._hist = hist

    def createHistogram(self, name, x):
        return self._hist


def test_pdf_histogram_scales_to_the_expected_event_count():
    ws = ROOT.RooWorkspace("w_test")
    ws.factory("Gaussian::g(x[0,10],m[5],s[1])")

    h = _pdf_histogram(ws.pdf("g"), ws.var("x"), expectedEvents=1234.0, undolog=False)

    assert h.Integral() == pytest.approx(1234.0, rel=1e-9)


def test_pdf_histogram_leaves_a_zero_integral_unscaled():
    """The bare `except: pass` swallows the ZeroDivisionError from expectedEvents/0 and the
    histogram comes back untouched rather than the call failing. Pinned, not replaced with a
    specific exception."""
    empty = make_hist("hpdf", [0.0, 1.0, 2.0], [0.0, 0.0])

    h = _pdf_histogram(_FakePdf(empty), None, expectedEvents=1234.0, undolog=False)

    assert h.Integral() == 0.0
    assert [h.GetBinContent(i) for i in range(1, 3)] == [0.0, 0.0]


def test_pdf_histogram_undoes_the_log_after_scaling():
    # contents sum to 3, so expectedEvents=3 makes the scale factor exactly 1 and isolates expHist
    hist = make_hist("hpdf", [0.0, 1.0, 2.0], [1.0, 2.0])

    h = _pdf_histogram(_FakePdf(hist), None, expectedEvents=3.0, undolog=True)

    assert h.GetBinContent(1) == pytest.approx(math.exp(1.0))
    assert h.GetBinContent(2) == pytest.approx(math.exp(2.0))


def test_pdf_histogram_leaves_contents_alone_without_undolog():
    hist = make_hist("hpdf", [0.0, 1.0, 2.0], [1.0, 2.0])

    h = _pdf_histogram(_FakePdf(hist), None, expectedEvents=3.0, undolog=False)

    assert [h.GetBinContent(i) for i in range(1, 3)] == [1.0, 2.0]


# ---------------------------------------------------------------------------
# WriteRoot - KNOWN_ISSUES issue 54
# ---------------------------------------------------------------------------

J100 = dict(
    wsfile=J100_WS,
    datafile="Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
    datahist="hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj",
    rebinfile="Input/data/dijetTLA/fullRun2TLAJ100mjj.root",
    rebinhist="Dijet mass distribution (J100)/Hist1D_y1",
    datafirstbin=481,
)


def test_writeroot_refuses_dirpercategory_false_issue54():
    """The branch this replaces called `self.channel_hpostfit.values()[-1]`, which raises
    TypeError on every call under Python 3. Refused explicitly now, rather than silently writing
    an empty file, because a silently empty PostFit_*.root is the failure mode CLAUDE.md's triage
    order puts above a crash."""
    pfe = PostfitExtractor(bkgonly=True, **J100)

    with pytest.raises(ValueError, match="dirPerCategory"):
        pfe.WriteRoot("unused.root", dirPerCategory=False)


def test_writeroot_refuses_before_extracting_or_touching_the_output_issue54(tmp_path):
    """Fails on the flag alone: no extraction runs, and an existing output file is not truncated.
    The old branch opened the file with RECREATE first and only then raised."""
    outfile = tmp_path / "PostFit.root"
    outfile.write_bytes(b"not a root file")

    pfe = PostfitExtractor(
        wsfile="/nonexistent/FitResult.root",
        datafile="/nonexistent/data.root",
        datahist="h",
    )

    with pytest.raises(ValueError, match="dirPerCategory"):
        pfe.WriteRoot(str(outfile), dirPerCategory=False)

    assert outfile.read_bytes() == b"not a root file"


def test_writeroot_defaults_to_the_refusing_branch_issue54():
    """The default is still False, so `pfe.WriteRoot(path)` - which is what
    ExtractPostfitFromWS.main() does when --dirpercategory is unset, and what the two
    run_buildAndFit_*swift.sh drivers therefore invoke - refuses rather than writing."""
    pfe = PostfitExtractor(bkgonly=True, **J100)

    with pytest.raises(ValueError):
        pfe.WriteRoot("unused.root")


def test_writeroot_writes_one_directory_per_channel(tmp_path):
    """The shape tests/repro.py reads, asserted directly rather than only through the golden
    comparison."""
    pfe = PostfitExtractor(bkgonly=True, **J100)
    outfile = tmp_path / "PostFit.root"

    pfe.WriteRoot(str(outfile), dirPerCategory=True)

    f = ROOT.TFile(str(outfile), "READ")
    try:
        names = sorted(k.GetName() for k in f.GetListOfKeys())
        assert names == sorted(pfe.channel_chi2)
        for channel in names:
            for hist in ("data", "postfit", "residuals", "chi2"):
                assert f.Get(f"{channel}/{hist}"), f"{channel}/{hist} missing"
    finally:
        f.Close()
