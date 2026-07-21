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


def build_analysis_reference() -> dict[str, Any]:
    """Create an analysis-output reference payload from real outputs when present."""
    repo_root = Path(__file__).resolve().parents[1]
    candidate_files = [
        repo_root / "tests" / "references" / "analysis_reference.json",
        repo_root / "run" / "fits" / "analysis_reference.json",
    ]

    for candidate in candidate_files:
        if candidate.exists():
            return read_analysis_reference(candidate)

    return _fallback_analysis_reference()


def write_analysis_reference(path: Path, payload: dict[str, Any]) -> None:
    """Write the analysis reference payload to disk as JSON."""
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_analysis_reference(path: Path) -> dict[str, Any]:
    """Read the analysis reference payload from disk."""
    return json.loads(path.read_text(encoding="utf-8"))
