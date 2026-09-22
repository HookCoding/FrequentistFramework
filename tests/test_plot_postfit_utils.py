"""Runs test_plot_postfit_utils.C under ROOT so `pytest tests` reaches get_val()'s own test.

get_val() lives in plot_postfit_utils.h, a C++ header, so it cannot be called from Python; this
just shells out to ROOT the same way tests/test_drivers.py shells out to bash, and checks the
macro's own assertions and exit status.
"""

import subprocess

from conftest import REPO_ROOT


def test_get_val_root_macro_passes():
    result = subprocess.run(
        ["root", "-l", "-b", "-q", "tests/test_plot_postfit_utils.C"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_plot_postfit_utils: OK" in result.stdout, result.stdout + result.stderr
