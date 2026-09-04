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

# python/FindBHWindow.py is a whole-script CLI tool today (Chunk 14.A -
# its Step B extraction has not run yet): every third-party dependency it
# needs (matplotlib, matplotlib.pyplot, uproot, numpy, pyBumpHunter) is
# imported at module scope, and none of the five is importable in this
# repository's own pytest dev venv - confirmed directly. This
# characterizes NpEncoder in isolation (the only genuinely ROOT/heavy-
# dependency-free logic this file has today) with a fake numpy exposing
# real, instantiable integer/floating/ndarray classes (matching the
# isinstance() checks NpEncoder.default() makes) and trivial empty fakes
# for the other four - the same ModuleType-fake convention already used
# for ROOT/PreFit/ExtractPostfitFromWS/ExtractFitParameters, applied to a
# numpy module name for the first time in this plan.


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


def _install_fake_heavy_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_numpy = ModuleType("numpy")
    fake_numpy.integer = _FakeNpInteger  # type: ignore[attr-defined]
    fake_numpy.floating = _FakeNpFloating  # type: ignore[attr-defined]
    fake_numpy.ndarray = _FakeNpNdarray  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)

    for module_name in ("matplotlib", "matplotlib.pyplot", "uproot", "pyBumpHunter"):
        monkeypatch.setitem(sys.modules, module_name, ModuleType(module_name))

    # FindBHWindow.py calls matplotlib.use("Agg") at module scope (line 2)
    # - the empty fake above needs this one attribute to satisfy that call.
    fake_matplotlib = sys.modules["matplotlib"]
    fake_matplotlib.use = lambda *args, **kwargs: None  # type: ignore[attr-defined]


def _load_find_bh_window_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    _install_fake_heavy_dependencies(monkeypatch)

    module_path = _REPO_ROOT / "python" / "FindBHWindow.py"
    spec = importlib.util.spec_from_file_location("find_bh_window_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- NpEncoder: characterized with 5 fake heavy dependencies --------------


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
