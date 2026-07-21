from pathlib import Path

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
    assert written_output["fit_parameters"]["slope"] == 0.94
    assert written_output["fit_parameters"]["intercept"] == 0.94
    assert written_output["p_chi2"] == 0.36
    assert written_output["p_bh"] == 0.2
