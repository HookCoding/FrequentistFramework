from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from python import plotPostFit as plot_post_fit

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYTHON_DIR = _REPO_ROOT / "python"
_FIXTURE_POSTFIT_FILE = (
    _REPO_ROOT
    / "run"
    / "fits"
    / "J100"
    / "run_481_3000_sixPar"
    / "PostFit_anaFit_sixPar_bkgOnly.root"
)

# python/plotPostFit.py defers every `import ROOT` to inside the specific
# functions that need it (load_postfit_histograms()/draw_postfit_canvas()/
# main() - see doc/TIER3_COMPLETION_PLAN.md Section 4.2's deferred-import
# rule, already applied to every other ROOT-touching function across this
# whole Tier 3 plan). parse_args() and build_ratio_histogram() touch no
# ROOT name at module or function scope at all, so importing this module
# above - a genuine, un-stubbed `from python import plotPostFit` - needs
# no ROOT presence whatsoever, real or fake (confirmed directly: this
# repository's own pytest dev venv cannot import ROOT at all, and this
# import still succeeds). This is a direct fix for GitHub Copilot's PR #6
# review of this file: an earlier version imported ROOT unconditionally at
# module scope and could only satisfy this import with a stub.
#
# load_postfit_histograms()/build_ratio_histogram()/draw_postfit_canvas()
# still build or read genuine ROOT objects once actually called, so they
# are exercised for real, as small inline scripts run via subprocess after
# sourcing scripts/setup_buildAndFit.sh - the same probe pattern Chunk
# 10.A's end-to-end test (kept below, unchanged) already established, and
# the same pattern test_authoritative_setup_provides_scientific_runtime
# uses.


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


# --- parse_args(): zero real ROOT needed ----------------------------------


def test_parse_args_parses_required_flags() -> None:
    args = plot_post_fit.parse_args(["-i", "in.root", "-o", "out.pdf"])

    assert args.inputFile == "in.root"
    assert args.output == "out.pdf"


def test_parse_args_accepts_long_flags() -> None:
    args = plot_post_fit.parse_args(["--inputFile", "in.root", "--output", "out.pdf"])

    assert args.inputFile == "in.root"
    assert args.output == "out.pdf"


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["-i", "in.root"],
        ["-o", "out.pdf"],
    ],
)
def test_parse_args_requires_both_flags(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        plot_post_fit.parse_args(argv)


# --- load_postfit_histograms(): real ROOT, real fixture file -------------


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_load_postfit_histograms_applies_styling_and_keeps_file_open() -> None:
    assert _FIXTURE_POSTFIT_FILE.exists(), "expected fixture PostFit ROOT file missing"

    snippet = f"""
import sys
sys.path.insert(0, {str(_PYTHON_DIR)!r})
import ROOT
import plotPostFit as ppf

histograms, postfit_file = ppf.load_postfit_histograms({str(_FIXTURE_POSTFIT_FILE)!r})

assert histograms.data.GetMarkerStyle() == 8
assert histograms.data.GetMarkerSize() == 0.5
assert histograms.data.GetMarkerColor() == ROOT.kBlack
assert histograms.data.GetLineWidth() == 0
assert histograms.postfit.GetLineWidth() == 2
assert histograms.postfit.GetLineColor() == ROOT.kAzure + 7
assert histograms.chi2.GetNbinsX() == 6

# The returned file must still be open and its histograms still usable -
# this is the real regression test for the file-lifetime fix described in
# plotPostFit.py's load_postfit_histograms() comment: a version that
# returned only the PostfitHistograms triple (discarding the TFile) was
# verified to garbage-collect the file and invalidate these same
# histograms before this point is even reached.
assert postfit_file.IsOpen()
assert histograms.postfit.GetNbinsX() > 0

print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


# --- build_ratio_histogram(): real, small, in-test ROOT.TH1D fixtures ----


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_build_ratio_histogram_computes_real_ratio_and_styling() -> None:
    # Per doc/TIER3_COMPLETION_PLAN.md Chunk 10: this function is tested
    # against small real ROOT.TH1D objects built in-test, not a full input
    # file - proving real division math, not just "was called."
    snippet = f"""
import sys
sys.path.insert(0, {str(_PYTHON_DIR)!r})
import ROOT
import plotPostFit as ppf

data = ROOT.TH1D("data_t", "data_t", 2, 0, 2)
data.SetBinContent(1, 10.0)
data.SetBinContent(2, 20.0)
postfit = ROOT.TH1D("postfit_t", "postfit_t", 2, 0, 2)
postfit.SetBinContent(1, 5.0)
postfit.SetBinContent(2, 40.0)

ratio = ppf.build_ratio_histogram(data, postfit)

assert ratio.GetBinContent(1) == 2.0
assert ratio.GetBinContent(2) == 0.5
assert ratio.GetTitle() == ""
assert ratio.GetYaxis().GetTitle() == "Data / Postfit"
assert ratio.GetYaxis().GetNdivisions() == 505
assert ratio.GetXaxis().GetTitle() == "Observable [units]"
assert ratio.GetMarkerStyle() == 20

print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


# --- draw_postfit_canvas(): real ROOT graphics objects, no file needed ---


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_draw_postfit_canvas_draws_expected_content_in_each_pad() -> None:
    # Asserts the actual content GitHub Copilot's PR #6 review flagged as
    # unprotected: not just "two pads exist", but that pad1 really holds
    # the data/postfit histograms plus a legend with the right entries and
    # the chi2/ndof annotation, and pad2 really holds the ratio histogram.
    # This is also the direct regression test for a real bug found while
    # writing it (see doc/ACTIVITY_LOG.md): the legend was being silently
    # garbage-collected out of the canvas before this fix, and this
    # assertion set was confirmed to fail against that unfixed version.
    snippet = f"""
import sys
sys.path.insert(0, {str(_PYTHON_DIR)!r})
import ROOT
ROOT.gROOT.SetBatch(True)
import plotPostFit as ppf

data = ROOT.TH1D("data_t2", "data_t2", 2, 0, 2)
data.SetBinContent(1, 10.0)
data.SetBinContent(2, 20.0)
postfit = ROOT.TH1D("postfit_t2", "postfit_t2", 2, 0, 2)
postfit.SetBinContent(1, 5.0)
postfit.SetBinContent(2, 40.0)
chi2 = ROOT.TH1D("chi2_t2", "chi2_t2", 6, 0, 6)
chi2.SetBinContent(6, 1.2345)
ratio = ppf.build_ratio_histogram(data, postfit)

canvas = ppf.draw_postfit_canvas(data, postfit, chi2, ratio)

assert isinstance(canvas, ROOT.TCanvas)
pads = canvas.GetListOfPrimitives()
pad_names = sorted(p.GetName() for p in pads if isinstance(p, ROOT.TPad))
assert pad_names == ["pad1", "pad2"]
pad1 = pads[0]
pad2 = pads[1]

pad1_prims = list(pad1.GetListOfPrimitives())
pad1_hist_names = [p.GetName() for p in pad1_prims if p.ClassName() == "TH1D"]
assert pad1_hist_names == ["data_t2", "postfit_t2"]

legends = [p for p in pad1_prims if p.ClassName() == "TLegend"]
assert len(legends) == 1, "legend missing or duplicated in pad1"
entries = list(legends[0].GetListOfPrimitives())
assert [(e.GetLabel(), e.GetOption()) for e in entries] == [
    ("Data", "lep"),
    ("Postfit", "l"),
]

latexes = [p for p in pad1_prims if p.ClassName() == "TLatex"]
assert any(t.GetTitle() == "#chi^{{2}}/ndof = 1.234" for t in latexes), (
    [t.GetTitle() for t in latexes]
)

pad2_prims = list(pad2.GetListOfPrimitives())
pad2_hist_names = [p.GetName() for p in pad2_prims if p.ClassName() == "TH1D"]
assert pad2_hist_names == [ratio.GetName()]

print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


# --- main(): unmodified, relocated verbatim from Chunk 10.A --------------
#
# plotPostFit.py needs a real ROOT/RooFit runtime this repository's own
# pytest dev venv does not have. It is only ever invoked in production
# after scripts/setup_buildAndFit.sh has been sourced (see
# scripts/run_anaFit_J100.sh/run_anaFit_J50.sh), which puts the LCG/CVMFS-
# provided "python" (with ROOT importable) on PATH. This test sources that
# same setup script itself inside a subprocess.run(["bash", "-lc", ...])
# call before invoking the script, mirroring the exact probe pattern
# already established by
# test_analysis_workflows_integration.py::test_authoritative_setup_provides_scientific_runtime.
_PROBE = r"""
repo_dir="$PWD"
source "$repo_dir/scripts/setup_buildAndFit.sh" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    echo "setup_status=$setup_status"
    exit "$setup_status"
fi

python "$repo_dir/python/plotPostFit.py" -i "$PLOT_POST_FIT_INPUT" -o "$PLOT_POST_FIT_OUTPUT"
"""


def _run_plot_post_fit_script(
    input_file: Path, output_file: Path
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PLOT_POST_FIT_INPUT"] = str(input_file)
    env["PLOT_POST_FIT_OUTPUT"] = str(output_file)

    return subprocess.run(
        ["bash", "-lc", _PROBE],
        cwd=_REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_plot_post_fit_script_produces_nonempty_pdf_for_real_fixture(tmp_path: Path) -> None:
    # Do not attempt byte-identical PDF comparison - ROOT's PDF output is
    # not guaranteed bit-reproducible across environments/fonts, and Tier 1
    # already established (2026-08-20 activity-log entry, "Plotting
    # separated from scientific acceptance") that PDF artifacts are
    # excluded from strict scientific comparison. The meaningful, stable
    # invariant characterized here is "runs successfully against a real
    # fixture and produces a real, non-empty plot."
    assert _FIXTURE_POSTFIT_FILE.exists(), "expected fixture PostFit ROOT file missing"
    outfile = tmp_path / "postFit.pdf"

    completed = _run_plot_post_fit_script(_FIXTURE_POSTFIT_FILE, outfile)

    assert completed.returncode == 0, (
        "plotPostFit.py subprocess failed:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert outfile.exists()
    assert outfile.stat().st_size > 0
