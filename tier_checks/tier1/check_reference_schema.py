from __future__ import annotations
import json, time
from tier_checks.core.base import TierCheck
from tier_checks.core.context import CheckContext
from tier_checks.core.models import CheckResult
from tier_checks.tier1.reference_contract import validate


class ReferenceSchemaCheck(TierCheck):
    check_id = "reference-schema"
    tier = 1
    requirement = "The frozen analysis reference follows the J100/J50 background-only schema."

    def run(self, context: CheckContext) -> CheckResult:
        started = time.monotonic()
        path = context.path("tests/references/analysis_reference.json")
        try:
            errors = validate(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            errors = [f"cannot read reference: {type(exc).__name__}: {exc}"]
        return CheckResult(
            self.check_id,
            self.tier,
            self.requirement,
            "FAIL" if errors else "PASS",
            "frozen reference schema valid" if not errors else f"{len(errors)} schema issue(s)",
            tuple(errors),
            time.monotonic() - started,
        )


CHECK = ReferenceSchemaCheck()
