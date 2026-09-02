from __future__ import annotations

from pathlib import Path

import pytest

from python import run_execution


def test_execute_returns_the_real_subprocess_return_code() -> None:
    assert run_execution.execute("exit 0") == 0
    assert run_execution.execute("exit 3") == 3


def test_execute_prints_the_command_before_running_it(
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_execution.execute("echo hello")

    captured = capsys.readouterr()
    assert "EXECUTE: echo hello" in captured.out
    assert "hello" in captured.out


def test_execute_required_accepts_success_with_expected_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_output = tmp_path / "result.root"

    def create_fresh_output(cmd):
        expected_output.write_text("fresh result")
        return 0

    monkeypatch.setattr(run_execution, "execute", create_fresh_output)

    assert run_execution.execute_required(
        "analysis command",
        "test analysis",
        expected_outputs=[str(expected_output)],
    )
    assert expected_output.read_text() == "fresh result"


def test_execute_required_rejects_stale_expected_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_output = tmp_path / "result.root"
    expected_output.write_text("stale result")

    def return_success_without_output(cmd):
        assert not expected_output.exists()
        return 0

    monkeypatch.setattr(run_execution, "execute", return_success_without_output)

    assert not run_execution.execute_required(
        "analysis command",
        "test analysis",
        expected_outputs=[str(expected_output)],
    )
    assert not expected_output.exists()


def test_execute_required_rejects_nonzero_command_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(run_execution, "execute", lambda cmd: 7)

    assert not run_execution.execute_required(
        "analysis command",
        "test analysis",
    )


def test_execute_required_rejects_missing_expected_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_output = tmp_path / "missing-result.root"

    monkeypatch.setattr(run_execution, "execute", lambda cmd: 0)

    assert not run_execution.execute_required(
        "analysis command",
        "test analysis",
        expected_outputs=[str(missing_output)],
    )
