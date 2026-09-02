import json
import os


def write_analysis_results(
    folder,
    p_chi2,
    masked,
    provenance,
):
    results_path = os.path.join(folder, "analysis_results.json")
    temporary_path = results_path + ".tmp"

    payload = {
        "schema_version": 2,
        "status": "success",
        "masked": bool(masked),
        "p_chi2": float(p_chi2),
        "provenance": provenance,
    }

    with open(temporary_path, "w") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")

    os.replace(temporary_path, results_path)
    return results_path
