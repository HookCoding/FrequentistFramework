from __future__ import annotations

from pathlib import Path

from python.analysis_commands import (
    build_quickfit_command,
    build_xmlreader_command,
    execute,
    execute_required,
)


def test_build_xmlreader_command_preserves_analysis_arguments() -> None:
    assert build_xmlreader_command("top.xml", "workspace.root") == (
        "xmlAnaWSBuilder/build/bin/XMLReader -x top.xml " '-o "logy integral" --minimizerStrategy 0'
    )


def test_build_quickfit_command_preserves_mask_and_log_arguments() -> None:
    command, logfile = build_quickfit_command(
        "workspace.root",
        "nsig_signal",
        (500, 600),
        "FitResult.root",
    )

    assert "-p nsig_signal" in command
    assert "--range SBLo_Run3TLA,SBHi_Run3TLA" in command
    assert "-o FitResult.root" in command
    assert logfile == "quickFitLog.log"


def test_execute_returns_zero_for_successful_command() -> None:
    result = execute("printf 'ok\\n'")
    assert result == 0


def test_execute_required_accepts_success_with_expected_output(tmp_path: Path) -> None:
    expected_output = tmp_path / "result.txt"
    expected_output.write_text("done")

    assert execute_required(
        "printf 'done' > /dev/null",
        "command success",
        expected_outputs=[str(expected_output)],
    )


def test_execute_required_rejects_nonzero_status() -> None:
    assert not execute_required("false", "failing command")


def test_execute_required_rejects_missing_expected_output(tmp_path: Path) -> None:
    missing_output = tmp_path / "missing.txt"

    assert not execute_required(
        "printf 'done\\n'",
        "command without file output",
        expected_outputs=[str(missing_output)],
    )


def test_execute_required_reports_missing_output_only_when_needed(tmp_path: Path) -> None:
    present_output = tmp_path / "present.txt"
    present_output.write_text("ok")

    assert execute_required(
        "printf 'done\\n'",
        "command with present file",
        expected_outputs=[str(present_output)],
    )


def test_execute_required_handles_empty_expected_outputs() -> None:
    assert execute_required("printf 'done\\n'", "simple command")
