# Stop a previous run's output being read as this run's

**Written** 2026-09-21. **Branch** `claude-skills`. Resolves
[KNOWN_ISSUES.md](../KNOWN_ISSUES.md) issue 49.

## The problem

Run folders are reused — `folder` is a function of `rangelow`, `rangehigh` and `pars`, and
`run_anaFit.py` only `os.makedirs()` it — and nothing deletes what a previous run left there. Three
readers then treat leftovers as this run's:

- Both Run 2 drivers select the postfit file to plot on the **existence** of
  `PostFit_*_bkgOnly_masked.root`. A run that masked before and now passes p(chi2) unmasked writes
  no masked file, finds the old one, and draws `postFit.pdf` from it under the label
  `masked fit - BumpHunter window blinded`.
- `plot_postfit.cpp` opens the masked `PostFit`/`FitParameters` files if they exist and draws the
  red "masked" curve from whatever it finds, so `post_fit.pdf` overlays a previous run's fit on
  this one's.
- `plot_postfit.cpp` also reads `BHresults.json` whenever it is present, so a run that never
  invoked BumpHunter is stamped with an earlier run's global p-value and mask window.

The same hole swallows a **crashed** run. Both drivers plot after `run_anaFit.py` returns — that is
deliberate, the plots are the diagnostics — so a run that dies in `execute_checked()` leaves the
previous run's `PostFit_*.root` in place and the driver plots it. The masked case is the one the
review found; it is not the only one.

This is the upper triage tier in [CLAUDE.md](../CLAUDE.md)'s terms: the analysis runs to completion
and puts numbers in front of a reader that do not belong to it. It is fixed rather than recorded
for a second reason — the drivers' own comment, added by issue 48, says they "now plot whichever
fit was accepted", and in this case they do not.

## Why the review's one-line fix is not the fix

The Copilot comment proposes replacing `-f` with `-nt`, i.e. selecting the masked file when it is
newer than the unmasked one. It is correct for the drivers' own selection and it is one line, but:

- it leaves `plot_postfit.cpp` and `BHresults.json` reading stale files, which is two of the three
  readers;
- it does nothing for the crashed-run case, where **both** files are stale and `-nt` picks between
  them quite happily;
- it makes which fit gets plotted depend on filesystem timestamps, which do not survive a copy to
  EOS, an `rsync` or a tarball — and `OUT_DIR` exists precisely so these folders can live on EOS.

The defect is that the run folder is not the run's. Fix that instead.

## Design

At the start of `run_anaFit()`, delete **exactly the files this invocation is about to produce** —
by name, computed from the same expressions that create them. No directory wipe, no globbing.

**`shutil.rmtree(folder)` is rejected, and the reason is concrete.** `scripts/run_anaFitLoop.sh`
takes one `-r runfolder` and is invoked once per (mass, width, pseudodata), with `outputfile`
parameterised by mass and width — `FitResult_anaFit_fivePar_pseudodata${p}_mean${sigmean}_width${sigwidth}.root`
— inside a *shared* folder. A directory wipe would delete every previous mass's results. Deleting
by name cannot: a name this invocation will write is a name it would have overwritten anyway.
`--folder` is also arbitrary user input, and `rmtree` on it is a hazard out of proportion to the
bug.

The list, each entry from the line that creates it:

| product | expression |
|---|---|
| top card | `{folder}/dijetTLA_fromTemplate.xml`, or `…_mR{sigmean}.xml` when `sigwidth == -999` |
| category card | `{folder}/category_dijetTLA_fromTemplate.xml`, same `mR` variant |
| background card | `{folder}/background_dijetTLA_fromTemplate.xml` |
| signal card | `{folder}/signal_dijetTLA_fromTemplate.xml` |
| workspace | `wsfile`, and `wsfile` with `.root` → `.pdf` (XMLReader's plot) |
| fit products | `outputfile`, plus its `FitResult` → `PostFit` / `FitParameters` twins, and `quickFitLog…​.log` / `edm…​.pdf` from `build_fit_extract` |
| limits | `outputfile` with `FitResult` → `Limits`, when `dolimit` |
| masked twins | the top and category cards with `.xml` → `_masked.xml`; `wsfile` and `outputfile` with `.root` → `_masked.root`, each with the derivatives above |
| BumpHunter | `{folder}/BHresults.json` |
| driver plots | `{folder}/postFit.pdf`, `{folder}/post_fit.pdf` |

The masked twins are deleted **unconditionally**, whether or not this run will mask. That is the
whole point: their presence is what the readers take as a signal.

`AnaWSBuilder.dtd` is deliberately kept — a symlink recreated only when absent, carrying no run
state.

The two driver plots are in the list even though the drivers write them, not `run_anaFit.py`. They
are derived from files this function owns, they live in its folder, and leaving them out would mean
a crashed run keeps a `postFit.pdf` that looks current. Deleting them makes that case fail closed:
no plot rather than a wrong one.

**Decided 2026-09-21 by the repository owner, in answer to this plan's one open question:** the
two plots go in the list — "if a run fails there should be nothing left". Taken literally that is
not quite what deleting at the *start* of the run achieves, and the difference is deliberate. A run
that dies midway keeps what it wrote before dying, which in practice is `quickFitLog_*.log` and
`edm_*.pdf` — the only record of why the fit failed, and the diagnostics issue 38 explicitly chose
to keep on a failure. What a failed run no longer leaves is anything that reads as a *result*: the
previous run's `PostFit_*`/`FitResult_*` are gone, no PostFit file is written, `plotPostFit.py`
therefore fails, and there is no plot at all rather than a plot of something else.

**Why here and not in the drivers.** Three readers, one folder, one place that creates it. Putting
it in `run_anaFit()` also covers `run_anaFit.sh`, `run_anaFit_syst.sh` and `run_anaFitLoop.sh`
without touching them.

## Sections

### §1 — The name list and its test

New `python/run_outputs.py`, about forty lines: `derived_outputs(folder, wsfile, outputfile,
sigmean, sigwidth, dolimit)` returning the list above as paths. Pure string work, **no ROOT
import**, so it is testable with the repository's `.venv` pytest.

New `tests/test_run_outputs.py`, asserting:

- For J50, `set(derived_outputs(…)) == set(baseline_J50["directory_listing"]) - {"AnaWSBuilder.dtd"}`
  — the J50 baseline records a run that masked, so its listing is the complete product set.
- For J100, whose recorded run never masked, the listing minus the dtd is a **subset** of the
  derived list, and the difference is exactly the masked twins.
- The `sigwidth == -999` branch produces the `mR{sigmean}` card names.
- Every returned path is inside `folder`.

Both baselines are committed, so the test ties the deletion list to two real runs and fails if a
product is added later without being added here — which is the failure mode that would quietly
reintroduce this bug.

Nothing calls the helper yet. Zero behaviour change; committable on its own.

### §2 — Call it, verify it, document it

`run_anaFit()` calls `derived_outputs()` immediately after the `os.makedirs` block and removes each
path, ignoring `FileNotFoundError`, printing one line with the count. Then:

- `KNOWN_ISSUES.md` issue 49 → **Fixed**, entry kept as the record of what was wrong.
- A `CHANGELOG.md` entry.
- `doc/IMPROVEMENTS.md`: the "Fixed … Both drivers now plot whichever fit was accepted" paragraph
  gains the freshness half, since that claim was only conditionally true until this change.
- The comment above the selection block in both Run 2 drivers.

## Verification

Run in this order; step 1 is what makes the rest meaningful.

1. **Show the bug first, on the current code.** J100 into a scratch `OUT_DIR`; plant an empty
   `PostFit_anaFit_sixPar_bkgOnly_masked.root` and a `BHresults.json` in its folder; re-run.
   Expected today: `postFit.pdf` is drawn from the planted file and labelled
   `masked fit - BumpHunter window blinded`. A fix that cannot be shown to change a demonstrated
   failure is not verified.
2. Apply §1 and §2, repeat step 1. Expected: both planted files gone, label reads `unmasked fit`.
3. J50 into scratch: the masked set is still produced, `postFit.pdf` still reads
   `masked fit - BumpHunter window blinded`, `post_fit.pdf` still draws both fits.
4. `python tests/repro.py check` on both analyses, **baselines untouched**. Expected PASS with
   identical `directory_listing`s: every file deleted at the start is rewritten by the same run.
5. `.venv/bin/pytest tests/test_run_outputs.py`.
6. Confirm `run/run_481_3000_sixPar/` and `run/run_J50_302_2997_sixPar/` are untouched throughout
   (mtimes predate the work) — all runs go to `OUT_DIR`, never the recorded directories.

If step 4 changes a listing, **stop and report it**: that means the product set is not what §1's
test says it is, and re-cutting a baseline to accommodate it is the one operation that could bless
a real regression.

## What this does not do

- **Issue 23** — `bump.png` and `BH_statistics.png` written to the repository root by
  `FindBHWindow.py`. A different directory and a 2021 fit-path write; recorded separately and left.
- **Issue 47** — the drivers' failure banner. Unrelated, still open.
- **No freshness labelling in `plot_postfit.cpp`.** Once the folder holds only this run's output
  there is nothing to distinguish, and issue 44's hardcoded luminosity stays open on its own terms.
- **No `--keep-old` escape hatch.** Nothing in the repository wants one; add it if a workflow
  appears that reruns part of a fit into a folder it means to keep.
- **No baseline re-cut**, under any outcome.
