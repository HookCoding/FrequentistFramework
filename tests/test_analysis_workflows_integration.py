from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from python.analysis_reference import (
    assert_analysis_reference_close,
    build_analysis_reference,
    read_analysis_reference,
)

REQUIRED_ARTIFACTS = (
    "background_dijetTLA_fromTemplate.xml",
    "category_dijetTLA_fromTemplate.xml",
    "dijetTLA_fromTemplate.xml",
    "signal_dijetTLA_fromTemplate.xml",
    "dijetisrTLA_combWS_sixPar.root",
    "FitResult_anaFit_sixPar_bkgOnly.root",
    "FitParameters_anaFit_sixPar_bkgOnly.root",
    "PostFit_anaFit_sixPar_bkgOnly.root",
    "quickFitLog_anaFit_sixPar_bkgOnly.log",
    "analysis_results.json",
)

WORKFLOWS = (
    (
        "J100",
        "scripts/run_anaFit_J100.sh",
        "run_481_3000_sixPar",
    ),
    (
        "J50",
        "scripts/run_anaFit_J50.sh",
        "run_344_2079_sixPar",
    ),
)

APPROVED_SCIENTIFIC_PYTHON_EXECUTABLES = {
    "/cvmfs/sft.cern.ch/lcg/views/LCG_102a/" "x86_64-centos9-gcc11-opt/bin/python",
    "/cvmfs/sft.cern.ch/lcg/views/LCG_102a/" "x86_64-ubuntu2204-gcc11-opt/bin/python",
}


def _require_runtime(repo_root: Path) -> None:
    required_paths = (
        "scripts/setup_buildAndFit.sh",
        "xmlAnaWSBuilder/build/bin/XMLReader",
        "quickFit/build/quickFit",
        "pyBumpHunter/pyBH_env/bin/python3",
        "python/FindBHWindow.py",
        "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
        "Input/data/dijetTLA/mjj_spectra_J50_dataAll.root",
        "Input/data/dijetisrTLA/mjjResolutionBinning_481.root",
        "Input/data/dijetisrTLA/mjjResolutionBinning_344.root",
    )

    missing = [
        relative_path
        for relative_path in required_paths
        if not (repo_root / relative_path).exists()
    ]

    if missing:
        pytest.fail(
            "Required analysis runtime paths are missing:\n"
            + "\n".join(f"  - {path}" for path in missing)
        )


def _run_workflow(
    repo_root: Path,
    temporary_root: Path,
    workflow: str,
    launcher: str,
    fit_directory_name: str,
) -> None:
    output_root = temporary_root / "run" / "fits"
    console_log = temporary_root / f"{workflow}-console.log"
    run_start_ns = time.time_ns()

    environment = os.environ.copy()
    environment.update(
        {
            "ANAFIT_OUTPUT_DIR": str(output_root),
            "ANAFIT_SKIP_PLOTS": "1",
            "FIT_PARS": "six",
        }
    )

    with console_log.open("w", encoding="utf-8") as stream:
        completed = subprocess.run(
            [str(repo_root / launcher)],
            cwd=repo_root,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )

    if completed.returncode != 0:
        pytest.fail(
            f"{workflow} analysis failed with exit code "
            f"{completed.returncode}.\n"
            f"Console log: {console_log}\n\n"
            f"{console_log.read_text(encoding='utf-8', errors='replace')[-8000:]}"
        )

    fit_directory = output_root / workflow / fit_directory_name

    for filename in REQUIRED_ARTIFACTS:
        artifact = fit_directory / filename

        assert artifact.is_file(), (
            f"{workflow} did not create required artifact: {artifact}\n"
            f"Console log: {console_log}"
        )
        assert (
            artifact.stat().st_size > 0
        ), f"{workflow} created an empty required artifact: {artifact}"
        assert (
            artifact.stat().st_mtime_ns >= run_start_ns
        ), f"{workflow} artifact is not fresh: {artifact}"

    conditional_outputs = (
        list(fit_directory.glob("*_masked.root"))
        + list(fit_directory.glob("*_masked.xml"))
        + list(fit_directory.glob("BHresults.json"))
    )

    assert not conditional_outputs, (
        f"{workflow} unexpectedly entered the masked-fit path: " f"{conditional_outputs}"
    )


@pytest.mark.integration
@pytest.mark.requires_root
def test_authoritative_j100_j50_workflows_match_frozen_reference(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    _require_runtime(repo_root)

    for workflow, launcher, fit_directory_name in WORKFLOWS:
        _run_workflow(
            repo_root=repo_root,
            temporary_root=tmp_path,
            workflow=workflow,
            launcher=launcher,
            fit_directory_name=fit_directory_name,
        )

    fresh = build_analysis_reference(tmp_path)
    frozen = read_analysis_reference(repo_root / "tests" / "references" / "analysis_reference.json")

    expected_python_executable = os.environ.get("ANAFIT_EXPECTED_PYTHON_EXECUTABLE")
    if expected_python_executable is not None:
        assert expected_python_executable in APPROVED_SCIENTIFIC_PYTHON_EXECUTABLES, (
            "Unapproved expected scientific Python executable: " f"{expected_python_executable}"
        )

        for workflow_payload in frozen.values():
            workflow_payload["provenance"]["runtime"][
                "python_executable"
            ] = expected_python_executable

    assert_analysis_reference_close(fresh, frozen)


def test_scientific_artifact_contract_excludes_plots() -> None:
    assert REQUIRED_ARTIFACTS

    plot_suffixes = (".pdf", ".png", ".jpg", ".jpeg", ".svg")
    plot_artifacts = [
        artifact for artifact in REQUIRED_ARTIFACTS if artifact.lower().endswith(plot_suffixes)
    ]

    assert plot_artifacts == []


@pytest.mark.requires_root
@pytest.mark.requires_analysis_dependencies
def test_authoritative_setup_provides_scientific_runtime() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    probe = r"""
repo_dir="$PWD"
source "$repo_dir/scripts/setup_buildAndFit.sh" >/dev/null
setup_status=$?

if (( setup_status != 0 )); then
    echo "setup_status=$setup_status"
    exit "$setup_status"
fi

python --version
root-config --version

python - <<'INNER_PY'
import platform
import ROOT

print("python_import_version=" + platform.python_version())
print("root_import_version=" + ROOT.gROOT.GetVersion())
INNER_PY

for path in \
  xmlAnaWSBuilder/build/bin/XMLReader \
  quickFit/build/quickFit \
  pyBumpHunter/pyBH_env/bin/python3 \
  python/FindBHWindow.py \
  Input/data/dijetTLA/mjj_spectra_J100_dataAll.root \
  Input/data/dijetTLA/mjj_spectra_J50_dataAll.root \
  Input/data/dijetisrTLA/mjjResolutionBinning_481.root \
  Input/data/dijetisrTLA/mjjResolutionBinning_344.root
do
    if [[ ! -e "$path" ]]; then
        echo "missing=$path"
        exit 10
    fi
done

for path in \
  xmlAnaWSBuilder/build/bin/XMLReader \
  quickFit/build/quickFit \
  pyBumpHunter/pyBH_env/bin/python3
do
    if [[ ! -x "$path" ]]; then
        echo "not_executable=$path"
        exit 11
    fi
done
"""

    completed = subprocess.run(
        ["bash", "-lc", probe],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, (
        "Authoritative scientific-runtime setup failed:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )

    assert "Python 3.9.12" in completed.stdout
    assert "6.26/08" in completed.stdout
    assert "python_import_version=3.9.12" in completed.stdout
    assert "root_import_version=6.26/08" in completed.stdout
    assert "missing=" not in completed.stdout
    assert "not_executable=" not in completed.stdout
