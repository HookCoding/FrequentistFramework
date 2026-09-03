import json
import os

from run_execution import execute_required


def load_bumphunter_results(results_file):
    try:
        with open(results_file) as file:
            results = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            "Could not read valid BumpHunter results from {}: {}".format(
                results_file,
                error,
            )
        ) from error

    if not isinstance(results, dict):
        raise ValueError("BumpHunter results in {} must be a JSON object".format(results_file))

    required_keys = ("BlindRange", "MaskMin", "MaskMax")
    missing_keys = [key for key in required_keys if key not in results]
    if missing_keys:
        raise ValueError(
            "BumpHunter results in {} are missing required keys: {}".format(
                results_file,
                ", ".join(missing_keys),
            )
        )

    try:
        mask_min = int(results["MaskMin"])
        mask_max = int(results["MaskMax"])
    except (TypeError, ValueError) as error:
        raise ValueError(
            "BumpHunter MaskMin and MaskMax must be integer-compatible values"
        ) from error

    if mask_min >= mask_max:
        raise ValueError("BumpHunter MaskMin must be smaller than MaskMax")

    blind_range = results["BlindRange"]
    if not isinstance(blind_range, str) or not blind_range.strip():
        raise ValueError("BumpHunter BlindRange must be a non-empty string")

    return {
        "BlindRange": blind_range,
        "MaskMin": mask_min,
        "MaskMax": mask_max,
    }


def run_bumphunter(postfitfile, folder):
    bhresults_file = "{}/BHresults.json".format(folder)

    if os.path.exists(bhresults_file):
        os.remove(bhresults_file)

    bumphunter_command = (
        "pyBumpHunter/pyBH_env/bin/python3 "
        "python/FindBHWindow.py "
        "--inputfile %s "
        "--bkghist %s "
        "--datahist %s "
        "--outputjson %s"
    ) % (
        postfitfile,
        "Run3TLA_rebinned/postfit",
        "Run3TLA_rebinned/data",
        bhresults_file,
    )

    if not execute_required(
        bumphunter_command,
        "BumpHunter masking-window calculation",
        expected_outputs=[bhresults_file],
    ):
        raise RuntimeError("BumpHunter masking-window calculation failed")

    return load_bumphunter_results(bhresults_file)


def should_mask(p_value, threshold):
    # Not simply "p_value <= threshold": that is equivalent to
    # "not (p_value > threshold)" for ordinary floats, but not for NaN,
    # where both "p_value > threshold" and "p_value <= threshold" are
    # False under IEEE 754 comparison rules. The coordinator's original
    # gating was "if p_value > threshold: <success>", so a NaN p-value
    # (a real possibility from a degenerate fit) took the masking branch.
    # Writing the negation explicitly preserves that for NaN inputs too.
    return not (p_value > threshold)
