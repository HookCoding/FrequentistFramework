from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_WSFILE = (
    _REPO_ROOT
    / "run"
    / "fits"
    / "J100"
    / "run_481_3000_sixPar"
    / "FitResult_anaFit_sixPar_bkgOnly.root"
)
_FIXTURE_DATAFILE = _REPO_ROOT / "Input" / "data" / "dijetTLA" / "mjj_spectra_J100_dataAll.root"
_FIXTURE_DATAHIST = "hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj"
_FIXTURE_REBINFILE = _REPO_ROOT / "Input" / "data" / "dijetisrTLA" / "mjjResolutionBinning_481.root"

# python/ExtractPostfitFromWS.py does `import ROOT` and `from ROOT import
# *` at module scope, unconditionally - like Chunk 15's
# ExtractFitParameters.py, this file is not being restructured to defer
# those imports (Chunk 16's own Rationale: the primary decomposition
# target is Extract()'s internal structure, not its import shape). Every
# function/method here - getNPars(), expHist(), getChi2(), and every
# PostfitExtractor method - needs a real ROOT/RooFit object to do
# anything meaningful, so there is no ROOT-free "fast" fragment to test
# with a stub, unlike createBinning.py's resolve_bin_edges() or
# FindBHWindow.py's compute_mask_window(). Every test below runs as a
# real-ROOT subprocess snippet, the same probe pattern
# test_plot_post_fit.py/test_extract_fit_parameters.py already
# established.
#
# Fixtures used, read directly from run_fit.py:130-166 and
# scripts/run_anaFit_J100.sh (matching exactly what production passes,
# despite PostfitExtractor's own "wsfile" name meaning the fit-result
# file here too - see Chunk 15's own documented note on the shared
# parameter name): the already-committed
# FitResult_anaFit_sixPar_bkgOnly.root as wsfile (confirmed directly:
# it contains both the "fitResult" RooFitResult Chunk 15 reads and a
# "combWS" RooWorkspace with a "ModelConfig" this file reads - the same
# file serves both extractor classes), the committed J100
# datafile/datahist, and the committed mjjResolutionBinning_481.root as
# rebinfile - no synthetic fixture needed for any of the three, the
# same low fixture-sourcing risk Chunk 15 had.


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


_CONSTRUCT_EXTRACTOR = f"""
import sys
sys.path.insert(0, "python")
import ROOT
from ExtractPostfitFromWS import PostfitExtractor

f = ROOT.TFile({str(_FIXTURE_DATAFILE)!r})
d = f.Get({_FIXTURE_DATAHIST!r})
datafirstbin = d.FindBin(481) - 1
f.Close()

pfe = PostfitExtractor(
    datafile={str(_FIXTURE_DATAFILE)!r},
    datahist={_FIXTURE_DATAHIST!r},
    datafirstbin=datafirstbin,
    wsfile={str(_FIXTURE_WSFILE)!r},
    rebinfile={str(_FIXTURE_REBINFILE)!r},
    rebinhist="mjjBinning",
    maskmin=-1,
    maskmax=-1,
    bkgonly=True,
)
pfe.Extract()
"""


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_extract_and_accessors_characterize_todays_real_and_buggy_behavior() -> None:
    # Pins down, in one real run against the committed J100 fixture, both
    # today's correct behavior and today's two dormant bugs - exactly
    # as they exist now, so Step B's extraction cannot accidentally
    # "clean up" either bug (Chunk 5's own precedent). Real values below
    # were independently observed by running this exact construction
    # twice and confirming bit-identical results before writing these
    # assertions, not guessed.
    assert _FIXTURE_WSFILE.exists(), f"expected committed fixture missing: {_FIXTURE_WSFILE}"
    assert _FIXTURE_DATAFILE.exists(), f"expected committed fixture missing: {_FIXTURE_DATAFILE}"
    assert _FIXTURE_REBINFILE.exists(), f"expected committed fixture missing: {_FIXTURE_REBINFILE}"

    # pytest is not importable inside the bare `python - <<'INNER_PY'`
    # subprocess snippet below (it runs under the ambient LCG
    # interpreter, outside this test process) - float comparisons use a
    # plain manual tolerance, not pytest.approx().
    snippet = _CONSTRUCT_EXTRACTOR + """
def approx(actual, expected, tol=1e-9):
    return abs(actual - expected) <= tol * max(1.0, abs(expected))

# Extract() builds 4 real categories from this single-channel fixture:
# the base channel, its bkgonly variant, and both rebinned variants -
# confirmed directly, not assumed.
categories = list(pfe.GetCategories())
assert categories == [
    "Run3TLA",
    "Run3TLA_bkgonly",
    "Run3TLA_rebinned",
    "Run3TLA_bkgonly_rebinned",
], categories

# getChi2()'s external mutation of the extractor it is passed - called
# 4 times inside Extract(), once per category above - characterized
# directly on its real, populated dict state for the base channel.
assert approx(pfe.channel_chi2["Run3TLA"], 2513.0871912425)
assert pfe.channel_nbins["Run3TLA"] == 2519
assert pfe.channel_npars["Run3TLA"] == 6
assert pfe.channel_ndof["Run3TLA"] == 2513
assert approx(pfe.channel_pval["Run3TLA"], 0.4957578521660618)
assert pfe.channel_hresiduals["Run3TLA"].GetNbinsX() == 2519
assert pfe.channel_hchi2["Run3TLA"].GetNbinsX() == 6

# GetChi2()/GetPval() correctly use next(iter(dict.values())) in their
# no-channelname fallback - today's correct behavior, preserved.
assert approx(pfe.GetChi2(), 2513.0871912425)
assert approx(pfe.GetPval(), 0.4957578521660618)
assert approx(pfe.GetChi2("Run3TLA"), 2513.0871912425)
assert approx(pfe.GetPval("Run3TLA"), 0.4957578521660618)

# GetNbins()/GetNpars()/GetNdof()/GetH1Chi2()/GetH1Postfit()/
# GetH1Residuals() incorrectly use next(iter(dict)) (dict KEYS, not
# values) in their no-channelname fallback - today's real, dormant bug,
# pinned exactly as observed (a channel-name string instead of the
# real int/histogram), not fixed here. Six accessors, not five: this
# plan's original design pass undercounted GetNdof as unaffected -
# corrected after a real run showed it has the identical bug.
assert pfe.GetNbins() == "Run3TLA"
assert pfe.GetNpars() == "Run3TLA"
assert pfe.GetNdof() == "Run3TLA"
assert pfe.GetH1Chi2() == "Run3TLA"
assert pfe.GetH1Postfit() == "Run3TLA"
assert pfe.GetH1Residuals() == "Run3TLA"

# The same six accessors work correctly when channelname IS supplied -
# proving the bug is specific to the omitted-argument fallback, not a
# general break (this is exactly the call shape run_fit.py's own real
# call sites always use, so production is unaffected).
assert pfe.GetNbins("Run3TLA") == 2519
assert pfe.GetNpars("Run3TLA") == 6
assert pfe.GetNdof("Run3TLA") == 2513
assert pfe.GetH1Chi2("Run3TLA").GetNbinsX() == 6
assert pfe.GetH1Postfit("Run3TLA").GetNbinsX() == 2519
assert pfe.GetH1Residuals("Run3TLA").GetNbinsX() == 2519

print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_writeroot_dirpercategory_true_produces_expected_output_for_real_fixture(
    tmp_path: Path,
) -> None:
    # dirPerCategory=True is the only branch run_fit.py's own call site
    # ever uses (run_fit.py:165) - characterized end to end here,
    # matching the "real script/whole-pipeline" test every other chunk
    # in this plan also adds. dirPerCategory=False is Chunk 16a's own,
    # separately-scoped concern (a real Python-3 TypeError today).
    outfile = tmp_path / "out.root"
    snippet = _CONSTRUCT_EXTRACTOR + f"""
pfe.WriteRoot({str(outfile)!r}, dirPerCategory=True)
print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))

    assert outfile.exists()

    verify_snippet = f"""
import ROOT
f = ROOT.TFile.Open({str(outfile)!r})
for category in (
    "Run3TLA",
    "Run3TLA_bkgonly",
    "Run3TLA_rebinned",
    "Run3TLA_bkgonly_rebinned",
):
    d = f.Get(category)
    assert d, f"missing output directory for category {{category}}"
    for key_name in ("data", "postfit", "residuals", "chi2"):
        obj = d.Get(key_name)
        assert obj, f"missing {{key_name}} in category {{category}}"
        assert obj.GetNbinsX() > 0, (category, key_name, obj.GetNbinsX())
f.Close()
print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(verify_snippet))
