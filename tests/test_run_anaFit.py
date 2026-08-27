from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_run_anafit_module(
    monkeypatch: pytest.MonkeyPatch,
):
    dependency_stubs = {
        "ROOT": {},
        "ExtractPostfitFromWS": {"PostfitExtractor": object},
        "ExtractFitParameters": {"FitParameterExtractor": object},
        "PreFit": {"PreFitter": object},
    }

    for module_name, attributes in dependency_stubs.items():
        module = ModuleType(module_name)
        for attribute_name, value in attributes.items():
            setattr(module, attribute_name, value)
        monkeypatch.setitem(sys.modules, module_name, module)

    module_path = Path(__file__).resolve().parents[1] / "python" / "run_anaFit.py"
    spec = importlib.util.spec_from_file_location("run_anaFit_under_test", module_path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("analysis_status", [0, -1])
def test_main_propagates_analysis_status(
    monkeypatch: pytest.MonkeyPatch,
    analysis_status: int,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    monkeypatch.setattr(
        module,
        "run_anaFit",
        lambda **kwargs: analysis_status,
    )

    result = module.main(
        [
            "--datafile",
            "input.root",
            "--datahist",
            "data",
            "--topfile",
            "top.xml",
            "--categoryfile",
            "category.xml",
            "--backgroundfile",
            "background.xml",
            "--signalfile",
            "signal.xml",
            "--wsfile",
            "workspace.root",
            "--outputfile",
            "fit-result.root",
            "--nbkg",
            "dummy",
        ]
    )

    assert result == analysis_status


def test_execute_required_accepts_success_with_expected_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    expected_output = tmp_path / "result.root"

    def create_fresh_output(cmd):
        expected_output.write_text("fresh result")
        return 0

    monkeypatch.setattr(module, "execute", create_fresh_output)

    assert module.execute_required(
        "analysis command",
        "test analysis",
        expected_outputs=[str(expected_output)],
    )
    assert expected_output.read_text() == "fresh result"


def test_execute_required_rejects_stale_expected_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    expected_output = tmp_path / "result.root"
    expected_output.write_text("stale result")

    def return_success_without_output(cmd):
        assert not expected_output.exists()
        return 0

    monkeypatch.setattr(module, "execute", return_success_without_output)

    assert not module.execute_required(
        "analysis command",
        "test analysis",
        expected_outputs=[str(expected_output)],
    )
    assert not expected_output.exists()


def test_execute_required_rejects_nonzero_command_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    monkeypatch.setattr(module, "execute", lambda cmd: 7)

    assert not module.execute_required(
        "analysis command",
        "test analysis",
    )


def test_execute_required_rejects_missing_expected_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    missing_output = tmp_path / "missing-result.root"

    monkeypatch.setattr(module, "execute", lambda cmd: 0)

    assert not module.execute_required(
        "analysis command",
        "test analysis",
        expected_outputs=[str(missing_output)],
    )


def test_build_fit_extract_stops_after_xmlreader_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    calls: list[str] = []

    def fail_xmlreader(cmd, description, expected_outputs=()):
        calls.append(description)
        return False

    monkeypatch.setattr(module, "execute_required", fail_xmlreader)

    with pytest.raises(
        RuntimeError,
        match="XMLReader workspace generation failed",
    ):
        module.build_fit_extract(
            topfile="top.xml",
            datafile="input.root",
            datahist="data",
            rangelow=481,
            rangehigh=3000,
            wsfile="workspace.root",
            fitresultfile="FitResult.root",
        )

    assert calls == ["XMLReader workspace generation"]


def test_build_fit_extract_stops_after_quickfit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    calls: list[str] = []

    def execute_required_with_quickfit_failure(
        cmd,
        description,
        expected_outputs=(),
    ):
        calls.append(description)
        return description != "quickFit background or signal fit"

    monkeypatch.setattr(
        module,
        "execute_required",
        execute_required_with_quickfit_failure,
    )

    with pytest.raises(
        RuntimeError,
        match="quickFit failed",
    ):
        module.build_fit_extract(
            topfile="top.xml",
            datafile="input.root",
            datahist="data",
            rangelow=481,
            rangehigh=3000,
            wsfile="workspace.root",
            fitresultfile="FitResult.root",
        )

    assert calls == [
        "XMLReader workspace generation",
        "quickFit background or signal fit",
    ]


@pytest.mark.parametrize(
    ("launcher_name", "region"),
    [
        ("run_anaFit_J100.sh", "J100"),
        ("run_anaFit_J50.sh", "J50"),
    ],
)
def test_launcher_propagates_analysis_failure_before_plotting(
    tmp_path: Path,
    launcher_name: str,
    region: str,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    setup_script = tmp_path / "fake-setup.sh"
    analysis_runner = tmp_path / "fake-analysis-runner.sh"
    output_dir = tmp_path / "outputs"
    runner_marker = tmp_path / "runner-called.txt"

    setup_script.write_text("#!/bin/bash\n")
    setup_script.chmod(0o755)

    analysis_runner.write_text(
        "#!/bin/bash\n" f'printf "%s\\n" "$*" > "{runner_marker}"\n' "exit 23\n"
    )
    analysis_runner.chmod(0o755)

    environment = os.environ.copy()
    environment.update(
        {
            "ANAFIT_OUTPUT_DIR": str(output_dir),
            "ANAFIT_SETUP_SCRIPT": str(setup_script),
            "ANAFIT_RUNNER": str(analysis_runner),
            "FIT_PARS": "six",
        }
    )

    completed = subprocess.run(
        ["bash", str(repo_root / "scripts" / launcher_name)],
        cwd=repo_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 23
    assert "run_anaFit.py failed with exit code 23" in completed.stderr
    assert runner_marker.is_file()

    runner_arguments = runner_marker.read_text()
    expected_folder = output_dir / region
    assert f"--folder {expected_folder}" in runner_arguments

    assert not list(output_dir.rglob("postFit.pdf"))
    assert not list(output_dir.rglob("plotPostFit.pdf"))


def test_load_bumphunter_results_accepts_valid_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "500,600", "MaskMin": 500, "MaskMax": 600}')

    assert module.load_bumphunter_results(str(results_file)) == {
        "BlindRange": "500,600",
        "MaskMin": 500,
        "MaskMax": 600,
    }


def test_load_bumphunter_results_rejects_malformed_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    results_file = tmp_path / "BHresults.json"
    results_file.write_text("{not valid JSON")

    with pytest.raises(ValueError, match="Could not read valid BumpHunter results"):
        module.load_bumphunter_results(str(results_file))


def test_load_bumphunter_results_rejects_missing_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "500,600"}')

    with pytest.raises(ValueError, match="missing required keys"):
        module.load_bumphunter_results(str(results_file))


@pytest.mark.parametrize(
    ("mask_min", "mask_max"),
    [
        ("invalid", 600),
        (600, 500),
        (500, 500),
    ],
)
def test_load_bumphunter_results_rejects_invalid_mask_limits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mask_min: object,
    mask_max: object,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    results_file = tmp_path / "BHresults.json"
    results_file.write_text(
        json.dumps(
            {
                "BlindRange": "500,600",
                "MaskMin": mask_min,
                "MaskMax": mask_max,
            }
        )
    )

    with pytest.raises(ValueError, match="MaskMin|MaskMax"):
        module.load_bumphunter_results(str(results_file))


def test_run_bumphunter_removes_stale_output_and_loads_fresh_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "stale", "MaskMin": 1, "MaskMax": 2}')

    def create_fresh_results(
        cmd,
        description,
        expected_outputs=(),
    ):
        assert not results_file.exists()
        assert description == "BumpHunter masking-window calculation"
        assert expected_outputs == [str(results_file)]
        assert str(results_file) in cmd

        results_file.write_text('{"BlindRange": "500,600", "MaskMin": 500, "MaskMax": 600}')
        return True

    monkeypatch.setattr(
        module,
        "execute_required",
        create_fresh_results,
    )

    results = module.run_bumphunter(
        "fresh-postfit.root",
        str(tmp_path),
    )

    assert results == {
        "BlindRange": "500,600",
        "MaskMin": 500,
        "MaskMax": 600,
    }


def test_run_bumphunter_propagates_command_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    stale_results = tmp_path / "BHresults.json"
    stale_results.write_text('{"BlindRange": "stale", "MaskMin": 1, "MaskMax": 2}')

    def fail_bumphunter(
        cmd,
        description,
        expected_outputs=(),
    ):
        assert not stale_results.exists()
        return False

    monkeypatch.setattr(
        module,
        "execute_required",
        fail_bumphunter,
    )

    with pytest.raises(
        RuntimeError,
        match="BumpHunter masking-window calculation failed",
    ):
        module.run_bumphunter(
            "fresh-postfit.root",
            str(tmp_path),
        )

    assert not stale_results.exists()


def test_run_bumphunter_rejects_success_without_fresh_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    results_file = tmp_path / "BHresults.json"
    results_file.write_text('{"BlindRange": "stale", "MaskMin": 1, "MaskMax": 2}')

    def reject_missing_output(
        cmd,
        description,
        expected_outputs=(),
    ):
        assert not results_file.exists()
        assert expected_outputs == [str(results_file)]
        return False

    monkeypatch.setattr(
        module,
        "execute_required",
        reject_missing_output,
    )

    with pytest.raises(
        RuntimeError,
        match="BumpHunter masking-window calculation failed",
    ):
        module.run_bumphunter(
            "fresh-postfit.root",
            str(tmp_path),
        )

    assert not results_file.exists()


def test_run_bumphunter_rejects_invalid_fresh_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    results_file = tmp_path / "BHresults.json"

    def create_invalid_results(
        cmd,
        description,
        expected_outputs=(),
    ):
        results_file.write_text('{"BlindRange": "500,600"}')
        return True

    monkeypatch.setattr(
        module,
        "execute_required",
        create_invalid_results,
    )

    with pytest.raises(
        ValueError,
        match="missing required keys",
    ):
        module.run_bumphunter(
            "fresh-postfit.root",
            str(tmp_path),
        )


def _example_analysis_provenance() -> dict[str, object]:
    return {
        "repository_commit": "a" * 40,
        "runtime": {
            "python_version": "3.9.12",
            "python_executable": "/cvmfs/example/bin/python",
            "root_version": "6.26/08",
        },
        "tool_revisions": {
            "xmlAnaWSBuilder": "b" * 40,
            "quickFit": "c" * 40,
            "workspaceCombiner": "d" * 40,
            "pyBumpHunter": "e" * 40,
        },
        "input": {
            "path": "Input/data.root",
            "sha256": "f" * 64,
        },
        "configurations": {
            "topfile": {
                "path": "config/top.template",
                "sha256": "1" * 64,
            },
            "categoryfile": {
                "path": "config/category.template",
                "sha256": "2" * 64,
            },
            "backgroundfile": {
                "path": "config/background.template",
                "sha256": "3" * 64,
            },
            "signalfile": {
                "path": "config/signal.template",
                "sha256": "4" * 64,
            },
        },
        "invocation": {
            "datahist": "directory/histogram",
            "range_low": 481,
            "range_high": 3000,
            "signal_enabled": False,
            "limit_enabled": False,
            "prefit_enabled": True,
            "mask_threshold": 0.01,
        },
    }


def test_write_analysis_results_writes_success_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    results_path = module.write_analysis_results(
        folder=str(tmp_path),
        p_chi2=0.018478115147448883,
        masked=False,
        provenance=_example_analysis_provenance(),
    )

    assert Path(results_path) == tmp_path / "analysis_results.json"
    assert json.loads(Path(results_path).read_text()) == {
        "schema_version": 2,
        "status": "success",
        "masked": False,
        "p_chi2": pytest.approx(0.018478115147448883),
        "provenance": _example_analysis_provenance(),
    }
    assert not (tmp_path / "analysis_results.json.tmp").exists()


def test_write_analysis_results_records_masked_fit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    results_path = module.write_analysis_results(
        folder=str(tmp_path),
        p_chi2=0.0125,
        masked=True,
        provenance=_example_analysis_provenance(),
    )

    payload = json.loads(Path(results_path).read_text())

    assert payload["schema_version"] == 2
    assert payload["status"] == "success"
    assert payload["masked"] is True
    assert payload["p_chi2"] == pytest.approx(0.0125)


def test_write_analysis_results_atomically_replaces_existing_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    results_path = tmp_path / "analysis_results.json"
    results_path.write_text(
        '{"schema_version": 1, "status": "success", ' '"masked": false, "p_chi2": 999.0}\n'
    )

    module.write_analysis_results(
        folder=str(tmp_path),
        p_chi2=0.07891295444241458,
        masked=False,
        provenance=_example_analysis_provenance(),
    )

    payload = json.loads(results_path.read_text())

    assert payload["schema_version"] == 2
    assert payload["p_chi2"] == pytest.approx(0.07891295444241458)
    assert payload["provenance"] == _example_analysis_provenance()
    assert not (tmp_path / "analysis_results.json.tmp").exists()


@pytest.mark.parametrize(
    ("launcher_name", "region"),
    [
        ("run_anaFit_J100.sh", "J100"),
        ("run_anaFit_J50.sh", "J50"),
    ],
)
def test_launcher_can_skip_plots_after_successful_analysis(
    tmp_path: Path,
    launcher_name: str,
    region: str,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    setup_script = tmp_path / "fake-setup.sh"
    analysis_runner = tmp_path / "fake-analysis-runner.sh"
    output_dir = tmp_path / "outputs"
    runner_marker = tmp_path / "runner-called.txt"

    setup_script.write_text("#!/bin/bash\n")
    setup_script.chmod(0o755)

    analysis_runner.write_text(
        "#!/bin/bash\n" f'printf "%s\\n" "$*" > "{runner_marker}"\n' "exit 0\n"
    )
    analysis_runner.chmod(0o755)

    environment = os.environ.copy()
    environment.update(
        {
            "ANAFIT_OUTPUT_DIR": str(output_dir),
            "ANAFIT_SETUP_SCRIPT": str(setup_script),
            "ANAFIT_RUNNER": str(analysis_runner),
            "ANAFIT_SKIP_PLOTS": "1",
            "FIT_PARS": "six",
        }
    )

    completed = subprocess.run(
        ["bash", str(repo_root / "scripts" / launcher_name)],
        cwd=repo_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, (
        f"{launcher_name} failed while plots were disabled:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert runner_marker.is_file()

    runner_arguments = runner_marker.read_text()
    expected_folder = output_dir / region
    assert f"--folder {expected_folder}" in runner_arguments

    assert not list(output_dir.rglob("*.pdf"))
    assert "plot_postfit.cpp" not in completed.stdout
    assert "plot_postfit.cpp" not in completed.stderr


def test_calculate_file_sha256_returns_expected_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    input_file = tmp_path / "input.dat"
    input_file.write_bytes(b"FrequentistFramework provenance\n")

    assert module.calculate_file_sha256(input_file) == (
        "5996c8b6424bb4631b41e58ce078f0f53315db4a55ab4e8bf6f43950393d215c"
    )


def test_calculate_file_sha256_rejects_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    missing_file = tmp_path / "missing.dat"

    with pytest.raises(FileNotFoundError):
        module.calculate_file_sha256(missing_file)


def _create_test_git_repository(repository: Path) -> str:
    repository.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repository,
        check=True,
    )

    tracked_file = repository / "tracked.txt"
    tracked_file.write_text("committed content\n", encoding="utf-8")

    subprocess.run(
        ["git", "add", "tracked.txt"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Create test repository"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    )

    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def test_get_git_revision_returns_clean_repository_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    repository = tmp_path / "repository"
    expected_revision = _create_test_git_repository(repository)

    assert module.get_git_revision(repository) == expected_revision


@pytest.mark.parametrize("staged", [False, True])
def test_get_git_revision_rejects_tracked_modifications(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    staged: bool,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    repository = tmp_path / "repository"
    _create_test_git_repository(repository)

    (repository / "tracked.txt").write_text(
        "modified content\n",
        encoding="utf-8",
    )

    if staged:
        subprocess.run(
            ["git", "add", "tracked.txt"],
            cwd=repository,
            check=True,
        )

    with pytest.raises(
        RuntimeError,
        match="repository with tracked modifications",
    ):
        module.get_git_revision(repository)


def test_get_git_revision_ignores_untracked_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    repository = tmp_path / "repository"
    expected_revision = _create_test_git_repository(repository)

    (repository / "untracked-build-output.txt").write_text(
        "generated output\n",
        encoding="utf-8",
    )

    assert module.get_git_revision(repository) == expected_revision


def test_get_git_revision_rejects_non_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    with pytest.raises(
        RuntimeError,
        match="Could not determine Git revision",
    ):
        module.get_git_revision(tmp_path)


def test_collect_scientific_runtime_records_python_and_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    class FakeRootRuntime:
        @staticmethod
        def GetVersion() -> str:
            return "6.26/08"

    monkeypatch.setattr(
        module.ROOT,
        "gROOT",
        FakeRootRuntime(),
        raising=False,
    )
    monkeypatch.setattr(
        module.platform,
        "python_version",
        lambda: "3.9.12",
    )
    monkeypatch.setattr(
        module.sys,
        "executable",
        "/cvmfs/example/bin/python",
    )

    assert module.collect_scientific_runtime() == {
        "python_version": "3.9.12",
        "python_executable": "/cvmfs/example/bin/python",
        "root_version": "6.26/08",
    }


def test_collect_scientific_runtime_rejects_missing_root_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    class FakeRootRuntime:
        @staticmethod
        def GetVersion() -> str:
            return ""

    monkeypatch.setattr(
        module.ROOT,
        "gROOT",
        FakeRootRuntime(),
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="Could not determine the active ROOT version",
    ):
        module.collect_scientific_runtime()


def test_get_repository_root_returns_workspace_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    expected_root = Path(__file__).resolve().parents[1]

    assert module.get_repository_root() == expected_root


def test_get_repository_root_rejects_missing_git_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    fake_module_path = tmp_path / "python" / "run_anaFit.py"
    fake_module_path.parent.mkdir()
    fake_module_path.write_text("# fake module location\n")

    monkeypatch.setattr(module, "__file__", str(fake_module_path))

    with pytest.raises(
        RuntimeError,
        match="Could not locate the FrequentistFramework repository root",
    ):
        module.get_repository_root()


def test_resolve_analysis_path_resolves_repository_relative_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    input_file = tmp_path / "Input" / "data.root"
    input_file.parent.mkdir()
    input_file.write_bytes(b"ROOT fixture")

    resolved = module.resolve_analysis_path(
        "Input/data.root",
        repository_root=tmp_path,
    )

    assert resolved == input_file.resolve()


def test_resolve_analysis_path_preserves_absolute_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    input_file = tmp_path / "absolute-input.root"
    input_file.write_bytes(b"ROOT fixture")

    resolved = module.resolve_analysis_path(input_file)

    assert resolved == input_file.resolve()


def test_resolve_analysis_path_rejects_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    with pytest.raises(
        FileNotFoundError,
        match="Required analysis file does not exist",
    ):
        module.resolve_analysis_path(
            "Input/missing.root",
            repository_root=tmp_path,
        )


def test_build_file_provenance_records_relative_path_and_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    input_file = tmp_path / "Input" / "data.root"
    input_file.parent.mkdir()
    input_file.write_bytes(b"canonical input")

    provenance = module.build_file_provenance(
        "Input/data.root",
        repository_root=tmp_path,
    )

    assert provenance == {
        "path": "Input/data.root",
        "sha256": module.calculate_file_sha256(input_file),
    }


def test_build_file_provenance_records_external_absolute_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    external_file = tmp_path / "external" / "data.root"
    external_file.parent.mkdir()
    external_file.write_bytes(b"external input")

    provenance = module.build_file_provenance(
        external_file,
        repository_root=repository_root,
    )

    assert provenance == {
        "path": str(external_file.resolve()),
        "sha256": module.calculate_file_sha256(external_file),
    }


def test_build_file_provenance_rejects_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    with pytest.raises(
        FileNotFoundError,
        match="Required analysis file does not exist",
    ):
        module.build_file_provenance(
            "Input/missing.root",
            repository_root=tmp_path,
        )


def test_build_analysis_provenance_records_runtime_inputs_tools_and_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)
    repository_root = Path("/repository")

    monkeypatch.setattr(
        module,
        "get_repository_root",
        lambda: repository_root,
    )

    revisions = {
        repository_root: "a" * 40,
        repository_root / "xmlAnaWSBuilder": "b" * 40,
        repository_root / "quickFit": "c" * 40,
        repository_root / "workspaceCombiner": "d" * 40,
        repository_root / "pyBumpHunter": "e" * 40,
    }

    monkeypatch.setattr(
        module,
        "get_git_revision",
        lambda path: revisions[Path(path)],
    )
    monkeypatch.setattr(
        module,
        "collect_scientific_runtime",
        lambda: {
            "python_version": "3.9.12",
            "python_executable": "/cvmfs/example/bin/python",
            "root_version": "6.26/08",
        },
    )
    monkeypatch.setattr(
        module,
        "build_file_provenance",
        lambda path, repository_root=None: {
            "path": str(path),
            "sha256": "f" * 64,
        },
    )

    provenance = module.build_analysis_provenance(
        datafile="Input/data.root",
        datahist="directory/histogram",
        topfile="config/top.template",
        categoryfile="config/category.template",
        backgroundfile="config/background.template",
        signalfile="config/signal.template",
        rangelow=481,
        rangehigh=3000,
        dosignal=False,
        dolimit=False,
        doprefit=True,
        maskthreshold=0.01,
    )

    assert provenance == {
        "repository_commit": "a" * 40,
        "runtime": {
            "python_version": "3.9.12",
            "python_executable": "/cvmfs/example/bin/python",
            "root_version": "6.26/08",
        },
        "tool_revisions": {
            "xmlAnaWSBuilder": "b" * 40,
            "quickFit": "c" * 40,
            "workspaceCombiner": "d" * 40,
            "pyBumpHunter": "e" * 40,
        },
        "input": {
            "path": "Input/data.root",
            "sha256": "f" * 64,
        },
        "configurations": {
            "topfile": {
                "path": "config/top.template",
                "sha256": "f" * 64,
            },
            "categoryfile": {
                "path": "config/category.template",
                "sha256": "f" * 64,
            },
            "backgroundfile": {
                "path": "config/background.template",
                "sha256": "f" * 64,
            },
            "signalfile": {
                "path": "config/signal.template",
                "sha256": "f" * 64,
            },
        },
        "invocation": {
            "datahist": "directory/histogram",
            "range_low": 481,
            "range_high": 3000,
            "signal_enabled": False,
            "limit_enabled": False,
            "prefit_enabled": True,
            "mask_threshold": 0.01,
        },
    }


def test_run_anafit_writes_provenance_for_successful_unmasked_fit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    backgroundfile = tmp_path / "background.template"
    signalfile = tmp_path / "signal.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text(
        "CATEGORYFILE OUTPUTFILE SIGNAME\n",
        encoding="utf-8",
    )
    categoryfile.write_text(
        "BACKGROUNDFILE DATAFILE DATAHIST RANGELOW RANGEHIGH "
        "BINS NBKG NSIG SIGNAME SIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text(
        "background template\n",
        encoding="utf-8",
    )
    signalfile.write_text(
        "SIGNAME SIGMEAN SIGWIDTH\n",
        encoding="utf-8",
    )

    # Prevent the test from trying to create the real DTD symlink.
    (output_folder / "AnaWSBuilder.dtd").write_text(
        "test DTD\n",
        encoding="utf-8",
    )

    postfitfile = output_folder / "PostFit.root"
    parameterfile = output_folder / "FitParameters.root"
    expected_provenance = {
        "repository_commit": "a" * 40,
        "runtime": {
            "python_version": "3.9.12",
            "python_executable": "/cvmfs/example/bin/python",
            "root_version": "6.26/08",
        },
    }
    captured: dict[str, object] = {}

    def fake_build_fit_extract(**kwargs):
        captured["fit_arguments"] = kwargs
        return 0.25, str(postfitfile), str(parameterfile)

    def fake_build_analysis_provenance(**kwargs):
        captured["provenance_arguments"] = kwargs
        return expected_provenance

    def fake_write_analysis_results(**kwargs):
        captured["writer_arguments"] = kwargs
        return str(output_folder / "analysis_results.json")

    monkeypatch.setattr(
        module,
        "build_fit_extract",
        fake_build_fit_extract,
    )
    monkeypatch.setattr(
        module,
        "build_analysis_provenance",
        fake_build_analysis_provenance,
    )
    monkeypatch.setattr(
        module,
        "write_analysis_results",
        fake_write_analysis_results,
    )

    result = module.run_anaFit(
        datafile=str(datafile),
        datahist="directory/histogram",
        topfile=str(topfile),
        categoryfile=str(categoryfile),
        wsfile=str(output_folder / "workspace.root"),
        outputfile=str(output_folder / "FitResult.root"),
        nbkg="1.0E+03, 0, 2.0E+03",
        nsig="0, -1.0E+03, 1.0E+03",
        rangelow=481,
        rangehigh=3000,
        signame="test_signal",
        backgroundfile=str(backgroundfile),
        signalfile=str(signalfile),
        dosignal=False,
        dolimit=False,
        maskthreshold=0.01,
        doprefit=False,
        folder=str(output_folder),
    )

    assert result == 0

    assert captured["provenance_arguments"] == {
        "datafile": str(datafile),
        "datahist": "directory/histogram",
        "topfile": str(topfile),
        "categoryfile": str(categoryfile),
        "backgroundfile": str(backgroundfile),
        "signalfile": str(signalfile),
        "rangelow": 481,
        "rangehigh": 3000,
        "dosignal": False,
        "dolimit": False,
        "doprefit": False,
        "maskthreshold": 0.01,
    }

    assert captured["writer_arguments"] == {
        "folder": str(output_folder),
        "p_chi2": 0.25,
        "masked": False,
        "provenance": expected_provenance,
    }


def test_run_anafit_quicklimit_failure_prevents_success_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    backgroundfile = tmp_path / "background.template"
    signalfile = tmp_path / "signal.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text(
        "CATEGORYFILE OUTPUTFILE SIGNAME\n",
        encoding="utf-8",
    )
    categoryfile.write_text(
        "BACKGROUNDFILE DATAFILE DATAHIST RANGELOW RANGEHIGH "
        "BINS NBKG NSIG SIGNAME SIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text(
        "background template\n",
        encoding="utf-8",
    )
    signalfile.write_text(
        "SIGNAME SIGMEAN SIGWIDTH\n",
        encoding="utf-8",
    )
    (output_folder / "AnaWSBuilder.dtd").write_text(
        "test DTD\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "build_fit_extract",
        lambda **kwargs: (
            0.25,
            str(output_folder / "PostFit.root"),
            str(output_folder / "FitParameters.root"),
        ),
    )

    commands: list[str] = []

    def fail_quicklimit(command):
        commands.append(command)
        assert command.startswith("quickLimit ")
        return 9

    monkeypatch.setattr(module, "execute", fail_quicklimit)

    def reject_provenance(**kwargs):
        raise AssertionError("Provenance must not be generated after quickLimit failure")

    def reject_manifest(**kwargs):
        raise AssertionError("Success manifest must not be written after quickLimit failure")

    monkeypatch.setattr(
        module,
        "build_analysis_provenance",
        reject_provenance,
    )
    monkeypatch.setattr(
        module,
        "write_analysis_results",
        reject_manifest,
    )

    result = module.run_anaFit(
        datafile=str(datafile),
        datahist="directory/histogram",
        topfile=str(topfile),
        categoryfile=str(categoryfile),
        wsfile=str(output_folder / "workspace.root"),
        outputfile=str(output_folder / "FitResult.root"),
        nbkg="1.0E+03, 0, 2.0E+03",
        nsig="0, -1.0E+03, 1.0E+03",
        rangelow=481,
        rangehigh=3000,
        signame="test_signal",
        backgroundfile=str(backgroundfile),
        signalfile=str(signalfile),
        dosignal=True,
        dolimit=True,
        maskthreshold=0.01,
        doprefit=False,
        folder=str(output_folder),
    )

    assert result == -1
    assert len(commands) == 1
    assert not (output_folder / "analysis_results.json").exists()


@pytest.mark.parametrize("analysis_status", [0, -1, 23])
def test_injection_runner_propagates_analysis_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    analysis_status: int,
) -> None:
    inject_module = ModuleType("InjectGaussian")
    inject_module.InjectGaussian = object

    analysis_module = ModuleType("run_anaFit")
    captured: dict[str, object] = {}

    def fake_run_anafit(**kwargs):
        captured.update(kwargs)
        return analysis_status

    analysis_module.run_anaFit = fake_run_anafit

    monkeypatch.setitem(sys.modules, "InjectGaussian", inject_module)
    monkeypatch.setitem(sys.modules, "run_anaFit", analysis_module)

    module_path = Path(__file__).resolve().parents[1] / "python" / "run_injections_anaFit.py"
    spec = importlib.util.spec_from_file_location(
        "run_injections_anaFit_under_test",
        module_path,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.main(
        [
            "--datafile",
            "input.root",
            "--datahist",
            "directory/histogram",
            "--topfile",
            "top.xml",
            "--categoryfile",
            "category.xml",
            "--wsfile",
            "workspace.root",
            "--outputfile",
            "fit-result.root",
            "--nbkg",
            "1000,0,2000",
            "--rangelow",
            "481",
            "--rangehigh",
            "3000",
            "--folder",
            str(tmp_path / "output"),
        ]
    )

    assert result == analysis_status
    assert captured["datafile"] == "input.root"
    assert captured["datahist"] == "directory/histogram"
