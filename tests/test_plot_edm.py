from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_plot_edm_module(monkeypatch: pytest.MonkeyPatch):
    # plot_edm.py does "import matplotlib.pyplot as plt" (plus the unused
    # "import matplotlib.cm as cm" and "import numpy as np") at module
    # level. Neither matplotlib nor numpy is in requirements-dev-lock.txt
    # (they are not needed by anything else this repo's dev/test venv
    # runs) - the real dev venv genuinely cannot import this file today.
    # In production, plot_edm.py is only ever invoked as a subprocess from
    # within the LCG/CVMFS scientific environment (see run_fit.py's
    # "execute('python plot_edm.py ...')" call), the same environment
    # that provides ROOT - this mirrors that exact situation, so it is
    # stubbed here the same way ROOT is stubbed elsewhere in this suite.
    #
    # The fake matplotlib.pyplot records every call and (for savefig)
    # actually writes bytes to the requested path, so file-existence
    # assertions below are testing something real, not just "was called."
    savefig_calls: list[tuple[str, dict]] = []

    def fake_savefig(outname, **kwargs):
        savefig_calls.append((outname, kwargs))
        with open(outname, "wb") as f:
            f.write(b"fake-plot-bytes")

    fake_pyplot = ModuleType("matplotlib.pyplot")
    no_op_names = (
        "figure",
        "plot",
        "axhline",
        "yscale",
        "xscale",
        "xlabel",
        "ylabel",
        "title",
        "grid",
        "legend",
    )
    for name in no_op_names:
        setattr(fake_pyplot, name, lambda *args, **kwargs: None)
    fake_pyplot.savefig = fake_savefig

    fake_matplotlib = ModuleType("matplotlib")
    fake_cm = ModuleType("matplotlib.cm")
    fake_matplotlib.pyplot = fake_pyplot
    fake_matplotlib.cm = fake_cm

    monkeypatch.setitem(sys.modules, "matplotlib", fake_matplotlib)
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", fake_pyplot)
    monkeypatch.setitem(sys.modules, "matplotlib.cm", fake_cm)
    monkeypatch.setitem(sys.modules, "numpy", ModuleType("numpy"))

    module_path = Path(__file__).resolve().parents[1] / "plot_edm.py"
    spec = importlib.util.spec_from_file_location("plot_edm_under_test", module_path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, savefig_calls


def test_plot_minuit_continuous_produces_output_file_for_log_with_trace_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module, savefig_calls = _load_plot_edm_module(monkeypatch)

    logfile = tmp_path / "quickFitLog.log"
    logfile.write_text(
        "Info: VariableMetricBuilder 0 - FCN = 239657.378 Edm = 241476.8088 NCalls = 91\n"
        "Info: VariableMetricBuilder 1 - FCN = 2460.723513 Edm = 1358.762988 NCalls = 104\n"
        "Info: VariableMetricBuilder 2 - FCN = 1307.984942 Edm = 5.913640346 NCalls = 118\n"
        "Info: VariableMetricBuilder 0 - FCN = 1258.971313 Edm = 1.837610217e-10 NCalls = 65\n"
    )
    outfile = tmp_path / "edm.pdf"

    module.plot_minuit_continuous(str(logfile), str(outfile))

    assert outfile.exists()
    assert outfile.stat().st_size > 0
    (call,) = savefig_calls
    outname, kwargs = call
    assert outname == str(outfile)
    assert kwargs == {"bbox_inches": "tight"}


def test_plot_minuit_continuous_produces_output_for_real_quickfit_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The plan calls this out explicitly as a real, already-available
    # fixture - a genuine production quickFit log, not a synthetic one.
    module, savefig_calls = _load_plot_edm_module(monkeypatch)

    repo_root = Path(__file__).resolve().parents[1]
    real_log = (
        repo_root
        / "run"
        / "fits"
        / "J100"
        / "run_481_3000_sixPar"
        / "quickFitLog_anaFit_sixPar_bkgOnly.log"
    )
    assert real_log.exists(), "expected fixture log missing"
    outfile = tmp_path / "edm.pdf"

    module.plot_minuit_continuous(str(real_log), str(outfile))

    assert outfile.exists()
    assert outfile.stat().st_size > 0
    assert len(savefig_calls) == 1


def test_plot_minuit_continuous_no_output_when_no_matching_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module, savefig_calls = _load_plot_edm_module(monkeypatch)

    logfile = tmp_path / "quickFitLog.log"
    logfile.write_text("RooFit v3.60 -- nothing matching the Minuit trace pattern here\n")
    outfile = tmp_path / "edm.pdf"

    module.plot_minuit_continuous(str(logfile), str(outfile))

    assert not outfile.exists()
    assert savefig_calls == []
    assert "No matching data found." in capsys.readouterr().out


def test_plot_minuit_continuous_exits_with_status_1_for_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module, savefig_calls = _load_plot_edm_module(monkeypatch)

    with pytest.raises(SystemExit) as exc_info:
        module.plot_minuit_continuous(
            str(tmp_path / "does_not_exist.log"),
            str(tmp_path / "edm.pdf"),
        )

    assert exc_info.value.code == 1
    assert savefig_calls == []
    assert "Error: The file was not found." in capsys.readouterr().out
