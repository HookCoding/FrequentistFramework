from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.analysis_bumphunter import (
    load_bumphunter_results,
    prepare_bumphunter_command,
    should_mask,
    validate_mask_range,
)


def test_prepare_bumphunter_command_preserves_analysis_arguments() -> None:
    command = prepare_bumphunter_command("postfit.root", "BHresults.json")

    assert "--inputfile postfit.root" in command
    assert "--bkghist Run3TLA_rebinned/postfit" in command
    assert "--datahist Run3TLA_rebinned/data" in command
    assert "--outputjson BHresults.json" in command


def test_validate_mask_range_accepts_valid_bounds() -> None:
    validate_mask_range(500, 600)


def test_validate_mask_range_rejects_equal_bounds() -> None:
    with pytest.raises(ValueError, match="smaller than"):
        validate_mask_range(500, 500)


def test_validate_mask_range_rejects_reversed_bounds() -> None:
    with pytest.raises(ValueError, match="smaller than"):
        validate_mask_range(600, 500)


def test_should_mask_returns_true_below_threshold() -> None:
    assert should_mask(0.005, 0.01)


def test_should_mask_returns_false_above_threshold() -> None:
    assert not should_mask(0.05, 0.01)


def test_load_bumphunter_results_accepts_valid_payload(tmp_path: Path) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "500,600", "MaskMin": 500, "MaskMax": 600}')

    assert load_bumphunter_results(str(results_file)) == {
        "BlindRange": "500,600",
        "MaskMin": 500,
        "MaskMax": 600,
    }


def test_load_bumphunter_results_rejects_malformed_json(tmp_path: Path) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text("{not valid JSON")

    with pytest.raises(ValueError, match="Could not read valid BumpHunter results"):
        load_bumphunter_results(str(results_file))


def test_load_bumphunter_results_rejects_missing_keys(tmp_path: Path) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "500,600"}')

    with pytest.raises(ValueError, match="missing required keys"):
        load_bumphunter_results(str(results_file))


@pytest.mark.parametrize(
    ("mask_min", "mask_max"),
    [("invalid", 600), (600, 500), (500, 500)],
)
def test_load_bumphunter_results_rejects_invalid_mask_limits(
    tmp_path: Path,
    mask_min: object,
    mask_max: object,
) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text(
        json.dumps({"BlindRange": "500,600", "MaskMin": mask_min, "MaskMax": mask_max})
    )

    with pytest.raises(ValueError, match="MaskMin|MaskMax"):
        load_bumphunter_results(str(results_file))


def test_run_bumphunter_removes_stale_output_and_loads_fresh_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = __import__("python.analysis_bumphunter", fromlist=["run_bumphunter"])
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "stale", "MaskMin": 1, "MaskMax": 2}')

    def fake_execute_required(cmd, description, expected_outputs=()):
        assert not results_file.exists()
        assert description == "BumpHunter masking-window calculation"
        assert expected_outputs == [str(results_file)]
        assert str(results_file) in cmd
        results_file.write_text('{"BlindRange": "500,600", "MaskMin": 500, "MaskMax": 600}')
        return True

    monkeypatch.setattr(module, "execute_required", fake_execute_required)

    assert module.run_bumphunter("fresh-postfit.root", str(tmp_path)) == {
        "BlindRange": "500,600",
        "MaskMin": 500,
        "MaskMax": 600,
    }


def test_run_bumphunter_propagates_command_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = __import__("python.analysis_bumphunter", fromlist=["run_bumphunter"])
    stale_results = tmp_path / "BHresults.json"
    stale_results.write_text('{"BlindRange": "stale", "MaskMin": 1, "MaskMax": 2}')

    def fake_execute_required(cmd, description, expected_outputs=()):
        assert not stale_results.exists()
        return False

    monkeypatch.setattr(module, "execute_required", fake_execute_required)

    with pytest.raises(RuntimeError, match="BumpHunter masking-window calculation failed"):
        module.run_bumphunter("fresh-postfit.root", str(tmp_path))

    assert not stale_results.exists()


def test_run_bumphunter_rejects_invalid_fresh_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = __import__("python.analysis_bumphunter", fromlist=["run_bumphunter"])
    results_file = tmp_path / "BHresults.json"

    def fake_execute_required(cmd, description, expected_outputs=()):
        results_file.write_text('{"BlindRange": "500,600"}')
        return True

    monkeypatch.setattr(module, "execute_required", fake_execute_required)

    with pytest.raises(ValueError, match="missing required keys"):
        module.run_bumphunter("fresh-postfit.root", str(tmp_path))
