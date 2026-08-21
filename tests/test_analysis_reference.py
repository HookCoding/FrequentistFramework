import json
from pathlib import Path

import pytest

from python.analysis_reference import (
    FIT_PARAMETER_ATOL,
    FIT_PARAMETER_RTOL,
    PVALUE_ATOL,
    PVALUE_RTOL,
    _extract_optional_bh_pvalue,
    _validate_analysis_provenance,
    _validate_analysis_reference,
    _validate_workflow_payload,
    assert_analysis_reference_close,
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
    assert written_output["J100"]["p_chi2"] == pytest.approx(0.018448750724012808)
    assert written_output["J100"]["p_bh"] is None
    assert written_output["J100"]["cls_limit_points"] == []

    assert written_output["J50"]["fit_parameters"]["nbkg"] == pytest.approx(6.53097e8)
    assert written_output["J50"]["fit_parameters"]["p2"] == pytest.approx(6.5024)
    assert written_output["J50"]["fit_parameters"]["p3"] == pytest.approx(6.15143)
    assert written_output["J50"]["fit_parameters"]["p4"] == pytest.approx(0.0699209)
    assert written_output["J50"]["fit_parameters"]["p5"] == pytest.approx(-0.0273909)
    assert written_output["J50"]["fit_parameters"]["p6"] == pytest.approx(-0.00118504)
    assert written_output["J50"]["p_chi2"] == pytest.approx(0.07853114301666252)
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


def test_analysis_results_manifest_supplies_chi2_pvalue(tmp_path: Path) -> None:
    j100_dir = tmp_path / "run" / "fits" / "J100" / "run_481_3000_sixPar"
    j50_dir = tmp_path / "run" / "fits" / "J50" / "run_344_2079_sixPar"
    j100_dir.mkdir(parents=True)
    j50_dir.mkdir(parents=True)

    for fit_dir, nbkg, p_chi2 in (
        (j100_dir, 1000, 0.018478115147448883),
        (j50_dir, 2000, 0.07891295444241458),
    ):
        (fit_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log").write_text(
            f"nbkg = {nbkg}\np2 = 2.5\n",
            encoding="utf-8",
        )
        (fit_dir / "analysis_results.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "success",
                    "masked": False,
                    "p_chi2": p_chi2,
                }
            ),
            encoding="utf-8",
        )

    output = build_analysis_reference(repo_root=tmp_path)

    assert output["J100"]["p_chi2"] == pytest.approx(0.018478115147448883)
    assert output["J50"]["p_chi2"] == pytest.approx(0.07891295444241458)


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": 1, "status": "success", "masked": False},
        {
            "schema_version": 2,
            "status": "success",
            "masked": False,
            "p_chi2": 0.5,
        },
        {
            "schema_version": 1,
            "status": "failed",
            "masked": False,
            "p_chi2": 0.5,
        },
        {
            "schema_version": 1,
            "status": "success",
            "masked": "false",
            "p_chi2": 0.5,
        },
        {
            "schema_version": 1,
            "status": "success",
            "masked": False,
            "p_chi2": "invalid",
        },
        {
            "schema_version": 1,
            "status": "success",
            "masked": False,
            "p_chi2": 1.5,
        },
    ],
)
def test_analysis_results_manifest_rejects_invalid_payload(
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    j100_dir = tmp_path / "run" / "fits" / "J100" / "run_481_3000_sixPar"
    j50_dir = tmp_path / "run" / "fits" / "J50" / "run_344_2079_sixPar"
    j100_dir.mkdir(parents=True)
    j50_dir.mkdir(parents=True)

    for fit_dir in (j100_dir, j50_dir):
        (fit_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log").write_text(
            "nbkg = 1000\np2 = 2.5\n",
            encoding="utf-8",
        )

    (j100_dir / "analysis_results.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"analysis[ -]results|Analysis[ -]results",
    ):
        build_analysis_reference(repo_root=tmp_path)


def test_analysis_results_manifest_rejects_malformed_json(
    tmp_path: Path,
) -> None:
    j100_dir = tmp_path / "run" / "fits" / "J100" / "run_481_3000_sixPar"
    j50_dir = tmp_path / "run" / "fits" / "J50" / "run_344_2079_sixPar"
    j100_dir.mkdir(parents=True)
    j50_dir.mkdir(parents=True)

    for fit_dir in (j100_dir, j50_dir):
        (fit_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log").write_text(
            "nbkg = 1000\np2 = 2.5\n",
            encoding="utf-8",
        )

    (j100_dir / "analysis_results.json").write_text(
        "{invalid JSON",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Could not read valid analysis results",
    ):
        build_analysis_reference(repo_root=tmp_path)


def _complete_reference_payload() -> dict[str, object]:
    return {
        "J100": {
            "fit_parameters": {
                "nbkg": 765246000.0,
                "p2": 8.79763,
                "p3": 6.34479,
                "p4": 1.12277,
                "p5": 0.358837,
                "p6": 0.0417963,
            },
            "p_chi2": 0.018448750724012808,
            "p_bh": None,
            "cls_limit_points": [],
        },
        "J50": {
            "fit_parameters": {
                "nbkg": 653097000.0,
                "p2": 6.5024,
                "p3": 6.15143,
                "p4": 0.0699209,
                "p5": -0.0273909,
                "p6": -0.00118504,
            },
            "p_chi2": 0.07853114301666252,
            "p_bh": None,
            "cls_limit_points": [],
        },
    }


def test_analysis_reference_comparison_accepts_identical_payloads() -> None:
    expected = _complete_reference_payload()
    actual = _complete_reference_payload()

    assert_analysis_reference_close(actual, expected)


def test_analysis_reference_comparison_accepts_fit_parameter_within_tolerance() -> None:
    expected = _complete_reference_payload()
    actual = _complete_reference_payload()

    expected_value = expected["J100"]["fit_parameters"]["p2"]
    allowed = FIT_PARAMETER_ATOL + FIT_PARAMETER_RTOL * abs(expected_value)
    actual["J100"]["fit_parameters"]["p2"] = expected_value + 0.5 * allowed

    assert_analysis_reference_close(actual, expected)


def test_analysis_reference_comparison_accepts_pvalue_within_tolerance() -> None:
    expected = _complete_reference_payload()
    actual = _complete_reference_payload()

    expected_value = expected["J50"]["p_chi2"]
    allowed = PVALUE_ATOL + PVALUE_RTOL * abs(expected_value)
    actual["J50"]["p_chi2"] = expected_value + 0.5 * allowed

    assert_analysis_reference_close(actual, expected)


def test_analysis_reference_comparison_rejects_fit_parameter_outside_tolerance() -> None:
    expected = _complete_reference_payload()
    actual = _complete_reference_payload()

    expected_value = expected["J100"]["fit_parameters"]["p2"]
    allowed = FIT_PARAMETER_ATOL + FIT_PARAMETER_RTOL * abs(expected_value)
    actual["J100"]["fit_parameters"]["p2"] = expected_value + 2.0 * allowed

    with pytest.raises(
        AssertionError,
        match="J100 fit parameter p2 differs outside tolerance",
    ):
        assert_analysis_reference_close(actual, expected)


def test_analysis_reference_comparison_rejects_pvalue_outside_tolerance() -> None:
    expected = _complete_reference_payload()
    actual = _complete_reference_payload()

    expected_value = expected["J50"]["p_chi2"]
    allowed = PVALUE_ATOL + PVALUE_RTOL * abs(expected_value)
    actual["J50"]["p_chi2"] = expected_value + 2.0 * allowed

    with pytest.raises(
        AssertionError,
        match="J50 p_chi2 differs outside tolerance",
    ):
        assert_analysis_reference_close(actual, expected)


def test_analysis_reference_comparison_rejects_parameter_name_change() -> None:
    expected = _complete_reference_payload()
    actual = _complete_reference_payload()

    actual["J100"]["fit_parameters"]["unexpected_parameter"] = actual["J100"]["fit_parameters"].pop(
        "p6"
    )

    with pytest.raises(ValueError, match="unsupported fit parameter"):
        assert_analysis_reference_close(actual, expected)


def test_analysis_reference_comparison_rejects_pvalue_presence_change() -> None:
    expected = _complete_reference_payload()
    actual = _complete_reference_payload()

    actual["J100"]["p_bh"] = 0.25

    with pytest.raises(
        AssertionError,
        match="J100 p_bh presence differs",
    ):
        assert_analysis_reference_close(actual, expected)


def test_analysis_reference_comparison_rejects_cls_structure_change() -> None:
    expected = _complete_reference_payload()
    actual = _complete_reference_payload()

    actual["J50"]["cls_limit_points"] = [{"mass": 500, "limit": 1.2}]

    with pytest.raises(
        AssertionError,
        match="J50 cls_limit_points differ",
    ):
        assert_analysis_reference_close(actual, expected)


def _valid_analysis_provenance() -> dict[str, object]:
    return {
        "repository_commit": "a" * 40,
        "runtime": {
            "python_version": "3.9.12",
            "python_executable": "/cvmfs/example/bin/python",
            "root_version": "6.26/08",
        },
        "tool_revisions": {
            "xmlAnaWSBuilder": "b" * 40,
            "quickFit": "c" * 40,
            "workspaceCombiner": "d" * 40,
            "pyBumpHunter": "e" * 40,
        },
        "input": {
            "path": "Input/data.root",
            "sha256": "f" * 64,
        },
        "configurations": {
            "topfile": {
                "path": "config/top.template",
                "sha256": "1" * 64,
            },
            "categoryfile": {
                "path": "config/category.template",
                "sha256": "2" * 64,
            },
            "backgroundfile": {
                "path": "config/background.template",
                "sha256": "3" * 64,
            },
            "signalfile": {
                "path": "config/signal.template",
                "sha256": "4" * 64,
            },
        },
        "invocation": {
            "datahist": "directory/histogram",
            "range_low": 481,
            "range_high": 3000,
            "signal_enabled": False,
            "limit_enabled": False,
            "prefit_enabled": True,
            "mask_threshold": 0.01,
        },
    }


def test_validate_analysis_provenance_accepts_complete_payload() -> None:
    payload = _valid_analysis_provenance()

    validated = _validate_analysis_provenance(payload)

    assert validated["repository_commit"] == "a" * 40
    assert validated["runtime"]["python_version"] == "3.9.12"
    assert validated["runtime"]["root_version"] == "6.26/08"
    assert validated["input"]["sha256"] == "f" * 64
    assert validated["invocation"]["range_low"] == 481
    assert validated["invocation"]["range_high"] == 3000
    assert validated["invocation"]["mask_threshold"] == pytest.approx(0.01)


@pytest.mark.parametrize(
    ("mutation", "error_pattern"),
    [
        (
            lambda payload: payload.pop("runtime"),
            "Analysis provenance has invalid keys",
        ),
        (
            lambda payload: payload.update({"repository_commit": "not-a-git-revision"}),
            "must be a full Git revision",
        ),
        (
            lambda payload: payload["runtime"].pop("root_version"),
            "runtime has invalid keys",
        ),
        (
            lambda payload: payload["tool_revisions"].pop("quickFit"),
            "tool_revisions has invalid keys",
        ),
        (
            lambda payload: payload["input"].update({"sha256": "not-a-sha256"}),
            "must be a lowercase SHA-256 digest",
        ),
        (
            lambda payload: payload["configurations"].pop("topfile"),
            "configurations has invalid keys",
        ),
        (
            lambda payload: payload["invocation"].update({"range_low": 3000, "range_high": 481}),
            "range_low smaller than range_high",
        ),
        (
            lambda payload: payload["invocation"].update({"signal_enabled": "false"}),
            "signal_enabled must be boolean",
        ),
        (
            lambda payload: payload["invocation"].update({"mask_threshold": 1.5}),
            "mask_threshold must be numeric and between 0 and 1",
        ),
    ],
)
def test_validate_analysis_provenance_rejects_invalid_payload(
    mutation,
    error_pattern: str,
) -> None:
    payload = _valid_analysis_provenance()
    mutation(payload)

    with pytest.raises(ValueError, match=error_pattern):
        _validate_analysis_provenance(payload)


def test_schema_two_analysis_manifest_supplies_chi2_pvalue(
    tmp_path: Path,
) -> None:
    j100_dir = tmp_path / "run" / "fits" / "J100" / "run_481_3000_sixPar"
    j50_dir = tmp_path / "run" / "fits" / "J50" / "run_344_2079_sixPar"
    j100_dir.mkdir(parents=True)
    j50_dir.mkdir(parents=True)

    for fit_dir, nbkg, p_chi2 in (
        (j100_dir, 1000, 0.018448750724012808),
        (j50_dir, 2000, 0.07853114301666252),
    ):
        (fit_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log").write_text(
            f"nbkg = {nbkg}\np2 = 2.5\n",
            encoding="utf-8",
        )

        (fit_dir / "analysis_results.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "status": "success",
                    "masked": False,
                    "p_chi2": p_chi2,
                    "provenance": _valid_analysis_provenance(),
                }
            ),
            encoding="utf-8",
        )

    output = build_analysis_reference(repo_root=tmp_path)

    assert output["J100"]["p_chi2"] == pytest.approx(0.018448750724012808)
    assert output["J50"]["p_chi2"] == pytest.approx(0.07853114301666252)
