from __future__ import annotations
import sys, time
from tier_checks.core.base import TierCheck
from tier_checks.core.command import output_tail, run_command
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult


class TargetedTestsCheck(TierCheck):
    check_id = "targeted-tests"
    tier = 1
    requirement = "The targeted Tier 1 regression tests pass."
    supported_depths = frozenset({"in-depth"})

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        command = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_analysis_reference.py",
            "tests/test_compare_root_outputs.py",
            "tests/test_repo_utils.py",
            "-q",
        ]
        try:
            code, output = run_command(command, context.repo, context.timeout)
            details = output_tail(output)
        except Exception as exc:
            code, details = 1, (f"execution failed: {type(exc).__name__}: {exc}",)
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "PASS" if code == 0 else "FAIL",
            "targeted tests passed" if code == 0 else f"targeted tests exited {code}",
            details,
            time.monotonic() - started,
        )


CHECK = TargetedTestsCheck()
