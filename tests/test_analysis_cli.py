from __future__ import annotations

from pathlib import Path

from python.analysis_cli import main


def _required_args(folder: Path) -> list[str]:
    return [
        "--datafile",
        "input.root",
        "--datahist",
        "data",
        "--topfile",
        "top.xml",
        "--categoryfile",
        "category.xml",
        "--wsfile",
        "workspace.root",
        "--outputfile",
        "fit-result.root",
        "--nbkg",
        "dummy",
        "--folder",
        str(folder),
    ]


def test_main_normalizes_signal_name_and_forwards_arguments(tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    result = main(
        _required_args(tmp_path),
        lambda **kwargs: calls.append(kwargs) or 0,
    )

    assert result == 0
    assert calls[0]["signame"] == "mean1000_width7.0"
    assert calls[0]["systdict"] is None


def test_main_loads_signal_systematics_from_requested_file(tmp_path: Path) -> None:
    systematics = tmp_path / "systematics.json"
    systematics.write_text('{"1000": {"nominal_mean": 1000}}')
    calls: list[dict[str, object]] = []

    main(
        _required_args(tmp_path) + ["--sysfile", str(systematics)],
        lambda **kwargs: calls.append(kwargs) or 0,
    )

    assert calls[0]["systdict"] == {"nominal_mean": 1000}
