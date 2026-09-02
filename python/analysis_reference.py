import json
import math
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
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"Could not read valid JSON from {bh_path}") from error

    if not isinstance(bh_results, dict):
        raise ValueError(f"BH results payload in {bh_path} must be a JSON object")

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
    raise FileNotFoundError(
        f"No supported background-only log found in {fit_dir} (searched: {searched})"
    )


def _validate_sha256(value: Any, description: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{description} must be a lowercase SHA-256 digest")

    return value


def _validate_git_revision(value: Any, description: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError(f"{description} must be a full Git revision")

    return value


def _validate_file_provenance(
    payload: Any,
    description: str,
) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must be a JSON object")

    required_keys = {"path", "sha256"}
    payload_keys = set(payload)

    if payload_keys != required_keys:
        raise ValueError(
            f"{description} has invalid keys "
            f"(missing={sorted(required_keys - payload_keys)}, "
            f"unexpected={sorted(payload_keys - required_keys)})"
        )

    file_path = payload["path"]
    if not isinstance(file_path, str) or not file_path:
        raise ValueError(f"{description} path must be a non-empty string")

    return {
        "path": file_path,
        "sha256": _validate_sha256(
            payload["sha256"],
            f"{description} sha256",
        ),
    }


def _extract_analysis_results(fit_dir: Path) -> Optional[dict[str, Any]]:
    results_path = fit_dir / "analysis_results.json"
    if not results_path.exists():
        return None

    try:
        results = json.loads(results_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"Could not read valid analysis results from {results_path}") from error

    if not isinstance(results, dict):
        raise ValueError(f"Analysis results payload in {results_path} must be a JSON object")

    schema_version = results.get("schema_version")

    if schema_version == 1:
        required_keys = {
            "schema_version",
            "status",
            "masked",
            "p_chi2",
        }
    elif schema_version == 2:
        required_keys = {
            "schema_version",
            "status",
            "masked",
            "p_chi2",
            "provenance",
        }
    else:
        raise ValueError(
            f"Unsupported analysis-results schema version in {results_path}: " f"{schema_version}"
        )

    result_keys = set(results)
    missing_keys = required_keys - result_keys
    unexpected_keys = result_keys - required_keys

    if missing_keys or unexpected_keys:
        raise ValueError(
            f"Analysis results in {results_path} have invalid keys "
            f"(missing={sorted(missing_keys)}, "
            f"unexpected={sorted(unexpected_keys)})"
        )

    provenance = None
    if schema_version == 2:
        provenance = _validate_analysis_provenance(results["provenance"])

    if results["status"] != "success":
        raise ValueError(f"Analysis results in {results_path} do not record a successful run")

    if not isinstance(results["masked"], bool):
        raise ValueError(f"Analysis results masked field in {results_path} must be boolean")

    p_chi2 = results["p_chi2"]
    if not isinstance(p_chi2, (int, float)) or isinstance(p_chi2, bool):
        raise ValueError(f"Analysis results p_chi2 in {results_path} must be numeric")

    p_chi2 = float(p_chi2)
    if not 0.0 <= p_chi2 <= 1.0:
        raise ValueError(f"Analysis results p_chi2 in {results_path} must be between 0 and 1")

    return {
        "p_chi2": p_chi2,
        "provenance": provenance,
    }


def _build_workflow_payload(fit_dir: Path) -> dict[str, Any]:
    log_path = _choose_background_only_log(fit_dir)
    fit_params, legacy_p_chi2 = _extract_log_observables(log_path)
    if not fit_params:
        raise ValueError(f"No fit parameters parsed from {log_path}")

    manifest_results = _extract_analysis_results(fit_dir)
    p_chi2 = manifest_results["p_chi2"] if manifest_results is not None else legacy_p_chi2

    payload = {
        "fit_parameters": fit_params,
        "p_chi2": p_chi2,
        "p_bh": _extract_optional_bh_pvalue(fit_dir),
        "cls_limit_points": [],
    }

    if manifest_results is not None and manifest_results["provenance"] is not None:
        stable_provenance = dict(manifest_results["provenance"])
        # repository_commit and repository_dirty describe the specific run
        # instance that produced this manifest, not the scientific result
        # itself, so both are excluded from the stable cross-run/cross-
        # environment comparison (matching repository_commit's existing
        # treatment, for the same self-referential-identity reasoning).
        stable_provenance.pop("repository_commit")
        stable_provenance.pop("repository_dirty")
        payload["provenance"] = stable_provenance

    return payload


def _validate_workflow_payload(workflow_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    required_keys = {"fit_parameters", "p_chi2", "p_bh", "cls_limit_points"}
    optional_keys = {"provenance"}
    payload_keys = set(payload)
    missing = required_keys - payload_keys
    unexpected = payload_keys - required_keys - optional_keys
    if missing or unexpected:
        raise ValueError(
            f"Workflow {workflow_name} has invalid keys "
            f"(missing={sorted(missing)}, unexpected={sorted(unexpected)})"
        )

    fit_parameters_raw = payload["fit_parameters"]
    if not isinstance(fit_parameters_raw, dict):
        raise ValueError(f"Workflow {workflow_name} fit_parameters must be a dictionary")

    fit_parameters: dict[str, float] = {}
    for name, value in fit_parameters_raw.items():
        if name not in _FIT_PARAMETER_NAMES:
            raise ValueError(
                f"Workflow {workflow_name} contains unsupported fit parameter '{name}'"
            )
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

    validated = {
        "fit_parameters": fit_parameters,
        "p_chi2": None if p_chi2 is None else float(p_chi2),
        "p_bh": None if p_bh is None else float(p_bh),
        "cls_limit_points": cls_limit_points,
    }

    if "provenance" in payload:
        validated["provenance"] = _validate_reference_provenance(payload["provenance"])

    return validated


def _validate_analysis_reference(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Analysis reference must be a dictionary")

    validated: dict[str, Any] = {}
    required_workflows = [name for name, _ in WORKFLOW_FIT_DIRS]
    payload_workflows = set(payload)
    missing_workflows = sorted(set(required_workflows) - payload_workflows)
    unexpected_workflows = sorted(payload_workflows - set(required_workflows))
    if missing_workflows or unexpected_workflows:
        raise ValueError(
            "Analysis reference has invalid workflows "
            f"(missing={missing_workflows}, unexpected={unexpected_workflows})"
        )

    for workflow_name in required_workflows:
        workflow_payload = payload[workflow_name]
        if not isinstance(workflow_payload, dict):
            raise ValueError(f"Workflow {workflow_name} payload must be a dictionary")
        validated[workflow_name] = _validate_workflow_payload(workflow_name, workflow_payload)

    return validated


FIT_PARAMETER_RTOL = 1e-6
FIT_PARAMETER_ATOL = 1e-8
PVALUE_RTOL = 1e-5
PVALUE_ATOL = 1e-8


def _assert_numeric_close(
    actual: float,
    expected: float,
    *,
    relative_tolerance: float,
    absolute_tolerance: float,
    description: str,
) -> None:
    if not math.isfinite(actual) or not math.isfinite(expected):
        raise AssertionError(
            f"{description} must contain finite values: " f"actual={actual}, expected={expected}"
        )

    difference = abs(actual - expected)
    allowed = absolute_tolerance + relative_tolerance * abs(expected)

    if difference > allowed:
        raise AssertionError(
            f"{description} differs outside tolerance: "
            f"actual={actual}, expected={expected}, "
            f"difference={difference}, allowed={allowed}, "
            f"rtol={relative_tolerance}, atol={absolute_tolerance}"
        )


def assert_analysis_reference_close(
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    actual = _validate_analysis_reference(actual)
    expected = _validate_analysis_reference(expected)

    if set(actual) != set(expected):
        raise AssertionError(
            f"Workflow names differ: actual={sorted(actual)}, " f"expected={sorted(expected)}"
        )

    for workflow_name in expected:
        actual_workflow = actual[workflow_name]
        expected_workflow = expected[workflow_name]

        actual_provenance = actual_workflow.get("provenance")
        expected_provenance = expected_workflow.get("provenance")

        if actual_provenance != expected_provenance:
            raise AssertionError(
                f"{workflow_name} provenance differs: "
                f"actual={actual_provenance}, expected={expected_provenance}"
            )

        actual_parameters = actual_workflow["fit_parameters"]
        expected_parameters = expected_workflow["fit_parameters"]

        if set(actual_parameters) != set(expected_parameters):
            raise AssertionError(
                f"{workflow_name} fit-parameter names differ: "
                f"actual={sorted(actual_parameters)}, "
                f"expected={sorted(expected_parameters)}"
            )

        for parameter_name, expected_value in expected_parameters.items():
            _assert_numeric_close(
                actual_parameters[parameter_name],
                expected_value,
                relative_tolerance=FIT_PARAMETER_RTOL,
                absolute_tolerance=FIT_PARAMETER_ATOL,
                description=f"{workflow_name} fit parameter {parameter_name}",
            )

        for pvalue_name in ("p_chi2", "p_bh"):
            actual_pvalue = actual_workflow[pvalue_name]
            expected_pvalue = expected_workflow[pvalue_name]

            if actual_pvalue is None or expected_pvalue is None:
                if actual_pvalue is not expected_pvalue:
                    raise AssertionError(
                        f"{workflow_name} {pvalue_name} presence differs: "
                        f"actual={actual_pvalue}, expected={expected_pvalue}"
                    )
            else:
                _assert_numeric_close(
                    actual_pvalue,
                    expected_pvalue,
                    relative_tolerance=PVALUE_RTOL,
                    absolute_tolerance=PVALUE_ATOL,
                    description=f"{workflow_name} {pvalue_name}",
                )

        if actual_workflow["cls_limit_points"] != expected_workflow["cls_limit_points"]:
            raise AssertionError(
                f"{workflow_name} cls_limit_points differ: "
                f"actual={actual_workflow['cls_limit_points']}, "
                f"expected={expected_workflow['cls_limit_points']}"
            )


def build_analysis_reference(repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Create a deterministic J100/J50 background-only reference payload."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    payload: dict[str, Any] = {}
    for workflow_name, fit_dir_name in WORKFLOW_FIT_DIRS:
        fit_dir = repo_root / "run" / "fits" / workflow_name / fit_dir_name
        if not fit_dir.exists():
            raise FileNotFoundError(
                f"Expected fit directory for {workflow_name} not found: {fit_dir}"
            )
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
    path.write_text(
        json.dumps(validated_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _validate_runtime_provenance(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise ValueError("Analysis provenance runtime must be a JSON object")

    required_keys = {
        "python_version",
        "python_executable",
        "root_version",
    }
    payload_keys = set(payload)

    if payload_keys != required_keys:
        raise ValueError(
            "Analysis provenance runtime has invalid keys "
            f"(missing={sorted(required_keys - payload_keys)}, "
            f"unexpected={sorted(payload_keys - required_keys)})"
        )

    for key in required_keys:
        value = payload[key]
        if not isinstance(value, str) or not value:
            raise ValueError(f"Analysis provenance runtime {key} " "must be a non-empty string")

    return {key: payload[key] for key in sorted(required_keys)}


def _validate_tool_revisions(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise ValueError("Analysis provenance tool_revisions must be a JSON object")

    required_tools = {
        "xmlAnaWSBuilder",
        "quickFit",
        "workspaceCombiner",
        "pyBumpHunter",
    }
    payload_keys = set(payload)

    if payload_keys != required_tools:
        raise ValueError(
            "Analysis provenance tool_revisions has invalid keys "
            f"(missing={sorted(required_tools - payload_keys)}, "
            f"unexpected={sorted(payload_keys - required_tools)})"
        )

    return {
        tool: _validate_git_revision(
            payload[tool],
            f"Analysis provenance {tool} revision",
        )
        for tool in sorted(required_tools)
    }


def _validate_configuration_provenance(
    payload: Any,
) -> dict[str, dict[str, str]]:
    if not isinstance(payload, dict):
        raise ValueError("Analysis provenance configurations must be a JSON object")

    required_configurations = {
        "topfile",
        "categoryfile",
        "backgroundfile",
        "signalfile",
    }
    payload_keys = set(payload)

    if payload_keys != required_configurations:
        raise ValueError(
            "Analysis provenance configurations has invalid keys "
            f"(missing={sorted(required_configurations - payload_keys)}, "
            f"unexpected={sorted(payload_keys - required_configurations)})"
        )

    validated = {
        name: _validate_file_provenance(
            payload[name],
            f"Analysis provenance configuration {name}",
        )
        for name in ("topfile", "categoryfile")
    }

    for name in ("backgroundfile", "signalfile"):
        value = payload[name]
        validated[name] = (
            None
            if value is None
            else _validate_file_provenance(
                value,
                f"Analysis provenance configuration {name}",
            )
        )

    return validated


def _validate_invocation_provenance(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Analysis provenance invocation must be a JSON object")

    required_keys = {
        "datahist",
        "range_low",
        "range_high",
        "signal_enabled",
        "limit_enabled",
        "prefit_enabled",
        "mask_threshold",
    }
    payload_keys = set(payload)

    if payload_keys != required_keys:
        raise ValueError(
            "Analysis provenance invocation has invalid keys "
            f"(missing={sorted(required_keys - payload_keys)}, "
            f"unexpected={sorted(payload_keys - required_keys)})"
        )

    datahist = payload["datahist"]
    if not isinstance(datahist, str) or not datahist:
        raise ValueError("Analysis provenance invocation datahist " "must be a non-empty string")

    range_low = payload["range_low"]
    range_high = payload["range_high"]

    valid_range = (
        isinstance(range_low, int)
        and not isinstance(range_low, bool)
        and isinstance(range_high, int)
        and not isinstance(range_high, bool)
        and range_low < range_high
    )

    if not valid_range:
        raise ValueError(
            "Analysis provenance invocation requires integer bounds "
            "with range_low smaller than range_high"
        )

    for flag in (
        "signal_enabled",
        "limit_enabled",
        "prefit_enabled",
    ):
        if not isinstance(payload[flag], bool):
            raise ValueError(f"Analysis provenance invocation {flag} must be boolean")

    mask_threshold = payload["mask_threshold"]
    valid_threshold = (
        isinstance(mask_threshold, (int, float))
        and not isinstance(mask_threshold, bool)
        and 0.0 <= float(mask_threshold) <= 1.0
    )

    if not valid_threshold:
        raise ValueError(
            "Analysis provenance invocation mask_threshold " "must be numeric and between 0 and 1"
        )

    return {
        "datahist": datahist,
        "range_low": range_low,
        "range_high": range_high,
        "signal_enabled": payload["signal_enabled"],
        "limit_enabled": payload["limit_enabled"],
        "prefit_enabled": payload["prefit_enabled"],
        "mask_threshold": float(mask_threshold),
    }


def _validate_reference_provenance(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Analysis reference provenance must be a JSON object")

    required_keys = {
        "runtime",
        "tool_revisions",
        "input",
        "configurations",
        "invocation",
    }
    payload_keys = set(payload)

    if payload_keys != required_keys:
        raise ValueError(
            "Analysis reference provenance has invalid keys "
            f"(missing={sorted(required_keys - payload_keys)}, "
            f"unexpected={sorted(payload_keys - required_keys)})"
        )

    return {
        "runtime": _validate_runtime_provenance(payload["runtime"]),
        "tool_revisions": _validate_tool_revisions(payload["tool_revisions"]),
        "input": _validate_file_provenance(
            payload["input"],
            "Analysis reference provenance input",
        ),
        "configurations": _validate_configuration_provenance(payload["configurations"]),
        "invocation": _validate_invocation_provenance(payload["invocation"]),
    }


def _validate_analysis_provenance(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Analysis provenance must be a JSON object")

    required_keys = {
        "repository_commit",
        "repository_dirty",
        "runtime",
        "tool_revisions",
        "input",
        "configurations",
        "invocation",
    }
    payload_keys = set(payload)

    if payload_keys != required_keys:
        raise ValueError(
            "Analysis provenance has invalid keys "
            f"(missing={sorted(required_keys - payload_keys)}, "
            f"unexpected={sorted(payload_keys - required_keys)})"
        )

    repository_dirty = payload["repository_dirty"]
    if not isinstance(repository_dirty, bool):
        raise ValueError("Analysis provenance repository_dirty must be boolean")

    return {
        "repository_commit": _validate_git_revision(
            payload["repository_commit"],
            "Analysis provenance repository_commit",
        ),
        "repository_dirty": repository_dirty,
        "runtime": _validate_runtime_provenance(
            payload["runtime"],
        ),
        "tool_revisions": _validate_tool_revisions(
            payload["tool_revisions"],
        ),
        "input": _validate_file_provenance(
            payload["input"],
            "Analysis provenance input",
        ),
        "configurations": _validate_configuration_provenance(
            payload["configurations"],
        ),
        "invocation": _validate_invocation_provenance(
            payload["invocation"],
        ),
    }
