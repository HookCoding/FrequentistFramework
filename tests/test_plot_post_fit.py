from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_POSTFIT_FILE = (
    _REPO_ROOT
    / "run"
    / "fits"
    / "J100"
    / "run_481_3000_sixPar"
    / "PostFit_anaFit_sixPar_bkgOnly.root"
)

# python/plotPostFit.py has no functions yet - the entire 79-line file is
# top-level script code that does `import ROOT` at module scope (see
# doc/TIER3_COMPLETION_PLAN.md Chunk 10). It is only ever invoked in
# production after sourcing scripts/setup_buildAndFit.sh (see
# scripts/run_anaFit_J100.sh/run_anaFit_J50.sh), which puts the LCG/CVMFS-
# provided "python" (with ROOT importable) on PATH - not this repository's
# own pytest dev venv, where a bare `import ROOT` fails (confirmed
# directly). This characterization therefore runs the real, unmodified
# script as a subprocess, sourcing the same setup script the launchers use,
# mirroring the probe pattern already established by
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
