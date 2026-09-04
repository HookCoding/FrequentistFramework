from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from python import createBinning as create_binning

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RESOLUTION_FIT_PATH = _REPO_ROOT / "Input" / "data" / "dijetisrTLA" / "resolutionFits.root"

# python/createBinning.py defers `import ROOT` into each of the three
# functions that actually need it (load_resolution_fit(),
# build_binning_histogram(), main()), matching every other deferred-import
# module in this plan - only parse_args()/resolve_bin_edges() are
# ROOT-free. Confirmed directly: this repository's own pytest dev venv
# cannot import ROOT at all, and `from python import createBinning`
# still succeeds because of that deferral - the parse_args()/
# resolve_bin_edges() tests below need no stubbing at all.


# --- parse_args(): zero ROOT needed ---------------------------------------


def test_parse_args_parses_required_and_default_flags() -> None:
    args = create_binning.parse_args(["-s", "481", "-o", "out.root"])

    assert args.start == 481
    assert args.end == 1000
    assert args.output == "out.root"


def test_parse_args_accepts_long_flags_and_explicit_end() -> None:
    args = create_binning.parse_args(["--start", "481", "--end", "3000", "--output", "out.root"])

    assert args.start == 481
    assert args.end == 3000
    assert args.output == "out.root"


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["-s", "481"],
        ["-o", "out.root"],
    ],
)
def test_parse_args_requires_start_and_output(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        create_binning.parse_args(argv)


# --- resolve_bin_edges(): zero ROOT needed, a plain .Eval()-object ---------


class _FakeResolutionFit:
    """A hand-written fake exposing only `.Eval(x)`, exactly like a ROOT
    TF1 - resolve_bin_edges() needs nothing else, per doc/TIER3_COMPLETION_PLAN.md
    Chunk 13's own decomposition table."""

    def __init__(self, resolution: float) -> None:
        self._resolution = resolution

    def Eval(self, x: float) -> float:  # noqa: N802 - matches ROOT's own method name
        return self._resolution


def test_resolve_bin_edges_matches_the_real_fixture_result() -> None:
    # Cross-checks, via a pure-Python path with zero ROOT involved, the
    # same flat-5%-resolution/[481, 3000] result already verified for
    # real once this session (doc/TIER3_EXECUTION_TRACE.md Section 5) and
    # again by Chunk 13.A's own end-to-end subprocess test below - 38
    # bins, with the exact edge list independently computed and pinned
    # here (verified via a standalone reimplementation of the same
    # algorithm before writing this assertion, not guessed).
    edges = create_binning.resolve_bin_edges(_FakeResolutionFit(0.05), 481, 3000)

    assert edges == [
        481,
        505,
        530,
        556,
        584,
        613,
        644,
        676,
        710,
        746,
        783,
        822,
        863,
        906,
        951,
        999,
        1049,
        1101,
        1156,
        1214,
        1275,
        1339,
        1406,
        1476,
        1550,
        1628,
        1709,
        1794,
        1884,
        1978,
        2077,
        2181,
        2290,
        2404,
        2524,
        2650,
        2782,
        2921,
        3000,
    ]


def test_resolve_bin_edges_with_a_different_resolution_and_range() -> None:
    # A second, independent case (different resolution and range) proving
    # the previous test's match isn't coincidental - edge list computed
    # the same verified way.
    edges = create_binning.resolve_bin_edges(_FakeResolutionFit(0.1), 100, 200)

    assert edges == [100, 110, 121, 133, 146, 161, 177, 195, 200]


def test_resolve_bin_edges_caps_the_last_edge_at_rangehigh() -> None:
    # A range whose growth step would overshoot rangehigh must clamp to
    # it exactly, not exceed it - the min(..., rangehigh) call this
    # asserts on.
    edges = create_binning.resolve_bin_edges(_FakeResolutionFit(0.9), 100, 150)

    assert edges[-1] == 150
    assert edges[-2] < 150


# --- load_resolution_fit(): real ROOT, two failure paths -------------------


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


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_load_resolution_fit_raises_oserror_for_a_missing_file() -> None:
    # Confirmed directly, while writing this chunk's extraction: on this
    # repository's own installed PyROOT, ROOT.TFile.Open() itself raises
    # its own OSError for a missing file (a different message than
    # load_resolution_fit()'s own "if not tfile" guard would raise) -
    # that guard is therefore currently unreachable in practice here, but
    # is preserved verbatim from the original script rather than removed,
    # since it is not dead code on every PyROOT build (some return a null
    # TFile instead of raising). This test pins down the real, observable
    # behavior (an OSError is raised either way) without asserting on
    # either branch's specific message, since the actually-raised one
    # comes from ROOT, not from this function's own contract.
    snippet = """
import sys
sys.path.insert(0, "python")
import createBinning as cb

try:
    cb.load_resolution_fit("does/not/exist.root")
    raise SystemExit("expected OSError, none was raised")
except OSError:
    pass
print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_load_resolution_fit_raises_keyerror_when_key_missing(tmp_path: Path) -> None:
    # Unlike the OSError path above, this branch - a valid, openable file
    # that simply lacks the "gsc_mjj_reso_fit" key - is genuinely reached
    # by this function's own code, confirmed directly.
    empty_fixture = tmp_path / "empty_fixture.root"
    snippet = f"""
import ROOT
f = ROOT.TFile.Open({str(empty_fixture)!r}, "RECREATE")
f.Close()

import sys
sys.path.insert(0, "python")
import createBinning as cb

try:
    cb.load_resolution_fit({str(empty_fixture)!r})
    raise SystemExit("expected KeyError, none was raised")
except KeyError as error:
    assert "gsc_mjj_reso_fit" in str(error), error
print("SNIPPET_OK")
"""
    _assert_snippet_ok(_run_real_root_snippet(snippet))


# --- main(): unmodified end-to-end behavior, relocated from Chunk 13.A ----
#
# python/createBinning.py needs a real ROOT runtime this repository's own
# pytest dev venv does not have, and its input path is hardcoded, not
# injectable via any CLI flag, and this repository commits no real file
# at that path. This test writes a synthetic fixture to that real
# relative path before running the script, and removes it again in a
# `finally` block regardless of outcome - leaving nothing under Input/
# changed.


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
    # to exactly 38 bins. Now exercises the extracted main() (Chunk
    # 13.B), not the original inline script - the assertions are
    # unchanged from Chunk 13.A, per the Test Relocation Rule.
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
