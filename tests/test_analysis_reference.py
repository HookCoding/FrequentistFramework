from pathlib import Path

import pytest

from python.analysis_reference import (
    build_analysis_reference,
    read_analysis_reference,
    write_analysis_reference,
)


def test_analysis_reference_matches_frozen_output(tmp_path: Path) -> None:
    output = build_analysis_reference()
    reference_path = Path(__file__).resolve().parent / "references" / "analysis_reference.json"

    write_analysis_reference(tmp_path / "analysis_reference.json", output)
    written_output = read_analysis_reference(tmp_path / "analysis_reference.json")
    expected_output = read_analysis_reference(reference_path)

    assert written_output == expected_output
    assert written_output["fit_parameters"]["nbkg"] == pytest.approx(1.77642e7)
    assert written_output["fit_parameters"]["p2"] == pytest.approx(-23.6002)
    assert written_output["fit_parameters"]["p3"] == pytest.approx(28.4426)
    assert written_output["fit_parameters"]["p4"] == pytest.approx(7.96101)
    assert written_output["fit_parameters"]["p5"] == pytest.approx(1.27154)
    assert written_output["fit_parameters"]["p6"] == pytest.approx(0.102273)
    assert written_output["fit_parameters"]["p7"] == pytest.approx(0.00290281)
    assert written_output["p_chi2"] is None
    assert written_output["p_bh"] == pytest.approx(0.2368)
    assert written_output["cls_limit_points"] == []
