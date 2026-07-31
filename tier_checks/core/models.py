from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    tier: int
    requirement: str
    status: str
    summary: str
    details: tuple[str, ...] = ()
    duration_seconds: float = 0.0

    @property
    def successful(self) -> bool:
        return self.status in {"PASS", "WARN", "SKIP"}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
