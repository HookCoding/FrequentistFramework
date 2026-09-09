import json
import re
from pathlib import Path


def find_repo_root() -> Path:
    """Return the repository root by walking upward from this module."""
    return Path(__file__).resolve().parents[1]


def build_repo_snapshot() -> dict[str, object]:
    """Create a deterministic snapshot of key repository metadata."""
    repo_root = find_repo_root()
    excluded_entries = {".pytest_cache", ".ruff_cache", ".venv", "__pycache__"}
    curated_entries = {
        ".gitignore",
        ".gitmodules",
        ".pre-commit-config.yaml",
        "README.md",
        "atlasstyle-00-04-02",
        "background_dijetTLA_fromTemplate.xml",
        "config",
        "data",
        "doc",
        "install.sh",
        "plot_edm.py",
        "plot_postfit.cpp",
        "python",
        "run",
        "scripts",
        "setup.sh",
        "submission",
        "test.cpp",
        "tests",
    }
    top_level_entries = sorted(
        p.name
        for p in repo_root.iterdir()
        if p.exists() and p.name not in excluded_entries and p.name in curated_entries
    )
    return {
        "repo_root": ".",
        "python_dir_exists": (repo_root / "python").is_dir(),
        "tests_dir_exists": (repo_root / "tests").is_dir(),
        "readme_exists": (repo_root / "README.md").is_file(),
        "top_level_entries": top_level_entries,
    }


def write_repo_snapshot(path: Path, snapshot: dict[str, object]) -> None:
    """Write a JSON snapshot to disk."""
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_repo_snapshot(path: Path) -> dict[str, object]:
    """Read a JSON snapshot from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


# The pytest options that decide which tests run. Set in `addopts` they
# apply to every invocation in the repository, including gates that
# name a filter of their own, because `-k` and `-m` are independent and
# both apply. `--collect-only` there is the worst case: every gate
# collects, runs nothing, and exits 0.
#
# This lives here, rather than in the policy tests that also check it,
# because `scripts/quality_check.py` has to apply it *before* it starts
# pytest. A test cannot catch a configuration that stops tests from
# running, so the gate itself has to refuse first. Two copies of the
# rule is what let an earlier version of these checks drift, so there
# is one copy and two callers.
SELECTION_AFFECTING_PYTEST_OPTIONS = (
    "-k",
    "-m",
    "--deselect",
    "--collect-only",
    "--co",
    "--ignore",
)


def selection_affecting_addopts(pyproject_text: str) -> list[str]:
    """Any test-selecting option set in pytest's `addopts` configuration.

    The value is unquoted first: searching the quoted string directly
    finds nothing, because the opening quote sits where the option
    boundary is expected. Each option has to start and end a word, so
    `--color` is not `--co` and `-march` is not `-m`.
    """
    section = pyproject_text.partition("[tool.pytest.ini_options]")[2].partition("\n[")[0]
    addopts = re.search(r"^addopts\s*=\s*(.+)$", section, re.MULTILINE)
    if addopts is None:
        return []
    value = addopts.group(1).strip().strip("\"'")
    return [
        option
        for option in SELECTION_AFFECTING_PYTEST_OPTIONS
        if re.search(rf"(?:^|\s){re.escape(option)}(?:\s|=|$)", value)
    ]
