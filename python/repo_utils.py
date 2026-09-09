from __future__ import annotations

import json
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
# both apply. `--collect-only` there is the worst case, and it is not
# hypothetical: `addopts = ["--collect-only"]` made the full gate print
# "223/243 tests collected" and "All checks passed!" with exit code 0,
# having executed nothing.
#
# This lives here, rather than in the policy tests that also check it,
# because `scripts/quality_check.py` has to apply it *before* it starts
# pytest. A test cannot catch a configuration that stops tests from
# running, so the gate itself has to refuse first. Two copies of the
# rule is what let an earlier version of these checks drift, so there
# is one copy and two callers.
LONG_SELECTION_OPTIONS = (
    "--deselect",
    "--collect-only",
    "--co",
    "--ignore",
    "--ignore-glob",
)

# Short options that take a value and choose tests. pytest accepts the
# value attached (`-knothing`), so the letter is looked for anywhere in
# a single-dash word rather than only as a whole word.
SHORT_SELECTION_OPTIONS = ("-k", "-m")


def _load_toml(text: str) -> dict:
    """Parse TOML with whichever parser this interpreter has.

    `tomllib` is standard from 3.11; the LCG runtime's 3.9.12 has
    `tomli` instead. If neither is present this raises rather than
    returning nothing, because "no parser" must not read as "no
    offending options" - that is the failure mode this whole function
    exists to prevent.
    """
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - depends on interpreter
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError as error:  # pragma: no cover
            raise RuntimeError(
                "no TOML parser is available (tomllib on 3.11+, tomli on 3.9), so "
                "pytest's addopts cannot be checked - refusing to report it clean"
            ) from error
    return tomllib.loads(text)


def pytest_addopts_words(pyproject_text: str) -> list[str]:
    """The words pytest's `addopts` setting passes on every invocation.

    The value is read with a real TOML parser. Reading one physical
    line and stripping the outer quotes missed three forms pytest
    accepts, each confirmed against a real run: the array
    (`addopts = ["--collect-only"]`), the multiline string, and an
    array split across lines. The array form is the dangerous one - it
    exits 0 with nothing executed.
    """
    configured = (
        _load_toml(pyproject_text)
        .get("tool", {})
        .get("pytest", {})
        .get("ini_options", {})
        .get("addopts")
    )
    if configured is None:
        return []
    if isinstance(configured, str):
        return configured.split()
    if isinstance(configured, (list, tuple)):
        return [word for entry in configured for word in str(entry).split()]
    raise RuntimeError(f"unsupported pytest addopts value: {configured!r}")


def _selection_option(word: str) -> str | None:
    """The test-selecting option a single `addopts` word names, if any."""
    if word.startswith("--"):
        name = word.split("=", 1)[0]
        matched = [
            option for option in LONG_SELECTION_OPTIONS if option.startswith(name) and len(name) > 2
        ]
        # argparse accepts any unambiguous prefix, so `--col` is
        # `--collect-only`; a prefix of a selecting option counts as
        # that option.
        return matched[0] if matched else None
    if word.startswith("-") and len(word) > 1:
        for option in SHORT_SELECTION_OPTIONS:
            if option[1] in word[1:].split("=", 1)[0]:
                return option
    return None


def selection_affecting_addopts(pyproject_text: str) -> list[str]:
    """Every test-selecting option set in pytest's `addopts` configuration."""
    found = {
        option
        for word in pytest_addopts_words(pyproject_text)
        if (option := _selection_option(word)) is not None
    }
    return sorted(found)
