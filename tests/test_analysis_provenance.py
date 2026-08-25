from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_module(monkeypatch: pytest.MonkeyPatch):
    root_module = ModuleType("ROOT")
    root_module.gROOT = type("FakeRoot", (), {"GetVersion": lambda self: "6.26/08"})()
    monkeypatch.setitem(sys.modules, "ROOT", root_module)
    sys.modules.pop("python.analysis_provenance", None)
    return importlib.import_module("python.analysis_provenance")


def test_calculate_file_sha256_matches_standard_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module(monkeypatch)
    input_file = tmp_path / "input.dat"
    input_file.write_bytes(b"provenance")

    assert module.calculate_file_sha256(input_file) == hashlib.sha256(b"provenance").hexdigest()


def test_build_file_provenance_records_relative_path_and_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module(monkeypatch)
    input_file = tmp_path / "Input" / "data.root"
    input_file.parent.mkdir()
    input_file.write_bytes(b"ROOT fixture")

    assert module.build_file_provenance("Input/data.root", tmp_path) == {
        "path": "Input/data.root",
        "sha256": module.calculate_file_sha256(input_file),
    }


def test_get_git_revision_rejects_non_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module(monkeypatch)

    with pytest.raises(RuntimeError, match="Could not determine Git revision"):
        module.get_git_revision(tmp_path)


def test_collect_scientific_runtime_records_root_and_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module(monkeypatch)
    monkeypatch.setattr(module.platform, "python_version", lambda: "3.12.13")
    monkeypatch.setattr(module.sys, "executable", "/python")

    assert module.collect_scientific_runtime() == {
        "python_version": "3.12.13",
        "python_executable": "/python",
        "root_version": "6.26/08",
    }


def test_build_analysis_provenance_records_config_and_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module(monkeypatch)
    repository_root = Path("/repository")
    revision_map = {repository_root: "a" * 40}
    revision_map.update(
        {
            repository_root / name: chr(ord("b") + index) * 40
            for index, name in enumerate(
                ["xmlAnaWSBuilder", "quickFit", "workspaceCombiner", "pyBumpHunter"]
            )
        }
    )

    provenance = module.build_analysis_provenance(
        datafile="Input/data.root",
        datahist="data",
        topfile="config/top.xml",
        categoryfile="config/category.xml",
        backgroundfile=None,
        signalfile=None,
        rangelow=481,
        rangehigh=3000,
        dosignal=False,
        dolimit=False,
        doprefit=True,
        maskthreshold=0.01,
        repository_root=repository_root,
        revision_fn=lambda path: revision_map[Path(path)],
        runtime_fn=lambda: {"root_version": "6.26/08"},
        file_provenance_fn=lambda path, repository_root=None: {
            "path": str(path),
            "sha256": "f" * 64,
        },
    )

    assert provenance["repository_commit"] == "a" * 40
    assert provenance["input"]["path"] == "Input/data.root"
    assert provenance["invocation"]["range_low"] == 481
    assert provenance["invocation"]["prefit_enabled"] is True
