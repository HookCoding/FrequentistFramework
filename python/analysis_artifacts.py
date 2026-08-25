from __future__ import annotations

from pathlib import Path


def define_required_artifacts(folder: str | Path, parameter_count: int) -> list[Path]:
    """Define the standard artifacts expected after a fit completes.

    This is intentionally minimal and deterministic so it can be tested without
    ROOT or an analysis runtime.
    """
    if not isinstance(parameter_count, int):
        raise ValueError(
            f"parameter count must be an integer, got {type(parameter_count).__name__}"
        )
    if parameter_count <= 0:
        raise ValueError(f"parameter count must be positive, got {parameter_count}")

    folder_path = Path(folder)
    return [
        folder_path / "FitResult.root",
        folder_path / "PostFit.root",
        folder_path / "FitParameters.root",
        folder_path / "analysis_results.json",
    ]


def remove_stale_bumphunter_json(folder: str | Path) -> Path:
    """Remove a stale BumpHunter JSON file if it exists and return its path."""
    folder_path = Path(folder)
    bh_path = folder_path / "BHresults.json"
    if bh_path.exists():
        bh_path.unlink()
    return bh_path


def check_artifact_nonempty(path: str | Path) -> bool:
    """Return True only if the artifact exists and is non-empty."""
    artifact = Path(path)
    if not artifact.exists() or not artifact.is_file():
        return False
    return artifact.stat().st_size > 0


def check_artifact_freshness(path: str | Path, reference_time: float) -> bool:
    """Return True if the artifact exists and is newer than reference_time."""
    artifact = Path(path)
    if not artifact.exists() or not artifact.is_file():
        return False
    return artifact.stat().st_mtime > reference_time
