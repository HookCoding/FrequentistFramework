"""The Run 2 drivers (scripts/run_anaFit_run2.sh, scripts/run_anaFit_run2_J50.sh) share
everything past their configuration block through scripts/lib/anafit_driver.sh (plan
section 9). They are shell, not Python, so this tests them by actually running bash: the
library's functions directly (sourced into a throwaway bash -c), and the two full drivers
end to end with run_anaFit.py, python and root all replaced by recording stubs on PATH.

The test that matters most is test_both_drivers_emit_the_same_flag_names_...: the failure
mode this section exists to remove is "edited J100, forgot J50", and that test fails the
moment a flag is added to one driver's --run_anaFit.py invocation and not the other's.

Requires bash and, for the driver-level tests only, the repository's own setup.sh already
sourced - the driver's _setup_environment calls scripts/setup_buildAndFit.sh, which is a
no-op once $_DIRXMLWSBUILDER/$_DIRFIT are already set (true for this whole suite, since
conftest.py requires the LCG_102a environment for ROOT). The library-function tests below
that use a tmp_path cwd deliberately do NOT have those variables unset - they exercise
_setup_environment directly, not through a fresh setup_buildAndFit.sh source.
"""
import os
import shlex
import stat
import subprocess

import pytest

from conftest import REPO_ROOT

LIB = REPO_ROOT / "scripts" / "lib" / "anafit_driver.sh"
DRIVERS = {
    "J100": REPO_ROOT / "scripts" / "run_anaFit_run2.sh",
    "J50": REPO_ROOT / "scripts" / "run_anaFit_run2_J50.sh",
}

BARE_FLAGS = {"--dosignal", "--dolimit", "--doprefit"}

# The ten flags whose value each driver's configuration block sets differently. Every
# other flag must carry the identical value in both drivers, or this refactor's whole
# point - that they can no longer silently diverge - is broken by the very tests meant to
# guard it. See KNOWN_ISSUES.md issue 48 for why --outputfile/--folder/--wsfile differ
# (folder is prefixed "run_J50_" for J50) rather than sharing a naming scheme.
ALLOWED_TO_DIFFER = {
    "--rangelow", "--rangehigh", "--datafile", "--datahist", "--categoryfile",
    "--outputfile", "--folder", "--wsfile", "--rebinfile", "--rebinhist",
}


def _write_stub(path, body):
    path.write_text(f"#!/bin/bash\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _run_lib(snippet, cwd=REPO_ROOT, env=None):
    """Source the shared library into a throwaway bash -c and run snippet against it."""
    script = f". {shlex.quote(str(LIB))}\n{snippet}\n"
    return subprocess.run(
        ["bash", "-c", script], cwd=cwd, env=env if env is not None else dict(os.environ),
        capture_output=True, text=True,
    )


def _run_driver(tmp_path, driver):
    """Run a full driver with run_anaFit.py, python and root replaced by stubs that each
    record their argv, one token per line, and exit 0. Returns the three recorded argv
    lists (empty if the stub was never invoked)."""
    stub_dir = tmp_path / "stubs"
    stub_dir.mkdir(parents=True)
    run_anafit_log = tmp_path / "run_anafit.log"
    python_log = tmp_path / "python.log"
    root_log = tmp_path / "root.log"

    _write_stub(stub_dir / "run_anafit_stub.sh",
                f"printf '%s\\n' \"$@\" > {shlex.quote(str(run_anafit_log))}\nexit 0")
    _write_stub(stub_dir / "python",
                f"printf '%s\\n' \"$@\" > {shlex.quote(str(python_log))}\nexit 0")
    _write_stub(stub_dir / "root",
                f"printf '%s\\n' \"$@\" > {shlex.quote(str(root_log))}\nexit 0")

    env = dict(os.environ)
    env["OUT_DIR"] = str(tmp_path / "out")
    env["RUN_ANAFIT"] = str(stub_dir / "run_anafit_stub.sh")
    env["PATH"] = f"{stub_dir}:{env['PATH']}"

    result = subprocess.run(["bash", str(driver)], cwd=REPO_ROOT, env=env,
                             capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

    def _lines(log):
        return log.read_text().splitlines() if log.exists() else []

    return _lines(run_anafit_log), _lines(python_log), _lines(root_log)


def _parse_recorded_args(argv):
    """Split a recorded argv (one token per line, as _run_driver's stubs write it) into a
    {flag: value} dict for --flag value pairs, and the set of bare flags present."""
    flags = {tok for tok in argv if tok in BARE_FLAGS}
    pairs = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("--") and tok not in BARE_FLAGS:
            pairs[tok] = argv[i + 1]
            i += 2
        else:
            i += 1
    return pairs, flags


@pytest.mark.parametrize("driver", DRIVERS.values(), ids=DRIVERS.keys())
def test_bash_syntax(driver):
    result = subprocess.run(["bash", "-n", str(driver)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("driver", DRIVERS.values(), ids=DRIVERS.keys())
def test_both_drivers_source_the_shared_library(driver):
    assert ". scripts/lib/anafit_driver.sh" in driver.read_text()


def test_j100_driver_passes_its_configured_range_and_paths(tmp_path):
    run_anafit_argv, _, _ = _run_driver(tmp_path, DRIVERS["J100"])
    pairs, flags = _parse_recorded_args(run_anafit_argv)
    assert pairs["--rangelow"] == "481"
    assert pairs["--rangehigh"] == "3000"
    assert pairs["--datafile"] == "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root"
    assert pairs["--datahist"] == \
        "hists_yStar06_rejectEta_10_16/HLT_j0_perf_ds1_L1J100/h_mjj"
    # Spaces in the value must survive as one token, not be split at the --rebinhist call.
    assert pairs["--rebinhist"] == "Dijet mass distribution (J100)/Hist1D_y1"
    assert flags == {"--doprefit"}


def test_j50_driver_passes_its_configured_range_and_paths(tmp_path):
    run_anafit_argv, _, _ = _run_driver(tmp_path, DRIVERS["J50"])
    pairs, flags = _parse_recorded_args(run_anafit_argv)
    assert pairs["--rangelow"] == "302"
    assert pairs["--rangehigh"] == "2997"
    assert pairs["--datafile"] == "Input/data/dijetTLA/mjj_spectra_J50_dataAll.root"
    assert pairs["--datahist"] == "hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj"
    assert pairs["--rebinhist"] == "data"
    assert flags == {"--doprefit"}


def test_both_drivers_emit_the_same_flag_names_differing_only_in_the_ten_configured_values(tmp_path):
    j100_argv, _, _ = _run_driver(tmp_path / "j100", DRIVERS["J100"])
    j50_argv, _, _ = _run_driver(tmp_path / "j50", DRIVERS["J50"])
    j100_pairs, j100_flags = _parse_recorded_args(j100_argv)
    j50_pairs, j50_flags = _parse_recorded_args(j50_argv)

    assert set(j100_pairs) == set(j50_pairs)
    assert j100_flags == j50_flags == {"--doprefit"}

    differing = {k for k in j100_pairs if j100_pairs[k] != j50_pairs[k]}
    assert differing == ALLOWED_TO_DIFFER


@pytest.mark.parametrize("dosignal,dolimit,doprefit,expected", [
    (0, 0, 0, ""),
    (1, 0, 0, " --dosignal"),
    (0, 1, 0, " --dolimit"),
    (0, 0, 1, " --doprefit"),
    (1, 1, 0, " --dosignal --dolimit"),
    (1, 0, 1, " --dosignal --doprefit"),
    (0, 1, 1, " --dolimit --doprefit"),
    (1, 1, 1, " --dosignal --dolimit --doprefit"),
])
def test_build_flags_all_eight_combinations(dosignal, dolimit, doprefit, expected):
    result = _run_lib(f"_build_flags {dosignal} {dolimit} {doprefit}")
    assert result.stdout.rstrip("\n") == expected


def test_setup_environment_creates_the_output_directory_at_the_repo_root(tmp_path):
    out_dir = tmp_path / "out"
    result = _run_lib(f'_setup_environment {shlex.quote(str(out_dir))}; echo "EXIT:$?"')
    assert "EXIT:0" in result.stdout.splitlines()
    assert out_dir.is_dir()


def test_setup_environment_fails_outside_the_repository_root(tmp_path):
    # KNOWN_ISSUES.md issue 43: `return` inside a plain sourced script exits the driver
    # without killing an interactive shell; this is what makes that possible for a bash
    # function too, since the driver's own `if ! _setup_environment ...` still runs at the
    # top level of the sourced script, not inside a function.
    result = _run_lib('_setup_environment /tmp/wherever; echo "EXIT:$?"', cwd=tmp_path)
    assert "EXIT:1" in result.stdout.splitlines()


def test_select_postfit_falls_back_to_the_unmasked_file_when_no_masked_file_exists(tmp_path):
    (tmp_path / "PostFit_anaFit_sixPar_bkgOnly.root").touch()
    result = _run_lib(
        f'_select_postfit {shlex.quote(str(tmp_path))} six\n'
        'echo "$postfit_to_plot"\necho "$postfit_label"'
    )
    lines = result.stdout.splitlines()
    assert lines[0] == str(tmp_path / "PostFit_anaFit_sixPar_bkgOnly.root")
    assert lines[1] == "unmasked fit"


def test_select_postfit_prefers_the_masked_file_when_present(tmp_path):
    # Pins KNOWN_ISSUES.md issue 48: plotting the unmasked file unconditionally used to
    # show the REJECTED fit with nothing saying so.
    (tmp_path / "PostFit_anaFit_sixPar_bkgOnly.root").touch()
    (tmp_path / "PostFit_anaFit_sixPar_bkgOnly_masked.root").touch()
    result = _run_lib(
        f'_select_postfit {shlex.quote(str(tmp_path))} six\n'
        'echo "$postfit_to_plot"\necho "$postfit_label"'
    )
    lines = result.stdout.splitlines()
    assert lines[0] == str(tmp_path / "PostFit_anaFit_sixPar_bkgOnly_masked.root")
    assert lines[1] == "masked fit - BumpHunter window blinded"


def test_make_plots_invokes_python_and_root_with_the_expected_arguments(tmp_path):
    stub_dir = tmp_path / "stubs"
    stub_dir.mkdir()
    python_log = tmp_path / "python.log"
    root_log = tmp_path / "root.log"
    _write_stub(stub_dir / "python", f"printf '%s\\n' \"$@\" > {shlex.quote(str(python_log))}")
    _write_stub(stub_dir / "root", f"printf '%s\\n' \"$@\" > {shlex.quote(str(root_log))}")

    env = dict(os.environ)
    env["PATH"] = f"{stub_dir}:{env['PATH']}"

    _run_lib(
        '_make_plots /tmp/pf.root /tmp/folder J100yStar06 '
        '"masked fit - BumpHunter window blinded" six',
        env=env,
    )
    assert python_log.read_text().splitlines() == [
        "python/plotPostFit.py", "-i", "/tmp/pf.root", "-o", "/tmp/folder/postFit.pdf",
        "-c", "J100yStar06", "-l", "masked fit - BumpHunter window blinded",
    ]
    assert root_log.read_text().splitlines() == [
        "-l", "-q", 'plot_postfit.cpp("/tmp/folder", "six", "J100yStar06")',
    ]


def test_report_failure_is_silent_and_exits_zero_when_anafit_succeeded():
    result = _run_lib('_report_failure "" /tmp/out; echo "EXIT:$?"')
    assert result.stdout.strip() == "EXIT:0"


def test_report_failure_prints_the_banner_and_propagates_the_status_when_anafit_failed():
    # KNOWN_ISSUES.md issue 47: this fires on ANY non-zero anafit_failed, not only a
    # failed p(chi2) gate - a traceback or the rebin-pair ValueError reads the same
    # banner. Pinned as today's wording, not fixed here.
    result = _run_lib('_report_failure 1 /tmp/myrun; echo "EXIT:$?"')
    assert "ERROR: run_anaFit.py exited 1 - the fit did not pass p(chi2)" in result.stdout
    assert "/tmp/myrun are diagnostics only. See KNOWN_ISSUES.md issue 38." in result.stdout
    assert "EXIT:1" in result.stdout.splitlines()
