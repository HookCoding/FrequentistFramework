from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.analysis_results import (
    assemble_manifest_payload,
    validate_manifest_payload,
    write_analysis_results,
)


@pytest.fixture
def provenance() -> dict[str, object]:
    return {"repository_commit": "a" * 40, "runtime": {"python_version": "3.12.13"}}


def test_assemble_manifest_payload_preserves_schema_2_fields(provenance) -> None:
    payload = assemble_manifest_payload(0.25, False, provenance)

    assert payload == {
        "schema_version": 2,
        "status": "success",
        "masked": False,
        "p_chi2": 0.25,
        "provenance": provenance,
    }


def test_validate_manifest_payload_rejects_invalid_schema_and_values(provenance) -> None:
    payload = assemble_manifest_payload(0.25, False, provenance)
    payload["schema_version"] = 1

    with pytest.raises(ValueError, match="schema version 2"):
        validate_manifest_payload(payload)

    payload = assemble_manifest_payload(1.5, False, provenance)
    with pytest.raises(ValueError, match="between 0 and 1"):
        validate_manifest_payload(payload)


def test_write_analysis_results_atomically_writes_valid_payload(tmp_path: Path, provenance) -> None:
    results_path = write_analysis_results(tmp_path, 0.125, True, provenance)

    assert Path(results_path) == tmp_path / "analysis_results.json"
    assert json.loads(Path(results_path).read_text()) == {
        "schema_version": 2,
        "status": "success",
        "masked": True,
        "p_chi2": 0.125,
        "provenance": provenance,
    }
    assert not (tmp_path / "analysis_results.json.tmp").exists()
