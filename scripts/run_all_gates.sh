#!/usr/bin/env bash
# Runs every mandatory gate this repository defines, in one command:
#
#   1. the lightweight quality gate (pytest, Ruff, Black -
#      python scripts/quality_check.py --mode full);
#   2. the scientific runtime-readiness gate (ROOT/Python imports, the
#      required fixtures and executable artifacts are all present);
#   3. the real J100/J50 scientific analysis, end to end, compared
#      against the frozen reference (the "scientific gate");
#   4. every plotting-layer and hot-path-support test that needs a real
#      ROOT/RooFit runtime and is therefore deselected by gate 1 (the
#      "plotting-layer real-ROOT gate" - see doc/TIER3_SYSTEM.md);
#   5. the prepared external-dependency checkout checks (pinned
#      submodule revisions, tracked-source cleanliness);
#   6. the FindBHWindow.py dedicated-interpreter gate, against the
#      committed J100 PostFit fixture - the one file whose masked-path
#      correctness the gates above cannot exercise on their own.
#
# Gates 1-5 are the same five checks
# .github/workflows/scientific-analysis.yml runs (the lightweight gate
# also runs, alone, in .github/workflows/tier1-root-comparison.yml on
# every branch). Gate 6 has no counterpart step in that workflow, and
# the workflow in turn runs submodule-checkout, install.sh
# --check/--build and CVMFS-probe steps that this script does not - so
# this script is deliberately a superset of that workflow's test gates,
# not a mirror of it. Nothing enforces gate-step parity between the
# two: tests/test_repo_utils.py's two coverage tests compare which
# *test files* each one references, so they would not notice Gate 6
# being deleted from here (Gate 4 already references
# tests/test_find_bh_window.py) - only a test file referenced by
# neither. Gates 2 and 3 both live in
# tests/test_analysis_workflows_integration.py but are two distinct,
# separately-marked tests selected by two different invocations - see
# doc/TIER1_SYSTEM.md's own "Scientific runtime readiness" and
# "Executable characterization gate" entries - so both must be listed
# here explicitly; listing only one silently drops the other.
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

echo "[run-all-gates] Gate 1/6: lightweight quality gate (pytest, Ruff, Black)"
run_gate "lightweight quality gate" "$python_bin" scripts/quality_check.py --mode full

echo
echo "[run-all-gates] Checking whether the ROOT-dependent scientific runtime is available here..."
setup_check_log="$(mktemp)"
if ! bash -lc 'source scripts/setup_buildAndFit.sh' >"$setup_check_log" 2>&1; then
    echo "[run-all-gates] FAILED: scripts/setup_buildAndFit.sh could not provide a ROOT runtime here"
    echo "[run-all-gates] (no CVMFS mount, or the scientific dependencies are not built - see:"
    sed 's/^/[run-all-gates]   /' "$setup_check_log"
    echo "[run-all-gates] )."
    echo "[run-all-gates] Gates 2-6 (everything that needs ROOT) cannot run without it - this is a"
    echo "[run-all-gates] hard failure, since this script's purpose is to run every gate."
    rm -f "$setup_check_log"
    failures=$((failures + 1))
else
    rm -f "$setup_check_log"

    echo "[run-all-gates] Gate 2/6: scientific runtime-readiness gate"
    run_gate "scientific runtime-readiness gate" bash -lc '
        source scripts/setup_buildAndFit.sh >/dev/null
        python -m pytest tests/test_analysis_workflows_integration.py \
          -k authoritative_setup_provides_scientific_runtime -v
    '

    echo "[run-all-gates] Gate 3/6: the real J100/J50 scientific analysis, end to end"
    run_gate "scientific gate (J100/J50 authoritative workflows)" bash -lc '
        source scripts/setup_buildAndFit.sh >/dev/null
        python -m pytest tests/test_analysis_workflows_integration.py \
          -m "integration and requires_root" -v
    '

    echo "[run-all-gates] Gate 4/6: plotting-layer and hot-path-support real-ROOT regression gate"
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

    echo "[run-all-gates] Gate 5/6: prepared external-dependency checkout checks"
    run_gate "prepared-dependency gate" bash -lc '
        source scripts/setup_buildAndFit.sh >/dev/null
        python -m pytest tests/test_repo_utils.py -m "requires_analysis_dependencies" -v
    '

    echo "[run-all-gates] Gate 6/6: FindBHWindow.py dedicated-interpreter gate"
    run_gate "FindBHWindow.py dedicated-interpreter gate" bash -lc '
        repo_dir="$PWD"
        source scripts/setup_buildAndFit.sh >/dev/null
        export PYTHONPATH="$repo_dir/pyBumpHunter:$PYTHONPATH"
        work_dir="$(mktemp -d)"
        trap '"'"'rm -rf "$work_dir"'"'"' EXIT
        cd "$work_dir" || exit 1
        python3 "$repo_dir/python/FindBHWindow.py" \
          --inputfile "$repo_dir/run/fits/J100/run_481_3000_sixPar/PostFit_anaFit_sixPar_bkgOnly.root" \
          --bkghist Run3TLA_rebinned/postfit --datahist Run3TLA_rebinned/data \
          --outputjson "$work_dir/BHresults.json"
    '
fi

echo
if (( failures > 0 )); then
    echo "[run-all-gates] FAILED: one or more gates did not pass. See above for detail."
    exit 1
fi

echo "[run-all-gates] All gates passed."
exit 0
