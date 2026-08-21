# Tier-1 system: authoritative J100/J50 safety net

This guide describes the current Tier-1 safety system for the authoritative Run-2 background-only workflows:

- `scripts/run_anaFit_J100.sh`
- `scripts/run_anaFit_J50.sh`

Tier 1 must remain passing before Tier-3 refactoring or Tier-4 orchestration begins.

## Current status

The executable characterization gate is complete and passing for canonical J100 and J50 background-only six-parameter fits.

It now:

- reruns both real launchers in fresh isolated output directories;
- requires fresh, non-empty scientific artifacts;
- extracts results only from fresh outputs;
- validates schema-version-2 manifests and provenance;
- compares fit parameters and chi-square p-values using explicit tolerances;
- rejects deliberate scientific drift;
- excludes diagnostic plots from scientific acceptance.

CLs remains intentionally deferred. `cls_limit_points` must remain `[]` for both canonical workflows.

## Canonical workflow contracts

### J100

- Input: `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root`
- Histogram: `hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj`
- Fit range: 481 to 3000 GeV
- Model: six-parameter background-only
- Prefit: enabled
- Mask threshold: `0.01`
- Signal and limit flags: disabled
- Output: `run/fits/J100/run_481_3000_sixPar/`

### J50

- Input: `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root`
- Histogram: `hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj`
- Fit range: 344 to 2079 GeV
- Model: six-parameter background-only
- Prefit: enabled
- Mask threshold: `0.01`
- Signal and limit flags: disabled
- Output: `run/fits/J50/run_344_2079_sixPar/`

These contracts are protected by launcher regression tests.

## Authoritative files

- `python/run_anaFit.py`
- `python/analysis_reference.py`
- `scripts/run_anaFit_J100.sh`
- `scripts/run_anaFit_J50.sh`
- `scripts/setup_buildAndFit.sh`
- `scripts/compare_root_outputs.py`
- `scripts/quality_check.py`
- `tests/references/analysis_reference.json`
- `tests/references/repo_snapshot.json`
- `tests/test_analysis_reference.py`
- `tests/test_compare_root_outputs.py`
- `tests/test_repo_utils.py`
- `tests/test_run_anaFit.py`
- `tests/test_analysis_workflows_integration.py`

Both launchers are executable and support the documented direct invocation.

## Output isolation and plot policy

Use an isolated output root with:

```bash
ANAFIT_OUTPUT_DIR=/tmp/anafit-output ./scripts/run_anaFit_J100.sh
```

If unset, the default remains `run/fits`.

The scientific gate sets:

```bash
ANAFIT_SKIP_PLOTS=1
```

Normal user runs still create plots by default. PDFs and other images are not required scientific artifacts.

## Required fresh artifacts

Each canonical integration run must create fresh, non-empty copies of:

- `background_dijetTLA_fromTemplate.xml`
- `category_dijetTLA_fromTemplate.xml`
- `dijetTLA_fromTemplate.xml`
- `signal_dijetTLA_fromTemplate.xml`
- `dijetisrTLA_combWS_sixPar.root`
- `FitResult_anaFit_sixPar_bkgOnly.root`
- `FitParameters_anaFit_sixPar_bkgOnly.root`
- `PostFit_anaFit_sixPar_bkgOnly.root`
- `quickFitLog_anaFit_sixPar_bkgOnly.log`
- `analysis_results.json`

The canonical unmasked gate rejects unexpected `BHresults.json`, `*_masked.root`, or `*_masked.xml` files.

## Failure and stale-output protection

The implementation and tests enforce:

- Python and launcher exit-status propagation;
- mandatory XMLReader and quickFit success;
- required fresh workspace, fit-result, and log artifacts;
- stale BumpHunter JSON removal;
- mandatory fresh BumpHunter results when masking is triggered;
- malformed or incomplete BumpHunter result rejection;
- invalid mask-bound rejection;
- no successful manifest after a failed analysis.

## Schema-version-2 manifests

Canonical manifests:

- `run/fits/J100/run_481_3000_sixPar/analysis_results.json`
- `run/fits/J50/run_344_2079_sixPar/analysis_results.json`

Each records:

- success and masking state;
- accepted chi-square p-value;
- repository commit;
- scientific Python executable and version;
- ROOT version;
- four external dependency revisions;
- input and configuration paths and SHA-256 values;
- histogram, fit range, mode flags, prefit state, and mask threshold.

Schema-version-1 reading remains supported for legacy manifests. Fresh canonical runs must produce schema version 2.

Canonical p-values:

- J100: `0.018448750724012808`
- J50: `0.07853114301666252`

## Frozen reference and tolerances

Each workflow payload contains exactly:

- `fit_parameters`
- `p_chi2`
- `p_bh`
- `cls_limit_points`

Current canonical values use numerical `p_chi2`, `p_bh: null`, and `cls_limit_points: []`.

Provisional tolerances:

- fit parameter `rtol=1e-6`, `atol=1e-8`;
- p-value `rtol=1e-5`, `atol=1e-8`.

Workflow names, payload keys, fit parameter names, BumpHunter presence, and CLs contents remain exact.

## Gate commands

### Lightweight full gate

```bash
python scripts/quality_check.py --mode full
```

Latest verified result:

- 105 collected;
- 103 passed;
- 2 prepared-dependency tests deselected;
- 0 expected failures;
- Ruff and Black passed;
- exit code 0.

### Prepared dependency gate

```bash
python -m pytest tests/test_repo_utils.py \
  -m "requires_analysis_dependencies" -v
```

Latest result: 2 passed, 11 deselected, exit code 0.

### Scientific runtime readiness

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -k authoritative_setup_provides_scientific_runtime -v
```

### Executable characterization gate

```bash
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
```

Latest result: 1 passed, 2 deselected, 116.02 seconds, exit code 0.

## Runtime split

Development quality environment:

- Python 3.12.13
- pytest 9.1.1
- Ruff 0.16.0
- Black 26.5.1

Scientific environment after `scripts/setup_buildAndFit.sh`:

- LCG `LCG_102a`
- `x86_64-centos9-gcc11-opt`
- Python 3.9.12
- ROOT/PyROOT 6.26/08

## ROOT comparison boundary

`compare_root_outputs.py` compares explicitly selected nested TH1 paths. It checks object presence and type, histogram class, bin counts, contents, errors, and edges with tolerances. It does not automatically inventory every ROOT object.

## Installation status and remaining limitations

The Git submodule declarations have matching `160000` Git index gitlinks at the verified pinned dependency revisions.

The destructive installer behavior has been removed. `install.sh` now provides a verified read-only `--check` mode that validates:

- parent dependency gitlinks and checked-out revisions;
- absence of tracked dependency source modifications;
- the pinned nested RooFitExtensions revisions;
- required setup and installation files.

The dedicated pyBumpHunter installer is non-destructive, reuses the authoritative LCG 102a scientific packages, preserves a valid existing environment, and refuses to overwrite an invalid environment.

No expected installation-policy failures remain in the lightweight gate.

A complete non-destructive C++ dependency build mode has not yet been enabled. Clean-clone scientific acquisition and building still require end-to-end verification before the installer can be described as fully operational.

## Operating commands

```bash
./scripts/run_anaFit_J100.sh
./scripts/run_anaFit_J50.sh
```

Optional selection:

```bash
FIT_PARS="six seven" ./scripts/run_anaFit_J100.sh
FIT_PARS="six" ./scripts/run_anaFit_J50.sh
```

## Scope boundary

CLs, Tier-3 refactoring, and Tier-4 orchestration remain out of scope. Tier 3 should not begin until this change set is reviewed and committed and the remaining installation risks are accepted or repaired.
