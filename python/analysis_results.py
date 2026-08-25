from __future__ import annotations

import json
import os
from pathlib import Path


def assemble_manifest_payload(p_chi2, masked, provenance) -> dict[str, object]:
    return {
        "schema_version": 2,
        "status": "success",
        "masked": bool(masked),
        "p_chi2": float(p_chi2),
        "provenance": provenance,
    }


def validate_manifest_payload(payload: dict[str, object]) -> None:
    required_keys = {"schema_version", "status", "masked", "p_chi2", "provenance"}
    if set(payload) != required_keys:
        raise ValueError("Analysis results payload has invalid schema-2 keys")
    if payload["schema_version"] != 2:
        raise ValueError("Analysis results payload must use schema version 2")
    if payload["status"] != "success":
        raise ValueError("Analysis results payload must record a successful run")
    if not isinstance(payload["masked"], bool):
        raise ValueError("Analysis results masked field must be boolean")
    if not isinstance(payload["p_chi2"], (int, float)) or isinstance(payload["p_chi2"], bool):
        raise ValueError("Analysis results p_chi2 field must be numeric")
    if not 0.0 <= float(payload["p_chi2"]) <= 1.0:
        raise ValueError("Analysis results p_chi2 field must be between 0 and 1")
    if not isinstance(payload["provenance"], dict):
        raise ValueError("Analysis results provenance field must be an object")


def write_analysis_results(folder, p_chi2, masked, provenance):
    results_path = Path(folder) / "analysis_results.json"
    temporary_path = Path(f"{results_path}.tmp")
    payload = assemble_manifest_payload(p_chi2, masked, provenance)
    validate_manifest_payload(payload)
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")
    os.replace(temporary_path, results_path)
    return str(results_path)
