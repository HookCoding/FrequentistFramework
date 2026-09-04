# Full execution trace: `scripts/run_anaFit_J100.sh` -> output

This traces one complete, real invocation of the J100 launcher -
`scripts/run_anaFit_J100.sh` with its committed defaults (`FIT_PARS=six`,
`sigmean=400`, `dosignal=0`, `dolimit=0`, `doprefit=1`,
`maskthreshold=0.01`) - from shell script to the last file it writes,
listing every file it executes along the way. It then classifies each
file against `doc/TIER3_SYSTEM.md`'s decomposition-and-testing system:
part of it, legitimately outside its stated scope, or a different
category entirely (third-party code). It closes with one defect found
and fixed while doing this trace (`python/createBinning.py`'s syntax
error).

This document does not re-describe the seven `run_anaFit.py` modules or
the plotting layer in detail - `doc/TIER3_SYSTEM.md` already does that
authoritatively. It exists to answer a narrower question `TIER3_SYSTEM.md`
doesn't: *of everything a real J100 run actually touches, what fraction
sits inside the Tier 3 system versus outside it, and which specific
outside-it files are on the hot path* (as opposed to the ~40 other
untouched scripts under `python/` that a J100 run never calls at all).

## 1. The trace

```
scripts/run_anaFit_J100.sh
|
+-- . scripts/setup_buildAndFit.sh          [sets up ROOT/RooFit env + PATH/LD_LIBRARY_PATH
|                                             for the XMLReader/quickFit binaries; shell, no Python]
|
+-- python/run_anaFit.py --datafile ... --doprefit   [entry point]
    |
    +-- run_cli.build_arg_parser() / normalize_signal_name()
    +-- main(args) -> run_anaFit(...)
        |
        +-- run_provenance.build_analysis_provenance(...)
        |     +-- get_repository_root() -> repo_utils.find_repo_root()
        |     +-- calculate_file_sha256(...) / get_git_revision(...)
        |     +-- collect_scientific_runtime()   [deferred `import ROOT`]
        |
        +-- run_templates.prepare_run_templates(...)
        |     +-- _stage_xml_templates(...)      [copies/edits the 4 XML templates]
        |           +-- doprefit=1, so: _seed_prefit_parameters(...)
        |                 +-- from PreFit import PreFitter   <-- python/PreFit.py (*)
        |
        +-- run_fit.build_fit_extract(...)                    [called once for the global fit]
        |     +-- validates fitresultfile's "FitResult" basename contract
        |     +-- execute_required: xmlAnaWSBuilder/build/bin/XMLReader     <-- submodule binary
        |     +-- execute_required: quickFit/build/quickFit                <-- submodule binary
        |     +-- execute: python plot_edm.py <quickFitLog> <edm>.pdf      <-- Tier 3 (plotting layer)
        |     +-- [only if Input/data/dijetisrTLA/mjjResolutionBinning_481.root is missing:]
        |     |     execute: python3 python/createBinning.py -s 481 ...    <-- python/createBinning.py (*)(!)
        |     +-- deferred: import ROOT, ExtractPostfitFromWS, ExtractFitParameters
        |     +-- ExtractPostfitFromWS.PostfitExtractor(...).GetPval(...) / .WriteRoot(postfitfile)
        |     |                                                            <-- python/ExtractPostfitFromWS.py (*)
        |     +-- ExtractFitParameters.FitParameterExtractor(...).WriteRoot(parameterfile)
        |                                                                  <-- python/ExtractFitParameters.py (*)
        |
        +-- run_masking.should_mask(pval_global, maskthreshold)            [Tier 3; NaN-safe predicate]
        |     |
        |     +-- [only if the real fit's p(chi2) requires masking - not knowable statically]
        |           run_masking.run_bumphunter(postfitfile, folder)
        |             +-- execute_required: pyBumpHunter/pyBH_env/bin/python3 python/FindBHWindow.py
        |             |                                                    <-- python/FindBHWindow.py (*)
        |             |     (the bump-hunting algorithm itself lives in the external
        |             |      pyBumpHunter submodule, invoked *by* FindBHWindow.py)
        |             +-- run_masking.load_bumphunter_results(...)         [Tier 3]
        |             +-- a second run_fit.build_fit_extract(..., maskrange=...) call
        |                   - re-walks the entire build_fit_extract chain above again,
        |                     this time against the masked workspace/templates
        |
        +-- [dolimit=0 in this script, so the quickLimit branch is never reached here;
        |    it would call the external quickFit submodule's `quickLimit` binary directly
        |    from run_anaFit.py, via execute() - not deferred, not decomposed further]
        |
        +-- run_manifest.write_analysis_results(...) -> analysis_results.json   [Tier 3]
|
+-- [if ANAFIT_SKIP_PLOTS != 1, true for a real run:]
      python python/plotPostFit.py -i PostFit_..._bkgOnly.root -o postFit.pdf   <-- Tier 3 (plotting layer)
      root -l -q plot_postfit.cpp("$folder", "six")                             <-- Tier 3 (plotting layer)
        (reads PostFit_*.root / FitParameters_*.root, writes post_fit.pdf)
```

`(*)` marks a file that does not follow the Tier 3 system (Section 3
below). `(!)` marks the one defect found and fixed while tracing
(Section 5).

**Output artifacts of one unmasked sixPar/bkgOnly J100 run**, all under
`$out_dir/J100/run_481_3000_sixPar/`:
`dijetisrTLA_combWS_sixPar.root`, `FitResult_anaFit_sixPar_bkgOnly.root`,
`quickFitLog_anaFit_sixPar_bkgOnly.log`,
`edm_anaFit_sixPar_bkgOnly.pdf`, `PostFit_anaFit_sixPar_bkgOnly.root`,
`FitParameters_anaFit_sixPar_bkgOnly.root`, `analysis_results.json`,
`postFit.pdf`, `post_fit.pdf`. If masking triggers, add `BHresults.json`
and the six `*_masked.*` siblings of the workspace/fit/postfit/parameter/
log/edm files above.

## 2. Files in this trace that ARE part of the Tier 3 system

Per `doc/TIER3_SYSTEM.md`'s module maps: `python/run_anaFit.py`,
`run_cli.py`, `run_provenance.py`, `run_templates.py`, `run_fit.py`,
`run_masking.py`, `run_manifest.py`, `run_execution.py` (used
transitively by several of the above), `plot_edm.py`,
`python/plotPostFit.py`, `plot_postfit.cpp`. Each is decomposed into
small single-responsibility functions, each has a dedicated test file,
and each is registered in `scripts/quality_check.py`'s `python_targets`/
`test_targets`. Not repeated here - see `doc/TIER3_SYSTEM.md` directly.

## 3. Files in this trace that do NOT follow the Tier 3 system

`doc/TIER3_SYSTEM.md`'s own Scope section already states this boundary
explicitly: Tier 3 covers exactly four files
(`run_anaFit.py`/`plot_edm.py`/`plotPostFit.py`/`plot_postfit.cpp`), and
"every other script under `python/`... remain[s] untouched, as they were
before Tier 3." What follows is the concrete list of which untouched
files actually sit on this specific hot path, with what "untouched"
means for each in practice:

| File | Lines | Decomposition | Dedicated test file | Registered in `quality_check.py`? | Module-level `import ROOT`? |
|---|---|---|---|---|---|
| `python/PreFit.py` | 208 | One `PreFitter` class + a `main()` CLI wrapper (unused from this call path) | None | No | Yes |
| `python/ExtractPostfitFromWS.py` | 460 | 3 free helper functions + one large `PostfitExtractor` class + `main()` | None | No | Yes (`import ROOT` and `from ROOT import *`) |
| `python/ExtractFitParameters.py` | 108 | One `FitParameterExtractor` class + `main()` | None | No | Yes (`import ROOT` and `from ROOT import *`) |
| `python/createBinning.py` | 32 | No functions at all - a flat top-level script | None | No | Yes - **and it does not parse** (Section 5) |
| `python/FindBHWindow.py` | 113 | One `NpEncoder` helper class + `main()` | None | No | No (delegates to the external `pyBumpHunter` submodule) |
| `scripts/setup_buildAndFit.sh` | - | Shell, not Python - out of `quality_check.py`'s Python-only scope entirely | None of its own (only exercised indirectly, by being sourced inside other tests) | N/A (shell) | N/A |

"No dedicated test file" is verified, not assumed: every mention of
`PreFit`/`PreFitter`, `ExtractPostfitFromWS`/`PostfitExtractor`,
`ExtractFitParameters`/`FitParameterExtractor`, `createBinning`, or
`FindBHWindow` inside `tests/` is either (a) a `ModuleType`-stub
monkeypatch used to isolate the Tier 3 module actually under test (e.g.
`tests/test_run_fit.py`, `tests/test_run_anaFit.py`,
`tests/test_run_templates.py`), or (b) a literal command-string
assertion inside `tests/test_analysis_workflows_integration.py`'s
end-to-end integration test, which exercises these five files' real
behavior only as an opaque subprocess, not as a unit under test. None of
the five has a `tests/test_<name>.py` of its own the way every Tier 3
module does.

This is a documented, deliberate scope boundary from `doc/TIER3_COMPLETION_PLAN.md`
- not a surprise, and not something this document is proposing to change.
It's recorded here so the boundary is visible against the *actual* call
graph of a real run, not just as an abstract "everything else is
untouched" statement.

## 4. Different category: third-party code (not this repository's)

`xmlAnaWSBuilder/build/bin/XMLReader`, `quickFit/build/quickFit` (and
`quickLimit`, on the `dolimit=1` path not exercised here), and the
`pyBumpHunter` package `python/FindBHWindow.py` delegates its actual
window-finding algorithm to, are all external Git submodules (confirmed
via `.gitmodules`: `xmlAnaWSBuilder`, `quickFit`, `pyBumpHunter`,
`workspaceCombiner`, each pointing at a separate `tofitsch`/`scikit-hep`
GitHub repository). Tier 3 - or any future tier of this repository's own
refactoring plan - has no jurisdiction over them; they are not evaluated
against the Tier 3 system at all.

## 5. Defect found and fixed: `python/createBinning.py` could not run

`python/createBinning.py` did not parse:

```
$ python3 -c "import ast; ast.parse(open('python/createBinning.py').read())"
  File "python/createBinning.py", line 11
    if not tfile or tfile.IsZombie():
IndentationError: unexpected indent
```

Lines 11-15 (the `tfile`/`IsZombie`/`reso_fit` null-checks) were indented
by one leading space relative to every top-level statement around them -
introduced in commit `e6bfd96` ("Revert \"Revert \"First task: implement
reproducibility checking after changes\"\"\"", 2026-07-30). Any invocation
of this script - `python3 python/createBinning.py ...`, exactly how
`run_fit.py`'s `build_fit_extract()` calls it - failed immediately at
compile time, before argument parsing even ran.

**Why this had never surfaced**: `build_fit_extract()` only calls it
conditionally - `if not os.path.exists(binningFileName): execute(...)` -
and both committed fixtures this repository's tests actually exercise
already exist: `Input/data/dijetisrTLA/mjjResolutionBinning_481.root`
(J100's `rangelow=481`) and `mjjResolutionBinning_344.root` (J50's
`rangelow=344`), both tracked in Git. The branch that calls
`createBinning.py` had therefore never executed in the scientific gate,
in CI, or (as far as this repository's committed history shows) in any
verified run.

**Impact had it fired**: a future run using any `rangelow` other than 481
or 344 with no pre-built binning fixture would have hit this. Worse, the
call site uses `execute()`, not `execute_required()` - its return code is
never checked - so the failure would not have stopped the run or raised
an error; it would have silently continued with a missing rebin file,
and failed later inside `PostfitExtractor` (which reads
`rebinfile=Input/data/dijetisrTLA/mjjResolutionBinning_{rangelow}.root`)
with a more confusing ROOT-level error, far from the actual cause.

**Fix**: dedented the five lines back to column 0, matching every other
top-level statement in the file. A pure whitespace change - no other
line was touched.

**Verification performed**:
- `python3 -c "import ast; ast.parse(...)"` now succeeds.
- Ran the fixed script for real, exactly as `run_fit.py` invokes it
  (`python3 python/createBinning.py -s 481 -e 3000 -o <path>`), against a
  synthetic `Input/data/dijetisrTLA/resolutionFits.root` fixture built
  on the fly with a trivial `TF1` named `gsc_mjj_reso_fit` (this repo
  does not commit a real `resolutionFits.root` at all - a separate,
  pre-existing gap, not introduced or fixed here). The script exited 0
  and wrote a real `mjjBinning` `TH1F` with 38 bins spanning exactly
  `[481, 3000]`, confirmed by reading it back with `ROOT.TFile.Open(...)`.
  The synthetic input and the scratch output were both deleted afterward;
  nothing under `Input/` was left changed.
- Reran the scientific gate
  (`tests/test_analysis_workflows_integration.py::test_authoritative_j100_j50_workflows_match_frozen_reference`)
  end to end: 1 passed, 2 deselected, 289.19s, exit code 0 - confirms the
  fix causes zero regression to the real J100/J50 authoritative
  workflows (which don't exercise this branch, since their own fixtures
  are already committed).
- Reran `python scripts/quality_check.py --mode full`: 172 passed, 8
  deselected, Ruff clean, Black clean, exit code 0 (unaffected, since
  `createBinning.py` is not registered in `quality_check.py`'s
  `python_targets` - see Section 3; this fix does not change that).

This fix is scoped to exactly the syntax defect: `createBinning.py`
still has no decomposition into functions, no dedicated test file, and
is still unregistered in `quality_check.py` - it remains outside the
Tier 3 system per Section 3 above, just no longer broken.

## Verification performed

- Every file named above was read directly, not inferred from memory or
  from `doc/TIER3_SYSTEM.md`'s prior descriptions.
- `grep -rn` across `tests/` for each of the five out-of-scope filenames'
  class/module names, confirming every match is a stub or a subprocess
  command-string assertion, never a direct unit test of that file's own
  logic.
- `python3 -c "import ast; ast.parse(...)"` run against all five
  out-of-scope Python files individually; at trace time, only
  `createBinning.py` failed to parse - since fixed, and independently
  verified end to end; see Section 5's own "Verification performed".
- Confirmed both `mjjResolutionBinning_481.root` and
  `mjjResolutionBinning_344.root` are tracked and present in
  `Input/data/dijetisrTLA/`, and that 481/344 match J100's/J50's own
  `rangelow` values in `scripts/run_anaFit_J100.sh`/`run_anaFit_J50.sh`.
- Confirmed via `.gitmodules` and `git submodule status` that
  `xmlAnaWSBuilder`, `quickFit`, `pyBumpHunter`, and `workspaceCombiner`
  are external submodules, not this repository's own code.
