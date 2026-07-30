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
