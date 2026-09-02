from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from python import run_provenance


def test_calculate_file_sha256_returns_expected_digest(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "input.dat"
    input_file.write_bytes(b"FrequentistFramework provenance\n")

    assert run_provenance.calculate_file_sha256(input_file) == (
        "5996c8b6424bb4631b41e58ce078f0f53315db4a55ab4e8bf6f43950393d215c"
    )


def test_calculate_file_sha256_rejects_missing_file(
    tmp_path: Path,
) -> None:
    missing_file = tmp_path / "missing.dat"

    with pytest.raises(FileNotFoundError):
        run_provenance.calculate_file_sha256(missing_file)


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
) -> None:
    repository = tmp_path / "repository"
    expected_revision = _create_test_git_repository(repository)

    revision, dirty = run_provenance.get_git_revision(repository)
    assert revision == expected_revision
    assert dirty is False


@pytest.mark.parametrize("staged", [False, True])
def test_get_git_revision_warns_for_tracked_modifications(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    staged: bool,
) -> None:
    repository = tmp_path / "repository"
    expected_revision = _create_test_git_repository(repository)

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

    revision, dirty = run_provenance.get_git_revision(repository)
    assert revision == expected_revision
    assert dirty is True

    captured = capsys.readouterr()
    assert "WARNING: Recording Git revision" in captured.out
    assert expected_revision in captured.out
    assert "repository with tracked modifications" in captured.out
    assert "tracked.txt" in captured.out


def test_get_git_revision_ignores_untracked_files(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    expected_revision = _create_test_git_repository(repository)

    (repository / "untracked-build-output.txt").write_text(
        "generated output\n",
        encoding="utf-8",
    )

    revision, dirty = run_provenance.get_git_revision(repository)
    assert revision == expected_revision
    assert dirty is False


def test_get_git_revision_rejects_non_repository(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RuntimeError,
        match="Could not determine Git revision",
    ):
        run_provenance.get_git_revision(tmp_path)


def test_collect_scientific_runtime_records_python_and_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # collect_scientific_runtime() imports ROOT locally (deferred - it is
    # the only function in this module that touches ROOT at all), so
    # there is no module-level run_provenance.ROOT attribute to patch.
    # Installing a fake module directly into sys.modules["ROOT"] is what
    # the function's own local "import ROOT" statement will find, since
    # Python's import machinery checks sys.modules before doing any real
    # import work.
    class FakeRootRuntime:
        @staticmethod
        def GetVersion() -> str:
            return "6.26/08"

    fake_root_module = ModuleType("ROOT")
    fake_root_module.gROOT = FakeRootRuntime()
    monkeypatch.setitem(sys.modules, "ROOT", fake_root_module)

    monkeypatch.setattr(
        run_provenance.platform,
        "python_version",
        lambda: "3.9.12",
    )
    monkeypatch.setattr(
        run_provenance.sys,
        "executable",
        "/cvmfs/example/bin/python",
    )

    assert run_provenance.collect_scientific_runtime() == {
        "python_version": "3.9.12",
        "python_executable": "/cvmfs/example/bin/python",
        "root_version": "6.26/08",
    }


def test_collect_scientific_runtime_rejects_missing_root_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRootRuntime:
        @staticmethod
        def GetVersion() -> str:
            return ""

    fake_root_module = ModuleType("ROOT")
    fake_root_module.gROOT = FakeRootRuntime()
    monkeypatch.setitem(sys.modules, "ROOT", fake_root_module)

    with pytest.raises(
        RuntimeError,
        match="Could not determine the active ROOT version",
    ):
        run_provenance.collect_scientific_runtime()


def test_get_repository_root_returns_workspace_root() -> None:
    expected_root = Path(__file__).resolve().parents[1]

    assert run_provenance.get_repository_root() == expected_root


def test_get_repository_root_rejects_missing_git_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # get_repository_root() delegates its base-path computation to
    # repo_utils.find_repo_root() (Chunk 3's one narrow reuse exception -
    # see run_provenance.py's own get_repository_root()). The original
    # version of this test faked a missing-.git directory by patching the
    # loaded module's __file__, which only worked because
    # get_repository_root() used to compute Path(__file__).resolve()
    # directly against its own module. That mechanism no longer reaches
    # anything once the base-path computation lives in a different
    # module's __file__ (repo_utils.py) - patching find_repo_root() as
    # looked up in run_provenance's own namespace is the direct,
    # necessary replacement.
    fake_workspace_root = tmp_path / "workspace-without-git"
    fake_workspace_root.mkdir()

    monkeypatch.setattr(
        run_provenance,
        "find_repo_root",
        lambda: fake_workspace_root,
    )

    with pytest.raises(
        RuntimeError,
        match="Could not locate the FrequentistFramework repository root",
    ):
        run_provenance.get_repository_root()


def test_resolve_analysis_path_resolves_repository_relative_file(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "Input" / "data.root"
    input_file.parent.mkdir()
    input_file.write_bytes(b"ROOT fixture")

    resolved = run_provenance.resolve_analysis_path(
        "Input/data.root",
        repository_root=tmp_path,
    )

    assert resolved == input_file.resolve()


def test_resolve_analysis_path_preserves_absolute_file(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "absolute-input.root"
    input_file.write_bytes(b"ROOT fixture")

    resolved = run_provenance.resolve_analysis_path(input_file)

    assert resolved == input_file.resolve()


def test_resolve_analysis_path_rejects_missing_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Required analysis file does not exist",
    ):
        run_provenance.resolve_analysis_path(
            "Input/missing.root",
            repository_root=tmp_path,
        )


def test_resolve_analysis_path_uses_get_repository_root_when_omitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_file = tmp_path / "Input" / "data.root"
    input_file.parent.mkdir()
    input_file.write_bytes(b"ROOT fixture")

    monkeypatch.setattr(run_provenance, "get_repository_root", lambda: tmp_path)

    resolved = run_provenance.resolve_analysis_path("Input/data.root")

    assert resolved == input_file.resolve()


def test_build_file_provenance_records_relative_path_and_hash(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "Input" / "data.root"
    input_file.parent.mkdir()
    input_file.write_bytes(b"canonical input")

    provenance = run_provenance.build_file_provenance(
        "Input/data.root",
        repository_root=tmp_path,
    )

    assert provenance == {
        "path": "Input/data.root",
        "sha256": run_provenance.calculate_file_sha256(input_file),
    }


def test_build_file_provenance_records_external_absolute_path(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    external_file = tmp_path / "external" / "data.root"
    external_file.parent.mkdir()
    external_file.write_bytes(b"external input")

    provenance = run_provenance.build_file_provenance(
        external_file,
        repository_root=repository_root,
    )

    assert provenance == {
        "path": str(external_file.resolve()),
        "sha256": run_provenance.calculate_file_sha256(external_file),
    }


def test_build_file_provenance_rejects_missing_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Required analysis file does not exist",
    ):
        run_provenance.build_file_provenance(
            "Input/missing.root",
            repository_root=tmp_path,
        )


def test_build_file_provenance_uses_get_repository_root_when_omitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_file = tmp_path / "Input" / "data.root"
    input_file.parent.mkdir()
    input_file.write_bytes(b"canonical input")

    monkeypatch.setattr(run_provenance, "get_repository_root", lambda: tmp_path)

    provenance = run_provenance.build_file_provenance("Input/data.root")

    assert provenance == {
        "path": "Input/data.root",
        "sha256": run_provenance.calculate_file_sha256(input_file),
    }


def test_build_analysis_provenance_records_runtime_inputs_tools_and_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = Path("/repository")

    monkeypatch.setattr(
        run_provenance,
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
        run_provenance,
        "get_git_revision",
        lambda path: (revisions[Path(path)], False),
    )
    monkeypatch.setattr(
        run_provenance,
        "collect_scientific_runtime",
        lambda: {
            "python_version": "3.9.12",
            "python_executable": "/cvmfs/example/bin/python",
            "root_version": "6.26/08",
        },
    )
    monkeypatch.setattr(
        run_provenance,
        "build_file_provenance",
        lambda path, repository_root=None: {
            "path": str(path),
            "sha256": "f" * 64,
        },
    )

    provenance = run_provenance.build_analysis_provenance(
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
        "repository_dirty": False,
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


def test_build_analysis_provenance_records_dirty_repository_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_root = Path("/repository")

    monkeypatch.setattr(
        run_provenance,
        "get_repository_root",
        lambda: repository_root,
    )

    def fake_get_git_revision(path):
        # Only the main repository is dirty; the four tool checkouts are
        # clean, confirming their dirty state (discarded via [0] in
        # production) never leaks into the persisted payload.
        if Path(path) == repository_root:
            return "a" * 40, True
        return "b" * 40, False

    monkeypatch.setattr(run_provenance, "get_git_revision", fake_get_git_revision)
    monkeypatch.setattr(
        run_provenance,
        "collect_scientific_runtime",
        lambda: {
            "python_version": "3.9.12",
            "python_executable": "/cvmfs/example/bin/python",
            "root_version": "6.26/08",
        },
    )
    monkeypatch.setattr(
        run_provenance,
        "build_file_provenance",
        lambda path, repository_root=None: {
            "path": str(path),
            "sha256": "f" * 64,
        },
    )

    provenance = run_provenance.build_analysis_provenance(
        datafile="Input/data.root",
        datahist="directory/histogram",
        topfile="config/top.template",
        categoryfile="config/category.template",
        backgroundfile=None,
        signalfile=None,
        rangelow=481,
        rangehigh=3000,
        dosignal=False,
        dolimit=False,
        doprefit=True,
        maskthreshold=0.01,
    )

    assert provenance["repository_commit"] == "a" * 40
    assert provenance["repository_dirty"] is True
    assert provenance["tool_revisions"] == {
        "xmlAnaWSBuilder": "b" * 40,
        "quickFit": "b" * 40,
        "workspaceCombiner": "b" * 40,
        "pyBumpHunter": "b" * 40,
    }
