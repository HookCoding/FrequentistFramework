from __future__ import annotations
import time
from tier_checks.core.base import TierCheck
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult
from tier_checks.tier1.manifest import WORKFLOWS


class WorkflowOutputsCheck(TierCheck):
    check_id = "workflow-outputs"
    tier = 1
    requirement = "Recorded J100/J50 fit directories and background-only logs exist."

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        failures = []
        details = []
        for name, spec in WORKFLOWS.items():
            fit_dir = context.path(spec["fit_dir"])
            log = fit_dir / spec["log"]
            if not fit_dir.is_dir():
                failures.append(f"{name}: missing directory {spec['fit_dir']}")
            elif not log.is_file():
                failures.append(f"{name}: missing log {log.relative_to(context.repo)}")
            elif log.stat().st_size == 0:
                failures.append(f"{name}: output log is empty")
            else:
                details.append(
                    f"{name}: {log.relative_to(context.repo)} ({log.stat().st_size} bytes)"
                )
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "FAIL" if failures else "PASS",
            (
                "recorded workflow outputs present"
                if not failures
                else f"{len(failures)} output issue(s)"
            ),
            tuple(details + failures),
            time.monotonic() - started,
        )


CHECK = WorkflowOutputsCheck()
