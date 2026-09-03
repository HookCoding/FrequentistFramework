from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_DIR = _REPO_ROOT / "run" / "fits" / "J100" / "run_481_3000_sixPar"

# plot_postfit.cpp (repository root) has one function, plot_postfit(), and
# no existing test harness of any kind exists yet for ROOT macros in this
# repository (see doc/TIER3_COMPLETION_PLAN.md Chunk 11). It is only ever
# invoked in production after scripts/setup_buildAndFit.sh has been
# sourced (see scripts/run_anaFit_J100.sh/run_anaFit_J50.sh, both of which
# run `root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\")"` after
# sourcing that script), which puts the LCG/CVMFS-provided "root" on PATH.
# This test sources that same setup script itself inside a
# subprocess.run(["bash", "-lc", ...]) call before invoking the macro,
# mirroring the exact probe pattern already established for
# python/plotPostFit.py's own end-to-end test
# (tests/test_plot_post_fit.py) and
# test_authoritative_setup_provides_scientific_runtime.
_PROBE = r"""
repo_dir="$PWD"
source "$repo_dir/scripts/setup_buildAndFit.sh" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    echo "setup_status=$setup_status"
    exit "$setup_status"
fi

root -l -b -q "plot_postfit.cpp(\"$PLOT_POSTFIT_IN_DIR\", \"$PLOT_POSTFIT_PARS\")"
"""


def _run_plot_postfit_macro(in_dir: Path, pars_str: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PLOT_POSTFIT_IN_DIR"] = str(in_dir)
    env["PLOT_POSTFIT_PARS"] = pars_str

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
def test_plot_postfit_macro_produces_nonempty_pdf_for_real_fixture(tmp_path: Path) -> None:
    # Characterizes the whole macro's current, unmodified output against
    # the already-committed J100 fixture directory, which has no
    # BHresults.json - exercising the current no-BumpHunter fallback path
    # (bump_hunter = false), per doc/TIER3_COMPLETION_PLAN.md Chunk 11.
    #
    # Do not attempt byte-identical PDF comparison as a documented
    # contract - ROOT's PDF output is not guaranteed bit-reproducible
    # across environments/fonts, and Tier 1 already established
    # (2026-08-20 activity-log entry, "Plotting separated from scientific
    # acceptance") that PDF artifacts are excluded from strict scientific
    # comparison, the same policy already cited for
    # tests/test_plot_post_fit.py. The meaningful, stable invariant
    # characterized here is "runs successfully against a real fixture and
    # produces a real, non-empty plot."
    assert _FIXTURE_DIR.exists(), "expected J100 sixPar fixture directory missing"

    # Never write into the tracked fixture itself - the macro writes
    # post_fit.pdf into in_dir, so this test works only against a
    # tmp_path copy.
    copied_dir = tmp_path / _FIXTURE_DIR.name
    shutil.copytree(_FIXTURE_DIR, copied_dir)
    (copied_dir / "post_fit.pdf").unlink(missing_ok=True)

    completed = _run_plot_postfit_macro(copied_dir, "six")

    assert completed.returncode == 0, (
        "plot_postfit.cpp macro failed:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    outfile = copied_dir / "post_fit.pdf"
    assert outfile.exists()
    assert outfile.stat().st_size > 0
