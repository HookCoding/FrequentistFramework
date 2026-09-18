"""Re-run the post-fit extraction against a recorded workspace and demand the recorded answer.

This is not a unit test. It is the second half of `tests/repro.py check` - everything downstream
of quickFit - run against fixtures instead of against a fresh fit. It needs no built binaries, no
CVMFS fit and no HTCondor, and it finishes in seconds rather than the 4-6 minutes a full check
takes. That is its whole purpose: it makes the decomposition of ExtractPostfitFromWS.py
affordable to iterate on.

What it proves: given the same workspace and the same data, the extraction still produces the
same histograms, bin for bin, including the six-bin chi2 summary the p(chi2) gate is read from.

What it does not prove: that the fit which produced the workspace is unchanged. Only
`tests/repro.py check` covers that, and it is still the gate for every section boundary.

The fixtures are copies of the two recorded runs under `run/`, taken 2026-09-18:
    FitResult_J100_sixPar.root        <- run/run_481_3000_sixPar/FitResult_anaFit_sixPar_bkgOnly.root
    PostFit_J100_sixPar.root          <- run/run_481_3000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root
    FitResult_J50_sixPar_masked.root  <- run/run_J50_302_2997_sixPar/..._masked.root
    PostFit_J50_sixPar_masked.root    <- run/run_J50_302_2997_sixPar/..._masked.root
The FitResult files carry both `fitResult` and `combWS`, which is why the workspace argument
below points at a file named FitResult.
"""

import pytest
import ROOT

from conftest import FIXTURES
from roothelpers import assert_hists_equal

from ExtractPostfitFromWS import PostfitExtractor

# The constructor arguments each recorded run actually used, read off the two drivers and
# build_fit_extract(). If any of these drift from the drivers, this test is comparing a different
# extraction against the recorded one and its PASS means nothing - hence the companion test in
# tests/test_drivers.py (plan section 9) asserting the drivers still pass these values.
J100 = dict(
    wsfile=str(FIXTURES / "FitResult_J100_sixPar.root"),
    recorded=str(FIXTURES / "PostFit_J100_sixPar.root"),
    datafile="Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
    datahist="hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj",
    rebinfile="Input/data/dijetTLA/fullRun2TLAJ100mjj.root",
    rebinhist="Dijet mass distribution (J100)/Hist1D_y1",
    rangelow=481,
    # The unmasked J100 fit passes the p(chi2) gate, so no BumpHunter window was ever applied.
    maskmin=-1,
    maskmax=-1,
)

J50_MASKED = dict(
    wsfile=str(FIXTURES / "FitResult_J50_sixPar_masked.root"),
    recorded=str(FIXTURES / "PostFit_J50_sixPar_masked.root"),
    datafile="Input/data/dijetTLA/mjj_spectra_J50_dataAll.root",
    datahist="hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj",
    rebinfile="Input/data/dijetTLAnlo/binning2021/data_J100yStar06_range171_3217.root",
    rebinhist="data",
    rangelow=302,
    # The J50 fit fails the gate, so this is the masked repeat. These are the only recorded
    # values where maskmin/maskmax are not -1, which makes this the one real exercise of the
    # mask branch in getChi2 - the J100 case cannot reach it at all.
    maskmin=582,
    maskmax=662,
)


def _data_first_bin(datafile, datahist, rangelow):
    """Reproduce run_anaFit.py:134-137 exactly: the bin index just below the fit range."""
    f = ROOT.TFile(datafile)
    d = f.Get(datahist)
    assert d, f"no {datahist!r} in {datafile!r}"
    first = d.FindBin(rangelow) - 1
    f.Close()
    return first


def _extract(config, outfile):
    pfe = PostfitExtractor(
        wsfile=config["wsfile"],
        datafile=config["datafile"],
        datahist=config["datahist"],
        datafirstbin=_data_first_bin(config["datafile"], config["datahist"], config["rangelow"]),
        rebinfile=config["rebinfile"],
        rebinhist=config["rebinhist"],
        maskmin=config["maskmin"],
        maskmax=config["maskmax"],
        bkgonly=True,
    )
    pfe.WriteRoot(str(outfile), dirPerCategory=True)
    return pfe


def _directory_names(path):
    f = ROOT.TFile(path, "READ")
    try:
        return sorted(k.GetName() for k in f.GetListOfKeys())
    finally:
        f.Close()


@pytest.mark.parametrize("config,label", [(J100, "J100"), (J50_MASKED, "J50_masked")])
def test_extraction_reproduces_recorded_postfit(config, label, tmp_path):
    out = tmp_path / f"PostFit_{label}.root"
    _extract(config, out)

    got_dirs = _directory_names(str(out))
    want_dirs = _directory_names(config["recorded"])
    assert got_dirs == want_dirs, f"channel directories changed: {got_dirs} != {want_dirs}"

    f_got = ROOT.TFile(str(out), "READ")
    f_want = ROOT.TFile(config["recorded"], "READ")
    try:
        for channel in want_dirs:
            for name in ("data", "postfit", "residuals", "chi2"):
                assert_hists_equal(
                    f_got.Get(f"{channel}/{name}"),
                    f_want.Get(f"{channel}/{name}"),
                    context=f"{label} {channel}/{name}",
                )
    finally:
        f_got.Close()
        f_want.Close()


@pytest.mark.parametrize("config,label", [(J100, "J100"), (J50_MASKED, "J50_masked")])
def test_gate_pvalue_matches_recorded(config, label, tmp_path):
    """The one number the whole analysis turns on, asserted on its own.

    run_anaFit.py:189 reads GetPval(channel + "_bkgonly_rebinned") and run_anaFit.py:455 decides
    from it whether to accept the fit or go round again with a BumpHunter window masked. The
    test above would catch a change here too, but only as one of several thousand bins; this one
    names it, so a failure says what broke rather than where.
    """
    pfe = _extract(config, tmp_path / f"PostFit_{label}.root")
    channel = [c for c in pfe.GetCategories() if c.endswith("_bkgonly_rebinned")]
    assert len(channel) == 1, f"expected exactly one gated channel, got {channel}"

    got = pfe.GetPval(channel[0])

    f = ROOT.TFile(config["recorded"], "READ")
    try:
        # Bin 6 is the p-value, by the labelling ExtractPostfitFromWS.py:105-110 writes.
        h = f.Get(f"{channel[0]}/chi2")
        assert h.GetXaxis().GetBinLabel(6) == "pval", "chi2 summary bin 6 is no longer the p-value"
        want = h.GetBinContent(6)
    finally:
        f.Close()

    assert got == pytest.approx(want, rel=1e-12), f"{label} gate p-value moved: {got} != {want}"


def test_extractor_refuses_a_half_given_rebin_pair():
    """KNOWN_ISSUES issue 46: one of the pair used to be indistinguishable from neither, and
    fell through to a binning that stops at 1000 GeV while both drivers fit to 3000 and 2997."""
    with pytest.raises(ValueError):
        PostfitExtractor(
            wsfile=J100["wsfile"],
            datafile=J100["datafile"],
            datahist=J100["datahist"],
            rebinfile=J100["rebinfile"],
            rebinhist=None,
        )
    with pytest.raises(ValueError):
        PostfitExtractor(
            wsfile=J100["wsfile"],
            datafile=J100["datafile"],
            datahist=J100["datahist"],
            rebinfile=None,
            rebinhist=J100["rebinhist"],
        )
