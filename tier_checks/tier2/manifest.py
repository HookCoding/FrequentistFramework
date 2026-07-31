EXPECTED_TOOLS = {
    "pytest": "9.1.1",
    "ruff": "0.16.0",
    "black": "26.5.1",
}

DEPENDENCY_FILES = (
    "requirements-dev.txt",
    "requirements-dev-lock.txt",
)

QUALITY_TARGETS = (
    "python/analysis_reference.py",
    "python/repo_utils.py",
    "scripts/compare_root_outputs.py",
    "scripts/quality_check.py",
    "tests/test_analysis_reference.py",
    "tests/test_compare_root_outputs.py",
    "tests/test_repo_utils.py",
    "tier_checks",
)
