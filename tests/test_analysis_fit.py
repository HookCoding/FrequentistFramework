from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest


def _load_module(monkeypatch: pytest.MonkeyPatch):
    root_module = ModuleType("ROOT")
    monkeypatch.setitem(sys.modules, "ROOT", root_module)
    postfit_module = ModuleType("ExtractPostfitFromWS")
    postfit_module.PostfitExtractor = object
    monkeypatch.setitem(sys.modules, "ExtractPostfitFromWS", postfit_module)
    fit_parameter_module = ModuleType("ExtractFitParameters")
    fit_parameter_module.FitParameterExtractor = object
    monkeypatch.setitem(sys.modules, "ExtractFitParameters", fit_parameter_module)
    sys.modules.pop("python.analysis_fit", None)
    return importlib.import_module("python.analysis_fit")


def test_build_fit_extract_stops_after_xmlreader_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module(monkeypatch)
    calls: list[str] = []

    def fail_command(command, description, expected_outputs=()):
        calls.append(description)
        return False

    with pytest.raises(RuntimeError, match="XMLReader workspace generation failed"):
        module.build_fit_extract(
            "top.xml",
            "input.root",
            "data",
            481,
            3000,
            "workspace.root",
            "FitResult.root",
            execute_required_fn=fail_command,
            execute_fn=lambda command: 0,
        )

    assert calls == ["XMLReader workspace generation"]


def test_build_fit_extract_rejects_missing_command_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module(monkeypatch)

    with pytest.raises(ValueError, match="Command execution functions are required"):
        module.build_fit_extract(
            "top.xml",
            "input.root",
            "data",
            481,
            3000,
            "workspace.root",
            "FitResult.root",
        )
