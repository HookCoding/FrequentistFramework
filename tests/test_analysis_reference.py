import json
from pathlib import Path

import pytest

from python.analysis_reference import (
    _extract_optional_bh_pvalue,
    _validate_analysis_reference,
    _validate_workflow_payload,
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
    assert set(written_output.keys()) == {"J100", "J50"}

    assert written_output["J100"]["fit_parameters"]["nbkg"] == pytest.approx(7.65246e8)
    assert written_output["J100"]["fit_parameters"]["p2"] == pytest.approx(8.79763)
    assert written_output["J100"]["fit_parameters"]["p3"] == pytest.approx(6.34479)
    assert written_output["J100"]["fit_parameters"]["p4"] == pytest.approx(1.12277)
    assert written_output["J100"]["fit_parameters"]["p5"] == pytest.approx(0.358837)
    assert written_output["J100"]["fit_parameters"]["p6"] == pytest.approx(0.0417963)
    assert written_output["J100"]["p_chi2"] is None
    assert written_output["J100"]["p_bh"] is None
    assert written_output["J100"]["cls_limit_points"] == []

    assert written_output["J50"]["fit_parameters"]["nbkg"] == pytest.approx(6.53097e8)
    assert written_output["J50"]["fit_parameters"]["p2"] == pytest.approx(6.5024)
    assert written_output["J50"]["fit_parameters"]["p3"] == pytest.approx(6.15143)
    assert written_output["J50"]["fit_parameters"]["p4"] == pytest.approx(0.0699209)
    assert written_output["J50"]["fit_parameters"]["p5"] == pytest.approx(-0.0273909)
    assert written_output["J50"]["fit_parameters"]["p6"] == pytest.approx(-0.00118504)
    assert written_output["J50"]["p_chi2"] is None
    assert written_output["J50"]["p_bh"] is None
    assert written_output["J50"]["cls_limit_points"] == []


def test_background_only_build_does_not_require_bhresults_json(tmp_path: Path) -> None:
    j100_dir = tmp_path / "run" / "fits" / "J100" / "run_481_3000_sixPar"
    j50_dir = tmp_path / "run" / "fits" / "J50" / "run_344_2079_sixPar"
    j100_dir.mkdir(parents=True)
    j50_dir.mkdir(parents=True)

    (j100_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log").write_text(
        "nbkg = 1000\np2 = 2.5\np3 = 3.5\np4 = 4.5\np5 = 5.5\np6 = 6.5\n",
        encoding="utf-8",
    )
    (j50_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log").write_text(
        "nbkg = 2000\np2 = 1.5\np3 = 2.5\np4 = 3.5\np5 = 4.5\np6 = 5.5\n",
        encoding="utf-8",
    )

    output = build_analysis_reference(repo_root=tmp_path)

    assert output["J100"]["fit_parameters"]["nbkg"] == pytest.approx(1000.0)
    assert output["J100"]["p_chi2"] is None
    assert output["J100"]["p_bh"] is None

    assert output["J50"]["fit_parameters"]["nbkg"] == pytest.approx(2000.0)
    assert output["J50"]["p_chi2"] is None
    assert output["J50"]["p_bh"] is None


def test_optional_bh_pvalue_is_parsed_when_available(tmp_path: Path) -> None:
    j100_dir = tmp_path / "run" / "fits" / "J100" / "run_481_3000_sixPar"
    j50_dir = tmp_path / "run" / "fits" / "J50" / "run_344_2079_sixPar"
    j100_dir.mkdir(parents=True)
    j50_dir.mkdir(parents=True)

    (j100_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log").write_text(
        "nbkg = 100\np2 = 2\n", encoding="utf-8"
    )
    (j50_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log").write_text(
        "nbkg = 200\np2 = 3\n", encoding="utf-8"
    )
    (j100_dir / "BHresults.json").write_text(
        json.dumps({"pyBHresult": {"global_Pval": 0.42}}), encoding="utf-8"
    )

    output = build_analysis_reference(repo_root=tmp_path)

    assert output["J100"]["p_bh"] == pytest.approx(0.42)
    assert output["J50"]["p_bh"] is None


def _valid_workflow_payload() -> dict[str, object]:
    return {
        "fit_parameters": {"nbkg": 1.0},
        "p_chi2": None,
        "p_bh": None,
        "cls_limit_points": [],
    }


def test_analysis_reference_rejects_unexpected_workflow() -> None:
    payload = {
        "J100": _valid_workflow_payload(),
        "J50": _valid_workflow_payload(),
        "J75": _valid_workflow_payload(),
    }

    with pytest.raises(ValueError, match=r"unexpected=.*J75"):
        _validate_analysis_reference(payload)


def test_workflow_payload_rejects_unexpected_key() -> None:
    payload = _valid_workflow_payload()
    payload["unexpected"] = 123

    with pytest.raises(ValueError, match=r"unexpected=.*unexpected"):
        _validate_workflow_payload("J100", payload)


def test_optional_bh_pvalue_rejects_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "BHresults.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="Could not read valid JSON"):
        _extract_optional_bh_pvalue(tmp_path)


def test_optional_bh_pvalue_rejects_non_object_json(tmp_path: Path) -> None:
    (tmp_path / "BHresults.json").write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a JSON object"):
        _extract_optional_bh_pvalue(tmp_path)


def test_optional_bh_pvalue_wraps_read_oserror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bh_path = tmp_path / "BHresults.json"
    bh_path.write_text("{}", encoding="utf-8")
    original_read_text = Path.read_text

    def raise_for_bh_path(path: Path, *args: object, **kwargs: object) -> str:
        if path == bh_path:
            raise OSError("simulated read failure")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", raise_for_bh_path)

    with pytest.raises(ValueError, match="Could not read valid JSON"):
        _extract_optional_bh_pvalue(tmp_path)
