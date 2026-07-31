# Tier-1 environment provenance and pinning (2026-07-29)

This file records the **observed runtime/tooling state** used for Tier-1 verification,
plus the intended pinning/constraint baseline for reproducible checks.

---

## 1) Runtime provenance snapshot

Captured from bounded local probes executed during Tier-1 completion work.

- `python_executable`: `/usr/bin/python3`
- `python_version`: `3.9.25`
- `pyproject.toml` requirement: `requires-python = ">=3.11"`

### Python tooling availability

- `pytest`: available (`8.4.2`)
- `ruff`: not available
- `black`: not available

### ROOT / RooFit provenance

- `root-config --version`: `6.40.02`
- `ROOT` module discoverability (`importlib.util.find_spec("ROOT")`): `true`
- Prior bounded PyROOT probe in this Tier-1 continuation reported:
  - `root_import = ok`
  - `root_version = 6.40.02`
  - `roofit_available = true`

Note: direct PyROOT import probes are slow in this environment and intermittently hit
timeout bounds, so `root-config` + module discoverability were used as bounded checks.

### Authoritative workflow path checks

- `xmlAnaWSBuilder/setup_lxplus.sh`: present
- `quickFit/setup_lxplus.sh`: present
- `run/fits/J100/run_481_3000_sixPar/quickFitLog_anaFit_sixPar_bkgOnly.log`: present
- `run/fits/J50/run_344_2079_sixPar/quickFitLog_anaFit_sixPar_bkgOnly.log`: present
- `run/fits/J100/run_481_3000_sixPar/BHresults.json`: absent (optional)
- `run/fits/J50/run_344_2079_sixPar/BHresults.json`: absent (optional)

---

## 2) Tier-1 pinning/constraint baseline

The Tier-1 gate and docs assume:

1. **Python**: `>=3.11` (authoritative project requirement from `pyproject.toml`)
2. **Test runner**: `pytest` installed
3. **Full mode tooling**: `ruff` and `black` installed
4. **Fit runtime**: ROOT/PyROOT/RooFit stack available for analysis workflows

### Current mismatch to resolve

- Active interpreter is `3.9.25`, which is below the declared `>=3.11` baseline.
- `ruff` and `black` are not installed in the active interpreter environment.

Implications:

- `scripts/quality_check.py --mode fast` can still run targeted Tier-1 tests when `pytest` is available.
- `scripts/quality_check.py --mode full` is expected to fail early with actionable
  install guidance until `ruff` and `black` are installed.

---

## 3) Reproduction commands for this provenance

```bash
python3 -m pytest --version
python3 - <<'PY'
import importlib.util
print('ROOT module discoverable:', importlib.util.find_spec('ROOT') is not None)
PY
root-config --version
```
