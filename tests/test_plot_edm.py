from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

import plot_edm

_SYNTHETIC_LOG_TEXT = (
    "Info: VariableMetricBuilder 0 - FCN = 239657.378 Edm = 241476.8088 NCalls = 91\n"
    "Info: VariableMetricBuilder 1 - FCN = 2460.723513 Edm = 1358.762988 NCalls = 104\n"
    "Info: VariableMetricBuilder 2 - FCN = 1307.984942 Edm = 5.913640346 NCalls = 118\n"
    "Info: VariableMetricBuilder 0 - FCN = 1258.971313 Edm = 1.837610217e-10 NCalls = 65\n"
)
_SYNTHETIC_LOG_PARSED = (
    [0, 1, 2, 3],
    [241476.8088, 1358.762988, 5.913640346, 1.837610217e-10],
    [0, 3],
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REAL_QUICKFIT_LOG = (
    _REPO_ROOT
    / "run"
    / "fits"
    / "J100"
    / "run_481_3000_sixPar"
    / "quickFitLog_anaFit_sixPar_bkgOnly.log"
)


def _stub_matplotlib(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict]]:
    # matplotlib.pyplot is imported inside plot_minuit_edm_trace() itself
    # (deferred - see plot_edm.py), only once there is data to plot, so
    # this stub is only needed by tests that actually reach that point:
    # importing plot_edm and calling parse_minuit_edm_log() need none of
    # this at all. The fake savefig records every call and actually
    # writes bytes to the requested path, so file-existence assertions
    # below are testing something real, not just "was called."
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
    fake_matplotlib.pyplot = fake_pyplot

    monkeypatch.setitem(sys.modules, "matplotlib", fake_matplotlib)
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", fake_pyplot)

    return savefig_calls


def test_parse_minuit_edm_log_returns_exact_parsed_values(tmp_path: Path) -> None:
    logfile = tmp_path / "quickFitLog.log"
    logfile.write_text(_SYNTHETIC_LOG_TEXT)

    result = plot_edm.parse_minuit_edm_log(str(logfile))

    assert result == _SYNTHETIC_LOG_PARSED


def test_parse_minuit_edm_log_returns_empty_lists_when_no_matching_lines(
    tmp_path: Path,
) -> None:
    logfile = tmp_path / "quickFitLog.log"
    logfile.write_text("RooFit v3.60 -- nothing matching the Minuit trace pattern here\n")

    result = plot_edm.parse_minuit_edm_log(str(logfile))

    assert result == ([], [], [])


def test_parse_minuit_edm_log_raises_file_not_found_for_missing_file(
    tmp_path: Path,
) -> None:
    # Decision recorded in doc/ACTIVITY_LOG.md's Tier 3 Chunk 9.B entry:
    # unlike the original single function (which caught FileNotFoundError
    # itself and called sys.exit(1)), parse_minuit_edm_log() lets it
    # propagate naturally - it is meant to be a pure, directly-callable
    # function, and sys.exit() inside it would kill the whole calling
    # process rather than let a caller decide how to handle a missing
    # file. plot_minuit_continuous() (below) is the thin CLI-facing
    # wrapper that still does the print + sys.exit(1), preserving the
    # exact external behavior characterized in Chunk 9.A.
    with pytest.raises(FileNotFoundError):
        plot_edm.parse_minuit_edm_log(str(tmp_path / "does_not_exist.log"))


def test_plot_minuit_edm_trace_produces_output_file_for_non_empty_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    savefig_calls = _stub_matplotlib(monkeypatch)
    cumulative_x, edm_values, star_indices = _SYNTHETIC_LOG_PARSED
    outfile = tmp_path / "edm.pdf"

    plot_edm.plot_minuit_edm_trace(cumulative_x, edm_values, star_indices, str(outfile))

    assert outfile.exists()
    assert outfile.stat().st_size > 0
    (call,) = savefig_calls
    outname, kwargs = call
    assert outname == str(outfile)
    assert kwargs == {"bbox_inches": "tight"}


def test_plot_minuit_edm_trace_no_output_for_empty_data(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # No matplotlib stub installed at all - the empty-data early return
    # happens before the deferred "import matplotlib.pyplot", so this
    # exercises real code with zero stubbing.
    outfile = tmp_path / "edm.pdf"

    plot_edm.plot_minuit_edm_trace([], [], [], str(outfile))

    assert not outfile.exists()
    assert "No matching data found." in capsys.readouterr().out


def test_plot_minuit_continuous_produces_output_file_for_log_with_trace_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    savefig_calls = _stub_matplotlib(monkeypatch)
    logfile = tmp_path / "quickFitLog.log"
    logfile.write_text(_SYNTHETIC_LOG_TEXT)
    outfile = tmp_path / "edm.pdf"

    plot_edm.plot_minuit_continuous(str(logfile), str(outfile))

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
    savefig_calls = _stub_matplotlib(monkeypatch)
    assert _REAL_QUICKFIT_LOG.exists(), "expected fixture log missing"
    outfile = tmp_path / "edm.pdf"

    plot_edm.plot_minuit_continuous(str(_REAL_QUICKFIT_LOG), str(outfile))

    assert outfile.exists()
    assert outfile.stat().st_size > 0
    assert len(savefig_calls) == 1


def test_plot_minuit_continuous_no_output_when_no_matching_lines(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # No matplotlib stub installed - see
    # test_plot_minuit_edm_trace_no_output_for_empty_data above for why
    # this path needs none.
    logfile = tmp_path / "quickFitLog.log"
    logfile.write_text("RooFit v3.60 -- nothing matching the Minuit trace pattern here\n")
    outfile = tmp_path / "edm.pdf"

    plot_edm.plot_minuit_continuous(str(logfile), str(outfile))

    assert not outfile.exists()
    assert "No matching data found." in capsys.readouterr().out


def test_plot_minuit_continuous_exits_with_status_1_for_missing_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # No matplotlib stub installed - the missing-file path never reaches
    # plot_minuit_edm_trace() at all.
    with pytest.raises(SystemExit) as exc_info:
        plot_edm.plot_minuit_continuous(
            str(tmp_path / "does_not_exist.log"),
            str(tmp_path / "edm.pdf"),
        )

    assert exc_info.value.code == 1
    assert "Error: The file was not found." in capsys.readouterr().out
