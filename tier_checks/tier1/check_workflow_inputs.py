from __future__ import annotations
import re, time
from tier_checks.core.base import TierCheck
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult
from tier_checks.tier1.manifest import WORKFLOWS


class WorkflowInputsCheck(TierCheck):
    check_id = "workflow-inputs"
    tier = 1
    requirement = "J100 and J50 entrypoints use their recorded Run-2 ROOT inputs."

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        failures = []
        details = []
        for name, spec in WORKFLOWS.items():
            script, input_path = context.path(spec["script"]), context.path(spec["input"])
            if not script.is_file():
                failures.append(f"{name}: missing script {spec['script']}")
                continue
            if not input_path.is_file():
                failures.append(f"{name}: missing input {spec['input']}")
            text = re.sub(r"\\\s*\n\s*", "", script.read_text(encoding="utf-8", errors="replace"))
            if spec["input"] not in text and input_path.name not in text:
                failures.append(f"{name}: script does not reference {spec['input']}")
            else:
                details.append(f"{name}: input contract found")
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "FAIL" if failures else "PASS",
            "workflow input contracts valid" if not failures else f"{len(failures)} input issue(s)",
            tuple(details + failures),
            time.monotonic() - started,
        )


CHECK = WorkflowInputsCheck()
