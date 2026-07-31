from __future__ import annotations
import sys, time
from tier_checks.core.base import TierCheck
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult


class PythonEnvironmentCheck(TierCheck):
    check_id = "python-environment"
    tier = 2
    requirement = (
        "The active Python interpreter satisfies the project requirement of Python 3.11 or newer."
    )

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        ok = sys.version_info >= (3, 11)
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "PASS" if ok else "FAIL",
            f"Python {sys.version.split()[0]}" + (" satisfies >=3.11" if ok else " is below 3.11"),
            (f"executable: {sys.executable}",),
            time.monotonic() - started,
        )


CHECK = PythonEnvironmentCheck()
