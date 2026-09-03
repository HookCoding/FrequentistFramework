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
    commands: list[str] = []

    def execute_required_with_quickfit_failure(
        cmd,
        description,
        expected_outputs=(),
    ):
        calls.append(description)
        commands.append(cmd)
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

    quickfit_command = commands[1]
    assert " > quickFitLog.log 2>&1" in quickfit_command
    assert chr(38) + chr(62) not in quickfit_command


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


def test_replaceinfile_applies_ordered_regex_substitutions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # replaceinfile() has no direct test today - only indirect coverage
    # through the full integration gate. Chaining PLACEHOLDER_A ->
    # PLACEHOLDER_B -> final_value (rather than two independent
    # substitutions) proves substitutions apply in order against the
    # already-modified text, not all at once against the original.
    module = _load_run_anafit_module(monkeypatch)
    target_file = tmp_path / "template.xml"
    target_file.write_text("PLACEHOLDER_A\n", encoding="utf-8")

    module.replaceinfile(
        str(target_file),
        [("PLACEHOLDER_A", "PLACEHOLDER_B"), ("PLACEHOLDER_B", "final_value")],
    )

    assert target_file.read_text(encoding="utf-8") == "final_value\n"


def test_run_anafit_stages_templates_for_a_representative_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No existing test asserts on the *content* of the generated template
    # files - test_run_anafit_writes_provenance_for_successful_unmasked_fit
    # only inspects what gets passed to the (mocked-away) fit/provenance
    # functions. This is the first direct characterization of the
    # templating block itself, for a doprefit=False, signalfile=None case.
    module = _load_run_anafit_module(monkeypatch)

    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    backgroundfile = tmp_path / "background.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text("CATEGORYFILE\nOUTPUTFILE\nSIGNAME\n", encoding="utf-8")
    categoryfile.write_text(
        "BACKGROUNDFILE\nDATAFILE\nDATAHIST\nRANGELOW\nRANGEHIGH\n"
        "BINS\nNBKG\nNSIG\nSIGNAME\nSIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text("background template\n", encoding="utf-8")
    (output_folder / "AnaWSBuilder.dtd").write_text("test DTD\n", encoding="utf-8")

    wsfile = output_folder / "workspace.root"

    monkeypatch.setattr(
        module,
        "build_fit_extract",
        lambda **kwargs: (
            0.25,
            str(output_folder / "PostFit.root"),
            str(output_folder / "FitParameters.root"),
        ),
    )
    monkeypatch.setattr(module, "build_analysis_provenance", lambda **kwargs: {})
    monkeypatch.setattr(
        module,
        "write_analysis_results",
        lambda **kwargs: str(output_folder / "analysis_results.json"),
    )

    result = module.run_anaFit(
        datafile=str(datafile),
        datahist="directory/histogram",
        topfile=str(topfile),
        categoryfile=str(categoryfile),
        wsfile=str(wsfile),
        outputfile=str(output_folder / "FitResult.root"),
        nbkg="1.0E+03, 0, 2.0E+03",
        nsig="0, -1.0E+03, 1.0E+03",
        rangelow=481,
        rangehigh=3000,
        signame="test_signal",
        backgroundfile=str(backgroundfile),
        signalfile=None,
        dosignal=False,
        dolimit=False,
        maskthreshold=0.01,
        doprefit=False,
        folder=str(output_folder),
    )

    assert result == 0

    tmptopfile = output_folder / "dijetTLA_fromTemplate.xml"
    tmpcategoryfile = output_folder / "category_dijetTLA_fromTemplate.xml"
    tmpbackgroundfile = output_folder / "background_dijetTLA_fromTemplate.xml"
    # Computed unconditionally in production regardless of whether
    # signalfile was actually provided - see the categoryfile assertion
    # below, which expects this same value for the SIGNALFILE placeholder.
    tmpsignalfile = output_folder / "signal_dijetTLA_fromTemplate.xml"

    xml_categoryfile = os.path.relpath(str(tmpcategoryfile), os.getcwd())
    xml_wsfile = os.path.relpath(str(wsfile), os.getcwd())
    xml_backgroundfile = os.path.relpath(str(tmpbackgroundfile), os.getcwd())
    xml_signalfile = os.path.relpath(str(tmpsignalfile), os.getcwd())

    assert tmptopfile.read_text(encoding="utf-8") == (
        f"{xml_categoryfile}\n{xml_wsfile}\ntest_signal\n"
    )
    assert tmpcategoryfile.read_text(encoding="utf-8") == (
        f"{xml_backgroundfile}\n{datafile}\ndirectory/histogram\n481\n3000\n"
        f"2519\n1.0E+03, 0, 2.0E+03\n0, -1.0E+03, 1.0E+03\ntest_signal\n{xml_signalfile}\n"
    )
    # backgroundfile itself is copied through unmodified (no doprefit, so
    # no PAR substitution) - only referenced by the categoryfile above.
    assert tmpbackgroundfile.read_text(encoding="utf-8") == "background template\n"


def test_run_anafit_prefit_seeds_background_file_from_fitted_parameters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_run_anafit_module(monkeypatch)

    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    # "sixPar" matches only the "six" branch of the elif chain -> nPars=6,
    # avoiding the "three"/"four" double-match quirk exercised separately
    # below.
    backgroundfile = tmp_path / "background_sixPar.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text("CATEGORYFILE\nOUTPUTFILE\nSIGNAME\n", encoding="utf-8")
    categoryfile.write_text(
        "BACKGROUNDFILE\nDATAFILE\nDATAHIST\nRANGELOW\nRANGEHIGH\n"
        "BINS\nNBKG\nNSIG\nSIGNAME\nSIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text(
        '<!-- <ModelItem name="commented_out" [PAR1,-99,99] /> -->\n'
        '<ModelItem name="par1" value="[PAR1,-5,5]" />\n'
        '<ModelItem name="par2" value="[PAR2,-6.5,6.5]" />\n',
        encoding="utf-8",
    )
    (output_folder / "AnaWSBuilder.dtd").write_text("test DTD\n", encoding="utf-8")

    captured_prefitter_kwargs: dict[str, object] = {}

    class FakePreFitter:
        def __init__(self, **kwargs):
            captured_prefitter_kwargs.update(kwargs)

        def Fit(self):
            return [11.0, 22.0, 33.0, 44.0, 55.0, 66.0], 12345.0

    monkeypatch.setattr(module, "PreFitter", FakePreFitter)
    monkeypatch.setattr(
        module,
        "build_fit_extract",
        lambda **kwargs: (
            0.25,
            str(output_folder / "PostFit.root"),
            str(output_folder / "FitParameters.root"),
        ),
    )
    monkeypatch.setattr(module, "build_analysis_provenance", lambda **kwargs: {})
    monkeypatch.setattr(
        module,
        "write_analysis_results",
        lambda **kwargs: str(output_folder / "analysis_results.json"),
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
        signalfile=None,
        dosignal=False,
        dolimit=False,
        maskthreshold=0.01,
        doprefit=True,
        folder=str(output_folder),
    )

    assert result == 0

    # nPars=6 -> default range [1, -30, -30, -30, -30, -30]/[1, 30, 30, 30, 30, 30],
    # with PAR1 and PAR2's ranges (both index 0 and 1) overridden by the
    # parsed background file's two (uncommented) ModelItem lines - the
    # commented-out PAR1 line above is skipped by the "<!--" guard.
    assert captured_prefitter_kwargs["nPars"] == 6
    assert captured_prefitter_kwargs["parRangeLow"] == [-5.0, -6.5, -30, -30, -30, -30]
    assert captured_prefitter_kwargs["parRangeHigh"] == [5.0, 6.5, 30, 30, 30, 30]
    assert captured_prefitter_kwargs["nRetries1"] == 2000 * 6
    assert captured_prefitter_kwargs["nRetries2"] == 2 * 6
    assert captured_prefitter_kwargs["datafile"] == str(datafile)
    assert captured_prefitter_kwargs["xMin"] == 481
    assert captured_prefitter_kwargs["xMax"] == 3000

    # Real, verified quirk: the substitution loop does a plain
    # replaceinfile(tmpbackgroundfile, [("PAR1", "11.0")]) per parameter -
    # a naive substring/regex swap of the literal text "PARn", not a
    # replacement of the whole "[PARn,lo,hi]" range annotation. The
    # annotation brackets survive in the output with just the "PARn"
    # token inside them replaced (including inside the commented-out
    # line, since replaceinfile operates over the whole file text, blind
    # to comments). This is existing behavior, not something Step B may
    # "clean up" while moving this code.
    tmpbackgroundfile = output_folder / "background_dijetTLA_fromTemplate.xml"
    assert tmpbackgroundfile.read_text(encoding="utf-8") == (
        '<!-- <ModelItem name="commented_out" [11.0,-99,99] /> -->\n'
        '<ModelItem name="par1" value="[11.0,-5,5]" />\n'
        '<ModelItem name="par2" value="[22.0,-6.5,6.5]" />\n'
    )

    # PreFitter's fitted nbkg is folded into the NBKG placeholder as
    # "<value>, 0, <2x value>" - confirmed via the categoryfile it feeds.
    tmpcategoryfile = output_folder / "category_dijetTLA_fromTemplate.xml"
    assert "1.2E+04, 0, 2.5E+04" in tmpcategoryfile.read_text(encoding="utf-8")


def test_run_anafit_prefit_npars_detection_matching_both_three_and_four_resolves_to_four(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Regression test for a real, verified quirk: nPars detection is a
    # standalone "if 'three' in backgroundfile: nPars = 3" followed by a
    # *separate* elif chain covering "four" through "ten" - not one
    # unified if/elif ladder. A background-file path matching both
    # "three" and "four" currently resolves to nPars=4, not 3, because
    # the "four" elif branch (part of the second, independent if/elif
    # chain) runs after the standalone "three" check unconditionally
    # sets nPars=3, and overwrites it. This must survive Step B's move
    # unchanged - Step B must copy this structure exactly, not unify it.
    module = _load_run_anafit_module(monkeypatch)

    datafile = tmp_path / "input.root"
    topfile = tmp_path / "top.template"
    categoryfile = tmp_path / "category.template"
    backgroundfile = tmp_path / "background_threefour.template"
    output_folder = tmp_path / "output"

    output_folder.mkdir()
    datafile.write_bytes(b"test ROOT input")
    topfile.write_text("CATEGORYFILE\nOUTPUTFILE\nSIGNAME\n", encoding="utf-8")
    categoryfile.write_text(
        "BACKGROUNDFILE\nDATAFILE\nDATAHIST\nRANGELOW\nRANGEHIGH\n"
        "BINS\nNBKG\nNSIG\nSIGNAME\nSIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text("background template\n", encoding="utf-8")
    (output_folder / "AnaWSBuilder.dtd").write_text("test DTD\n", encoding="utf-8")

    captured_prefitter_kwargs: dict[str, object] = {}

    class FakePreFitter:
        def __init__(self, **kwargs):
            captured_prefitter_kwargs.update(kwargs)

        def Fit(self):
            return [0.0] * captured_prefitter_kwargs["nPars"], 1.0

    monkeypatch.setattr(module, "PreFitter", FakePreFitter)
    monkeypatch.setattr(
        module,
        "build_fit_extract",
        lambda **kwargs: (
            0.25,
            str(output_folder / "PostFit.root"),
            str(output_folder / "FitParameters.root"),
        ),
    )
    monkeypatch.setattr(module, "build_analysis_provenance", lambda **kwargs: {})
    monkeypatch.setattr(
        module,
        "write_analysis_results",
        lambda **kwargs: str(output_folder / "analysis_results.json"),
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
        signalfile=None,
        dosignal=False,
        dolimit=False,
        maskthreshold=0.01,
        doprefit=True,
        folder=str(output_folder),
    )

    assert result == 0
    assert captured_prefitter_kwargs["nPars"] == 4


def test_run_anafit_stages_signal_template_with_systematic_placeholders(
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
    topfile.write_text("CATEGORYFILE\nOUTPUTFILE\nSIGNAME\n", encoding="utf-8")
    categoryfile.write_text(
        "BACKGROUNDFILE\nDATAFILE\nDATAHIST\nRANGELOW\nRANGEHIGH\n"
        "BINS\nNBKG\nNSIG\nSIGNAME\nSIGNALFILE\n",
        encoding="utf-8",
    )
    backgroundfile.write_text("background template\n", encoding="utf-8")
    signalfile.write_text(
        "SIGNAME\nSIGMEAN\nSIGWIDTH\nNOMINAL_MEAN\nNOMINAL_WIDTH\n"
        "NOMINAL_ALPHAL\nNOMINAL_ALPHAH\nNOMINAL_NL\nNOMINAL_NH\n"
        "[MAG_SCALE_JES]\n[MAG_RESOLUTION_JER]\n[MAG_SCALE_UNLISTED]\n",
        encoding="utf-8",
    )
    (output_folder / "AnaWSBuilder.dtd").write_text("test DTD\n", encoding="utf-8")

    systdict = {
        "nominal_mean": 1234.5,
        "nominal_sigma": 12.3,
        "nominal_alpha_l": 1.1,
        "nominal_alpha_h": 1.2,
        "nominal_n_l": 5,
        "nominal_n_h": 6,
        "unc_mean_sources": {"JES": 0.02},
        "unc_sigma_sources": {"JER": 0.03},
    }

    monkeypatch.setattr(
        module,
        "build_fit_extract",
        lambda **kwargs: (
            0.25,
            str(output_folder / "PostFit.root"),
            str(output_folder / "FitParameters.root"),
        ),
    )
    monkeypatch.setattr(module, "build_analysis_provenance", lambda **kwargs: {})
    monkeypatch.setattr(
        module,
        "write_analysis_results",
        lambda **kwargs: str(output_folder / "analysis_results.json"),
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
        systdict=systdict,
    )

    assert result == 0

    tmpsignalfile = output_folder / "signal_dijetTLA_fromTemplate.xml"
    seeded_content = tmpsignalfile.read_text(encoding="utf-8")

    assert seeded_content == (
        "test_signal\n1000\n7.0\n1234.5\n12.3\n1.1\n1.2\n5\n6\n" "[0.02]\n[0.03]\n[0]\n"
    )


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
