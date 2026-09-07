#!/usr/bin/env bash
# Runs every mandatory gate this repository defines, in one command:
#
#   1. the lightweight quality gate (pytest, Ruff, Black -
#      python scripts/quality_check.py --mode full);
#   2. the prepared external-dependency checkout checks (pinned
#      submodule revisions, tracked-source cleanliness);
#   3. the scientific runtime-readiness gate (ROOT/Python imports, the
#      required fixtures and executable artifacts are all present);
#   4. the real J100/J50 scientific analysis, end to end, compared
#      against the frozen reference (the "scientific gate");
#   5. every plotting-layer and hot-path-support test that needs a real
#      ROOT/RooFit runtime and is therefore deselected by gate 1 (the
#      "plotting-layer real-ROOT gate" - see doc/TIER3_SYSTEM.md).
#
# Gates 1 and 2 need no ROOT runtime and therefore always run, before
# the ROOT-availability check below. Gate 2's two tests only inspect the
# dependency checkouts with git - see
# tests/test_repo_utils.py's test_external_dependency_checkouts_match_pinned_revisions
# and ..._have_no_tracked_source_changes, which call `git rev-parse`/
# `git status` and touch nothing else - so running them inside the ROOT
# conditional would let a missing CVMFS mount silently hide a real
# dependency-checkout failure. They carry
# requires_analysis_dependencies because they need the prepared
# checkouts, not because they need ROOT.
#
# These five are the same five test gates
# .github/workflows/scientific-analysis.yml runs (the lightweight gate
# also runs, alone, in .github/workflows/tier1-root-comparison.yml on
# every branch); that workflow additionally runs submodule-checkout,
# install.sh --check/--build and CVMFS-probe steps this script does
# not. Gates 3 and 4 both live in
# tests/test_analysis_workflows_integration.py but are two distinct,
# separately-marked tests selected by two different invocations - see
# doc/TIER1_SYSTEM.md's own "Scientific runtime readiness" and
# "Executable characterization gate" entries - so both must be listed
# here explicitly; listing only one silently drops the other.
#
# tests/test_repo_utils.py's two gate-coverage tests keep gates 2-5
# honest: each of those four gates is the only pytest invocation here
# naming its own test file or -k/-m selector, so deleting any one of
# them makes those tests fail. They parse this file's real pytest
# command lines, so a selector mentioned only in an echo or a comment
# does not count as coverage.
#
# There is deliberately no separate FindBHWindow.py gate here.
# tests/test_find_bh_window.py's own marked end-to-end test - which
# gate 5 runs - already invokes python/FindBHWindow.py as a real
# subprocess against the same committed J100 PostFit fixture, with the
# same ambient python3 plus pyBumpHunter PYTHONPATH, and asserts far
# more about the outcome (MaskMin/MaskMax, BlindRange, both output
# PNGs) than a bare exit-status check could. A separate invocation here
# would duplicate it exactly while proving less. Neither exercises the
# production pyBumpHunter/pyBH_env interpreter that
# run_masking.run_bumphunter() actually invokes, which is broken in
# this environment - see doc/TIER3_SYSTEM.md's Known limitations.
#
# Unlike .githooks/pre-commit - which skips the ROOT-dependent gates
# with a warning when scripts/setup_buildAndFit.sh can't provide a ROOT
# runtime here, so a commit is never blocked on a machine that
# legitimately lacks CVMFS - this script's whole purpose is to run
# every gate. If the ROOT-dependent runtime isn't available, it fails
# loudly instead of silently reporting a partial pass.
#
# Usage:
#   bash scripts/run_all_gates.sh
#
# Every gate's own real output is printed as it runs. A one-line
# PASSED/FAILED summary is printed for each gate, and the script exits
# non-zero if any gate failed (all gates still run - it does not stop
# at the first failure, so one broken gate doesn't hide another).

set -uo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir" || exit 1

python_bin="python"
if [[ -x "$repo_dir/.venv/bin/python" ]]; then
    python_bin="$repo_dir/.venv/bin/python"
fi

failures=0

run_gate() {
    local description="$1"
    shift
    echo
    echo "[run-all-gates] ==> $description"
    if "$@"; then
        echo "[run-all-gates] PASSED: $description"
    else
        echo "[run-all-gates] FAILED: $description"
        failures=$((failures + 1))
    fi
}

echo "[run-all-gates] Gate 1/5: lightweight quality gate (pytest, Ruff, Black)"
run_gate "lightweight quality gate" "$python_bin" scripts/quality_check.py --mode full

echo
echo "[run-all-gates] Gate 2/5: prepared external-dependency checkout checks (no ROOT needed)"
run_gate "prepared-dependency gate" "$python_bin" -m pytest tests/test_repo_utils.py \
  -m "requires_analysis_dependencies" -v

echo
echo "[run-all-gates] Checking whether the ROOT-dependent scientific runtime is available here..."
setup_check_log="$(mktemp)"
if ! bash -lc 'source scripts/setup_buildAndFit.sh' >"$setup_check_log" 2>&1; then
    echo "[run-all-gates] FAILED: scripts/setup_buildAndFit.sh could not provide a ROOT runtime here"
    echo "[run-all-gates] (no CVMFS mount, or the scientific dependencies are not built - see:"
    sed 's/^/[run-all-gates]   /' "$setup_check_log"
    echo "[run-all-gates] )."
    echo "[run-all-gates] Gates 3-5 (everything that needs ROOT) cannot run without it - this is a"
    echo "[run-all-gates] hard failure, since this script's purpose is to run every gate."
    rm -f "$setup_check_log"
    failures=$((failures + 1))
else
    rm -f "$setup_check_log"

    echo "[run-all-gates] Gate 3/5: scientific runtime-readiness gate"
    run_gate "scientific runtime-readiness gate" bash -lc '
        source scripts/setup_buildAndFit.sh >/dev/null
        python -m pytest tests/test_analysis_workflows_integration.py \
          -k authoritative_setup_provides_scientific_runtime -v
    '

    echo "[run-all-gates] Gate 4/5: the real J100/J50 scientific analysis, end to end"
    run_gate "scientific gate (J100/J50 authoritative workflows)" bash -lc '
        source scripts/setup_buildAndFit.sh >/dev/null
        python -m pytest tests/test_analysis_workflows_integration.py \
          -m "integration and requires_root" -v
    '

    echo "[run-all-gates] Gate 5/5: plotting-layer and hot-path-support real-ROOT regression gate"
    run_gate "plotting-layer/hot-path real-ROOT gate" bash -lc '
        source scripts/setup_buildAndFit.sh >/dev/null
        python -m pytest \
          tests/test_plot_post_fit.py \
          tests/test_plot_postfit_macro.py \
          tests/test_read_bumphunter_results.py \
          tests/test_create_binning.py \
          tests/test_extract_fit_parameters.py \
          tests/test_extract_postfit_from_ws.py \
          tests/test_find_bh_window.py \
          tests/test_pre_fit.py \
          -m "requires_analysis_dependencies" -v
    '
fi

echo
if (( failures > 0 )); then
    echo "[run-all-gates] FAILED: one or more gates did not pass. See above for detail."
    exit 1
fi

echo "[run-all-gates] All gates passed."
exit 0
