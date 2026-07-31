from __future__ import annotations
from typing import Any

REQUIRED_KEYS = {"fit_parameters", "p_chi2", "p_bh", "cls_limit_points"}
SUPPORTED_PARAMETERS = {"nbkg", "p2", "p3", "p4", "p5", "p6", "p7"}


def validate(payload: Any) -> list[str]:
    errors = []
    if not isinstance(payload, dict):
        return ["top-level reference must be an object"]
    if set(payload) != {"J100", "J50"}:
        errors.append("top-level workflows must be exactly J100 and J50")
    for name in ("J100", "J50"):
        item = payload.get(name)
        if not isinstance(item, dict):
            errors.append(f"{name}: payload missing or not an object")
            continue
        if set(item) != REQUIRED_KEYS:
            errors.append(f"{name}: keys do not match the contract")
        pars = item.get("fit_parameters")
        if not isinstance(pars, dict) or not set(pars).issubset(SUPPORTED_PARAMETERS):
            errors.append(f"{name}: unsupported fit parameters")
        elif any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in pars.values()):
            errors.append(f"{name}: fit parameters must be numeric")
        for key in ("p_chi2", "p_bh"):
            value = item.get(key)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float))
            ):
                errors.append(f"{name}: {key} must be numeric or null")
        if item.get("cls_limit_points") != []:
            errors.append(f"{name}: cls_limit_points must remain [] while CLs is deferred")
    return errors
