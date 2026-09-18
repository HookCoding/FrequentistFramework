#!/usr/bin/env bash
# Both test suites, in the order that reports a break soonest.
#
#   . setup.sh                  # the LCG_102a view; see tests/conftest.py for why it is required
#   bash tests/run_all.sh --quick    # unit suite, then J100 only        (~2 min)
#   bash tests/run_all.sh            # unit suite, then both analyses    (~4-6 min)
#
# Arguments are passed through to `repro.py check`.
#
# The unit suite runs first and stops the script on failure. It takes seconds; `check` re-runs
# real fits and takes minutes. Running it second means an extraction that broke something is
# reported after a full re-fit rather than before one.
#
# A green `check` on its own is NOT the bar. README.md says commit only on PASS, and that means
# both suites - a refactor can leave every recorded number untouched and still have broken a
# function that no recorded number happens to exercise.
#
# tests/repro.py is deliberately not modified to do this. It is the safety net for the
# decomposition work, and a wrapper gets the same result without editing it.

set -u

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

echo "== unit suite =="
if ! python3 -m pytest tests -q; then
    echo
    echo "FAIL: the unit suite failed. repro.py check was not run - fix this first." >&2
    exit 1
fi

echo
echo "== reproducibility check =="
python3 tests/repro.py check "$@"
