from __future__ import annotations

from abc import ABC, abstractmethod

from .context import CheckContext
from .models import CheckResult


class TierCheck(ABC):
    check_id: str
    tier: int
    requirement: str
    supported_depths = frozenset({"fast", "in-depth"})

    @abstractmethod
    def run(self, context: CheckContext) -> CheckResult:
        raise NotImplementedError
