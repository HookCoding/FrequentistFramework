from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

REQUIRED_BASELINE_PATHS = [
    "scripts/run_anaFit_J100.sh",
    "scripts/run_anaFit_J50.sh",
    "scripts/setup_buildAndFit.sh",
    "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
    "Input/data/dijetTLA/mjj_spectra_J50_dataAll.root",
    "tests/references/analysis_reference.json",
    "tests/references/repo_snapshot.json",
]

OPTIONAL_WORKFLOW_HINT_PATHS = [
    "xmlAnaWSBuilder/setup_lxplus.sh",
    "quickFit/setup_lxplus.sh",
]


def _module_is_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _check_required_paths(repo_root: Path) -> None:
    missing = [path for path in REQUIRED_BASELINE_PATHS if not (repo_root / path).exists()]
    if not missing:
        return

    print("[tier1] Missing required baseline paths for the J100/J50 Run-2 workflow:")
    for path in missing:
        print(f"  - {path}")
    print("[tier1] Restore the missing files/inputs before running quality checks.")
    raise SystemExit(1)


def _print_optional_workflow_hints(repo_root: Path) -> None:
    missing = [path for path in OPTIONAL_WORKFLOW_HINT_PATHS if not (repo_root / path).exists()]
    if not missing:
        return

    print("[tier1] Note: fit runtime dependencies are not fully present:")
    for path in missing:
        print(f"  - {path}")
    print(
        "[tier1] You can still run unit/lint checks, but fit scripts may fail until these "
        "dependencies are installed."
    )


def _ensure_python_tools_available(required_modules: list[str]) -> None:
    missing_modules = [module for module in required_modules if not _module_is_available(module)]
    if not missing_modules:
        return

    print("[tier1] Missing required Python tooling modules:")
    for module in missing_modules:
        print(f"  - {module}")
    print(
        "[tier1] Install them with:\n"
        f"  {sys.executable} -m pip install {' '.join(missing_modules)}"
    )
    raise SystemExit(2)


def run_command(command: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Tier-1 quality checks for the authoritative J100/J50 Run-2 workflow."
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "full"],
        default="fast",
        help="fast: baseline checks + targeted Tier-1 pytest; full: fast + ruff + black.",
    )
    return parser.parse_args()


def _run_fast_checks(repo_root: Path, test_targets: list[str]) -> None:
    _ensure_python_tools_available(["pytest"])
    run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "not requires_analysis_dependencies",
            *test_targets,
        ],
        repo_root,
    )


def _run_full_checks(repo_root: Path, python_targets: list[str], test_targets: list[str]) -> None:
    _run_fast_checks(repo_root, test_targets)
    _ensure_python_tools_available(["ruff", "black"])
    run_command([sys.executable, "-m", "ruff", "check", *python_targets, *test_targets], repo_root)
    run_command(
        [sys.executable, "-m", "black", "--check", *python_targets, *test_targets], repo_root
    )


def main() -> None:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    _check_required_paths(repo_root)
    _print_optional_workflow_hints(repo_root)

    python_targets = [
        "plot_edm.py",
        "python/analysis_reference.py",
        "python/createBinning.py",
        "python/ExtractFitParameters.py",
        "python/ExtractPostfitFromWS.py",
        "python/FindBHWindow.py",
        "python/plotPostFit.py",
        "python/PreFit.py",
        "python/repo_utils.py",
        "python/run_anaFit.py",
        "python/run_cli.py",
        "python/run_execution.py",
        "python/run_fit.py",
        "python/run_manifest.py",
        "python/run_masking.py",
        "python/run_provenance.py",
        "python/run_templates.py",
        "scripts/compare_root_outputs.py",
        "scripts/quality_check.py",
    ]
    test_targets = [
        "tests/test_analysis_reference.py",
        "tests/test_compare_root_outputs.py",
        "tests/test_create_binning.py",
        "tests/test_extract_fit_parameters.py",
        "tests/test_extract_postfit_from_ws.py",
        "tests/test_find_bh_window.py",
        "tests/test_plot_edm.py",
        "tests/test_plot_post_fit.py",
        "tests/test_plot_postfit_macro.py",
        "tests/test_pre_fit.py",
        "tests/test_read_bumphunter_results.py",
        "tests/test_repo_utils.py",
        "tests/test_run_anaFit.py",
        "tests/test_run_cli.py",
        "tests/test_run_execution.py",
        "tests/test_run_fit.py",
        "tests/test_run_manifest.py",
        "tests/test_run_masking.py",
        "tests/test_run_provenance.py",
        "tests/test_run_templates.py",
    ]

    if args.mode == "fast":
        _run_fast_checks(repo_root, test_targets)
        return

    _run_full_checks(repo_root, python_targets, test_targets)


if __name__ == "__main__":
    main()
