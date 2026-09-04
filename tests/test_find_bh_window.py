from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

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

# python/FindBHWindow.py (Chunk 14.B): matplotlib/matplotlib.pyplot/
# uproot/pyBumpHunter are now deferred into the one function each
# actually needs; only `numpy` remains module-level. Loading this module
# therefore now needs only a fake `numpy` - a genuine, called-out
# exception to the Test Relocation Rule (Chunk 14's own plan text): Step
# A's NpEncoder tests dropped three of their four stubs here, since the
# other three heavy dependencies are no longer module-level. The fake
# numpy exposes real, instantiable integer/floating/ndarray classes,
# matching the isinstance() checks NpEncoder.default() makes - the same
# ModuleType-fake convention already used for ROOT/PreFit/
# ExtractPostfitFromWS/ExtractFitParameters, applied to a numpy module
# name for the first time in this plan.


class _FakeNpInteger:
    def __init__(self, value: int) -> None:
        self._value = value

    def __int__(self) -> int:
        return self._value


class _FakeNpFloating:
    def __init__(self, value: float) -> None:
        self._value = value

    def __float__(self) -> float:
        return self._value


class _FakeNpNdarray:
    def __init__(self, data: list) -> None:
        self._data = data

    def tolist(self) -> list:
        return self._data


def _install_fake_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_numpy = ModuleType("numpy")
    fake_numpy.integer = _FakeNpInteger  # type: ignore[attr-defined]
    fake_numpy.floating = _FakeNpFloating  # type: ignore[attr-defined]
    fake_numpy.ndarray = _FakeNpNdarray  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)


def _load_find_bh_window_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    _install_fake_numpy(monkeypatch)

    module_path = _REPO_ROOT / "python" / "FindBHWindow.py"
    spec = importlib.util.spec_from_file_location("find_bh_window_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- NpEncoder: characterized with a single fake numpy dependency --------


def test_npencoder_serializes_numpy_integer(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_find_bh_window_module(monkeypatch)

    result = module.NpEncoder().default(_FakeNpInteger(5))

    assert result == 5
    assert isinstance(result, int)


def test_npencoder_serializes_numpy_floating(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_find_bh_window_module(monkeypatch)

    result = module.NpEncoder().default(_FakeNpFloating(1.5))

    assert result == 1.5
    assert isinstance(result, float)


def test_npencoder_serializes_numpy_ndarray(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_find_bh_window_module(monkeypatch)

    result = module.NpEncoder().default(_FakeNpNdarray([1, 2, 3]))

    assert result == [1, 2, 3]


def test_npencoder_falls_back_to_default_for_unknown_types(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_find_bh_window_module(monkeypatch)

    class _Unrelated:
        pass

    with pytest.raises(TypeError):
        module.NpEncoder().default(_Unrelated())


# --- parse_args(): zero ROOT/uproot/pyBumpHunter needed, only numpy ------


def test_parse_args_parses_required_and_default_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_find_bh_window_module(monkeypatch)

    args = module.parse_args(["--inputfile", "in.root"])

    assert args.inputfile == "in.root"
    assert args.datahist == "data"
    assert args.bkghist == "postfit"
    assert args.outputjson == "BHresults.json"
    assert args.usebinnumbers is False


def test_parse_args_accepts_every_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_find_bh_window_module(monkeypatch)

    args = module.parse_args(
        [
            "--inputfile",
            "in.root",
            "--datahist",
            "d",
            "--bkghist",
            "b",
            "--outputjson",
            "out.json",
            "--inputxmlcard",
            "in.xml",
            "--outputxmlcard",
            "out.xml",
            "--usebinnumbers",
        ]
    )

    assert args.inputfile == "in.root"
    assert args.datahist == "d"
    assert args.bkghist == "b"
    assert args.outputjson == "out.json"
    assert args.inputxmlcard == "in.xml"
    assert args.outputxmlcard == "out.xml"
    assert args.usebinnumbers is True


def test_parse_args_requires_inputfile(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_find_bh_window_module(monkeypatch)

    with pytest.raises(SystemExit):
        module.parse_args([])


# --- crop_data_to_background_range(): plain lists, no numpy call needed --


def test_crop_data_to_background_range_finds_the_matching_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_find_bh_window_module(monkeypatch)
    bins = [10, 20, 30]
    bins_data = [0, 5, 10, 15, 20, 25, 30, 35]
    data = [0, 1, 2, 3, 4, 5, 6, 7]

    cropped, firstbindata = module.crop_data_to_background_range(bins, bins_data, data)

    # Independently verified before writing this assertion: the first
    # bins_data entry >= bins[0]=10 is index 2; the *last* entry
    # <= bins[-1]=30 is index 6 (the loop keeps overwriting lastbindata,
    # it does not break early on the second search - preserved exactly).
    assert firstbindata == 2
    assert cropped == [2, 3, 4, 5]


# --- compute_mask_window(): plain dict/list, no numpy call needed --------


def test_compute_mask_window_uses_observable_values_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_find_bh_window_module(monkeypatch)
    state = {"min_loc_ar": [3], "min_width_ar": [2]}
    bins = [0, 10, 20, 30, 40, 50, 60]

    result = module.compute_mask_window(state, bins, firstbindata=1, use_bin_numbers=False)

    assert result["MaskMin"] == bins[3]
    assert result["MaskMax"] == bins[3 + 2]
    assert result["BlindRange"] == "30,50"
    assert result["pyBHresult"] is state


def test_compute_mask_window_uses_bin_numbers_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A genuinely different formula from the default branch above - not
    # an alias of it - preserved and tested as its own distinct branch.
    module = _load_find_bh_window_module(monkeypatch)
    state = {"min_loc_ar": [3], "min_width_ar": [2]}
    bins = [0, 10, 20, 30, 40, 50, 60]

    result = module.compute_mask_window(state, bins, firstbindata=1, use_bin_numbers=True)

    assert result["MaskMin"] == 1 + 3
    assert result["MaskMax"] == 1 + 3 + 2
    assert result["BlindRange"] == "4,6"


# --- write_mask_window_json(): exercises NpEncoder end to end ------------


def test_write_mask_window_json_uses_npencoder_for_numpy_types(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_find_bh_window_module(monkeypatch)
    outfile = tmp_path / "out.json"
    out_dict = {
        "MaskMin": _FakeNpInteger(5),
        "MaskMax": _FakeNpFloating(10.0),
        "BlindRange": "5,10",
    }

    module.write_mask_window_json(out_dict, str(outfile))

    written = json.loads(outfile.read_text())
    assert written == {"MaskMin": 5, "MaskMax": 10.0, "BlindRange": "5,10"}


# --- main(): real, whole-script end-to-end behavior ------------------------
#
# python/FindBHWindow.py's own production interpreter,
# pyBumpHunter/pyBH_env/bin/python3, is confirmed broken in this
# environment: its pyvenv.cfg sets include-system-site-packages = false,
# and neither uproot nor matplotlib was ever installed into its own
# site-packages (only pyBumpHunter itself, as an egg) -
# `pyBumpHunter/pyBH_env/bin/python3 -c "import uproot"` fails with
# ModuleNotFoundError. This is a separate, pre-existing environment gap,
# not something this chunk's extraction caused or is in scope to fix
# (mirrors createBinning.py's own missing-resolutionFits.root gap).
#
# A working alternative was found and verified instead: the ambient
# `python` scripts/setup_buildAndFit.sh already puts on PATH (the same
# LCG_102a interpreter test_plot_post_fit.py's real-ROOT tests use) has
# numpy/matplotlib/uproot all genuinely importable directly. It does not
# have a genuine pyBumpHunter (importing it there resolves to this
# repository's own top-level pyBumpHunter/ submodule directory as an
# empty namespace package) unless the submodule's own package directory
# is explicitly appended to the *existing* PYTHONPATH (not replacing it -
# replacing it was tried first and broke matplotlib, since the LCG
# view's own setup already populates PYTHONPATH with the entries
# matplotlib/uproot resolve from). With that append, all four
# dependencies resolve correctly together - no new package installs, no
# production-code change; this is purely a test-harness environment
# setup, mirrored exactly in doc/TIER3_COMPLETION_PLAN.md Chunk 14's own
# "A further discovery" section.
#
# Since seed=666 is fixed, the result is fully deterministic - confirmed
# directly across two separate real runs before writing this assertion.
# Kept unchanged from Chunk 14.A (Test Relocation Rule) - now exercises
# the extracted main(), not the original inline script.


def _run_find_bh_window_script(
    inputfile: Path,
    bkghist: str,
    datahist: str,
    outputjson: Path,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    # scripts/setup_buildAndFit.sh checks for xmlAnaWSBuilder/quickFit
    # relative to the *current* directory, so it must be sourced while
    # still at the repository root - the subprocess itself therefore
    # always runs with cwd=_REPO_ROOT, and this probe `cd`s into the
    # caller's requested `cwd` only afterward, for the actual script
    # invocation (so bump.png/BH_statistics.png land there, not in the
    # repository).
    probe = f"""
repo_dir={str(_REPO_ROOT)!r}
source "$repo_dir/scripts/setup_buildAndFit.sh" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    echo "setup_status=$setup_status"
    exit "$setup_status"
fi

export PYTHONPATH="$repo_dir/pyBumpHunter:$PYTHONPATH"
cd {str(cwd)!r}
python3 "$repo_dir/python/FindBHWindow.py" \\
  --inputfile "{inputfile}" \\
  --bkghist {bkghist} --datahist {datahist} \\
  --outputjson "{outputjson}"
"""
    return subprocess.run(
        ["bash", "-lc", probe],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.requires_analysis_dependencies
def test_findbhwindow_script_computes_expected_mask_window_for_real_fixture(
    tmp_path: Path,
) -> None:
    # No @pytest.mark.requires_root: this script never imports ROOT
    # (confirmed directly - it depends on uproot/pyBumpHunter instead),
    # so requires_analysis_dependencies alone correctly describes what it
    # needs (a real CVMFS/LCG mount), matching the marker's own
    # documented meaning in pyproject.toml. This is the first test in
    # this repository to use requires_analysis_dependencies without
    # requires_root - a genuinely new combination, not an oversight.
    assert _FIXTURE_POSTFIT_FILE.exists(), "expected fixture PostFit ROOT file missing"
    outfile = tmp_path / "BHresults.json"

    # bump.png/BH_statistics.png are hardcoded, cwd-relative filenames the
    # script writes with no path parameter - the probe `cd`s into
    # tmp_path before invoking the script, keeping them out of the
    # repository and leaving nothing under the repo changed by this test.
    completed = _run_find_bh_window_script(
        _FIXTURE_POSTFIT_FILE,
        "Run3TLA_rebinned/postfit",
        "Run3TLA_rebinned/data",
        outfile,
        tmp_path,
    )

    assert completed.returncode == 0, (
        "FindBHWindow.py subprocess failed:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert outfile.exists()
    assert (tmp_path / "bump.png").exists()
    assert (tmp_path / "BH_statistics.png").exists()

    result = json.loads(outfile.read_text())
    assert result["MaskMin"] == 595.0
    assert result["MaskMax"] == 691.0
    assert result["BlindRange"] == "595,691"
    assert "pyBHresult" in result
