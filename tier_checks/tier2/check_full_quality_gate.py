from __future__ import annotations
import sys, time
from tier_checks.core.base import TierCheck
from tier_checks.core.command import output_tail, run_command
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult


class FullQualityGateCheck(TierCheck):
    check_id = "full-quality-gate"
    tier = 2
    requirement = "The repository's complete quality gate exits with code 0."
    supported_depths = frozenset({"in-depth"})

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        command = [sys.executable, "scripts/quality_check.py", "--mode", "full"]
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
            "full quality gate passed" if code == 0 else f"full quality gate exited {code}",
            details,
            time.monotonic() - started,
        )


CHECK = FullQualityGateCheck()
