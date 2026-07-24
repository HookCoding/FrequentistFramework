import json
import re
from pathlib import Path
from typing import Any, Optional


def _read_json_payload(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return read_analysis_reference(path)
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"Could not read analysis reference: {path}") from error


def _extract_fit_parameters(log_path: Path) -> dict[str, float]:
    if not log_path.exists():
        return {}

    parameters: dict[str, float] = {}
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.search(
            r"^\s*([A-Za-z0-9_]+)\s*=\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)", line
        )
        if match:
            name, value = match.groups()
            if name in {"nbkg", "p2", "p3", "p4", "p5", "p6", "p7"}:
                parameters[name] = float(value)
    return parameters


def _candidate_fit_dirs(repo_root: Path) -> list[Path]:
    fits_dir = repo_root / "run" / "fits"
    if not fits_dir.exists():
        return []

    candidates = []
    for path in sorted(fits_dir.iterdir(), key=lambda item: item.name):
        if not path.is_dir():
            continue
        if re.search(r"run_135_1000_(six|seven)Par$", path.name):
            candidates.append(path)

    ordered_names = ["run_135_1000_sevenPar", "run_135_1000_sixPar"]
    ordered_candidates = []
    for name in ordered_names:
        matching = [path for path in candidates if path.name == name]
        if matching:
            ordered_candidates.extend(matching)
    return ordered_candidates


def build_analysis_reference(repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Create an analysis reference from real outputs or fail clearly."""
    repo_root = repo_root or Path(__file__).resolve().parents[1]

    generated_reference = repo_root / "run" / "fits" / "analysis_reference.json"
    payload = _read_json_payload(generated_reference)
    if payload is not None:
        return payload

    for fit_dir in _candidate_fit_dirs(repo_root):
        bh_results_path = fit_dir / "BHresults.json"
        log_candidates = [
            fit_dir / "quickFitLog_anaFit_sevenPar_bkgOnly.log",
            fit_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log",
        ]
        fit_log_path = next((path for path in log_candidates if path.exists()), None)
        if fit_log_path is None:
            continue

        fit_parameters = _extract_fit_parameters(fit_log_path)
        if not fit_parameters:
            raise ValueError(
                f"No fit parameters could be extracted from {fit_log_path}"
            )

        if not bh_results_path.exists():
            continue

        try:
            bh_results = json.loads(bh_results_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise ValueError(
                f"Could not read BumpHunter results: {bh_results_path}"
            ) from error

        pybh_result = bh_results.get("pyBHresult")

        if not isinstance(pybh_result, dict):
            raise KeyError(
                f"BumpHunter results do not contain a valid 'pyBHresult': "
                f"{bh_results_path}"
            )

        if "global_Pval" not in pybh_result:
            raise KeyError(
                f"BumpHunter results do not contain "
                f"'pyBHresult.global_Pval': {bh_results_path}"
            )

        return {
            "fit_parameters": fit_parameters,
            "p_chi2": None,
            "p_bh": float(pybh_result["global_Pval"]),
            "cls_limit_points": [],
        }

    raise FileNotFoundError(
        "No analysis reference or complete fit output was found. "
        "Provide run/fits/analysis_reference.json, or run the expected fit "
        "and provide both its quickFit log and BHresults.json before running "
        "the regression tests."
    )


def write_analysis_reference(path: Path, payload: dict[str, Any]) -> None:
    """Write the analysis reference payload to disk as JSON."""
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_analysis_reference(path: Path) -> dict[str, Any]:
    """Read the analysis reference payload from disk."""
    return json.loads(path.read_text(encoding="utf-8"))
