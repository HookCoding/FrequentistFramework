"""Unit tests for the binning half of PostfitExtractor.Extract() (decomposition plan section 6a).

Five functions, all pure histogram plumbing: reconstruct the postfit bin edges from the data
histogram, copy the pdf onto them, crop the data to them, read the resolution binning, and rebin
a channel pair onto it. None of them touches the workspace, which is why they are split out
first - the workspace-lifetime half is section 6b.

Plus the one behaviour change in section 6a: `Extract()` no longer overwrites its own
`datafirstbin`, so calling it twice produces the same answer. That is KNOWN_ISSUES issue 51,
whose status line always said it would be fixed here rather than earlier.
"""

import array
import math

import pytest
import ROOT

from conftest import FIXTURES
from roothelpers import make_hist

from ExtractPostfitFromWS import (
    PostfitExtractor,
    _bin_edges_from_data,
    _postfit_histogram,
    _crop_data,
    _rebin_edges,
    _rebin_channel,
)


# ---------------------------------------------------------------------------
# _bin_edges_from_data
# ---------------------------------------------------------------------------

def test_bin_edges_from_data_offsets_by_datafirstbin():
    """The one use of datafirstbin in the whole method, and exactly what the two reassignments
    this section removes used to corrupt."""
    h_data = make_hist("data", list(range(11)), [1.0] * 10)

    edges = _bin_edges_from_data(h_data, nBins=3, datafirstbin=2)

    # data bin 3 low edge through data bin 6 low edge
    assert edges == [2.0, 3.0, 4.0, 5.0]


def test_bin_edges_from_data_with_zero_offset_starts_at_the_first_bin():
    h_data = make_hist("data", list(range(11)), [1.0] * 10)

    assert _bin_edges_from_data(h_data, nBins=3, datafirstbin=0) == [0.0, 1.0, 2.0, 3.0]


def test_bin_edges_from_data_returns_nbins_plus_one_edges():
    h_data = make_hist("data", list(range(11)), [1.0] * 10)

    for nBins in (1, 4, 8):
        assert len(_bin_edges_from_data(h_data, nBins, datafirstbin=1)) == nBins + 1


def test_bin_edges_from_data_copies_variable_edges_rather_than_computing_them():
    """The real data histograms are not uniform outside the fitted range. The edges are read off
    the data, never derived from a width."""
    h_data = make_hist("data", [100.0, 110.0, 125.0, 145.0, 200.0, 300.0], [1.0] * 5)

    assert _bin_edges_from_data(h_data, nBins=2, datafirstbin=1) == [110.0, 125.0, 145.0]


# ---------------------------------------------------------------------------
# _postfit_histogram
# ---------------------------------------------------------------------------

def test_postfit_histogram_copies_by_bin_index_not_by_x_position():
    """hpdf carries the pdf observable's own binning; only the ordinal position survives. The two
    axes below deliberately do not overlap at all, so a value-based copy would produce zeros."""
    hpdf = make_hist("hpdf", [0.0, 1.0, 2.0, 3.0], [7.0, 8.0, 9.0])
    binEdges = [481.0, 500.0, 530.0, 600.0]

    h = _postfit_histogram(hpdf, nBins=3, binEdges=binEdges)

    assert h.GetName() == "postfit"
    assert h.GetNbinsX() == 3
    assert [h.GetBinLowEdge(i) for i in range(1, 5)] == binEdges
    assert [h.GetBinContent(i) for i in range(1, 4)] == [7.0, 8.0, 9.0]


def test_postfit_histogram_zeroes_every_error():
    hpdf = make_hist("hpdf", [0.0, 1.0, 2.0], [100.0, 400.0])  # errors 10 and 20

    h = _postfit_histogram(hpdf, nBins=2, binEdges=[481.0, 500.0, 530.0])

    assert h.GetBinError(1) == 0.0
    assert h.GetBinError(2) == 0.0


def test_postfit_histogram_is_detached_from_any_directory():
    hpdf = make_hist("hpdf", [0.0, 1.0], [1.0])

    assert not _postfit_histogram(hpdf, 1, [481.0, 500.0]).GetDirectory()


# ---------------------------------------------------------------------------
# _crop_data
# ---------------------------------------------------------------------------

def test_crop_data_sums_the_source_bins_inside_each_new_edge_pair():
    h_data = make_hist("data", list(range(11)), [float(i) for i in range(1, 11)])

    cropped = _crop_data(h_data, nBins=3, binEdges=[2.0, 4.0, 6.0, 8.0])

    assert cropped.GetNbinsX() == 3
    assert [cropped.GetBinContent(i) for i in range(1, 4)] == [3 + 4, 5 + 6, 7 + 8]


def test_crop_data_combines_errors_in_quadrature():
    h_data = make_hist("data", list(range(11)), [float(i) for i in range(1, 11)])

    cropped = _crop_data(h_data, nBins=3, binEdges=[2.0, 4.0, 6.0, 8.0])

    # make_hist gives sqrt(content), so quadrature over bins 3 and 4 is sqrt(3+4)
    assert cropped.GetBinError(1) == pytest.approx(math.sqrt(7.0))


def test_crop_data_is_detached_from_any_directory():
    """TH1::Rebin clones through gDirectory, so without the explicit detachment the result would
    be owned by whatever file happened to be open - and both workspace files close before
    WriteRoot runs."""
    h_data = make_hist("data", list(range(11)), [1.0] * 10)

    assert not _crop_data(h_data, 3, [2.0, 4.0, 6.0, 8.0]).GetDirectory()


# ---------------------------------------------------------------------------
# _rebin_edges
# ---------------------------------------------------------------------------

def _write_binning_file(tmp_path, edges):
    path = str(tmp_path / "binning.root")
    f = ROOT.TFile(path, "RECREATE")
    h = ROOT.TH1D("mjjBinning", "", len(edges) - 1, array.array("d", [float(e) for e in edges]))
    h.Write()
    f.Close()
    return path


def test_rebin_edges_drops_edges_outside_the_fitted_range(tmp_path):
    rebinfile = _write_binning_file(tmp_path, [100.0, 200.0, 481.0, 520.0, 600.0, 900.0])
    h_postfit = make_hist("postfit", [481.0, 500.0, 530.0, 600.0], [1.0, 1.0, 1.0])

    edges = _rebin_edges(rebinfile, "mjjBinning", h_postfit)

    # 100 and 200 are below the postfit's first edge; 900 is above the upper limit
    assert edges == [481.0, 520.0, 600.0]


def test_rebin_edges_upper_limit_is_one_bin_past_the_last_edge(tmp_path):
    """The comparison at the heart of this function uses GetBinLowEdge(GetNbinsX()+2), not the
    last edge, so an edge in the bin beyond the fitted range is kept. Both locked analyses fit a
    1 GeV uniform range, which is why nothing is admitted there in practice; this pins the
    arithmetic so a change to it is visible."""
    h_postfit = make_hist("postfit", [481.0, 482.0, 483.0, 484.0], [1.0, 1.0, 1.0])
    assert h_postfit.GetBinLowEdge(h_postfit.GetNbinsX() + 2) == 485.0

    kept = _rebin_edges(_write_binning_file(tmp_path, [481.0, 483.0, 485.0]), "mjjBinning",
                        h_postfit)
    assert kept == [481.0, 483.0, 485.0]

    dropped = _rebin_edges(_write_binning_file(tmp_path, [481.0, 483.0, 486.0]), "mjjBinning",
                           h_postfit)
    assert dropped == [481.0, 483.0]


def test_rebin_edges_extrapolates_the_upper_limit_with_the_average_width(tmp_path):
    """TAxis computes an out-of-range bin from (xmax-xmin)/nbins, not from the last bin's width.
    On the uniform ranges both drivers fit these are the same number; on a non-uniform postfit
    they are not, and this records which one the code uses."""
    h_postfit = make_hist("postfit", [0.0, 1.0, 2.0, 30.0], [1.0, 1.0, 1.0])

    # last bin is 28 wide, but the limit is 0 + 4*(30/3) = 40
    assert h_postfit.GetBinLowEdge(h_postfit.GetNbinsX() + 2) == 40.0
    assert _rebin_edges(_write_binning_file(tmp_path, [0.0, 35.0, 45.0]), "mjjBinning",
                        h_postfit) == [0.0, 35.0]


def test_rebin_edges_closes_the_binning_file_before_returning(tmp_path):
    rebinfile = _write_binning_file(tmp_path, [481.0, 520.0, 600.0])
    h_postfit = make_hist("postfit", [481.0, 500.0, 600.0], [1.0, 1.0])

    n_before = ROOT.gROOT.GetListOfFiles().GetEntries()
    _rebin_edges(rebinfile, "mjjBinning", h_postfit)

    assert ROOT.gROOT.GetListOfFiles().GetEntries() == n_before


# ---------------------------------------------------------------------------
# _rebin_channel
# ---------------------------------------------------------------------------

def test_rebin_channel_rebins_both_histograms_onto_the_supplied_edges():
    h_postfit = make_hist("postfit", [0.0, 1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0])
    h_data = make_hist("data", [0.0, 1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0])

    postfit, data = _rebin_channel(h_postfit, h_data, [0.0, 2.0, 4.0], "h_mjj")

    assert postfit.GetNbinsX() == 2
    assert [postfit.GetBinContent(i) for i in range(1, 3)] == [3.0, 7.0]
    assert data.GetNbinsX() == 2
    assert [data.GetBinContent(i) for i in range(1, 3)] == [30.0, 70.0]


def test_rebin_channel_names_the_pair_postfit_and_after_the_data_histogram():
    h_postfit = make_hist("postfit", [0.0, 1.0, 2.0], [1.0, 2.0])
    h_data = make_hist("data", [0.0, 1.0, 2.0], [10.0, 20.0])

    postfit, data = _rebin_channel(h_postfit, h_data, [0.0, 2.0], "hists_yStar06/h_mjj")

    assert postfit.GetName() == "postfit"
    assert data.GetName() == "hists_yStar06/h_mjj"


def test_rebin_channel_detaches_both_results_explicitly():
    """Not decoration: TH1::Rebin(n, newname, edges) clones through gDirectory, so the result is
    owned by whatever directory is current - gROOT during Extract() today, but a TFile if one
    were open, and these are the histograms run_anaFit.py:189 reads the gating p-value from."""
    h_postfit = make_hist("postfit", [0.0, 1.0, 2.0], [1.0, 2.0])
    h_data = make_hist("data", [0.0, 1.0, 2.0], [10.0, 20.0])

    postfit, data = _rebin_channel(h_postfit, h_data, [0.0, 2.0], "h_mjj")

    assert not postfit.GetDirectory()
    assert not data.GetDirectory()


def test_rebin_leaves_gdirectory_ownership_out_of_it_even_with_a_file_open(tmp_path):
    """The failure this guards against, made concrete: with a file open, an undetached Rebin
    result is deleted when that file closes."""
    h_postfit = make_hist("postfit", [0.0, 1.0, 2.0], [1.0, 2.0])
    h_data = make_hist("data", [0.0, 1.0, 2.0], [10.0, 20.0])

    f = ROOT.TFile(str(tmp_path / "open.root"), "RECREATE")
    try:
        postfit, data = _rebin_channel(h_postfit, h_data, [0.0, 2.0], "h_mjj")
    finally:
        f.Close()

    assert postfit.GetBinContent(1) == 3.0
    assert data.GetBinContent(1) == 30.0


# ---------------------------------------------------------------------------
# Extract() is now idempotent - KNOWN_ISSUES issue 51
# ---------------------------------------------------------------------------

J100 = dict(
    wsfile=str(FIXTURES / "FitResult_J100_sixPar.root"),
    datafile="Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
    datahist="hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj",
    rebinfile="Input/data/dijetTLA/fullRun2TLAJ100mjj.root",
    rebinhist="Dijet mass distribution (J100)/Hist1D_y1",
    datafirstbin=481,
)


def _j100_extractor():
    return PostfitExtractor(bkgonly=True, **J100)


def test_extract_no_longer_overwrites_datafirstbin_issue51():
    """Before this section `Extract()` reassigned the constructor argument to a bin number in the
    rebinned histogram - measured as 481 in, -1 out - so a second call computed its bin edges
    from -1."""
    pfe = _j100_extractor()
    assert pfe.datafirstbin == 481

    pfe.Extract()

    assert pfe.datafirstbin == 481


def test_extract_twice_gives_the_same_gate_pvalue_issue51():
    """The number the analysis turns on. Nothing enforces a single Extract(): WriteRoot calls it
    when h_data is falsy and each of the nine lazy accessors calls it when its own cache is
    empty."""
    pfe = _j100_extractor()

    pfe.Extract()
    first = pfe.GetPval("J100yStar06_bkgonly_rebinned")
    pfe.Extract()
    second = pfe.GetPval("J100yStar06_bkgonly_rebinned")

    assert second == first


def test_extract_twice_gives_the_same_binning_for_every_channel_issue51():
    pfe = _j100_extractor()

    pfe.Extract()
    first = {
        name: [h.GetBinLowEdge(i) for i in range(1, h.GetNbinsX() + 2)]
        for name, h in pfe.channel_hpostfit.items()
    }
    pfe.Extract()
    second = {
        name: [h.GetBinLowEdge(i) for i in range(1, h.GetNbinsX() + 2)]
        for name, h in pfe.channel_hpostfit.items()
    }

    assert sorted(second) == sorted(first)
    for name in first:
        assert second[name] == first[name], name
