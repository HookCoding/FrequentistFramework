import hashlib
import platform
import re
import subprocess
import sys
from pathlib import Path

from repo_utils import find_repo_root


def get_repository_root():
    repository_root = find_repo_root()

    if not (repository_root / ".git").exists():
        raise RuntimeError(
            "Could not locate the FrequentistFramework repository root " "from {}".format(__file__)
        )

    return repository_root


def resolve_analysis_path(path, repository_root=None):
    candidate = Path(path)

    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        if repository_root is None:
            repository_root = get_repository_root()

        resolved = (Path(repository_root) / candidate).resolve()

    if not resolved.is_file():
        raise FileNotFoundError("Required analysis file does not exist: {}".format(resolved))

    return resolved


def calculate_file_sha256(path):
    digest = hashlib.sha256()

    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def build_file_provenance(path, repository_root=None):
    if repository_root is None:
        repository_root = get_repository_root()

    repository_root = Path(repository_root).resolve()
    resolved_path = resolve_analysis_path(
        path,
        repository_root=repository_root,
    )

    try:
        display_path = str(resolved_path.relative_to(repository_root))
    except ValueError:
        display_path = str(resolved_path)

    return {
        "path": display_path,
        "sha256": calculate_file_sha256(resolved_path),
    }


def get_git_revision(repository_path):
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repository_path),
            "rev-parse",
            "HEAD",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "Could not determine Git revision for {}: {}".format(
                repository_path,
                completed.stderr.strip(),
            )
        )

    revision = completed.stdout.strip()

    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError(
            "Invalid Git revision for {}: {!r}".format(
                repository_path,
                revision,
            )
        )

    status = subprocess.run(
        [
            "git",
            "-C",
            str(repository_path),
            "status",
            "--porcelain",
            "--untracked-files=no",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    if status.returncode != 0:
        raise RuntimeError(
            "Could not determine Git status for {}: {}".format(
                repository_path,
                status.stderr.strip(),
            )
        )

    dirty = bool(status.stdout.strip())

    if dirty:
        print(
            "WARNING: Recording Git revision {} for repository with "
            "tracked modifications: {}".format(
                revision,
                repository_path,
            )
        )
        print(status.stdout.rstrip())

    return revision, dirty


def collect_scientific_runtime():
    import ROOT

    root_version = ROOT.gROOT.GetVersion()

    if not isinstance(root_version, str) or not root_version:
        raise RuntimeError("Could not determine the active ROOT version")

    return {
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
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
):
    repository_root = get_repository_root()

    tool_repositories = {
        "xmlAnaWSBuilder": repository_root / "xmlAnaWSBuilder",
        "quickFit": repository_root / "quickFit",
        "workspaceCombiner": repository_root / "workspaceCombiner",
        "pyBumpHunter": repository_root / "pyBumpHunter",
    }

    configurations = {
        "topfile": build_file_provenance(
            topfile,
            repository_root=repository_root,
        ),
        "categoryfile": build_file_provenance(
            categoryfile,
            repository_root=repository_root,
        ),
        "backgroundfile": (
            None
            if backgroundfile is None
            else build_file_provenance(
                backgroundfile,
                repository_root=repository_root,
            )
        ),
        "signalfile": (
            None
            if signalfile is None
            else build_file_provenance(
                signalfile,
                repository_root=repository_root,
            )
        ),
    }

    repository_commit, repository_dirty = get_git_revision(repository_root)

    return {
        "repository_commit": repository_commit,
        "repository_dirty": repository_dirty,
        "runtime": collect_scientific_runtime(),
        "tool_revisions": {
            # Only the main repository's dirty state is persisted: the pinned
            # tool checkouts already have a dedicated, always-run tracked-
            # modification check (test_repo_utils.py::
            # test_external_dependency_checkouts_have_no_tracked_source_changes),
            # so duplicating that signal here would be redundant.
            name: get_git_revision(repository_path)[0]
            for name, repository_path in tool_repositories.items()
        },
        "input": build_file_provenance(
            datafile,
            repository_root=repository_root,
        ),
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
