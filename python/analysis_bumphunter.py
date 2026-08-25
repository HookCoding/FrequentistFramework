from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from python.analysis_artifacts import remove_stale_bumphunter_json
except ModuleNotFoundError:
    from analysis_artifacts import remove_stale_bumphunter_json
try:
    from python.analysis_commands import execute_required
except ModuleNotFoundError:
    from analysis_commands import execute_required


def validate_mask_range(mask_min: int, mask_max: int) -> None:
    """Validate BumpHunter mask bounds before continuing the masking refit."""
    if mask_min >= mask_max:
        raise ValueError("BumpHunter MaskMin must be smaller than MaskMax")


def should_mask(p_chi2: float, mask_threshold: float) -> bool:
    """Return True when a fit should be masked according to the configured threshold."""
    return float(p_chi2) < float(mask_threshold)


def load_bumphunter_results(results_file: str | os.PathLike[str]) -> dict[str, object]:
    """Read and validate a BumpHunter JSON payload."""
    file_path = Path(results_file)
    try:
        with file_path.open("r", encoding="utf-8") as file:
            results = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Could not read valid BumpHunter results from {file_path}: {error}"
        ) from error

    if not isinstance(results, dict):
        raise ValueError(f"BumpHunter results in {file_path} must be a JSON object")

    required_keys = ("BlindRange", "MaskMin", "MaskMax")
    missing_keys = [key for key in required_keys if key not in results]
    if missing_keys:
        missing_list = ", ".join(missing_keys)
        raise ValueError(
            f"BumpHunter results in {file_path} are missing required keys: {missing_list}"
        )

    try:
        mask_min = int(results["MaskMin"])
        mask_max = int(results["MaskMax"])
    except (TypeError, ValueError) as error:
        raise ValueError(
            "BumpHunter MaskMin and MaskMax must be integer-compatible values"
        ) from error

    validate_mask_range(mask_min, mask_max)

    blind_range = results["BlindRange"]
    if not isinstance(blind_range, str) or not blind_range.strip():
        raise ValueError("BumpHunter BlindRange must be a non-empty string")

    return {
        "BlindRange": blind_range,
        "MaskMin": mask_min,
        "MaskMax": mask_max,
    }


def prepare_bumphunter_command(postfit_file: str, output_json: str | os.PathLike[str]) -> str:
    """Build the established BumpHunter masking-window command."""
    return (
        "pyBumpHunter/pyBH_env/bin/python3 python/FindBHWindow.py "
        "--inputfile %s --bkghist %s --datahist %s --outputjson %s"
    ) % (postfit_file, "Run3TLA_rebinned/postfit", "Run3TLA_rebinned/data", output_json)


def run_bumphunter(postfitfile: str, folder: str | os.PathLike[str]) -> dict[str, object]:
    """Generate and validate BumpHunter masking data for a postfit file."""
    folder_path = Path(folder)
    bhresults_file = folder_path / "BHresults.json"
    remove_stale_bumphunter_json(folder_path)

    bumphunter_command = prepare_bumphunter_command(postfitfile, bhresults_file)

    if not execute_required(
        bumphunter_command,
        "BumpHunter masking-window calculation",
        expected_outputs=[str(bhresults_file)],
    ):
        raise RuntimeError("BumpHunter masking-window calculation failed")

    return load_bumphunter_results(bhresults_file)
