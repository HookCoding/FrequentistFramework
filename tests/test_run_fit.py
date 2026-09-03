from __future__ import annotations

import sys
from types import ModuleType

import pytest

from python import run_fit


def test_build_fit_extract_stops_after_xmlreader_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    commands: list[str] = []

    def fail_xmlreader(cmd, description, expected_outputs=()):
        calls.append(description)
        commands.append(cmd)
        return False

    # execute_required lives in a different module (run_execution.py), so
    # the patch target is run_fit's own copy of the name, not the function
    # object patched in isolation - the same necessary-consequence pattern
    # already documented for run_masking.run_bumphunter (Chunk 4.B).
    monkeypatch.setattr(run_fit, "execute_required", fail_xmlreader)

    with pytest.raises(
        RuntimeError,
        match="XMLReader workspace generation failed",
    ):
        run_fit.build_fit_extract(
            topfile="top.xml",
            datafile="input.root",
            datahist="data",
            rangelow=481,
            rangehigh=3000,
            wsfile="workspace.root",
            fitresultfile="FitResult.root",
        )

    assert calls == ["XMLReader workspace generation"]
    # A regression test for the readability fix (caught in review): the
    # command string used to be built via implicit adjacent-string-literal
    # concatenation with mixed quoting ("..." '...') and old-style "%s" %
    # substitution; rewritten as a single f-string. Pin down the exact
    # rendered command to confirm the runtime text is unchanged.
    assert commands == [
        'xmlAnaWSBuilder/build/bin/XMLReader -x top.xml -o "logy integral" --minimizerStrategy 0'
    ]


def test_build_fit_extract_stops_after_quickfit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        run_fit,
        "execute_required",
        execute_required_with_quickfit_failure,
    )

    with pytest.raises(
        RuntimeError,
        match="quickFit failed",
    ):
        run_fit.build_fit_extract(
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


def test_build_fit_extract_rejects_fitresultfile_without_fitresult_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A regression test for a real bug (caught in review, High severity):
    # postfitfile/parameterfile/logfile/edmplot are all derived from
    # fitresultfile by substituting "FitResult" for another token in its
    # basename - an undocumented contract. If the basename doesn't
    # contain "FitResult" at all, every substitution below used to be a
    # no-op, so postfitfile and parameterfile both silently collapsed
    # back to fitresultfile itself, and PostfitExtractor's/
    # FitParameterExtractor's RECREATE-mode writes would overwrite the
    # quickFit result twice. Must now fail fast, before quickFit runs.
    calls: list[str] = []

    def fake_execute_required(cmd, description, expected_outputs=()):
        calls.append(description)
        return True

    monkeypatch.setattr(run_fit, "execute_required", fake_execute_required)

    with pytest.raises(ValueError, match='must contain "FitResult"'):
        run_fit.build_fit_extract(
            topfile="top.xml",
            datafile="input.root",
            datahist="data",
            rangelow=481,
            rangehigh=3000,
            wsfile="workspace.root",
            fitresultfile="fit-result.root",  # no "FitResult" token
        )

    # XMLReader may have already run (it never touches fitresultfile), but
    # quickFit - which would otherwise overwrite its own output via the
    # collapsed sibling filenames - must never be reached.
    assert "quickFit background or signal fit" not in calls


class _FakeHist:
    def __init__(self, first_bin: int) -> None:
        self._first_bin = first_bin

    def FindBin(self, value):  # noqa: N802 - mirrors ROOT's own API naming
        return self._first_bin


class _FakeTFile:
    def __init__(self, first_bin: int) -> None:
        self._first_bin = first_bin
        self.closed = False

    def Get(self, name):  # noqa: N802 - mirrors ROOT's own API naming
        return _FakeHist(self._first_bin)

    def Close(self):  # noqa: N802 - mirrors ROOT's own API naming
        self.closed = True


class _FakePostfitExtractor:
    instances: list["_FakePostfitExtractor"] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.written = []
        _FakePostfitExtractor.instances.append(self)

    def GetPval(self, name):  # noqa: N802 - mirrors PostfitExtractor's own API naming
        return {"Run3TLA_rebinned": 0.42, "Run3TLA_bkgonly_rebinned": 0.24}[name]

    def WriteRoot(self, filename, dirPerCategory=False):  # noqa: N802, N803
        self.written.append((filename, dirPerCategory))


class _FakeFitParameterExtractor:
    instances: list["_FakeFitParameterExtractor"] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.written = []
        _FakeFitParameterExtractor.instances.append(self)

    def WriteRoot(self, filename):  # noqa: N802 - mirrors the real extractor's API
        self.written.append(filename)


def _prepare_build_fit_extract_success_doubles(
    monkeypatch: pytest.MonkeyPatch,
    first_bin: int = 9,
) -> list[str]:
    # build_fit_extract() only reaches ROOT / PostfitExtractor /
    # FitParameterExtractor once both execute_required calls (XMLReader,
    # quickFit) have already succeeded -- a plain "return True" is enough
    # to exercise the rest of the function's successful path.
    monkeypatch.setattr(
        run_fit,
        "execute_required",
        lambda cmd, description, expected_outputs=(): True,
    )
    executed_commands: list[str] = []
    monkeypatch.setattr(
        run_fit,
        "execute",
        lambda cmd: executed_commands.append(cmd),
    )
    # createBinning.py is only invoked when the resolution-binning file is
    # missing; forcing os.path.exists() to True keeps this characterization
    # test independent of what happens to exist on disk for this rangelow.
    monkeypatch.setattr(run_fit.os.path, "exists", lambda path: True)

    # ROOT, PostfitExtractor and FitParameterExtractor are all imported
    # inside build_fit_extract itself (deferred - see run_fit.py), not at
    # module level, so there is no run_fit.ROOT/run_fit.PostfitExtractor
    # attribute to patch directly. Instead, stub the modules those deferred
    # imports resolve against, the same technique already used for
    # run_provenance.collect_scientific_runtime's own deferred "import
    # ROOT" (Chunk 3.B/3.A).
    fake_root_module = ModuleType("ROOT")
    fake_root_module.TFile = lambda datafile: _FakeTFile(first_bin)
    monkeypatch.setitem(sys.modules, "ROOT", fake_root_module)

    _FakePostfitExtractor.instances = []
    fake_postfit_module = ModuleType("ExtractPostfitFromWS")
    fake_postfit_module.PostfitExtractor = _FakePostfitExtractor
    monkeypatch.setitem(sys.modules, "ExtractPostfitFromWS", fake_postfit_module)

    _FakeFitParameterExtractor.instances = []
    fake_fitparam_module = ModuleType("ExtractFitParameters")
    fake_fitparam_module.FitParameterExtractor = _FakeFitParameterExtractor
    monkeypatch.setitem(sys.modules, "ExtractFitParameters", fake_fitparam_module)

    return executed_commands


def test_build_fit_extract_succeeds_for_unmasked_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed_commands = _prepare_build_fit_extract_success_doubles(monkeypatch)

    result = run_fit.build_fit_extract(
        topfile="top.xml",
        datafile="input.root",
        datahist="data",
        rangelow=481,
        rangehigh=3000,
        wsfile="workspace.root",
        fitresultfile="FitResult.root",
    )

    assert result == (0.42, "PostFit.root", "FitParameters.root")

    # plot_edm.py is always shelled out to as a diagnostic, its result
    # discarded (a plain execute(), not execute_required()).
    assert any("plot_edm.py" in cmd for cmd in executed_commands)
    # No BumpHunter mask range means no createBinning.py call is reachable
    # here anyway (os.path.exists() was forced True), and no --range flag.
    assert not any("createBinning.py" in cmd for cmd in executed_commands)

    (pfe,) = _FakePostfitExtractor.instances
    assert pfe.kwargs["maskmin"] == -1
    assert pfe.kwargs["maskmax"] == -1
    assert pfe.kwargs["datafirstbin"] == 8  # FindBin(481) - 1, from the fake TFile
    assert pfe.written == [("PostFit.root", True)]

    (fpe,) = _FakeFitParameterExtractor.instances
    assert fpe.kwargs["wsfile"] == "FitResult.root"
    assert fpe.written == ["FitParameters.root"]


def test_build_fit_extract_succeeds_for_masked_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_build_fit_extract_success_doubles(monkeypatch)

    quickfit_commands: list[str] = []
    original_execute_required = run_fit.execute_required

    def execute_required_recording_quickfit(cmd, description, expected_outputs=()):
        if description == "quickFit background or signal fit":
            quickfit_commands.append(cmd)
        return original_execute_required(cmd, description, expected_outputs)

    monkeypatch.setattr(run_fit, "execute_required", execute_required_recording_quickfit)

    result = run_fit.build_fit_extract(
        topfile="top.xml",
        datafile="input.root",
        datahist="data",
        rangelow=481,
        rangehigh=3000,
        wsfile="workspace.root",
        fitresultfile="FitResult.root",
        maskrange=(500, 600),
    )

    assert result == (0.24, "PostFit.root", "FitParameters.root")

    (quickfit_command,) = quickfit_commands
    assert "--range SBLo_Run3TLA,SBHi_Run3TLA" in quickfit_command

    (pfe,) = _FakePostfitExtractor.instances
    assert pfe.kwargs["maskmin"] == 500
    assert pfe.kwargs["maskmax"] == 600
    # Masking a bkg-only fit means the p-value must come from the
    # correctly-renormalized postfit distribution, not the plain one.
    assert pfe.written == [("PostFit.root", True)]


def test_build_fit_extract_derives_siblings_from_basename_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A regression test for a real bug (caught in review): the sibling
    # output paths used to be derived by substituting "FitResult" across
    # the *entire* path, which could also rewrite a parent directory
    # component that happens to contain that token - here,
    # "FitResult_stage" - not just the filename itself. Only the basename
    # may change; the directory must survive untouched.
    executed_commands = _prepare_build_fit_extract_success_doubles(monkeypatch)

    result = run_fit.build_fit_extract(
        topfile="top.xml",
        datafile="input.root",
        datahist="data",
        rangelow=481,
        rangehigh=3000,
        wsfile="workspace.root",
        fitresultfile="run/FitResult_stage/FitResult_anaFit.root",
    )

    assert result == (
        0.42,
        "run/FitResult_stage/PostFit_anaFit.root",
        "run/FitResult_stage/FitParameters_anaFit.root",
    )

    (pfe,) = _FakePostfitExtractor.instances
    assert pfe.written == [("run/FitResult_stage/PostFit_anaFit.root", True)]

    (fpe,) = _FakeFitParameterExtractor.instances
    assert fpe.written == ["run/FitResult_stage/FitParameters_anaFit.root"]

    (plot_edm_command,) = (cmd for cmd in executed_commands if "plot_edm.py" in cmd)
    assert "run/FitResult_stage/quickFitLog_anaFit.log" in plot_edm_command
    assert "run/FitResult_stage/edm_anaFit.pdf" in plot_edm_command
