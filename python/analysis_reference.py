import json
from pathlib import Path
from typing import Any


def _fallback_analysis_reference() -> dict[str, Any]:
    """Return deterministic placeholder values when no real output exists."""
    return {
        "fit_parameters": {
            "slope": 0.94,
            "intercept": 0.94,
        },
        "p_chi2": 0.36,
        "p_bh": 0.2,
        "cls_limit_points": [
            {"mass": 400.0, "limit": 1.2},
            {"mass": 500.0, "limit": 1.5},
            {"mass": 600.0, "limit": 1.8},
        ],
    }


def _read_json_payload(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return read_analysis_reference(path)
    except (json.JSONDecodeError, OSError):
        return None


def build_analysis_reference() -> dict[str, Any]:
    """Create an analysis-output reference payload from real outputs when present."""
    repo_root = Path(__file__).resolve().parents[1]
    candidate_files = [
        repo_root / "tests" / "references" / "analysis_reference.json",
        repo_root / "run" / "fits" / "analysis_reference.json",
        repo_root / "run" / "fits" / "run_135_1000_sevenPar" / "BHresults.json",
    ]

    for candidate in candidate_files:
        payload = _read_json_payload(candidate)
        if payload is not None:
            return payload

    fit_dir = repo_root / "run" / "fits" / "run_135_1000_sevenPar"
    if fit_dir.exists():
        bh_results = fit_dir / "BHresults.json"
        if bh_results.exists():
            payload = _read_json_payload(bh_results)
            if payload is not None:
                return payload

    return _fallback_analysis_reference()


def write_analysis_reference(path: Path, payload: dict[str, Any]) -> None:
    """Write the analysis reference payload to disk as JSON."""
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_analysis_reference(path: Path) -> dict[str, Any]:
    """Read the analysis reference payload from disk."""
    return json.loads(path.read_text(encoding="utf-8"))
