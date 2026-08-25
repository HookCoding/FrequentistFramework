from __future__ import annotations

import hashlib
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

import ROOT


def get_repository_root(module_file: str | None = None) -> Path:
    source_file = Path(module_file) if module_file is not None else Path(__file__)
    repository_root = source_file.resolve().parents[1]
    if not (repository_root / ".git").exists():
        raise RuntimeError(
            "Could not locate the FrequentistFramework repository root " f"from {source_file}"
        )
    return repository_root


def resolve_analysis_path(path: str | Path, repository_root: str | Path | None = None) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        if repository_root is None:
            repository_root = get_repository_root()
        resolved = (Path(repository_root) / candidate).resolve()

    if not resolved.is_file():
        raise FileNotFoundError(f"Required analysis file does not exist: {resolved}")
    return resolved


def calculate_file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_file_provenance(
    path: str | Path,
    repository_root: str | Path | None = None,
) -> dict[str, str]:
    if repository_root is None:
        repository_root = get_repository_root()
    repository_root = Path(repository_root).resolve()
    resolved_path = resolve_analysis_path(path, repository_root=repository_root)
    try:
        display_path = str(resolved_path.relative_to(repository_root))
    except ValueError:
        display_path = str(resolved_path)
    return {"path": display_path, "sha256": calculate_file_sha256(resolved_path)}


def get_git_revision(repository_path: str | Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository_path), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Could not determine Git revision for {repository_path}: "
            f"{completed.stderr.strip()}"
        )
    revision = completed.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError(f"Invalid Git revision for {repository_path}: {revision!r}")
    return revision


def collect_scientific_runtime(
    root_module=ROOT,
    platform_module=platform,
    executable: str | None = None,
) -> dict[str, str]:
    root_version = root_module.gROOT.GetVersion()
    if not isinstance(root_version, str) or not root_version:
        raise RuntimeError("Could not determine the active ROOT version")
    return {
        "python_version": platform_module.python_version(),
        "python_executable": sys.executable if executable is None else executable,
        "root_version": root_version,
    }


def build_analysis_provenance(
    datafile,
    datahist,
    topfile,
    categoryfile,
    backgroundfile,
    signalfile,
    rangelow,
    rangehigh,
    dosignal,
    dolimit,
    doprefit,
    maskthreshold,
    *,
    repository_root=None,
    repository_root_fn: Callable[[], Path] = get_repository_root,
    revision_fn: Callable[[str | Path], str] = get_git_revision,
    runtime_fn: Callable[[], dict[str, str]] = collect_scientific_runtime,
    file_provenance_fn: Callable[..., dict[str, str]] = build_file_provenance,
):
    if repository_root is None:
        repository_root = repository_root_fn()

    tool_repositories = {
        "xmlAnaWSBuilder": Path(repository_root) / "xmlAnaWSBuilder",
        "quickFit": Path(repository_root) / "quickFit",
        "workspaceCombiner": Path(repository_root) / "workspaceCombiner",
        "pyBumpHunter": Path(repository_root) / "pyBumpHunter",
    }
    configurations = {
        "topfile": file_provenance_fn(topfile, repository_root=repository_root),
        "categoryfile": file_provenance_fn(categoryfile, repository_root=repository_root),
    }
    if backgroundfile is not None:
        configurations["backgroundfile"] = file_provenance_fn(
            backgroundfile, repository_root=repository_root
        )
    if signalfile is not None:
        configurations["signalfile"] = file_provenance_fn(
            signalfile, repository_root=repository_root
        )

    return {
        "repository_commit": revision_fn(repository_root),
        "runtime": runtime_fn(),
        "tool_revisions": {
            name: revision_fn(repository_path)
            for name, repository_path in tool_repositories.items()
        },
        "input": file_provenance_fn(datafile, repository_root=repository_root),
        "configurations": configurations,
        "invocation": {
            "datahist": datahist,
            "range_low": int(rangelow),
            "range_high": int(rangehigh),
            "signal_enabled": bool(dosignal),
            "limit_enabled": bool(dolimit),
            "prefit_enabled": bool(doprefit),
            "mask_threshold": float(maskthreshold),
        },
    }
