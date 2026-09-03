from __future__ import annotations

import json
from pathlib import Path

import pytest

from python import run_masking


def test_load_bumphunter_results_accepts_valid_payload(
    tmp_path: Path,
) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "500,600", "MaskMin": 500, "MaskMax": 600}')

    assert run_masking.load_bumphunter_results(str(results_file)) == {
        "BlindRange": "500,600",
        "MaskMin": 500,
        "MaskMax": 600,
    }


def test_load_bumphunter_results_rejects_malformed_json(
    tmp_path: Path,
) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text("{not valid JSON")

    with pytest.raises(ValueError, match="Could not read valid BumpHunter results"):
        run_masking.load_bumphunter_results(str(results_file))


def test_load_bumphunter_results_rejects_missing_keys(
    tmp_path: Path,
) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "500,600"}')

    with pytest.raises(ValueError, match="missing required keys"):
        run_masking.load_bumphunter_results(str(results_file))


@pytest.mark.parametrize(
    ("mask_min", "mask_max"),
    [
        ("invalid", 600),
        (600, 500),
        (500, 500),
    ],
)
def test_load_bumphunter_results_rejects_invalid_mask_limits(
    tmp_path: Path,
    mask_min: object,
    mask_max: object,
) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text(
        json.dumps(
            {
                "BlindRange": "500,600",
                "MaskMin": mask_min,
                "MaskMax": mask_max,
            }
        )
    )

    with pytest.raises(ValueError, match="MaskMin|MaskMax"):
        run_masking.load_bumphunter_results(str(results_file))


def test_load_bumphunter_results_rejects_non_dict_payload(
    tmp_path: Path,
) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text(json.dumps([1, 2, 3]))

    with pytest.raises(ValueError, match="must be a JSON object"):
        run_masking.load_bumphunter_results(str(results_file))


@pytest.mark.parametrize("blind_range", ["", "   "])
def test_load_bumphunter_results_rejects_invalid_blind_range(
    tmp_path: Path,
    blind_range: str,
) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text(
        json.dumps(
            {
                "BlindRange": blind_range,
                "MaskMin": 500,
                "MaskMax": 600,
            }
        )
    )

    with pytest.raises(ValueError, match="BlindRange must be a non-empty string"):
        run_masking.load_bumphunter_results(str(results_file))


def test_run_bumphunter_removes_stale_output_and_loads_fresh_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # execute_required lives in a different module (run_execution.py), so
    # the patch target is run_masking's own copy of the name, not the
    # function object patched in isolation - see the activity log's
    # Chunk 4.B entry for why this differs from run_bumphunter's other
    # (intra-module) call to load_bumphunter_results below.
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "stale", "MaskMin": 1, "MaskMax": 2}')

    def create_fresh_results(
        cmd,
        description,
        expected_outputs=(),
    ):
        assert not results_file.exists()
        assert description == "BumpHunter masking-window calculation"
        assert expected_outputs == [str(results_file)]
        assert str(results_file) in cmd

        results_file.write_text('{"BlindRange": "500,600", "MaskMin": 500, "MaskMax": 600}')
        return True

    monkeypatch.setattr(
        run_masking,
        "execute_required",
        create_fresh_results,
    )

    results = run_masking.run_bumphunter(
        "fresh-postfit.root",
        str(tmp_path),
    )

    assert results == {
        "BlindRange": "500,600",
        "MaskMin": 500,
        "MaskMax": 600,
    }


def test_run_bumphunter_propagates_command_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale_results = tmp_path / "BHresults.json"
    stale_results.write_text('{"BlindRange": "stale", "MaskMin": 1, "MaskMax": 2}')

    def fail_bumphunter(
        cmd,
        description,
        expected_outputs=(),
    ):
        assert not stale_results.exists()
        return False

    monkeypatch.setattr(
        run_masking,
        "execute_required",
        fail_bumphunter,
    )

    with pytest.raises(
        RuntimeError,
        match="BumpHunter masking-window calculation failed",
    ):
        run_masking.run_bumphunter(
            "fresh-postfit.root",
            str(tmp_path),
        )

    assert not stale_results.exists()


def test_run_bumphunter_rejects_success_without_fresh_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "stale", "MaskMin": 1, "MaskMax": 2}')

    def reject_missing_output(
        cmd,
        description,
        expected_outputs=(),
    ):
        assert not results_file.exists()
        assert expected_outputs == [str(results_file)]
        return False

    monkeypatch.setattr(
        run_masking,
        "execute_required",
        reject_missing_output,
    )

    with pytest.raises(
        RuntimeError,
        match="BumpHunter masking-window calculation failed",
    ):
        run_masking.run_bumphunter(
            "fresh-postfit.root",
            str(tmp_path),
        )

    assert not results_file.exists()


def test_run_bumphunter_rejects_invalid_fresh_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    results_file = tmp_path / "BHresults.json"

    def create_invalid_results(
        cmd,
        description,
        expected_outputs=(),
    ):
        results_file.write_text('{"BlindRange": "500,600"}')
        return True

    monkeypatch.setattr(
        run_masking,
        "execute_required",
        create_invalid_results,
    )

    with pytest.raises(
        ValueError,
        match="missing required keys",
    ):
        run_masking.run_bumphunter(
            "fresh-postfit.root",
            str(tmp_path),
        )


@pytest.mark.parametrize(
    ("p_value", "threshold", "expected"),
    [
        # Exact threshold: matches the coordinator's "not > threshold"
        # convention, i.e. should_mask(threshold, threshold) is True.
        (0.01, 0.01, True),
        (0.001, 0.01, True),  # clearly below the threshold
        (0.5, 0.01, False),  # clearly above the threshold
    ],
)
def test_should_mask_matches_coordinator_convention_at_exact_threshold(
    p_value: float,
    threshold: float,
    expected: bool,
) -> None:
    assert run_masking.should_mask(p_value, threshold) is expected


def test_should_mask_treats_nan_p_value_as_requiring_masking() -> None:
    # A regression test for a real bug (caught in review): "p_value <=
    # threshold" looks equivalent to "not (p_value > threshold)" for
    # ordinary floats, but is not for NaN - under IEEE 754 comparison
    # rules, both "nan > threshold" and "nan <= threshold" are False. The
    # coordinator's original gating was "if p_value > threshold:
    # <success>", so a NaN p-value (a real possibility from a degenerate
    # fit) took the masking branch; should_mask() must agree.
    assert run_masking.should_mask(float("nan"), 0.01) is True
