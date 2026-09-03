from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BH_LOG_FIXTURE = _REPO_ROOT / "tests" / "root_macros" / "BHresults_sample.json"

# Thin Python/pytest wrapper invoking the ROOT test macro
# tests/root_macros/test_read_bumphunter_results.cpp via subprocess.run,
# matching the wrapper pattern already used for
# tests/test_plot_postfit_macro.py. `read_bumphunter_results()` needs a
# real ROOT/RooFit runtime this repository's own pytest dev venv does not
# have, so this sources scripts/setup_buildAndFit.sh itself, same as
# every other real-ROOT test in this repository.
_PROBE = r"""
repo_dir="$PWD"
source "$repo_dir/scripts/setup_buildAndFit.sh" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    echo "setup_status=$setup_status"
    exit "$setup_status"
fi

root -l -b -q "tests/root_macros/test_read_bumphunter_results.cpp(\"$BH_LOG_FIXTURE\")"
"""


def _run_read_bumphunter_results_macro(fixture: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["BH_LOG_FIXTURE"] = str(fixture)

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
def test_read_bumphunter_results_matches_known_fixture_and_reports_missing_file() -> None:
    assert _BH_LOG_FIXTURE.exists(), "expected BHresults_sample.json fixture missing"

    completed = _run_read_bumphunter_results_macro(_BH_LOG_FIXTURE)

    assert completed.returncode == 0, (
        "test_read_bumphunter_results.cpp macro failed:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "TEST_READ_BUMPHUNTER_RESULTS_OK" in completed.stdout, completed.stdout
