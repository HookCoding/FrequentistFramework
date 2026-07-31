import json
import re
from pathlib import Path
from typing import Any, Optional


WORKFLOW_FIT_DIRS: tuple[tuple[str, str], ...] = (
    ("J100", "run_481_3000_sixPar"),
    ("J50", "run_344_2079_sixPar"),
)
_FIT_PARAMETER_NAMES = {"nbkg", "p2", "p3", "p4", "p5", "p6", "p7"}
_FLOAT_RE = r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
_FIT_PARAMETER_PATTERN = re.compile(rf"^\s*([A-Za-z0-9_]+)\s*=\s*{_FLOAT_RE}")
_CHI2_PVALUE_PATTERN = re.compile(
    rf"chi2[^\n]*p(?:[-_\s]*)val(?:ue)?[^\d+-]*{_FLOAT_RE}", re.IGNORECASE
)


def _extract_log_observables(log_path: Path) -> tuple[dict[str, float], Optional[float]]:
    if not log_path.exists():
        return {}, None

    parameters: dict[str, float] = {}
    p_chi2: Optional[float] = None
    with log_path.open(encoding="utf-8", errors="ignore") as stream:
        for line in stream:
            parameter_match = _FIT_PARAMETER_PATTERN.search(line)
            if parameter_match:
                name, value = parameter_match.groups()
                if name in _FIT_PARAMETER_NAMES:
                    parameters[name] = float(value)

            if p_chi2 is None:
                pvalue_match = _CHI2_PVALUE_PATTERN.search(line)
                if pvalue_match:
                    p_chi2 = float(pvalue_match.group(1))

    return parameters, p_chi2


def _extract_optional_bh_pvalue(fit_dir: Path) -> Optional[float]:
    bh_path = fit_dir / "BHresults.json"
    if not bh_path.exists():
        return None

    try:
        bh_results = json.loads(bh_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {bh_path}") from error

    pybh_result = bh_results.get("pyBHresult")
    if pybh_result is None:
        return None
    if not isinstance(pybh_result, dict):
        raise ValueError(f"Invalid pyBHresult payload in {bh_path}")

    global_pval = pybh_result.get("global_Pval")
    if global_pval is None:
        return None
    if not isinstance(global_pval, (int, float)):
        raise ValueError(f"Non-numeric global_Pval in {bh_path}")
    return float(global_pval)


def _choose_background_only_log(fit_dir: Path) -> Path:
    candidates = [
        fit_dir / "quickFitLog_anaFit_sixPar_bkgOnly.log",
        fit_dir / "quickFitLog_anaFit_sevenPar_bkgOnly.log",
    ]
    for log_path in candidates:
        if log_path.exists():
            return log_path

    searched = ", ".join(str(path.name) for path in candidates)
    raise FileNotFoundError(f"No supported background-only log found in {fit_dir} (searched: {searched})")


def _build_workflow_payload(fit_dir: Path) -> dict[str, Any]:
    log_path = _choose_background_only_log(fit_dir)
    fit_params, p_chi2 = _extract_log_observables(log_path)
    if not fit_params:
        raise ValueError(f"No fit parameters parsed from {log_path}")

    return {
        "fit_parameters": fit_params,
        "p_chi2": p_chi2,
        "p_bh": _extract_optional_bh_pvalue(fit_dir),
        "cls_limit_points": [],
    }


def _validate_workflow_payload(workflow_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    required_keys = {"fit_parameters", "p_chi2", "p_bh", "cls_limit_points"}
    missing = required_keys - set(payload)
    extra = set(payload) - required_keys
    if missing or extra:
        raise ValueError(f"Workflow {workflow_name} has invalid keys (missing={sorted(missing)}, unexpected={sorted(extra)})")
    fit_parameters_raw = payload["fit_parameters"]
    if not isinstance(fit_parameters_raw, dict):
        raise ValueError(f"Workflow {workflow_name} fit_parameters must be a dictionary")

    fit_parameters: dict[str, float] = {}
    for name, value in fit_parameters_raw.items():
        if name not in _FIT_PARAMETER_NAMES:
            raise ValueError(f"Workflow {workflow_name} contains unsupported fit parameter '{name}'")
        if not isinstance(value, (int, float)):
            raise ValueError(f"Workflow {workflow_name} parameter '{name}' must be numeric")
        fit_parameters[name] = float(value)

    if not fit_parameters:
        raise ValueError(f"Workflow {workflow_name} must include at least one fit parameter")

    p_chi2 = payload["p_chi2"]
    if p_chi2 is not None and not isinstance(p_chi2, (int, float)):
        raise ValueError(f"Workflow {workflow_name} p_chi2 must be numeric or null")

    p_bh = payload["p_bh"]
    if p_bh is not None and not isinstance(p_bh, (int, float)):
        raise ValueError(f"Workflow {workflow_name} p_bh must be numeric or null")

    cls_limit_points = payload["cls_limit_points"]
    if not isinstance(cls_limit_points, list):
        raise ValueError(f"Workflow {workflow_name} cls_limit_points must be a list")

    return {
        "fit_parameters": fit_parameters,
        "p_chi2": None if p_chi2 is None else float(p_chi2),
        "p_bh": None if p_bh is None else float(p_bh),
        "cls_limit_points": cls_limit_points,
    }


def _validate_analysis_reference(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Analysis reference must be a dictionary")

    validated: dict[str, Any] = {}
    required_workflows = [name for name, _ in WORKFLOW_FIT_DIRS]
    missing_workflows = [name for name in required_workflows if name not in payload]
    if missing_workflows:
        raise ValueError(f"Analysis reference is missing workflows: {missing_workflows}")

    for workflow_name in required_workflows:
        workflow_payload = payload[workflow_name]
        if not isinstance(workflow_payload, dict):
            raise ValueError(f"Workflow {workflow_name} payload must be a dictionary")
        validated[workflow_name] = _validate_workflow_payload(workflow_name, workflow_payload)

    return validated


def build_analysis_reference(repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Create a deterministic J100/J50 background-only reference payload."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    payload: dict[str, Any] = {}
    for workflow_name, fit_dir_name in WORKFLOW_FIT_DIRS:
        fit_dir = repo_root / "run" / "fits" / workflow_name / fit_dir_name
        if not fit_dir.exists():
            raise FileNotFoundError(f"Expected fit directory for {workflow_name} not found: {fit_dir}")
        payload[workflow_name] = _build_workflow_payload(fit_dir)

    return _validate_analysis_reference(payload)


def read_analysis_reference(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"Could not read analysis reference: {path}") from error

    if not isinstance(payload, dict):
        raise ValueError(f"Could not read analysis reference: {path}")
    return _validate_analysis_reference(payload)


def write_analysis_reference(path: Path, payload: dict[str, Any]) -> None:
    validated_payload = _validate_analysis_reference(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validated_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")