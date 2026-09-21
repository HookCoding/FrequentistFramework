"""Unit tests for python/plotPostFit.py (decomposition plan section 8).

Before this section the file had no functions at all: module-level code called parse_args()
against sys.argv and mutated ROOT.gStyle/gROOT the moment the module was imported, which is
why it could never be unit tested. main(argv) makes that stop, and is the section's real
content - the six helper extractions below it are the easy part.
"""

import pytest
import ROOT

from conftest import FIXTURES
from roothelpers import make_hist

import plotPostFit
from plotPostFit import (
    _parse_args,
    _load_histograms,
    _style_histograms,
    _draw_main_pad,
    _draw_fit_labels,
    _draw_ratio_pad,
    main,
)

J100_POSTFIT = FIXTURES / "PostFit_J100_sixPar.root"
J100_CHANNEL = "J100yStar06"


def test_the_module_has_no_import_time_side_effects():
    """The original script created a global `args` and mutated ROOT state as soon as it was
    imported. Nothing here should exist until main() runs - and the fact that this test file
    could even be collected is itself part of the proof, since pytest's own argv has neither
    -i nor -o."""
    assert not hasattr(plotPostFit, "args")
    assert not hasattr(plotPostFit, "postfit_file")


# ---------------------------------------------------------------------------
# _parse_args
# ---------------------------------------------------------------------------

def test_parse_args_matches_the_driver_invocation():
    """scripts/run_anaFit_run2.sh:133-135 and its J50 counterpart."""
    argv = [
        "-i", "/some/folder/PostFit_anaFit_sixPar_bkgOnly_masked.root",
        "-o", "/some/folder/postFit.pdf",
        "-c", "J100yStar06",
        "-l", "masked fit - BumpHunter window blinded",
    ]
    args = _parse_args(argv)
    assert args.inputFile == "/some/folder/PostFit_anaFit_sixPar_bkgOnly_masked.root"
    assert args.output == "/some/folder/postFit.pdf"
    assert args.channel == "J100yStar06"
    assert args.label == "masked fit - BumpHunter window blinded"


def test_parse_args_defaults_for_channel_and_label():
    args = _parse_args(["-i", "in.root", "-o", "out.pdf"])
    assert args.channel == "Run3TLA"
    assert args.label == ""


# ---------------------------------------------------------------------------
# _load_histograms
# ---------------------------------------------------------------------------

def _write_postfit_file(tmp_path, channel, data_contents, postfit_contents, chi2_contents, name="postfit.root"):
    path = str(tmp_path / name)
    f = ROOT.TFile(path, "RECREATE")
    d = f.mkdir(channel)
    d.cd()
    data_edges = list(range(len(data_contents) + 1))
    postfit_edges = list(range(len(postfit_contents) + 1))
    chi2_edges = list(range(len(chi2_contents) + 1))
    make_hist("data", data_edges, data_contents).Write("data")
    make_hist("postfit", postfit_edges, postfit_contents).Write("postfit")
    make_hist("chi2", chi2_edges, chi2_contents).Write("chi2")
    f.Close()
    return path


def test_load_histograms_reads_the_named_channels_three_histograms(tmp_path):
    path = _write_postfit_file(tmp_path, "chanA", [1.0, 2.0], [1.1, 2.1], [0.0] * 6)
    f = ROOT.TFile.Open(path, "READ")
    try:
        data, postfit, h_rchi2 = _load_histograms(f, "chanA")
        assert [data.GetBinContent(i) for i in (1, 2)] == [1.0, 2.0]
        assert [postfit.GetBinContent(i) for i in (1, 2)] == [1.1, 2.1]
        assert h_rchi2.GetNbinsX() == 6
    finally:
        f.Close()


def test_load_histograms_against_the_real_j100_fixture():
    """Reads the unrebinned, non-background-only channel - not the one the p(chi2) gate or
    plot_postfit.cpp read. Three consumers, three directory conventions, one file."""
    f = ROOT.TFile.Open(str(J100_POSTFIT), "READ")
    try:
        data, postfit, h_rchi2 = _load_histograms(f, J100_CHANNEL)
        assert data.GetNbinsX() == postfit.GetNbinsX()
        assert h_rchi2.GetNbinsX() == 6
    finally:
        f.Close()


# ---------------------------------------------------------------------------
# _style_histograms
# ---------------------------------------------------------------------------

def test_style_histograms_applies_the_documented_styling():
    data = make_hist("d", [0, 1, 2], [1.0, 2.0])
    postfit = make_hist("p", [0, 1, 2], [1.0, 2.0])
    _style_histograms(data, postfit)
    assert data.GetMarkerStyle() == 8
    assert data.GetMarkerSize() == pytest.approx(0.5)
    assert data.GetMarkerColor() == ROOT.kBlack
    assert data.GetLineWidth() == 0
    assert postfit.GetLineWidth() == 2
    assert postfit.GetLineColor() == ROOT.kAzure + 7


# ---------------------------------------------------------------------------
# _draw_main_pad
# ---------------------------------------------------------------------------

def test_draw_main_pad_geometry_and_legend():
    ROOT.gROOT.SetBatch(True)
    data = make_hist("d3", [0, 1, 2], [10.0, 20.0])
    postfit = make_hist("p3", [0, 1, 2], [11.0, 19.0])
    c, pad1, legend = _draw_main_pad(data, postfit)
    try:
        assert pad1.GetName() == "pad1"
        assert pad1.GetXlowNDC() == pytest.approx(0.0)
        assert pad1.GetYlowNDC() == pytest.approx(0.3)
        assert pad1.GetWNDC() == pytest.approx(1.0)
        assert pad1.GetHNDC() == pytest.approx(0.7)
        assert pad1.GetBottomMargin() == pytest.approx(0.0)
        assert legend.GetListOfPrimitives().GetSize() == 2
    finally:
        c.Close()


# ---------------------------------------------------------------------------
# _draw_fit_labels
# ---------------------------------------------------------------------------

def test_draw_fit_labels_formats_chi2_to_three_decimals_and_omits_the_label_when_empty():
    ROOT.gROOT.SetBatch(True)
    c = ROOT.TCanvas()
    try:
        text = _draw_fit_labels(1.23456, "")
        prims = ROOT.gPad.GetListOfPrimitives()
        assert prims.GetSize() == 1
        assert prims[0].GetTitle() == "#chi^{2}/ndof = 1.235"
        assert text is not None
    finally:
        c.Close()


def test_draw_fit_labels_draws_the_label_when_given():
    ROOT.gROOT.SetBatch(True)
    c = ROOT.TCanvas()
    try:
        _draw_fit_labels(0.5, "masked fit - BumpHunter window blinded")
        prims = ROOT.gPad.GetListOfPrimitives()
        assert prims.GetSize() == 2
        assert prims[1].GetTitle() == "masked fit - BumpHunter window blinded"
    finally:
        c.Close()


# ---------------------------------------------------------------------------
# _draw_ratio_pad
# ---------------------------------------------------------------------------

def test_draw_ratio_pad_computes_the_ratio_and_applies_the_hard_clip():
    ROOT.gROOT.SetBatch(True)
    c = ROOT.TCanvas()
    try:
        data = make_hist("d4", [0, 1], [110.0])
        postfit = make_hist("p4", [0, 1], [100.0])
        pad2, h_ratio = _draw_ratio_pad(data, postfit)
        assert h_ratio.GetBinContent(1) == pytest.approx(1.1)
        assert pad2.GetName() == "pad2"
        assert pad2.GetXlowNDC() == pytest.approx(0.0)
        assert pad2.GetYlowNDC() == pytest.approx(0.05)
        assert pad2.GetWNDC() == pytest.approx(1.0)
        assert pad2.GetHNDC() == pytest.approx(0.25)
        assert pad2.GetTopMargin() == pytest.approx(0.0)
        assert pad2.GetBottomMargin() == pytest.approx(0.3)
        # SetRangeUser(0.85, 1.15) is a hard clip: a ratio outside it is drawn off-scale
        # rather than flagged. GetMinimum()/GetMaximum() are how a TH1's Y-axis reports a
        # SetRangeUser bound back, since the Y "axis" has no real bins to look an edge up in.
        assert h_ratio.GetMinimum() == pytest.approx(0.85)
        assert h_ratio.GetMaximum() == pytest.approx(1.15)
    finally:
        c.Close()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def test_main_reads_chi2_ndof_from_bin_2_not_bin_6(tmp_path, monkeypatch):
    """Pins KNOWN_ISSUES issue 45 (already fixed, predating this refactor): bin 2 holds
    chi2/ndof and bin 6 holds the p-value. Reading bin 6 here would silently draw the
    p-value under a chi2/ndof label again."""
    chi2_contents = [111.0, 22.5, 6.0, 6.0, 0.0, 0.0009]
    path = _write_postfit_file(tmp_path, "chan", [1.0], [1.0], chi2_contents)

    recorded = {}

    def _record(rchi2, label):
        recorded["rchi2"] = rchi2
        return None

    monkeypatch.setattr(plotPostFit, "_draw_fit_labels", _record)

    main(["-i", path, "-o", str(tmp_path / "out.pdf"), "-c", "chan", "-l", ""])

    assert recorded["rchi2"] == pytest.approx(22.5)


def test_main_runs_end_to_end_against_the_real_j100_fixture(tmp_path):
    out = tmp_path / "postFit.pdf"
    main([
        "-i", str(J100_POSTFIT),
        "-o", str(out),
        "-c", J100_CHANNEL,
        "-l", "unmasked fit",
    ])
    assert out.exists()
    assert out.stat().st_size > 0
