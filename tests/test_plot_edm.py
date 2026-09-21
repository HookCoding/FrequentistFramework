"""Unit tests for plot_edm.py (decomposition plan section 8).

Importable as a bare top-level module here because `python3 -m pytest tests -q`, run from the
repository root as tests/run_all.sh does, puts the current working directory - the repository
root - on sys.path[0] the same way any `python -m` invocation does. That is a different
mechanism from tests/conftest.py's explicit `python/` insertion, and it is what makes a file
that lives at the repository root, rather than under python/, importable here at all. Verified
empirically rather than assumed.

parse_edm_trace keeps its name without a leading underscore: it is the one pure function in the
file and the one place a silent regex drift in the Minuit2 log format would go unnoticed, since
run_anaFit.py:129 calls plot_edm.py with execute() and ignores its exit code entirely.
"""

import pytest

from plot_edm import parse_edm_trace, _plot_edm_trace, plot_minuit_continuous

LOG_EXCERPT = """\
Some other line that does not match anything.
VariableMetric: 1 - FCN = 123.456 Edm = 1.5e-02 NCalls = 10
VariableMetric: 0 - FCN = 100.0 Edm = 5.0e-01 NCalls = 1
VariableMetric: 2 - FCN = 99.0 Edm = -3.2e-05 NCalls = 12
"""


def test_parse_edm_trace_reads_matching_lines_and_marks_resets(tmp_path):
    log = tmp_path / "fit.log"
    log.write_text(LOG_EXCERPT)

    cumulative_x, edm_values, star_indices = parse_edm_trace(str(log))

    assert cumulative_x == [0, 1, 2]
    assert edm_values == pytest.approx([1.5e-02, 5.0e-01, -3.2e-05])
    # The internal-iteration-0 line is the second matching line, so its global index is 1.
    assert star_indices == [1]


def test_parse_edm_trace_a_non_matching_line_contributes_nothing(tmp_path):
    log = tmp_path / "fit.log"
    log.write_text("nothing to see here\nnor here\n")

    cumulative_x, edm_values, star_indices = parse_edm_trace(str(log))

    assert cumulative_x == []
    assert edm_values == []
    assert star_indices == []


def test_parse_edm_trace_scientific_notation_parses(tmp_path):
    log = tmp_path / "fit.log"
    log.write_text("VariableMetric: 3 - FCN = 100.0 Edm = 2.71828e-07 NCalls = 4\n")

    cumulative_x, edm_values, star_indices = parse_edm_trace(str(log))

    assert edm_values == pytest.approx([2.71828e-07])


def test_parse_edm_trace_missing_file_prints_and_exits(capsys):
    with pytest.raises(SystemExit) as excinfo:
        parse_edm_trace("/no/such/file/anywhere.log")
    assert excinfo.value.code == 1
    assert "not found" in capsys.readouterr().out


def test_plot_edm_trace_with_no_data_prints_and_returns_without_a_file(tmp_path, capsys):
    outname = tmp_path / "should_not_exist.png"
    _plot_edm_trace([], [], [], str(outname))
    assert "No matching data found." in capsys.readouterr().out
    assert not outname.exists()


def test_plot_edm_trace_writes_the_output_file(tmp_path):
    outname = tmp_path / "trace.png"
    _plot_edm_trace([0, 1], [1.0, 0.5], [0], str(outname))
    assert outname.exists()
    assert outname.stat().st_size > 0


def test_plot_minuit_continuous_coordinates_parse_then_plot(tmp_path):
    log = tmp_path / "fit.log"
    log.write_text(LOG_EXCERPT)
    outname = tmp_path / "trace.png"

    plot_minuit_continuous(str(log), str(outname))

    assert outname.exists()
    assert outname.stat().st_size > 0
