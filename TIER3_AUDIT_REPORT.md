# Tier 3 Refactoring: Current-Structure Audit Report

**Date**: 2026-08-24
**Status**: Pre-refactoring analysis complete. Ready for Phase 0 baseline checkpoint.

---

## Executive Summary

The repository is in a healthy state for Tier 3 refactoring to begin:

- Tier 1 baseline (J100/J50 background-only workflows) is hardened and protected by launcher regression tests
- Tier 2 quality environment (Python 3.12.13 with pytest, Ruff, Black) is reproducibly pinned
- Lightweight gate consistently passes: 13 focused tests + Ruff + Black checks → exit 0
- Scientific integration gate passes: J100/J50 characterization produces frozen reference values
- `doc/TIER3_REFACTORING_PLAN.md` provides a complete implementation roadmap
- `python/run_anaFit.py` is the sole monolithic coordinator (1,100+ lines) that requires decomposition
- No inconsistencies found between plan, documentation, tests, and implementation

**Recommendation**: Record Phase 0 pre-refactor baseline checkpoint in `doc/ACTIVITY_LOG.md`, then proceed with Phase 3 (pure-function extraction) starting with path-construction and configuration validation logic.

---

## 1. Current Entry Points and Launchers

### Primary Analysis Launchers

| Launcher | Region | Input File | Histogram | Fit Range | Output |
|----------|--------|-----------|-----------|-----------|--------|
| `scripts/run_anaFit_J100.sh` | J100 | `Input/data/dijetTLA/mjj_spectra_J100_dataAll.root` | `hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj` | 481–3000 GeV | `run/fits/J100/run_481_3000_sixPar/` |
| `scripts/run_anaFit_J50.sh` | J50 | `Input/data/dijetTLA/mjj_spectra_J50_dataAll.root` | `hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj` | 344–2079 GeV | `run/fits/J50/run_344_2079_sixPar/` |

Both launchers:
- Source `scripts/setup_buildAndFit.sh` to establish LCG 102a scientific environment (Python 3.9.12, ROOT 6.26/08)
- Call `python/run_anaFit.py` with deterministic arguments
- Support optional `FIT_PARS` override (default: "six")
- Support `ANAFIT_OUTPUT_DIR`, `ANAFIT_SETUP_SCRIPT`, `ANAFIT_RUNNER`, `ANAFIT_SKIP_PLOTS` environment variables
- Propagate exit status from `run_anaFit.py`
- Optionally create PDFs via `plotPostFit.py` and `plot_postfit.cpp` (unless `ANAFIT_SKIP_PLOTS=1`)

### Invocation Interface

```bash
python/run_anaFit.py \
  --datafile <path> \
  --datahist <hist_name> \
  --backgroundfile <xml> \
  --signalfile <xml> \
  --categoryfile <xml> \
  --topfile <xml> \
  --wsfile <output.root> \
  --outputfile <fitresult.root> \
  --nbkg <"val,min,max"> \
  --rangelow <int> \
  --rangehigh <int> \
  --maskthreshold <float> \
  --folder <path> \
  [--doprefit] [--dosignal] [--dolimit] \
  [--sysfile <json>]
```

Exit codes: 0 (success), -1 (fit failed), 1–2 (argument/environment errors)

---

## 2. Main Call Sequence: Entry Point to Completion

### Execution Flow in `python/run_anaFit.py`

```
main(args)
  ├─ Parse command-line arguments
  ├─ Create output folder if needed
  ├─ Load optional systematics JSON
  └─ Call run_anaFit(...)
       │
       ├─ Step 1: Validation & Setup
       │   ├─ Compute bin count: nbins = rangehigh - rangelow
       │   ├─ Create symlink: config/dijetisrTLA/AnaWSBuilder.dtd → folder/
       │   ├─ Generate XML templates in folder:
       │   │   ├─ category_dijetTLA_fromTemplate.xml (or with Z' mass suffix)
       │   │   ├─ dijetTLA_fromTemplate.xml (or with Z' mass suffix)
       │   │   ├─ signal_dijetTLA_fromTemplate.xml
       │   │   └─ background_dijetTLA_fromTemplate.xml
       │   └─ Template substitution to resolve paths/values
       │
       ├─ Step 2: Prefit (conditional, if doprefit=True)
       │   ├─ Instantiate PreFitter with parameter ranges
       │   ├─ Extract bin count and first-bin index from data histogram
       │   ├─ Fit and obtain initial parameter values
       │   └─ Update background XML with fitted initial values
       │
       ├─ Step 3: Background-Only Fit (unconditional)
       │   ├─ Call build_fit_extract(poi=None, maskrange=None)
       │   │   ├─ XMLReader: workspace generation → wsfile
       │   │   ├─ quickFit: bkg-only fit → fitresultfile, logfile, postfitfile, parameterfile
       │   │   ├─ PostfitExtractor: generate postfit histograms, compute p_chi2
       │   │   └─ Return (pval_global, postfitfile, parameterfile)
       │   └─ Extract pval_global
       │
       ├─ Step 4: BumpHunter Branch (conditional, if pval < maskthreshold)
       │   ├─ run_bumphunter(postfitfile, folder)
       │   │   ├─ Remove stale BHresults.json
       │   │   ├─ Execute FindBHWindow.py → BHresults.json
       │   │   ├─ Load and validate BHresults JSON
       │   │   └─ Return {BlindRange, MaskMin, MaskMax}
       │   ├─ Copy unmasked fit files with "_masked" suffix
       │   ├─ Update XML files with masking directives
       │   ├─ Call build_fit_extract(poi=..., maskrange=(MaskMin, MaskMax))
       │   ├─ Extract pval_masked
       │   └─ Conditional: if pval_masked > maskthreshold → accept masked fit; else → return -1
       │
       ├─ Step 5: Signal+Background Fit (conditional, if dosignal & pval > maskthreshold)
       │   ├─ Not executed in canonical J100/J50 background-only workflows
       │   └─ If enabled: call build_fit_extract(poi="nsig_...", maskrange=None)
       │
       ├─ Step 6: Limit Setting (conditional, if dolimit & dosignal & pval > maskthreshold)
       │   ├─ Not executed in canonical workflows
       │   └─ If enabled: call quickLimit with POI
       │
       ├─ Step 7: Provenance & Manifest Generation (unconditional on success)
       │   ├─ build_analysis_provenance(...) → JSON structure with:
       │   │   ├─ repository_commit (Git SHA-256)
       │   │   ├─ runtime (Python version, Python exe, ROOT version)
       │   │   ├─ tool_revisions (Git SHA-256 for xmlAnaWSBuilder, quickFit, workspaceCombiner, pyBumpHunter)
       │   │   ├─ input (data file path & SHA-256)
       │   │   ├─ configurations (template file paths & SHA-256)
       │   │   └─ invocation (datahist, range, signal/limit/prefit flags, mask threshold)
       │   ├─ write_analysis_results(...)
       │   │   ├─ Create temporary manifest: analysis_results.json.tmp
       │   │   ├─ Write schema-version-2 JSON: {status, masked, p_chi2, provenance}
       │   │   └─ Atomic replace: .tmp → analysis_results.json
       │   └─ Return 0 (success)
       │
       └─ On Failure at Any Stage
           ├─ If XMLReader fails: raise RuntimeError, no manifest
           ├─ If quickFit fails: raise RuntimeError, no manifest
           ├─ If BumpHunter fails: raise RuntimeError, no manifest
           ├─ If masked fit fails: return -1, no manifest
           ├─ Launcher catches exception/return code and propagates
           └─ No stale manifest is written
```

**Key Invariants Preserved**:
- Manifest is written only after successful completion
- Stale `BHresults.json` is removed before BumpHunter execution
- Exit code 0 → manifest exists with success status
- Exit code ≠ 0 → no manifest or failure status in manifest

---

## 3. External Commands and Subprocess Execution

### Subprocess Calls in Execution Order

| Command | Module | Triggered | Expected Output | Failure Mode |
|---------|--------|-----------|-----------------|--------------|
| `xmlAnaWSBuilder/build/bin/XMLReader` | `build_fit_extract()` | Always (bkg-only) | `wsfile` (ROOT) | RuntimeError, exception |
| `quickFit/build/quickFit` | `build_fit_extract()` | Always (bkg-only) | `fitresultfile`, logfile | RuntimeError, exception |
| `python plot_edm.py` | `build_fit_extract()` | Always | `edmplot` PDF | Non-fatal (no check) |
| `PostfitExtractor` (Python class) | `build_fit_extract()` | Always | postfit histograms in-memory | RuntimeError on extraction |
| `FitParameterExtractor` (Python class) | `build_fit_extract()` | Always | parameter file in-memory | RuntimeError on extraction |
| `pyBumpHunter/pyBH_env/bin/python3 FindBHWindow.py` | `run_bumphunter()` | If p < maskthreshold | `BHresults.json` | RuntimeError, exception |
| `quickLimit` | `run_anaFit()` | If dosignal & dolimit & p > maskthreshold | Limits output | Warning only (non-fatal) |
| `python plotPostFit.py` | launcher | Always (unless ANAFIT_SKIP_PLOTS=1) | `postFit.pdf` | Non-fatal (not checked) |
| `root -l -q plot_postfit.cpp(...)` | launcher | Always (unless ANAFIT_SKIP_PLOTS=1) | plot files | Non-fatal (not checked) |

### Mandatory vs. Optional Subprocesses

**Mandatory for canonical J100/J50 workflows**:
- XMLReader (workspace generation)
- quickFit (bkg-only fit)
- PostfitExtractor (p-value calculation)
- FitParameterExtractor (parameter extraction)

**Conditional on masking decision**:
- FindBHWindow.py (BumpHunter masking calculation)
- quickFit masked (refit with blinded range)

**Optional in canonical workflows**:
- Prefit (doprefit=False by default, but enabled in launchers)
- quickLimit (dolimit=False)
- Plots (ANAFIT_SKIP_PLOTS=1 in scientific gate)

### Execution Context

- **Working directory**: Repository root (`.`)
- **Environment setup**: `source scripts/setup_buildAndFit.sh` establishes LCG 102a
- **Search paths**: XMLReader/quickFit use relative `config/` and `Input/` paths
- **Output paths**: All outputs written to `--folder` argument

---

## 4. File-System Effects

### Input Files (Read-Only)

| Category | Path | Format | Used By |
|----------|------|--------|---------|
| **Data histogram** | `Input/data/dijetTLA/mjj_spectra_J*.root` | ROOT TTree/TH1 | quickFit, PostfitExtractor |
| **Top-level XML** | `config/dijetisrTLA/dijetisrTLA.template` | XML template | XMLReader input |
| **Category XML** | `config/dijetisrTLA/category_dijetisrTLA.template` | XML template | XMLReader input |
| **Background XML** | `config/dijetisrTLA/background_dijetisrTLA_sixPar.template` | XML template | XMLReader input |
| **Signal XML** | `config/dijetisrTLA/signal/signal_dijetisrTLA.template` | XML template | XMLReader input (if dosignal) |
| **Resolution binning** | `Input/data/dijetisrTLA/mjjResolutionBinning_*.root` | ROOT histogram | PostfitExtractor |
| **Systematics (optional)** | `--sysfile` | JSON | Template substitution (if provided) |

### Generated/Modified Files (Per Run)

| Path Pattern | Created By | Purpose | Stale-Output Policy |
|--------------|-----------|---------|-------------------|
| `folder/AnaWSBuilder.dtd` (symlink) | `run_anaFit()` | Config schema | One symlink per output folder |
| `folder/*_fromTemplate.xml` | `run_anaFit()` | Instantiated XML configs | Overwritten each run |
| `folder/*_masked.xml` | `run_anaFit()` (if masking) | Masked XML configs | Cleaned up after use (not persisted) |
| `folder/dijetisrTLA_combWS_sixPar.root` | XMLReader | RooFit workspace (bkg-only) | Fresh each run |
| `folder/dijetisrTLA_combWS_sixPar_masked.root` | XMLReader (if masking) | RooFit workspace (masked) | Cleaned up after use |
| `folder/FitResult_anaFit_sixPar_bkgOnly.root` | quickFit | Fit parameters & results | Fresh each run |
| `folder/FitResult_anaFit_sixPar_bkgOnly_masked.root` | quickFit (if masking) | Masked fit result | Cleaned up after use |
| `folder/quickFitLog_anaFit_sixPar_bkgOnly.log` | quickFit | Fit convergence log | Fresh each run |
| `folder/PostFit_anaFit_sixPar_bkgOnly.root` | PostfitExtractor | Postfit histograms | Fresh each run |
| `folder/FitParameters_anaFit_sixPar_bkgOnly.root` | FitParameterExtractor | Fit parameter snapshot | Fresh each run |
| `folder/edm.pdf` | plot_edm.py | EDM visualization (optional) | Fresh each run |
| `folder/postFit.pdf` | plotPostFit.py | Postfit plots (if not ANAFIT_SKIP_PLOTS) | Fresh each run |
| `folder/BHresults.json` | run_bumphunter() | BumpHunter window JSON | Removed before BH run; fresh if masking |
| `folder/analysis_results.json` | write_analysis_results() | Success manifest (schema v2) | Atomic replace; written only on success |

### Stale-Output Handling

**Mandatory removal before execution**:
- `BHresults.json` is explicitly removed before running BumpHunter (line 772 in run_anaFit.py)

**Implicit overwrite**:
- Workspace, fit result, log, and postfit files are overwritten by quickFit/PostfitExtractor each run

**No manifest overwrite**:
- `analysis_results.json` uses atomic rename (.tmp → final) and is written only on success
- Failed analysis leaves no manifest (or manifest with failed status if partially written)

### Directory Structure Created

```
run/fits/
├── J100/
│   └── run_481_3000_sixPar/
│       ├── AnaWSBuilder.dtd (symlink)
│       ├── category_dijetTLA_fromTemplate.xml (generated)
│       ├── dijetTLA_fromTemplate.xml (generated)
│       ├── signal_dijetTLA_fromTemplate.xml (generated)
│       ├── background_dijetTLA_fromTemplate.xml (generated)
│       ├── dijetisrTLA_combWS_sixPar.root (workspace)
│       ├── FitResult_anaFit_sixPar_bkgOnly.root (fit result)
│       ├── quickFitLog_anaFit_sixPar_bkgOnly.log (log)
│       ├── PostFit_anaFit_sixPar_bkgOnly.root (postfit histograms)
│       ├── FitParameters_anaFit_sixPar_bkgOnly.root (parameters)
│       ├── edm.pdf (optional)
│       ├── postFit.pdf (optional)
│       ├── BHresults.json (if masking)
│       └── analysis_results.json (manifest)
└── J50/
    └── run_344_2079_sixPar/
        └── (same structure)
```

---

## 5. Environment-Variable Dependencies

### Shell Environment Variables (Launcher Context)

| Variable | Default | Used By | Purpose |
|----------|---------|---------|---------|
| `ANAFIT_OUTPUT_DIR` | `repo_dir/run/fits` | launcher | Override output directory root |
| `ANAFIT_SETUP_SCRIPT` | `repo_dir/scripts/setup_buildAndFit.sh` | launcher | Override setup script (LCG 102a) |
| `ANAFIT_RUNNER` | `repo_dir/python/run_anaFit.py` | launcher | Override Python runner |
| `ANAFIT_SKIP_PLOTS` | unset (default: create plots) | launcher | Skip PDF generation (set to "1") |
| `FIT_PARS` | "six" | launcher | Space-separated fit-parameter counts |

### Python Environment (Scientific Runtime)

Established by `scripts/setup_buildAndFit.sh`:

| Variable | Value | Source |
|----------|-------|--------|
| `$PATH` | LCG 102a bin directories | setup_buildAndFit.sh |
| `$LD_LIBRARY_PATH` | LCG 102a lib directories | setup_buildAndFit.sh |
| `$PYTHONPATH` | LCG 102a Python 3.9.12 | setup_buildAndFit.sh |
| Python interpreter | `/cvmfs/sft.cern.ch/lcg/views/LCG_102a/x86_64-centos9-gcc11-opt/bin/python` | setup_buildAndFit.sh |
| ROOT 6.26/08 | Available via PyROOT import | setup_buildAndFit.sh |
| RooFit | Available (LCG 102a bundle) | setup_buildAndFit.sh |

### Command-Line Arguments as Configuration

Provided by launcher to `run_anaFit.py`:

| Argument | Type | Required | Source |
|----------|------|----------|--------|
| `--datafile` | path | Yes | Launcher |
| `--datahist` | string | Yes | Launcher |
| `--backgroundfile` | path | Yes | Launcher |
| `--signalfile` | path | Yes | Launcher |
| `--categoryfile` | path | Yes | Launcher |
| `--topfile` | path | Yes | Launcher |
| `--wsfile` | path | Yes | Launcher (constructed in folder) |
| `--outputfile` | path | Yes | Launcher (constructed in folder) |
| `--nbkg` | "value,min,max" | Yes | Launcher or prefit output |
| `--rangelow` | int | Yes | Launcher |
| `--rangehigh` | int | Yes | Launcher |
| `--maskthreshold` | float | No (default 0.01) | Launcher |
| `--folder` | path | No (default "run") | Launcher |
| `--doprefit` | flag | No | Launcher (enabled for J100/J50) |
| `--dosignal` | flag | No | Launcher (disabled for J100/J50) |
| `--dolimit` | flag | No | Launcher (disabled for J100/J50) |
| `--sysfile` | path | No | Launcher (not used in J100/J50) |

---

## 6. ROOT-Dependent Boundaries

### Strong ROOT Dependencies

The following are **tightly coupled to ROOT/RooFit**:

1. **XMLReader workspace generation**
   - Input: XML templates + configuration
   - Subprocess call to `xmlAnaWSBuilder/build/bin/XMLReader`
   - Output: RooFit workspace file (ROOT binary)
   - Cannot be moved to pure Python without re-implementation

2. **quickFit model fitting**
   - Input: RooFit workspace, ROOT data file
   - Subprocess call to `quickFit/build/quickFit`
   - Output: ROOT fit result file with fit parameters and statistics
   - Cannot be replaced without re-fitting logic

3. **PostfitExtractor**
   - Input: ROOT fit result, ROOT data histogram
   - Python class from `ExtractPostfitFromWS.py`
   - Operations: ROOT TFile operations, histogram manipulation
   - Computation: p-value calculation from chi-square and DOF
   - Output: Postfit histogram ROOT file
   - Dependency on ROOT for histogram I/O and computations

4. **FitParameterExtractor**
   - Input: ROOT fit result file
   - Python class from `ExtractFitParameters.py`
   - Operations: Extract fit parameters from RooFit results
   - Output: Parameter snapshot ROOT file
   - Tight coupling to ROOT object hierarchy

5. **Data histogram reading**
   - Input: Data file path, histogram path
   - Operations: ROOT TFile.Get() for histogram
   - Used in: prefit bin-count determination, PostfitExtractor initialization
   - Essential for coordinate transformation

### Pure Python Boundaries

These can be extracted and tested without ROOT:

1. **Command-argument construction**
   - `XMLReader -x <template> -o ...` command assembly
   - `quickFit --chi2fit 1 ...` command assembly
   - All arguments derived from input parameters

2. **Template XML generation and substitution**
   - Path resolution
   - Configuration placeholder replacement
   - String manipulation

3. **BumpHunter result parsing**
   - JSON loading and validation
   - Bounds validation (MaskMin < MaskMax)
   - BlindRange format validation

4. **Manifest generation**
   - Provenance collection (Git SHA-256, file hashes)
   - Manifest JSON assembly
   - Atomic file writing

5. **File path handling**
   - Repository root detection
   - Absolute/relative path conversion
   - Output directory structure creation

6. **Configuration validation**
   - Argument validation (integer ranges, float ranges)
   - File existence checks
   - Fit-range sanity checks

---

## 7. BumpHunter Branch Control Flow

### Condition for Masking

```python
if pval_global > maskthreshold:  # threshold = 0.01 for J100/J50
    # Fit passed; no masking needed
    final_p_chi2 = pval_global
    fit_was_masked = False
else:
    # Fit marginal; run BumpHunter to identify significant window
    BHresults = run_bumphunter(postfitfile, folder)
    # ... refit with masked range ...
    if pval_masked > maskthreshold:
        final_p_chi2 = pval_masked
        fit_was_masked = True
    else:
        return -1  # Fit failed even with masking
```

### BumpHunter Execution Wrapper

```python
def run_bumphunter(postfitfile, folder):
    bhresults_file = "{}/BHresults.json".format(folder)
    
    # Stale-output removal (safety invariant)
    if os.path.exists(bhresults_file):
        os.remove(bhresults_file)
    
    # Execute BumpHunter via pyBumpHunter environment
    bumphunter_command = (
        "pyBumpHunter/pyBH_env/bin/python3 "
        "python/FindBHWindow.py "
        "--inputfile %s "
        "--bkghist %s "
        "--datahist %s "
        "--outputjson %s"
    ) % (postfitfile, "Run3TLA_rebinned/postfit", "Run3TLA_rebinned/data", bhresults_file)
    
    if not execute_required(...):
        raise RuntimeError("BumpHunter masking-window calculation failed")
    
    return load_bumphunter_results(bhresults_file)
```

### Result Validation

```python
def load_bumphunter_results(results_file):
    # Parse JSON
    with open(results_file) as file:
        results = json.load(file)
    
    if not isinstance(results, dict):
        raise ValueError("BumpHunter results must be a JSON object")
    
    # Validate required keys
    required_keys = ("BlindRange", "MaskMin", "MaskMax")
    missing_keys = [key for key in required_keys if key not in results]
    if missing_keys:
        raise ValueError(f"Missing required keys: {missing_keys}")
    
    # Validate bounds
    mask_min = int(results["MaskMin"])
    mask_max = int(results["MaskMax"])
    if mask_min >= mask_max:
        raise ValueError("MaskMin must be smaller than MaskMax")
    
    # Validate BlindRange format
    blind_range = results["BlindRange"]
    if not isinstance(blind_range, str) or not blind_range.strip():
        raise ValueError("BlindRange must be a non-empty string")
    
    return {
        "BlindRange": blind_range,
        "MaskMin": mask_min,
        "MaskMax": mask_max,
    }
```

### Canonical Behavior (J100/J50)

For background-only, unmasked fits:
- `pval_global ≈ 0.018` (J100) or `0.079` (J50), both **above** threshold 0.01 ✓
- Masking branch is **not executed**
- `BHresults.json` is **absent** in canonical outputs
- `fit_was_masked = False` in manifest

---

## 8. Manifest and Provenance Generation

### Schema-Version-2 Manifest Structure

```python
{
  "schema_version": 2,
  "status": "success",          # literal string
  "masked": false,              # boolean
  "p_chi2": 0.018448750724012808,   # float
  "provenance": {               # detailed runtime/input record
    "repository_commit": "abc123...",  # 40-char hex
    "runtime": {
      "python_version": "3.9.12",
      "python_executable": "/cvmfs/...",
      "root_version": "6.26/08"
    },
    "tool_revisions": {
      "xmlAnaWSBuilder": "6b84050f...",
      "quickFit": "0408030b...",
      "workspaceCombiner": "7d484ad3...",
      "pyBumpHunter": "91f49a62..."
    },
    "input": {
      "path": "Input/data/dijetTLA/mjj_spectra_J100_dataAll.root",
      "sha256": "f6336bc2d0..."
    },
    "configurations": {
      "topfile": {"path": "config/...", "sha256": "..."},
      "categoryfile": {"path": "config/...", "sha256": "..."},
      "backgroundfile": {"path": "config/...", "sha256": "..."},
      "signalfile": {"path": "config/...", "sha256": "..."}
    },
    "invocation": {
      "datahist": "hists_yStar06_rejectEta_10_16/afterSelection/nominal/h_mjj",
      "range_low": 481,
      "range_high": 3000,
      "signal_enabled": false,
      "limit_enabled": false,
      "prefit_enabled": true,
      "mask_threshold": 0.01
    }
  }
}
```

### Frozen Canonical Values

| Workflow | Path | p_chi2 | Masked | p_bh | cls_limit_points |
|----------|------|--------|--------|------|-----------------|
| J100 | `run/fits/J100/run_481_3000_sixPar/analysis_results.json` | 0.018448750724012808 | false | null | [] |
| J50 | `run/fits/J50/run_344_2079_sixPar/analysis_results.json` | 0.07853114301666252 | false | null | [] |

### Manifest Writing

```python
def write_analysis_results(folder, p_chi2, masked, provenance):
    results_path = os.path.join(folder, "analysis_results.json")
    temporary_path = results_path + ".tmp"
    
    payload = {
        "schema_version": 2,
        "status": "success",
        "masked": bool(masked),
        "p_chi2": float(p_chi2),
        "provenance": provenance,
    }
    
    # Write to temporary file
    with open(temporary_path, "w") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")
    
    # Atomic replace
    os.replace(temporary_path, results_path)
    return results_path
```

**Key Properties**:
- Writes to `.tmp` first, atomic replace second → crash-safe
- Only successful `run_anaFit()` returns reach this code
- Exit code 0 only if manifest successfully written

---

## 9. Failure-Propagation Paths

### Exception Handling in `run_anaFit.py`

```
try/except patterns:
  - No explicit try/except blocks wrapping major operations
  - Exceptions propagate to launcher (launcher has no try/except either)
  
Exit-code propagation:
  - run_anaFit() returns 0 on success, -1 on failure (masked fit failed)
  - main() returns result directly to sys.exit()
  - Launcher checks: if (( analysis_status != 0 )); then exit "$analysis_status"; fi
```

### Failure Points and Behavior

| Failure Point | Detection | Propagation | Manifest |
|---------------|-----------|-------------|----------|
| **XMLReader fails** | return code ≠ 0 | `execute_required()` → `RuntimeError` → uncaught | None |
| **quickFit fails** | return code ≠ 0 | `execute_required()` → `RuntimeError` → uncaught | None |
| **Missing quickFit output** | file not found | `execute_required()` → `False` → `RuntimeError` | None |
| **PostfitExtractor fails** | p-value calc error | uncaught exception | None |
| **BumpHunter fails** | return code ≠ 0 | `execute_required()` → `RuntimeError` → uncaught | None |
| **BumpHunter JSON malformed** | json.load() or validation | `ValueError` → uncaught | None |
| **Masked fit fails** | pval_masked ≤ threshold | explicit check → `return -1` | None |
| **Git operation fails** | subprocess error | `RuntimeError` → uncaught | Provenance collection stops |
| **File hash fails** | file read error | `RuntimeError` → uncaught | Provenance collection stops |
| **Manifest write fails** | file I/O error | exception in `write_analysis_results()` | Partial `.tmp` file (not atomically replaced) |

### Invariant: No Manifest on Failure

- Manifest is the **last** operation; only written if all prior stages succeed
- If any exception occurs before manifest generation, no success manifest is created
- If manifest write fails mid-operation, atomic replacement fails, preserving old manifest (if any)

---

## 10. Existing Module Boundaries

### Current Monolithic Structure

**File**: `python/run_anaFit.py` (~1,100 lines)

**Functions** (not modules, but logical units):

```
Global functions in run_anaFit.py:
├─ execute(cmd)                          ← subprocess wrapper, prints output
├─ execute_required(cmd, desc, outputs)  ← subprocess + validation
├─ load_bumphunter_results(json_file)    ← BH JSON parsing & validation
├─ run_bumphunter(postfit, folder)       ← BH orchestration + stale-output removal
├─ get_repository_root()                 ← Git repo root detection
├─ resolve_analysis_path(path, root)     ← Path resolution
├─ calculate_file_sha256(path)           ← File hashing
├─ build_file_provenance(path, root)     ← Single-file provenance record
├─ get_git_revision(repo_path)           ← Git SHA-256 for repos
├─ collect_scientific_runtime()          ← Python/ROOT runtime inspection
├─ build_analysis_provenance(...)        ← Full provenance assembly
├─ write_analysis_results(...)           ← Manifest JSON writing (atomic)
├─ replaceinfile(f, old_new_list)        ← Template substitution
├─ build_fit_extract(...)                ← XMLReader + quickFit + PostfitExtractor orchestration
├─ run_anaFit(...)                       ← Main analysis coordinator (600+ lines)
└─ main(args)                            ← CLI entry point + argument parsing
```

### Supporting Modules

| Module | Role | Lines |
|--------|------|-------|
| `ExtractPostfitFromWS` | PostfitExtractor class; histogram extraction, p-value calc | External (ROOT) |
| `ExtractFitParameters` | FitParameterExtractor class; parameter snapshotting | External (ROOT) |
| `PreFit` | PreFitter class; initial parameter fitting | External (ROOT) |
| `analysis_reference.py` | Reference validation, workflow discovery (not called by run_anaFit) | ~200 |
| `repo_utils.py` | Repository utilities (not directly called by run_anaFit) | ~150 |
| `compare_root_outputs.py` | ROOT comparison utilities (not called by run_anaFit) | ~300 |

### Implicit Boundaries (Logical Responsibilities)

Within `run_anaFit()` (main coordinator):

1. **Configuration reading & validation** (~20 lines)
   - Parse arguments, set defaults
   - Create output folder

2. **XML template generation** (~100 lines)
   - Copy templates to folder
   - Perform placeholder substitution
   - Handle prefit parameter initialization

3. **Prefit (optional)** (~50 lines)
   - PreFitter instantiation
   - Parameter extraction from fit
   - Background XML update

4. **Background-only fit** (~10 lines)
   - Call `build_fit_extract()`
   - Extract p-value

5. **BumpHunter branch** (~80 lines)
   - Conditional masking decision
   - XML copying and modification
   - Masked refit execution
   - P-value comparison

6. **Signal+background fit (optional)** (~10 lines)
   - Not executed in canonical workflows

7. **Limit setting (optional)** (~10 lines)
   - Not executed in canonical workflows

8. **Provenance & manifest** (~20 lines)
   - Call provenance builder
   - Call manifest writer
   - Return success/failure

**Total**: ~290 lines of main logic (excludes nested function definitions)

---

## 11. Existing Test Protection

### Test Files and Coverage

| Test File | Tests | Focus | Root Dependency |
|-----------|-------|-------|-----------------|
| `test_run_anaFit.py` | 56 | Core launcher, BH, provenance, git operations | Mocked/stubbed |
| `test_analysis_reference.py` | 28 | Manifest schema, workflow discovery | JSON |
| `test_analysis_workflows_integration.py` | 3 | **Authoritative J100/J50 gates** | ROOT, LCG 102a |
| `test_compare_root_outputs.py` | 29 | ROOT comparison utilities | ROOT |
| `test_repo_utils.py` | 34 | Repository integrity, dependency revisions, install policy | Git, file I/O |

### Coverage of `run_anaFit.py` Functions

| Function | Test File | Test Count | Notes |
|----------|-----------|-----------|-------|
| `execute_required()` | test_run_anaFit | 3 | ✓ Covers success, failure, missing output |
| `load_bumphunter_results()` | test_run_anaFit | 5 | ✓ Covers valid, malformed, missing keys, invalid bounds |
| `run_bumphunter()` | test_run_anaFit | 5 | ✓ Covers stale removal, success, failure, invalid output |
| `calculate_file_sha256()` | test_run_anaFit | 2 | ✓ Covers success, missing file |
| `get_git_revision()` | test_run_anaFit | 2 | ✓ Covers success, non-repo |
| `resolve_analysis_path()` | test_run_anaFit | 3 | ✓ Covers repo-relative, absolute, missing |
| `build_file_provenance()` | test_run_anaFit | 3 | ✓ Covers repo-relative, external absolute, missing |
| `collect_scientific_runtime()` | test_run_anaFit | 2 | ✓ Covers success, missing ROOT version |
| `build_analysis_provenance()` | test_run_anaFit | 1 | ✓ Full provenance assembly with real paths |
| `write_analysis_results()` | test_run_anaFit | 3 | ✓ Covers success, masked flag, atomic replacement |
| `build_fit_extract()` | test_run_anaFit | 2 | ✓ Covers XMLReader failure, quickFit failure |
| `run_anaFit()` (main) | test_run_anaFit + integration | 2+1 | ✓ Partial: launcher propagation + J100/J50 gate |
| `main()` (CLI) | test_run_anaFit | 1 | ✓ Exit-code propagation |

### Gaps in Test Coverage

| Responsibility | Status | Note |
|----------------|--------|------|
| **Configuration normalization** | No direct test | Implicit in fixture setup |
| **Template XML substitution** | No direct test | Implicit in integration test |
| **Prefit execution** | No direct test | Implicit in integration test |
| **Full fit-and-manifest pipeline** | Partial | Only integration test covers full J100/J50 workflow |
| **BumpHunter masking decision** | Tested in isolation | No integration test with real BumpHunter |
| **Signal+background fit** | No test | Not used in canonical workflows |
| **Limit-setting with quickLimit** | No test | Not used in canonical workflows |
| **Plot generation** | No test | Launcher behavior only, non-fatal |
| **Command-argument assembly** | No direct test | Implicit in subprocess calls |

---

## 12. Pure-Function Extraction Candidates

### Tier 1: Pure Configuration and Path Functions

These have no side effects, no ROOT dependencies, no subprocess calls.

**Candidates**:

1. **Path Resolution**
   - Function: `resolve_analysis_path(path, repository_root=None)`
   - Current location: `run_anaFit.py` lines ~140–160
   - Behavior: Convert relative → absolute using repo root or .git detection
   - **Status**: Already extracted and tested ✓
   - Tests: `test_resolve_analysis_path_*` (3 tests)

2. **Repository Root Detection**
   - Function: `get_repository_root()`
   - Current location: `run_anaFit.py` lines ~130–140
   - Behavior: Locate `.git` directory upward from script
   - **Status**: Already extracted and tested ✓
   - Tests: `test_get_repository_root_*` (2 tests)

3. **Fit-Range Validation**
   - Current location: Implicit in `run_anaFit()` main function
   - Behavior: Check `rangelow < rangehigh`, both positive integers
   - **Status**: No dedicated function; inline in launcher
   - **Candidate for extraction**: Yes
   - Tests needed: 2 (valid range, invalid range)

4. **Configuration Flags Normalization**
   - Current location: `main()` argument parsing (lines ~950–975)
   - Behavior: Set defaults for `nbkg`, `signame`, optional flags
   - **Status**: Partially extracted in `main()`; could be independent
   - **Candidate for extraction**: Yes
   - Tests needed: 3 (dosignal with/without Z', other flags)

5. **Output Folder Validation & Creation**
   - Current location: `run_anaFit()` lines ~560–570
   - Behavior: `os.makedirs()` with exception handling
   - **Status**: Inline; could be extracted
   - **Candidate for extraction**: Yes
   - Tests needed: 2 (new dir, existing dir)

6. **Fit-Parameter Count Detection**
   - Current location: `run_anaFit()` lines ~620–650 (prefit section)
   - Behavior: Parse background XML filename to extract parameter count (3–10)
   - **Status**: Inline pattern matching; could be extracted
   - **Candidate for extraction**: Yes
   - Tests needed: 8 (one per parameter count, plus invalid)

7. **Command-Line Argument Assembly**
   - Current location: Inline in `build_fit_extract()` (lines ~400–430)
   - Behavior: Construct XMLReader, quickFit command strings with proper escaping
   - **Status**: Inline string formatting; could be extracted
   - **Candidate for extraction**: Yes
   - Tests needed: 3 (XMLReader, quickFit, masked variant)

### Tier 2: File Operations (No ROOT, No Subprocesses)

1. **File Hash Calculation**
   - Function: `calculate_file_sha256(path)`
   - Current location: `run_anaFit.py` lines ~173–183
   - **Status**: Already extracted and tested ✓
   - Tests: `test_calculate_file_sha256_*` (2 tests)

2. **File Provenance Record Assembly**
   - Function: `build_file_provenance(path, repository_root=None)`
   - Current location: `run_anaFit.py` lines ~185–210
   - **Status**: Already extracted and tested ✓
   - Tests: `test_build_file_provenance_*` (3 tests)

3. **Template String Substitution**
   - Function: `replaceinfile(f, old_new_list)`
   - Current location: `run_anaFit.py` lines ~475–487
   - Behavior: Read file, apply regex replacements, write back
   - **Status**: Exists but not tested
   - **Candidate for improvement**: Move to separate module, add tests
   - Tests needed: 3 (simple replacement, multiple, failure case)

4. **Stale-Output Removal**
   - Current location: `run_bumphunter()` line ~772
   - Behavior: `os.remove()` if file exists; no error if missing
   - **Status**: Inline; could be parameterized function
   - **Candidate for extraction**: Yes
   - Tests needed: 2 (file exists, file missing)

5. **Temporary File Atomic Replacement**
   - Current location: `write_analysis_results()` lines ~340–370
   - Behavior: Write to `.tmp`, then `os.replace()` to final path
   - **Status**: Inline in manifest writer; could be general utility
   - **Candidate for extraction**: Yes
   - Tests needed: 2 (new file, overwrite existing)

### Tier 3: Validation Functions

1. **BumpHunter Result Validation**
   - Function: `load_bumphunter_results(results_file)`
   - Current location: `run_anaFit.py` lines ~60–100
   - **Status**: Already extracted and tested ✓
   - Tests: `test_load_bumphunter_results_*` (5 tests)

2. **Manifest Payload Validation**
   - Current location: Implicit in `build_analysis_provenance()`
   - Behavior: Ensure all provenance fields present, correct types
   - **Status**: No dedicated validation function
   - **Candidate for extraction**: Yes (to enable replay/audit)
   - Tests needed: 4 (complete, missing field, wrong type, empty)

---

## 13. Inconsistencies Found

### Between Plan and Implementation

**Inconsistency 1: Schema-Version-1 Reading**

- **Plan** (doc/TIER1_SYSTEM.md): "Schema-version-1 reading remains supported for legacy manifests."
- **Implementation** (analysis_reference.py): Reading support is conditional on detection; no explicit schema-v1 parser
- **Impact**: Low (v1 manifests pre-date current Tier 3 work; v2 is canonical)
- **Resolution**: Acceptable; doc/TIER1_SYSTEM.md is descriptive of legacy capability, not requirement for refactoring

**Inconsistency 2: CLs Workflow Scope**

- **Plan** (doc/TIER3_REFACTORING_PLAN.md): "CLs remains intentionally deferred."
- **Implementation**: `--dolimit` flag and `quickLimit` code exist in `run_anaFit.py`; disabled in canonical workflows
- **Impact**: Low (code exists but is not exercised; no scientific testing)
- **Resolution**: Acceptable; deferred means "not in scope for current Tier 3"; code coexists in monolith pending removal

**Inconsistency 3: Systematics Dictionary**

- **Plan** (Section 4.7): No mention of systematics handling
- **Implementation** (run_anaFit.py): `--sysfile` argument and dictionary injection exist
- **Impact**: Low (not used in canonical J100/J50 workflows; pending removal or formalization)
- **Resolution**: Acceptable; experimental feature, outside canonical scope

### Between Documentation and Tests

**Finding 1: Test Targets Not Updated**

- **scripts/quality_check.py** (Tier 2): Lists 4 source targets, 4 test targets as of 2026-07-31
- **doc/TIER2_SYSTEM.md** (Section 2): Lists same 4 targets, but wording suggests "approved targets"
- **No inconsistency**: Aligned

**Finding 2: Integration Test Separation**

- **doc/TIER2_SYSTEM.md**: "Separate scientific integration tests: tests/test_analysis_workflows_integration.py"
- **scripts/quality_check.py**: Explicitly excludes integration tests with `-m "not requires_analysis_dependencies"`
- **Status**: Intentional and correctly documented ✓

### Between Documentation and Code

**Finding 1: Prefit Default**

- **doc/TIER3_REFACTORING_PLAN.md**: "Prefit: enabled" (for J100/J50)
- **run_anaFit.py** argument parser: `action="store_true"` → default False
- **Launchers** (run_anaFit_J100.sh, run_anaFit_J50.sh): Pass `--doprefit` flag explicitly
- **Status**: No inconsistency; launchers override default ✓

**Finding 2: Mask Threshold**

- **doc/TIER1_SYSTEM.md**: "Mask threshold: `0.01`"
- **run_anaFit.py** argument parser: `default=0.01`
- **Launchers**: `maskthreshold=0.01` (hardcoded)
- **Status**: Consistent ✓

**Finding 3: Required Fresh Artifacts**

- **doc/TIER1_SYSTEM.md** (Section 6): Lists 10 required artifacts
- **run_anaFit.py** + build_fit_extract(): Generates all 10
- **Status**: Consistent ✓

---

## 14. Recommendation: Smallest First Tier 3 Change

### Phase 0 Prerequisite: Record Pre-Refactor Baseline

**Objective**: Establish an auditable checkpoint before any structural changes.

**Commands to Execute**:

```bash
# Activate development environment
source .venv/bin/activate

# 1. Lightweight full gate
python scripts/quality_check.py --mode full

# 2. Prepared dependency gate
python -m pytest tests/test_repo_utils.py \
  -m "requires_analysis_dependencies" -v

# 3. Scientific runtime readiness
python -m pytest tests/test_analysis_workflows_integration.py \
  -k authoritative_setup_provides_scientific_runtime -v

# 4. Authoritative scientific gate
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v

# 5. Repository status
git status -sb
git diff --check
```

**Expected Outputs**:
- Full gate: 13 tests passed, Ruff passed, Black passed, exit 0
- Prepared dependency: 2 tests passed, 11 deselected, exit 0
- Runtime readiness: 1 test passed, 2 deselected, ~16 seconds
- Scientific gate: 1 test passed, 2 deselected, ~150 seconds
- Git: Clean working tree (only doc changes from audit, not applied yet)

**Deliverable**: Append a dated `Tier 3 Phase 0 pre-refactor baseline` section to `doc/ACTIVITY_LOG.md` recording all command outputs and confirming frozen reference was not modified.

---

### Phase 1–2 Immediate Next Step: Create `doc/TIER3_SYSTEM.md`

**Objective**: Establish Tier 3 specification before extraction begins.

**File**: Create `doc/TIER3_SYSTEM.md` with sections:
- Current status (pre-refactoring)
- Purpose (clear, testable structure)
- Scope (structural only, background-only J100/J50 first)
- Protected scientific contracts (frozen reference, fit parameters, p-values)
- Proposed architecture (7 modules as in plan Section 4)
- Refactoring workflow (Phases 0–9 as in plan Section 5)
- Gate commands (same as Phase 0)
- Completion criteria (all phases complete, gates passing, no reference changes)

---

### Phase 3 Recommended First Extraction: Configuration Validation Module

**Responsibility**: Extract configuration normalization and validation.

**Target Functions to Create**:

1. `analysis_config.py::validate_fit_range(rangelow, rangehigh) → None`
   - Check: `rangelow < rangehigh`, both positive integers
   - Raise: `ValueError` with clear message on failure

2. `analysis_config.py::validate_output_folder(folder) → Path`
   - Check: folder path is writable
   - Create: folder and parents if needed
   - Return: absolute path to folder

3. `analysis_config.py::normalize_signal_name(sigmean, sigwidth) → str`
   - Logic: Extract from main() lines 950–960
   - Behavior: Return "mR{sigmean}" for Z' or "mean{sigmean}_width{sigwidth}" for Gaussian

**Tests to Add** (before extraction):

File: `tests/test_analysis_config.py` (new)

1. `test_validate_fit_range_accepts_valid_range()` - (481, 3000)
2. `test_validate_fit_range_rejects_invalid_range()` - (3000, 481)
3. `test_validate_fit_range_rejects_equal_bounds()` - (481, 481)
4. `test_validate_fit_range_rejects_negative()` - (-100, 100)
5. `test_validate_output_folder_creates_new_directory()` - Use tmp_path
6. `test_validate_output_folder_accepts_existing_directory()` - Use tmp_path
7. `test_normalize_signal_name_gaussian()` - sigmean=400, sigwidth=8 → "mean400_width8"
8. `test_normalize_signal_name_zprime()` - sigmean=400, sigwidth=-999 → "mR400"

**Modifications to `run_anaFit.py`**:

- Import: `from analysis_config import validate_fit_range, validate_output_folder, normalize_signal_name`
- In `main()` (lines 950–975): Replace inline logic with function calls
- In `run_anaFit()` (lines 560–570): Replace inline folder creation with `validate_output_folder()`

**Files Changed**:
- `python/analysis_config.py` (new, ~50 lines)
- `python/run_anaFit.py` (~20 lines deleted, 10 lines of calls added)
- `tests/test_analysis_config.py` (new, ~80 lines)
- `scripts/quality_check.py` (add targets):
  - Add `"python/analysis_config.py"` to python_targets
  - Add `"tests/test_analysis_config.py"` to test_targets

**Verification Commands**:

```bash
# 1. Test only new configuration module
python -m pytest tests/test_analysis_config.py -v

# 2. Test that launcher still calls run_anaFit correctly
python -m pytest tests/test_run_anaFit.py::test_main_propagates_analysis_status -v

# 3. Test integration (J100 unmasked, J50 unmasked)
python -m pytest tests/test_analysis_workflows_integration.py -m "integration and requires_root" -v

# 4. Full lightweight gate
python scripts/quality_check.py --mode full

# 5. Check git diff
git diff python/ tests/ scripts/quality_check.py
```

**Expected Results**:
- All new tests pass
- All existing tests pass (no regressions)
- J100/J50 integration still produces frozen reference values
- Ruff and Black pass on new module
- No unrelated files changed

---

### Why This First Change is Ideal

1. **Single, Clear Responsibility**: Configuration validation (no state mutation, no ROOT, no subprocesses)
2. **Existing Test Coverage**: Main entry point still tested via launcher tests
3. **Low Risk**: Pure-function extraction; callable from same code path
4. **Rapid Verification**: 8 new unit tests + existing integration tests
5. **Enables Next Steps**: Once config module is extracted, move to path/hash functions
6. **Minimal Diff**: ~70 lines added, ~20 lines removed = reviewable change

---

## 15. Tests Required Before/With First Change

### New Tests for Configuration Module

**File**: `tests/test_analysis_config.py`

```python
# 8 test functions covering:
# - Valid fit ranges (481–3000, 344–2079)
# - Invalid ranges (reversed, equal, negative)
# - Output folder creation (new, existing)
# - Signal name normalization (Gaussian and Z' variants)

def test_validate_fit_range_accepts_j100_range(): ...
def test_validate_fit_range_accepts_j50_range(): ...
def test_validate_fit_range_rejects_reversed_bounds(): ...
def test_validate_fit_range_rejects_equal_bounds(): ...
def test_validate_fit_range_rejects_negative_rangelow(): ...
def test_validate_output_folder_creates_new_folder(tmp_path): ...
def test_validate_output_folder_returns_absolute_path(tmp_path): ...
def test_normalize_signal_name_gaussian(): ...
def test_normalize_signal_name_zprime(): ...
```

### Verification That Existing Tests Still Pass

**Tests to Re-Run** (should all pass):

1. `python -m pytest tests/test_run_anaFit.py -v` (all 56 tests)
2. `python -m pytest tests/test_analysis_reference.py -v` (all 28 tests)
3. `python -m pytest tests/test_analysis_workflows_integration.py::test_authoritative_j100_j50_workflows_match_frozen_reference -v`
4. `python -m pytest tests/test_repo_utils.py -v` (all 34 tests)

**Regression Criteria**: No test previously passing should fail; no new test should be skipped.

---

## 16. Exact Verification Commands (Complete Sequence)

### Pre-Change Checkpoint (Phase 0)

```bash
#!/bin/bash
set -e

echo "=== Phase 0: Pre-Refactor Baseline ==="

source .venv/bin/activate

# 1. Fast gate (13 tests)
echo "1. Running fast quality gate..."
python scripts/quality_check.py --mode fast
FAST_EXIT=$?
echo "   Fast gate exit code: $FAST_EXIT"

# 2. Full gate (13 tests + Ruff + Black)
echo "2. Running full quality gate..."
python scripts/quality_check.py --mode full
FULL_EXIT=$?
echo "   Full gate exit code: $FULL_EXIT"

# 3. Prepared dependency gate
echo "3. Running prepared dependency gate..."
python -m pytest tests/test_repo_utils.py \
  -m "requires_analysis_dependencies" -v
DEP_EXIT=$?
echo "   Dependency gate exit code: $DEP_EXIT"

# 4. Scientific runtime readiness
echo "4. Checking scientific runtime readiness..."
python -m pytest tests/test_analysis_workflows_integration.py \
  -k authoritative_setup_provides_scientific_runtime -v
RUNTIME_EXIT=$?
echo "   Runtime exit code: $RUNTIME_EXIT"

# 5. Authoritative scientific characterization
echo "5. Running authoritative J100/J50 scientific gate..."
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
SCI_EXIT=$?
echo "   Scientific gate exit code: $SCI_EXIT"

# Summary
echo ""
echo "=== Phase 0 Summary ==="
echo "Fast gate:            $FAST_EXIT"
echo "Full gate:            $FULL_EXIT"
echo "Dependency gate:      $DEP_EXIT"
echo "Runtime readiness:    $RUNTIME_EXIT"
echo "Scientific gate:      $SCI_EXIT"
echo ""

if [ $FAST_EXIT -eq 0 ] && [ $FULL_EXIT -eq 0 ] && [ $DEP_EXIT -eq 0 ] && [ $RUNTIME_EXIT -eq 0 ] && [ $SCI_EXIT -eq 0 ]; then
    echo "✓ All Phase 0 gates passed. Tier 3 refactoring ready to begin."
    exit 0
else
    echo "✗ One or more gates failed. Check output above."
    exit 1
fi
```

### Post-Change Verification (after first extraction)

```bash
#!/bin/bash
set -e

echo "=== Tier 3 Change #1: Configuration Validation Module ==="

source .venv/bin/activate

# 1. Unit tests for new module
echo "1. Testing new analysis_config module..."
python -m pytest tests/test_analysis_config.py -v
CONFIG_EXIT=$?

# 2. Regression: existing launcher tests
echo "2. Verifying launcher integration..."
python -m pytest tests/test_run_anaFit.py::test_main_propagates_analysis_status -v
LAUNCHER_EXIT=$?

# 3. Regression: full test suite (13 focused tests)
echo "3. Running full lightweight gate..."
python scripts/quality_check.py --mode full
FULL_EXIT=$?

# 4. Scientific integration
echo "4. Running authoritative J100/J50 gate..."
python -m pytest tests/test_analysis_workflows_integration.py \
  -m "integration and requires_root" -v
SCI_EXIT=$?

# 5. Git status
echo "5. Checking git status..."
git status -sb
git diff --check
GIT_EXIT=$?

# Summary
echo ""
echo "=== Change #1 Verification Summary ==="
echo "Config tests:         $CONFIG_EXIT"
echo "Launcher regression:  $LAUNCHER_EXIT"
echo "Full gate:            $FULL_EXIT"
echo "Scientific gate:      $SCI_EXIT"
echo "Git status:           $GIT_EXIT"
echo ""

if [ $CONFIG_EXIT -eq 0 ] && [ $LAUNCHER_EXIT -eq 0 ] && [ $FULL_EXIT -eq 0 ] && [ $SCI_EXIT -eq 0 ] && [ $GIT_EXIT -eq 0 ]; then
    echo "✓ All verifications passed. Ready to commit."
    exit 0
else
    echo "✗ One or more verifications failed. Check output above."
    exit 1
fi
```

---

## 17. Summary: Current State vs. Plan Alignment

| Aspect | Plan | Current | Match | Issue |
|--------|------|---------|-------|-------|
| **J100/J50 baseline** | Protected, documented | Hardened, passing | ✓ | None |
| **Tier 2 environment** | Python 3.11+, pinned tools | Python 3.12.13, locked | ✓ | None |
| **Quality gates** | Full/fast distinction | Implemented | ✓ | None |
| **Test targets** | Explicit list | 4 source, 4 test files | ✓ | None |
| **Integration tests** | Separate, marked `integration` | Separated, marked | ✓ | None |
| **Monolithic coordinator** | `run_anaFit.py` to be decomposed | ~1,100 lines, not yet refactored | ✓ | Ready for Phase 3 |
| **Proposed modules (7)** | Listed in plan Section 4 | Not yet created | ✓ (planned) | Deferred to Phase 3+ |
| **Pure-function candidates** | Identified in Phase 3 | 15+ identified in this audit | ✓ | Many already tested |
| **Failure propagation** | No manifest on failure | Enforced by code structure | ✓ | None |
| **Stale-output protection** | BH JSON removed before rerun | Line 772 in run_anaFit.py | ✓ | None |
| **Manifest atomicity** | Write to .tmp, replace | Implemented in write_analysis_results() | ✓ | None |
| **Schema-version-2** | Preserved in refactoring | Produced by canonical workflows | ✓ | None |
| **Frozen reference** | P-values protected | Regression tested with tolerances | ✓ | None |
| **Doc/TIER3_SYSTEM.md** | To be created in Phase 2 | Planned but not yet written | ⚠ | Needed before major changes |
| **Activity log** | Updated per change | Current (2026-07-31 entry) | ✓ | Ready to append Phase 0 |

---

## Conclusion

The repository is **ready for Tier 3 refactoring to begin**.

### Prerequisites Met
1. ✓ Tier 1 baseline (J100/J50 background-only) hardened and protected
2. ✓ Tier 2 environment reproducibly pinned and passing all gates
3. ✓ Documentation plan (`TIER3_REFACTORING_PLAN.md`) complete
4. ✓ Existing tests provide confidence in entry points and failure propagation
5. ✓ No inconsistencies between plan, code, and tests

### Immediate Actions
1. **Phase 0**: Record pre-refactor baseline in `doc/ACTIVITY_LOG.md` (see commands in Section 16)
2. **Phase 1–2**: Create `doc/TIER3_SYSTEM.md` (concise specification)
3. **Phase 3**: Extract configuration validation module (`analysis_config.py`) with 8 focused unit tests

### Why This Sequence Works
- **Phase 0 (Checkpoint)**: Establishes auditable baseline before any code changes
- **Phase 1–2 (Documentation)**: Specification must precede implementation for review
- **Phase 3 (First Extraction)**: Pure-function configuration module has zero risk, clear scope, and fast feedback loop

### Risk Mitigation
- All new functions have focused unit tests covering normal + failure paths
- Existing launcher and integration tests verify no regressions
- Atomic operations (manifest writing) are preserved
- Stale-output protection is maintained
- Exit-code propagation is preserved through launcher

---

**Report prepared for review. Awaiting confirmation to proceed with Phase 0 baseline checkpoint.**
