from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RESOLUTION_FIT_PATH = _REPO_ROOT / "Input" / "data" / "dijetisrTLA" / "resolutionFits.root"

# python/createBinning.py is a flat top-level script today (Chunk 13.A -
# its Step B extraction has not run yet): it has no functions at all and
# always executes top-to-bottom on import or execution. This
# characterizes its whole-script behavior via subprocess, mirroring
# Chunk 10.A's own precedent for plotPostFit.py before its extraction
# (tests/test_plot_post_fit.py's Step A/end-to-end test).
#
# createBinning.py's input path, "Input/data/dijetisrTLA/resolutionFits.root",
# is hardcoded and not injectable via any CLI flag, and this repository
# commits no real file at that path (confirmed directly - see
# doc/TIER3_EXECUTION_TRACE.md Section 5). This test therefore writes a
# synthetic fixture to that real relative path before running the script,
# and removes it again in a `finally` block regardless of outcome -
# leaving nothing under Input/ changed, matching the manual verification
# already performed once this session when createBinning.py's syntax
# error was fixed.


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


def _write_synthetic_resolution_fit() -> None:
    # A flat 5%-resolution TF1 - the same synthetic fixture already
    # verified once this session (doc/TIER3_EXECUTION_TRACE.md Section 5)
    # to make createBinning.py's real growth loop produce exactly 38 bins
    # spanning [481, 3000].
    snippet = f"""
import ROOT
f = ROOT.TFile.Open({str(_RESOLUTION_FIT_PATH)!r}, "RECREATE")
fit = ROOT.TF1("gsc_mjj_reso_fit", "0.05 + 0.0*x", 0, 5000)
fit.Write()
f.Close()
print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_createBinning_script_produces_expected_binning_for_real_fixture(
    tmp_path: Path,
) -> None:
    # Reproduces exactly the verification already performed once this
    # session, when createBinning.py's syntax error was fixed: a flat
    # 5%-resolution TF1 over [0, 5000] against range [481, 3000] resolves
    # to exactly 38 bins. This is the current, unmodified script's real
    # behavior, pinned down before any extraction (Chunk 13's Step A).
    assert (
        not _RESOLUTION_FIT_PATH.exists()
    ), "a real resolutionFits.root already exists - refusing to overwrite it"
    outfile = tmp_path / "mjjResolutionBinning_481.root"

    _write_synthetic_resolution_fit()
    try:
        probe = f"""
repo_dir="$PWD"
source "$repo_dir/scripts/setup_buildAndFit.sh" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    echo "setup_status=$setup_status"
    exit "$setup_status"
fi

python3 "$repo_dir/python/createBinning.py" -s 481 -e 3000 -o "{outfile}"
"""
        completed = subprocess.run(
            ["bash", "-lc", probe],
            cwd=_REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, (
            "createBinning.py subprocess failed:\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    finally:
        _RESOLUTION_FIT_PATH.unlink(missing_ok=True)

    assert outfile.exists()

    verify_snippet = f"""
import ROOT
f = ROOT.TFile.Open({str(outfile)!r})
h = f.Get("mjjBinning")
assert h, "mjjBinning histogram missing from output file"
assert h.GetNbinsX() == 38, h.GetNbinsX()
assert h.GetXaxis().GetBinLowEdge(1) == 481.0
assert h.GetXaxis().GetBinUpEdge(h.GetNbinsX()) == 3000.0
f.Close()
print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(verify_snippet))
