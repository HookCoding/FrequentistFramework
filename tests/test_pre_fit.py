from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_DATAFILE = _REPO_ROOT / "Input" / "data" / "dijetTLA" / "mjj_spectra_J100_dataAll.root"
_FIXTURE_DATAHIST = "hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj"

# python/PreFit.py does `import ROOT` at module scope, unconditionally -
# like Chunk 15's ExtractFitParameters.py and Chunk 16's
# ExtractPostfitFromWS.py, this file's imports are not deferred.
# PreFitter.Fit() needs a real ROOT TH1/TF1/TStopwatch to do anything
# meaningful, so there is no ROOT-free "fast" fragment to test with a
# stub. Every test below runs as a real-ROOT subprocess snippet, the
# same probe pattern test_plot_post_fit.py/test_extract_fit_parameters.py/
# test_extract_postfit_from_ws.py already established.
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
