from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from .base import TierCheck


def _load_module(path: Path, package_root: Path) -> ModuleType:
    relative = path.relative_to(package_root.parent).with_suffix("")
    module_name = ".".join(relative.parts)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load check module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def discover_checks(package_root: Path, tiers: set[int]) -> list[TierCheck]:
    discovered: list[TierCheck] = []
    seen_ids: set[str] = set()
    for tier in sorted(tiers):
        folder = package_root / f"tier{tier}"
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("check_*.py")):
            module = _load_module(path, package_root)
            check = getattr(module, "CHECK", None)
            if not isinstance(check, TierCheck):
                raise TypeError(f"{path} must expose CHECK as a TierCheck instance")
            if check.tier != tier:
                raise ValueError(f"{path} declares tier {check.tier}, expected {tier}")
            if check.check_id in seen_ids:
                raise ValueError(f"Duplicate check_id: {check.check_id}")
            seen_ids.add(check.check_id)
            discovered.append(check)
    return discovered
