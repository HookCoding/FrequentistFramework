from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckContext:
    repo: Path
    depth: str
    timeout: int

    def path(self, relative: str) -> Path:
        return self.repo / relative
