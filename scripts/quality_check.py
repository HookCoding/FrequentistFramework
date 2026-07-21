from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    python_targets = ["python/repo_utils.py", "scripts/quality_check.py"]
    test_targets = ["tests/test_analysis_reference.py", "tests/test_repo_utils.py"]

    run_command([sys.executable, "-m", "pytest", *test_targets], repo_root)
    run_command([sys.executable, "-m", "ruff", "check", *python_targets, *test_targets], repo_root)
    run_command([sys.executable, "-m", "black", "--check", *python_targets], repo_root)


if __name__ == "__main__":
    main()
