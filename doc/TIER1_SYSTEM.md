# Tier-1 system (J100/J50 Run-2 baseline)

This document is the user-facing operating guide for the Tier-1 safety net in this repository.
It is intentionally scoped to the **authoritative Run-2 analysis entrypoints**:

- `scripts/run_anaFit_J100.sh`
- `scripts/run_anaFit_J50.sh`

Tier 1 exists to keep the project workable and reproducible before deeper refactor/orchestration work.

---

## 1) Purpose, audience, and status

### Purpose

Tier 1 provides fast, deterministic checks that fail clearly when baseline files, references, or tooling are missing.

### Intended audience

- Users running or validating the J100/J50 Run-2 baseline
- Developers changing Tier-1 Python/tests/docs
- Reviewers who need reproducible evidence for baseline health

### Current delivery status (scope lock)

- **In scope now:** J100/J50 background-only reference extraction and verification.
- **Out of scope now:** CLs extraction/validation in Tier 1.
- `cls_limit_points` is currently expected to be an empty list (`[]`) for both workflows.

---

## 2) Tier-1 goals and success criteria

Tier 1 is considered healthy when the following hold:

1. Required baseline files/inputs exist.
2. Deterministic targeted tests pass against frozen references.
3. Fast/full quality-gate behavior matches implementation.
4. Missing dependencies fail with actionable install guidance.

---

## 3) Authoritative workflow and data surface

### Authoritative entrypoint scripts

- `scripts/run_anaFit_J100.sh`
- `scripts/run_anaFit_J50.sh`

### Authoritative Run-2 inputs

- `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root`
- `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root`

### Authoritative fit output directories used by Tier 1

- `run/fits/J100/run_481_3000_sixPar/`
- `run/fits/J50/run_344_2079_sixPar/`

### Background-only logs expected by Tier-1 extraction

`python/analysis_reference.py` searches each fit directory for:

1. `quickFitLog_anaFit_sixPar_bkgOnly.log`
2. `quickFitLog_anaFit_sevenPar_bkgOnly.log`

If neither exists, reference extraction fails with `FileNotFoundError`.

---

## 4) Repository map (Tier-1 relevant files)

### Quality gate and checks

- `scripts/quality_check.py`

### Reference extraction and validation

- `python/analysis_reference.py`

### Tier-1 regression tests

- `tests/test_analysis_reference.py`
- `tests/test_compare_root_outputs.py`
- `tests/test_repo_utils.py`

### Frozen references

- `tests/references/analysis_reference.json`
- `tests/references/repo_snapshot.json`

### Provenance and change tracking

- `doc/TIER1_ENVIRONMENT_PROVENANCE.md`
- `doc/ACTIVITY_LOG.md`

---

## 5) Quality gate behavior (`scripts/quality_check.py`)

Tier 1 uses a single explicit gate with `--mode fast|full`.

### Required baseline paths (hard failure)

The gate requires:

- `scripts/run_anaFit_J100.sh`
- `scripts/run_anaFit_J50.sh`
- `scripts/setup_buildAndFit.sh`
- `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root`
- `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root`
- `tests/references/analysis_reference.json`
- `tests/references/repo_snapshot.json`

If any are missing, the script exits early and prints all missing paths.

### Optional workflow hints (non-fatal)

The gate warns (without failing) if these fit-runtime helper paths are absent:

- `xmlAnaWSBuilder/setup_lxplus.sh`
- `quickFit/setup_lxplus.sh`

### Fast mode (`--mode fast`, default)

Runs:

1. required baseline path checks,
2. optional workflow hints,
3. Python module availability check for `pytest`,
4. targeted Tier-1 tests:

```bash
python3 -m pytest tests/test_analysis_reference.py tests/test_compare_root_outputs.py tests/test_repo_utils.py
```

### Full mode (`--mode full`)

Runs everything in fast mode, then:

1. Python module availability checks for `ruff` and `black`,
2. lint check:

```bash
python3 -m ruff check python/analysis_reference.py python/repo_utils.py scripts/compare_root_outputs.py scripts/quality_check.py tests/test_analysis_reference.py tests/test_compare_root_outputs.py tests/test_repo_utils.py
```

3. format check:

```bash
python3 -m black --check python/analysis_reference.py python/repo_utils.py scripts/compare_root_outputs.py scripts/quality_check.py tests/test_analysis_reference.py tests/test_compare_root_outputs.py tests/test_repo_utils.py
```

### Exit semantics

- Exit `1`: required baseline path failure.
- Exit `2`: required Python tooling modules missing.
- Otherwise: propagates non-zero return codes from subprocess checks (pytest/ruff/black).

### Tool installation guidance

If tools are missing in your active interpreter environment:

```bash
python3 -m pip install pytest ruff black
```

---

## 6) Analysis reference contract (`python/analysis_reference.py`)

Tier-1 reference generation is deterministic and workflow-locked to:

- `("J100", "run_481_3000_sixPar")`
- `("J50", "run_344_2079_sixPar")`

Each workflow payload must contain exactly these required keys:

- `fit_parameters` (dict of supported numeric parameter names)
- `p_chi2` (numeric or `null`)
- `p_bh` (numeric or `null` from optional `BHresults.json`)
- `cls_limit_points` (list; currently expected `[]`)

Supported fit-parameter names are constrained to:

- `nbkg`, `p2`, `p3`, `p4`, `p5`, `p6`, `p7`

### Frozen reference expectations

Current `tests/references/analysis_reference.json` stores:

- top-level workflows: `J100`, `J50`
- `cls_limit_points: []` for both workflows
- `p_bh: null` and `p_chi2: null` in the current baseline snapshot

---

## 7) Operating procedures

### A) Run the Tier-1 gate

Fast mode:

```bash
python3 scripts/quality_check.py --mode fast
```

Full mode:

```bash
python3 scripts/quality_check.py --mode full
```

### B) Run authoritative fit workflows

From repository root:

```bash
./scripts/run_anaFit_J100.sh
./scripts/run_anaFit_J50.sh
```

Optional fit-parameter selection:

```bash
FIT_PARS="six seven" ./scripts/run_anaFit_J100.sh
FIT_PARS="six" ./scripts/run_anaFit_J50.sh
```

### C) Run only Tier-1 tests

```bash
python3 -m pytest tests/test_analysis_reference.py tests/test_compare_root_outputs.py tests/test_repo_utils.py -q
```

### D) Regenerate frozen analysis reference (when intended)

Only do this when the baseline is intentionally changed and reviewed:

```bash
python3 - <<'PY'
from pathlib import Path
from python.analysis_reference import build_analysis_reference, write_analysis_reference

repo = Path('.').resolve()
payload = build_analysis_reference(repo)
write_analysis_reference(repo / 'tests/references/analysis_reference.json', payload)
print('analysis reference updated')
PY
```

Then rerun targeted tests and include the change rationale in `doc/ACTIVITY_LOG.md`.

---

## 8) Troubleshooting

### Missing required baseline paths

- Symptom: gate exits immediately with missing path list.
- Action: restore missing files/inputs before rerunning checks.

### Missing `pytest`, `ruff`, or `black`

- Symptom: gate prints required modules and install command.
- Action: install into the active interpreter environment.

### Fast succeeds, full fails

- This is expected when `ruff`/`black` are not installed.
- See `doc/TIER1_ENVIRONMENT_PROVENANCE.md` for current environment evidence and mismatch notes.

### Fit-runtime dependency warnings

- Missing optional hint paths (`xmlAnaWSBuilder/setup_lxplus.sh`, `quickFit/setup_lxplus.sh`) do not block tests.
- They can still block fit execution; install/restore fit runtime dependencies before running workflows.

### Reference extraction failures

- If no supported background-only log exists in a fit directory, extraction fails by design.
- Ensure at least one of:
  - `quickFitLog_anaFit_sixPar_bkgOnly.log`
  - `quickFitLog_anaFit_sevenPar_bkgOnly.log`

### CLs confusion

- Tier-1 currently does **not** populate CLs in the frozen reference.
- `cls_limit_points` remains an empty list until the planned extension is implemented.

---

## 9) Reproducibility, provenance, and change tracking

- Keep runtime/tooling evidence current in `doc/TIER1_ENVIRONMENT_PROVENANCE.md`.
- Record every substantial Tier-1 documentation or behavior change in `doc/ACTIVITY_LOG.md` as a new dated section.
- For reviews, capture:

```bash
git status -sb
git diff -- doc/TIER1_SYSTEM.md doc/ACTIVITY_LOG.md
```

---

## 10) Scope boundaries and non-goals

- Tier 1 is intentionally conservative and lightweight.
- It prioritizes operability, deterministic checks, and clear failures.
- It does not introduce orchestration frameworks (Tier 4).
- It does not perform broad structural refactors (Tier 3).
- Background-only-first remains the current scope lock for J100/J50.

Keeping Tier 1 healthy reduces risk for later-tier implementation.
