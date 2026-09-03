from __future__ import annotations

import importlib.util
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

    # run_anaFit.py imports its extracted sibling modules with flat,
    # same-directory-style imports (e.g. "from run_execution import
    # execute"), matching how Python resolves them in production when the
    # script is invoked directly (its own directory is auto-prepended to
    # sys.path). Loading the file via importlib does not get that for
    # free, so it must be added explicitly here, mirroring what the
    # interpreter already does automatically outside of tests.
    monkeypatch.syspath_prepend(str(module_path.parent))

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


def _capture_run_anafit_kwargs(module, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_run_anaFit(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(module, "run_anaFit", fake_run_anaFit)
    return captured


def test_main_parses_representative_j100_style_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mirrors an actual invocation shape from scripts/run_anaFit_J100.sh:
    # backgroundfile/signalfile present, no --signame, no --dosignal/
    # --dolimit/--doprefit/--sysfile (all left at their defaults).
    #
    # This is now main()'s own wiring/smoke test (Tier 3 Chunk 7): argument
    # parsing itself is build_arg_parser()'s responsibility and
    # default-signame derivation is normalize_signal_name()'s, both unit-
    # tested directly in tests/test_run_cli.py. What's left to check here
    # is that main() still wires parser -> normalize_signal_name -> the
    # kwargs passed to run_anaFit() correctly, plus the one piece of CLI
    # logic that stays inline in main() itself: defaulting systdict to
    # None when --sysfile isn't given.
    module = _load_run_anafit_module(monkeypatch)
    captured = _capture_run_anafit_kwargs(module, monkeypatch)

    module.main(
        [
            "--datafile",
            "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
            "--datahist",
            "mjj_Data_2018",
            "--backgroundfile",
            "background.xml",
            "--signalfile",
            "signal.xml",
            "--categoryfile",
            "category.xml",
            "--topfile",
            "top.xml",
            "--wsfile",
            "workspace.root",
            "--sigmean",
            "1200",
            "--sigwidth",
            "8.5",
            "--nbkg",
            "2E8,0,3E8",
            "--rangelow",
            "481",
            "--rangehigh",
            "3000",
            "--outputfile",
            "FitResult.root",
            "--maskthreshold",
            "0.01",
            "--folder",
            str(tmp_path),
        ]
    )

    assert captured["datafile"] == "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root"
    assert captured["backgroundfile"] == "background.xml"
    assert captured["signalfile"] == "signal.xml"
    assert captured["rangelow"] == 481
    assert captured["rangehigh"] == 3000
    assert captured["dosignal"] is False
    assert captured["dolimit"] is False
    assert captured["doprefit"] is False
    assert captured["sigmean"] == 1200
    assert captured["sigwidth"] == 8.5
    assert captured["nsig"] == "0,-1E6,1E6"  # default, not passed explicitly
    assert captured["signame"] == "mean1200_width8.5"
    assert captured["maskthreshold"] == 0.01
    assert captured["systdict"] is None


def test_setup_build_and_fit_propagates_setup_lxplus_failure_and_restores_cwd(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    setup_script = repo_root / "scripts" / "setup_buildAndFit.sh"

    working_directory = tmp_path / "workdir"
    (working_directory / "xmlAnaWSBuilder").mkdir(parents=True)
    (working_directory / "quickFit").mkdir(parents=True)
    # setup_lxplus.sh is always sourced, never executed, so it must fail
    # via `return` (matching the real xmlAnaWSBuilder/quickFit checkouts'
    # own setup_lxplus.sh) -- `exit` here would terminate the entire
    # calling shell instead of just the source operation.
    (working_directory / "xmlAnaWSBuilder" / "setup_lxplus.sh").write_text(
        "#!/bin/bash\nreturn 1\n"
    )

    environment = os.environ.copy()
    environment.pop("ANAFIT_LCG_PLATFORM", None)
    environment.pop("_DIRXMLWSBUILDER", None)
    environment.pop("_DIRFIT", None)

    completed = subprocess.run(
        [
            "bash",
            "-c",
            f'cd "{working_directory}" && '
            f'source "{setup_script}"; '
            'echo "STATUS:$?"; '
            'echo "CWD:$(pwd)"',
        ],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert "STATUS:1" in completed.stdout
    # The failure must not leave the shell inside xmlAnaWSBuilder/ --
    # cd back to the pre-source directory is required before returning.
    assert f"CWD:{working_directory}" in completed.stdout


def test_setup_build_and_fit_lcg_platform_branch_exposes_build_directories(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    setup_script = repo_root / "scripts" / "setup_buildAndFit.sh"

    working_directory = tmp_path / "workdir"
    (working_directory / "xmlAnaWSBuilder" / "build" / "bin").mkdir(parents=True)
    (working_directory / "xmlAnaWSBuilder" / "build" / "lib").mkdir(parents=True)
    (working_directory / "xmlAnaWSBuilder" / "lib").mkdir(parents=True)
    (working_directory / "quickFit" / "build").mkdir(parents=True)
    (working_directory / "quickFit" / "lib").mkdir(parents=True)

    # ATLAS_LOCAL_ROOT_BASE is hardcoded to a real CVMFS path in
    # production; overriding it here (now that the script honors an
    # existing value) lets this test exercise the real
    # ANAFIT_LCG_PLATFORM branch with a fake ATLAS/lsetup stub instead of
    # requiring genuine CVMFS/Ubuntu infrastructure.
    fake_atlas_root = tmp_path / "fake-atlas-root"
    (fake_atlas_root / "user").mkdir(parents=True)
    (fake_atlas_root / "user" / "atlasLocalSetup.sh").write_text(
        "#!/bin/bash\nlsetup() { return 0; }\n"
    )

    environment = os.environ.copy()
    environment.update(
        {
            "ANAFIT_LCG_PLATFORM": "x86_64-fake-platform",
            "ATLAS_LOCAL_ROOT_BASE": str(fake_atlas_root),
        }
    )
    for stale_variable in ("_DIRXMLWSBUILDER", "_DIRFIT", "_BIN_PATH", "_LIB_PATH"):
        environment.pop(stale_variable, None)

    completed = subprocess.run(
        [
            "bash",
            "-c",
            f'cd "{working_directory}" && '
            f'source "{setup_script}"; '
            'echo "STATUS:$?"; '
            'echo "PATH:$PATH"; '
            'echo "LD_LIBRARY_PATH:$LD_LIBRARY_PATH"',
        ],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert "STATUS:0" in completed.stdout, completed.stdout + completed.stderr

    path_line = next(line for line in completed.stdout.splitlines() if line.startswith("PATH:"))
    ld_library_path_line = next(
        line for line in completed.stdout.splitlines() if line.startswith("LD_LIBRARY_PATH:")
    )

    xml_build_bin = str(working_directory / "xmlAnaWSBuilder" / "build" / "bin")
    xml_build_lib = str(working_directory / "xmlAnaWSBuilder" / "build" / "lib")
    xml_lib = str(working_directory / "xmlAnaWSBuilder" / "lib")
    quickfit_build = str(working_directory / "quickFit" / "build")
    quickfit_lib = str(working_directory / "quickFit" / "lib")

    assert xml_build_bin in path_line
    assert quickfit_build in path_line
    # The pre-fix, nonexistent xmlAnaWSBuilder/bin path must not reappear,
    # even via a future accidental partial revert.
    assert str(working_directory / "xmlAnaWSBuilder" / "bin") not in path_line

    assert xml_build_lib in ld_library_path_line
    assert xml_lib in ld_library_path_line
    assert quickfit_build in ld_library_path_line
    assert quickfit_lib in ld_library_path_line


@pytest.mark.parametrize(
    ("launcher_name", "region"),
    [
        ("run_anaFit_J100.sh", "J100"),
        ("run_anaFit_J50.sh", "J50"),
    ],
)
def test_launcher_propagates_setup_failure_before_running_analysis(
    tmp_path: Path,
    launcher_name: str,
    region: str,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    setup_script = tmp_path / "fake-setup.sh"
    analysis_runner = tmp_path / "fake-analysis-runner.sh"
    output_dir = tmp_path / "outputs"
    runner_marker = tmp_path / "runner-called.txt"

    setup_script.write_text("#!/bin/bash\necho 'setup failed' >&2\nexit 7\n")
    setup_script.chmod(0o755)

    analysis_runner.write_text(f'#!/bin/bash\ntouch "{runner_marker}"\nexit 0\n')
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

    assert completed.returncode == 7
    assert not runner_marker.exists()
    assert not list(output_dir.rglob("postFit.pdf"))


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

    captured_provenance = {
        "repository_commit": "a" * 40,
        "runtime": {
            "python_version": "3.9.12",
            "python_executable": "/cvmfs/example/bin/python",
            "root_version": "6.26/08",
        },
    }

    monkeypatch.setattr(
        module,
        "build_analysis_provenance",
        lambda **kwargs: captured_provenance,
    )

    def reject_manifest(**kwargs):
        raise AssertionError("Success manifest must not be written after quickLimit failure")

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
