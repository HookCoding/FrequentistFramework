from __future__ import annotations

import json
from pathlib import Path

import pytest

from python import run_manifest


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
) -> None:
    results_path = run_manifest.write_analysis_results(
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
) -> None:
    results_path = run_manifest.write_analysis_results(
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
) -> None:
    results_path = tmp_path / "analysis_results.json"
    results_path.write_text(
        '{"schema_version": 1, "status": "success", ' '"masked": false, "p_chi2": 999.0}\n'
    )

    run_manifest.write_analysis_results(
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


def test_write_analysis_results_coerces_masked_and_p_chi2_to_json_native_types(
    tmp_path: Path,
) -> None:
    # The function body explicitly calls bool(masked) and float(p_chi2)
    # before assembling the payload. Every other test here already passes
    # native bool/float values, so that coercion is never actually
    # exercised. Passing non-bool/non-float-but-coercible values here (an
    # int for each) is the only way to tell "the coercion runs" apart from
    # "the value happened to already be the right type" - and it is
    # exactly the kind of implicit-but-load-bearing behavior a verbatim
    # move must not silently drop.
    results_path = run_manifest.write_analysis_results(
        folder=str(tmp_path),
        p_chi2=1,
        masked=1,
        provenance=_example_analysis_provenance(),
    )

    payload = json.loads(Path(results_path).read_text())

    assert payload["p_chi2"] == pytest.approx(1.0)
    assert isinstance(payload["p_chi2"], float)
    assert payload["masked"] is True
    assert isinstance(payload["masked"], bool)
