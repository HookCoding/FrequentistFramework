import json
import subprocess
from pathlib import Path

import pytest

from python.repo_utils import (
    build_repo_snapshot,
    find_repo_root,
    read_repo_snapshot,
    write_repo_snapshot,
)


def test_find_repo_root_returns_workspace_root() -> None:
    repo_root = find_repo_root()

    assert repo_root == Path(__file__).resolve().parents[1]
    assert (repo_root / "README.md").exists()
    assert (repo_root / "python").is_dir()


def test_repo_snapshot_matches_frozen_reference(tmp_path: Path) -> None:
    snapshot = build_repo_snapshot()
    reference_path = (
        Path(__file__).resolve().parents[1] / "tests" / "references" / "repo_snapshot.json"
    )

    write_repo_snapshot(tmp_path / "snapshot.json", snapshot)
    written_snapshot = read_repo_snapshot(tmp_path / "snapshot.json")

    expected_snapshot = read_repo_snapshot(reference_path)

    assert written_snapshot == expected_snapshot
    assert written_snapshot["python_dir_exists"] is True
    assert written_snapshot["tests_dir_exists"] is True
    assert written_snapshot["readme_exists"] is True
    assert written_snapshot["top_level_entries"] == json.loads(
        json.dumps(expected_snapshot["top_level_entries"])
    )


DEPENDENCY_REVISIONS = {
    "xmlAnaWSBuilder": "6b84050f3c0206a6f30eb40b103cc101e68505cc",
    "quickFit": "0408030b6c8d74a2e2c27a864a02756132d08f5a",
    "workspaceCombiner": "7d484ad3f89c4075d2c567aa4503fc56e1bb9468",
    "pyBumpHunter": "91f49a622bd77622edb02a1a2788fc12835e5b72",
}


@pytest.mark.requires_analysis_dependencies
def test_external_dependency_checkouts_match_pinned_revisions() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    for dependency, expected_revision in DEPENDENCY_REVISIONS.items():
        dependency_path = repo_root / dependency

        assert (
            dependency_path.is_dir()
        ), f"Required dependency directory is missing: {dependency_path}"

        completed = subprocess.run(
            ["git", "-C", str(dependency_path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
        )

        assert completed.returncode == 0, (
            f"{dependency} is not a readable Git checkout:\n" f"{completed.stderr}"
        )
        assert completed.stdout.strip() == expected_revision, (
            f"{dependency} revision mismatch: "
            f"expected {expected_revision}, "
            f"found {completed.stdout.strip()}"
        )


@pytest.mark.requires_analysis_dependencies
def test_external_dependency_checkouts_have_no_tracked_source_changes() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    for dependency in DEPENDENCY_REVISIONS:
        dependency_path = repo_root / dependency

        completed = subprocess.run(
            [
                "git",
                "-C",
                str(dependency_path),
                "status",
                "--short",
                "--untracked-files=no",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        assert completed.returncode == 0, (
            f"Could not inspect {dependency} checkout:\n" f"{completed.stderr}"
        )
        assert not completed.stdout.strip(), (
            f"{dependency} contains tracked source modifications:\n" f"{completed.stdout}"
        )


def test_generated_output_ignore_policy_is_narrow() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    generated_outputs = [
        "run/fits/J100/run_481_3000_sixPar/audit_generated.root",
        "run/fits/J100/run_481_3000_sixPar/audit_generated.pdf",
        "run/fits/J100/run_481_3000_sixPar/audit_generated.xml",
        "run/fits/J100/run_481_3000_sixPar/audit_generated.log",
        "run/fits/J50/run_344_2079_sixPar/audit_generated.root",
        "run/fits/J50/run_344_2079_sixPar/audit_generated.pdf",
        "run/fits/J50/run_344_2079_sixPar/audit_generated.xml",
        "run/fits/J50/run_344_2079_sixPar/audit_generated.log",
    ]

    canonical_manifests = [
        "run/fits/J100/run_481_3000_sixPar/analysis_results.json",
        "run/fits/J50/run_344_2079_sixPar/analysis_results.json",
    ]

    for relative_path in generated_outputs:
        completed = subprocess.run(
            [
                "git",
                "check-ignore",
                "--quiet",
                "--no-index",
                relative_path,
            ],
            cwd=repo_root,
            check=False,
        )

        assert completed.returncode == 0, (
            f"Generated output is unexpectedly exposed to Git: " f"{relative_path}"
        )

    for relative_path in canonical_manifests:
        completed = subprocess.run(
            [
                "git",
                "check-ignore",
                "--quiet",
                "--no-index",
                relative_path,
            ],
            cwd=repo_root,
            check=False,
        )

        assert completed.returncode == 1, (
            f"Canonical analysis manifest is unexpectedly ignored: " f"{relative_path}"
        )


def test_no_untracked_generated_analysis_products() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    completed = subprocess.run(
        [
            "git",
            "status",
            "--short",
            "--untracked-files=all",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )

    generated_suffixes = (".root", ".pdf", ".xml", ".log")
    unexpected = []

    for line in completed.stdout.splitlines():
        status = line[:2]
        relative_path = line[3:]

        if status == "??" and relative_path.endswith(generated_suffixes):
            unexpected.append(relative_path)

    assert not unexpected, "Unexpected untracked generated analysis products:\n" + "\n".join(
        f"  - {path}" for path in unexpected
    )


def test_ci_runs_locked_lightweight_full_gate() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    workflow_path = repo_root / ".github" / "workflows" / "tier1-root-comparison.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    assert "uses: actions/checkout@" in workflow
    assert "uses: actions/setup-python@" in workflow
    assert 'python-version: "3.12.13"' in workflow
    assert "requirements-dev-lock.txt" in workflow
    assert "python -m pip install -r requirements-dev-lock.txt" in workflow
    assert "python scripts/quality_check.py --mode full" in workflow

    assert "tests/test_analysis_workflows_integration.py" not in workflow
    assert "requires_root" not in workflow
    assert "requires_analysis_dependencies" not in workflow

    assert "tier-2-m365" in workflow


def test_precommit_is_not_a_locked_development_dependency() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    direct_dependencies = (repo_root / "requirements-dev.txt").read_text(encoding="utf-8")
    locked_dependencies = (repo_root / "requirements-dev-lock.txt").read_text(encoding="utf-8")

    assert "pre-commit==" not in direct_dependencies
    assert "pre-commit==" not in locked_dependencies


def test_git_hook_pre_commit_gate_matches_authoritative_commands() -> None:
    # .githooks/pre-commit is a plain git-native hook, not the
    # third-party `pre-commit` framework the test above confirms is
    # absent - it wires the two already-authoritative commands
    # (scripts/quality_check.py --mode full, and the same "integration
    # and requires_root" scientific gate every Tier 3 chunk runs before
    # committing) into a mandatory local check, per
    # doc/TIER2_SYSTEM.md's "Optional pre-commit configuration" section.
    repo_root = Path(__file__).resolve().parents[1]

    hook_path = repo_root / ".githooks" / "pre-commit"
    installer_path = repo_root / "scripts" / "install_git_hooks.sh"

    assert hook_path.is_file(), "Missing .githooks/pre-commit"
    assert hook_path.stat().st_mode & 0o111, "the pre-commit hook must be executable"
    assert installer_path.is_file(), "Missing scripts/install_git_hooks.sh"
    assert installer_path.stat().st_mode & 0o111, "the hook installer must be executable"

    hook_text = hook_path.read_text(encoding="utf-8")
    installer_text = installer_path.read_text(encoding="utf-8")

    assert "scripts/quality_check.py --mode full" in hook_text
    assert "setup_buildAndFit.sh" in hook_text
    assert "tests/test_analysis_workflows_integration.py" in hook_text
    assert '"integration and requires_root"' in hook_text

    assert "core.hooksPath" in installer_text
    assert ".githooks" in installer_text


def test_authoritative_analysis_launchers_are_executable() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    launchers = (
        repo_root / "scripts" / "run_anaFit_J100.sh",
        repo_root / "scripts" / "run_anaFit_J50.sh",
    )

    for launcher in launchers:
        assert launcher.is_file(), f"Missing authoritative launcher: {launcher}"
        assert (
            launcher.stat().st_mode & 0o111
        ), f"Authoritative launcher is not executable: {launcher}"


def test_gitmodules_declares_expected_analysis_dependencies() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    gitmodules = (repo_root / ".gitmodules").read_text(encoding="utf-8")

    for dependency in DEPENDENCY_REVISIONS:
        assert f"path = {dependency}" in gitmodules


def test_declared_submodules_have_gitlink_entries() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    completed = subprocess.run(
        [
            "git",
            "ls-files",
            "--stage",
            *DEPENDENCY_REVISIONS,
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )

    gitlinks = {}

    for line in completed.stdout.splitlines():
        mode, _, _, path = line.split(maxsplit=3)
        gitlinks[path] = mode

    assert gitlinks == {dependency: "160000" for dependency in DEPENDENCY_REVISIONS}


def test_pybumphunter_installer_is_non_destructive_and_reproducible() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    installer = repo_root / "scripts" / "install_pyBumpHunter.sh"

    assert installer.is_file()
    assert installer.stat().st_mode & 0o111

    installer_text = installer.read_text(encoding="utf-8")
    active_lines = [
        line.strip()
        for line in installer_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    active_script = "\n".join(active_lines)

    assert "rm -rf" not in active_script
    assert "git pull" not in active_script
    assert "git clone" not in active_script
    assert "setup.py install" not in active_script
    assert "pip install --upgrade" not in active_script
    assert "virtualenv " not in active_script
    assert "LCG_105" not in active_script

    assert 'scientific_setup="$repo_root/scripts/setup_buildAndFit.sh"' in installer_text
    assert "--system-site-packages" in installer_text
    assert "--no-deps" in installer_text
    assert "--no-build-isolation" in installer_text
    assert '"$pybh_source"' in installer_text

    assert 'if [[ -e "$pybh_environment" ]]; then' in installer_text
    assert "existing_python_version" in installer_text
    assert "platform.python_version()" in installer_text
    assert "Existing pyBH_env uses Python" in installer_text
    assert "expected" in installer_text
    assert "Existing pyBH_env failed import validation" in installer_text
    assert "Existing pyBumpHunter environment is valid" in installer_text

    required_imports = {
        "import matplotlib",
        "import numpy",
        "import pyBumpHunter",
        "import scipy",
        "import uproot",
    }

    for required_import in required_imports:
        assert required_import in installer_text

    assert '"$environment_python" "$find_bh_window" --help' in installer_text


def test_install_script_is_non_destructive() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    installer = repo_root / "install.sh"

    assert installer.is_file()
    assert installer.stat().st_mode & 0o111

    installer_text = installer.read_text(encoding="utf-8")
    active_lines = [
        line.strip()
        for line in installer_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    active_script = "\n".join(active_lines)

    assert "rm -rf" not in active_script
    assert "git clone" not in active_script
    assert "git pull" not in active_script
    assert "git checkout" not in active_script
    assert "setup.py install" not in active_script
    assert "pip install --upgrade" not in active_script

    assert "--check" in installer_text
    assert "run_check" in installer_text
    assert "verify_parent_gitlink" in installer_text
    assert "verify_no_tracked_changes" in installer_text
    assert "verify_roofit_extensions" in installer_text
    assert 'mode" != "160000"' in installer_text
    assert "ba94bfcbfa4f4a4e3541ade09580399e409e8514" in installer_text
    assert "Installation contract check passed." in installer_text
    assert "No files were modified." in installer_text

    assert "--build" in installer_text
    assert "run_build() {" in installer_text
    assert "build_roofit_extensions() {" in installer_text
    assert "build_cpp_dependency() {" in installer_text
    assert "setup_scientific_environment() {" in installer_text

    assert "run_check" in installer_text
    assert "setup_scientific_environment" in installer_text
    assert 'install_jobs_value="${INSTALL_JOBS:-4}"' in installer_text
    assert "INSTALL_JOBS must be a positive integer" in installer_text

    assert 'mkdir -p "$build_dir"' in installer_text
    assert "cmake --build" in installer_text
    assert "--parallel" in installer_text

    assert "cmake --install" not in installer_text
    assert "CMAKE_INSTALL_PREFIX=/usr/local" not in installer_text

    assert "libRooFitExtensions.so" in installer_text
    assert "libRooFitExtensions_rdict.pcm" in installer_text
    assert "libRooFitExtensions.rootmap" in installer_text
    assert "RooFitExtensionsConfig.cmake" in installer_text

    assert "bin/XMLReader" in installer_text
    assert "libxmlAnaWSBuilder.so" in installer_text
    assert 'verify_executable_file "$build_dir/quickFit"' in installer_text
    assert "libquick.so" in installer_text
    assert 'verify_executable_file "$build_dir/manager"' in installer_text
    assert "libworkspaceCombiner.so" in installer_text

    assert "scripts/install_pyBumpHunter.sh" in installer_text
    assert "Non-destructive dependency build completed successfully." in installer_text

    command_dispatch = installer_text.split('case "$1" in', maxsplit=1)[1]
    assert "--build)" in command_dispatch
    assert "run_build" in command_dispatch
