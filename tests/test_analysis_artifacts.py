from __future__ import annotations

from pathlib import Path

import pytest

from python.analysis_artifacts import (
    check_artifact_freshness,
    check_artifact_nonempty,
    define_required_artifacts,
    remove_stale_bumphunter_json,
)


def test_define_required_artifacts_includes_expected_outputs(tmp_path: Path) -> None:
    artifacts = define_required_artifacts(tmp_path, 6)

    expected = [
        tmp_path / "FitResult.root",
        tmp_path / "PostFit.root",
        tmp_path / "FitParameters.root",
        tmp_path / "analysis_results.json",
    ]

    assert artifacts == expected


def test_define_required_artifacts_rejects_invalid_parameter_count(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="parameter count"):
        define_required_artifacts(tmp_path, 0)


def test_remove_stale_bumphunter_json_removes_existing_file(tmp_path: Path) -> None:
    bh_path = tmp_path / "BHresults.json"
    bh_path.write_text('{"stale": true}')

    removed_path = remove_stale_bumphunter_json(tmp_path)

    assert removed_path == bh_path
    assert not bh_path.exists()


def test_remove_stale_bumphunter_json_handles_missing_file(tmp_path: Path) -> None:
    removed_path = remove_stale_bumphunter_json(tmp_path)

    assert removed_path == tmp_path / "BHresults.json"
    assert not (tmp_path / "BHresults.json").exists()


def test_check_artifact_nonempty_accepts_nonempty_file(tmp_path: Path) -> None:
    artifact = tmp_path / "FitResult.root"
    artifact.write_text("content")

    assert check_artifact_nonempty(artifact)


def test_check_artifact_nonempty_rejects_missing_or_empty_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.root"
    empty = tmp_path / "empty.root"
    empty.write_text("")

    assert not check_artifact_nonempty(missing)
    assert not check_artifact_nonempty(empty)


def test_check_artifact_freshness_accepts_recent_file(tmp_path: Path) -> None:
    artifact = tmp_path / "FitResult.root"
    artifact.write_text("content")

    assert check_artifact_freshness(artifact, 0.0)


def test_check_artifact_freshness_rejects_stale_file(tmp_path: Path) -> None:
    artifact = tmp_path / "FitResult.root"
    artifact.write_text("content")

    stale_reference = artifact.stat().st_mtime + 10
    assert not check_artifact_freshness(artifact, stale_reference)
